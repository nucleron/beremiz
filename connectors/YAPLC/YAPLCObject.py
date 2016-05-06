#!/usr/bin/env python
# -*- coding: utf-8 -*-

#YAPLC connector, based on LPCObject.py and LPCAppObjet.py
#from PLCManager

if __name__ == "__main__":
    import os
    import sys
    __builtins__.BMZ_DBG = True
    append_path = os.path.dirname(os.path.realpath(__file__)) + "/../../"
    sys.path.append( append_path )

import ctypes
from YAPLCProto import *
from targets.typemapping import  LogLevelsCount, TypeTranslator, UnpackDebugBuffer
from util.ProcessLogger import ProcessLogger

class YAPLCObject():
    def __init__(self, libfile, confnodesroot, comportstr):
        self.TransactionLock = Lock()
        """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
        """
        self.MatchSwitch = True
        """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
        """
        self.PLCStatus = "Disconnected"
        self.libfile = libfile
        self.confnodesroot = confnodesroot
        self.PLCprint = confnodesroot.logger.writeyield
        self._Idxs = []
        try:
            self.connect( libfile, comportstr, 57600, 20 )
        except Exception,e:
            self.confnodesroot.logger.write_error(str(e)+"\n")
            self.SerialConnection = None
            self.PLCStatus = None #ProjectController is responsible to set "Disconnected" status

    def connect(self, libfile, comportstr, baud, timeout):
        self.SerialConnection = YAPLCProto( libfile, comportstr, baud, timeout )

    def HandleSerialTransaction(self, transaction):
        res = None
        failure=None
        #
        if self.SerialConnection is not None:
            try:
                self.PLCStatus, res = \
                    self.SerialConnection.HandleTransaction(transaction)
            except YAPLCProtoError,e:
                if self.SerialConnection is not None:
                    self.SerialConnection.Close()
                    self.SerialConnection = None
                failure = str(transaction) + str(e)
                self.PLCStatus = None #ProjectController is responsible to set "Disconnected" status
            except Exception,e:
                failure = str(transaction) + str(e)
        #
        if failure is not None:
            """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
            """
            if self.MatchSwitch:
                self.confnodesroot.logger.write_warning(failure+"\n")
            """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
            """
        return res

    def StartPLC(self):
        self.TransactionLock.acquire()
        self.HandleSerialTransaction(STARTTransaction())
        self.TransactionLock.release()

    def StopPLC(self):
        self.TransactionLock.acquire()
        self.HandleSerialTransaction(STOPTransaction())
        self.TransactionLock.release()
        return True

    def NewPLC(self, md5sum, data, extrafiles):
        if self.MatchMD5(md5sum) == False:
            self.confnodesroot.logger.write_warning(_("Will now upload firmware to PLC.\nThis may take some time, don't close the program.\n"))
            self.TransactionLock.acquire()
            #Will now boot target
            self.HandleSerialTransaction(BOOTTransaction())
            time.sleep(3)
            failure = None
            #Close connection
            self.SerialConnection.Close()
            #bootloader command
            #data contains full command line except serial port string which is passed to % operator
            #cmd = data % self.SerialConnection.port
            cmd = [token % {"serial_port": self.SerialConnection.port} for token in data]
            #wrapper to run command in separate window
            cmdhead = []
            cmdtail = []
            if os.name in ("nt", "ce"):
                #cmdwrap = "start \"Loading PLC, please wait...\" /wait %s \r"
                cmdhead.append("cmd")
                cmdhead.append("/c")
                cmdhead.append("start")
                cmdhead.append("Loading PLC, please wait...")
                cmdhead.append("/wait")
            else:
                """
                      WARNING: Not tested!!!
                """
                #cmdwrap = "xterm -e %s \r"
                cmdhead.append("xterm")
                cmdhead.append("-e")
            #Load a program
            #try:
                #os.system( cmdwrap % command )
            #except Exception,e:
            #    failure = str(e)
            command = cmdhead + cmd + cmdtail;
            status, result, err_result = ProcessLogger(self.confnodesroot.logger, command).spin()
            """
                    TODO: Process output?
            """
            #Reopen connection
            self.SerialConnection.Open()
            self.TransactionLock.release()

            if failure is not None:
                self.confnodesroot.logger.write_warning(failure+"\n")
                return False
            else:
                self.StopPLC();
                return self.PLCStatus == "Stopped"
        else:
            self.StopPLC();
            return self.PLCStatus == "Stopped"

    def GetPLCstatus(self):
        self.TransactionLock.acquire()
        strcounts = self.HandleSerialTransaction(GET_LOGCOUNTSTransaction())
        self.TransactionLock.release()
        if strcounts is not None and len(strcounts) == LogLevelsCount * 4:
            cstrcounts = ctypes.create_string_buffer(strcounts)
            ccounts = ctypes.cast(cstrcounts, ctypes.POINTER(ctypes.c_uint32))
            counts = [int(ccounts[idx]) for idx in xrange(LogLevelsCount)]
        else :
            counts = [0]*LogLevelsCount
        return self.PLCStatus, counts

    def MatchMD5(self, MD5):
        self.TransactionLock.acquire()
        """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
        """
        self.MatchSwitch = False
        data = self.HandleSerialTransaction(GET_PLCIDTransaction())
        self.MatchSwitch = True
        """
            WARNING: This is dirty hack to prevent beremiz logger deadlock
        """
        self.TransactionLock.release()
        if data is not None:
            return data[:32] == MD5[:32]
        return False

    def SetTraceVariablesList(self, idxs):
        """
        Call ctype imported function to append
        these indexes to registred variables in PLC debugger
        """
        if idxs:
            buff = ""
            # keep a copy of requested idx
            self._Idxs = idxs[:]
            for idx,iectype,force in idxs:
                idxstr = ctypes.string_at(
                          ctypes.pointer(
                           ctypes.c_uint32(idx)),4)
                if force !=None:
                    c_type,unpack_func, pack_func = TypeTranslator.get(iectype, (None,None,None))
                    forced_type_size = ctypes.sizeof(c_type) \
                        if iectype != "STRING" else len(force)+1
                    forced_type_size_str = chr(forced_type_size)
                    forcestr = ctypes.string_at(
                                ctypes.pointer(
                                 pack_func(c_type,force)),
                                 forced_type_size)
                    buff += idxstr + forced_type_size_str + forcestr
                else:
                    buff += idxstr + chr(0)
        else:
            buff = ""
            self._Idxs =  []

        self.TransactionLock.acquire()
        self.HandleSerialTransaction(SET_TRACE_VARIABLETransaction(buff))
        self.TransactionLock.release()

    def GetTraceVariables(self):
        """
        Return a list of variables, corresponding to the list of required idx
        """
        self.TransactionLock.acquire()
        strbuf = self.HandleSerialTransaction(GET_TRACE_VARIABLETransaction())
        self.TransactionLock.release()
        TraceVariables = []
        if strbuf is not None and len(strbuf) >= 4 and self.PLCStatus == "Started":
            size = len(strbuf) - 4
            ctick = ctypes.create_string_buffer(strbuf[:4])
            tick = ctypes.cast(ctick, ctypes.POINTER(ctypes.c_uint32)).contents
            if size > 0:
                cbuff = ctypes.create_string_buffer(strbuf[4:])
                buff = ctypes.cast(cbuff, ctypes.c_void_p)
                TraceBuffer = ctypes.string_at(buff.value, size)
                #Add traces
                TraceVariables.append((tick.value, TraceBuffer))
        return self.PLCStatus, TraceVariables

    def ResetLogCount(self):
        self.TransactionLock.acquire()
        self.HandleSerialTransaction(RESET_LOGCOUNTSTransaction())
        self.TransactionLock.release()

    def GetLogMessage(self, level, msgid):
        self.TransactionLock.acquire()
        strbuf = self.HandleSerialTransaction(GET_LOGMSGTransaction(level, msgid))
        self.TransactionLock.release()
        if strbuf is not None and len(strbuf) > 12:
            cbuf = ctypes.cast(
                          ctypes.c_char_p(strbuf[:12]),
                          ctypes.POINTER(ctypes.c_uint32))
            return (strbuf[12:],)+tuple(int(cbuf[idx]) for idx in range(3))
        return None

    def ForceReload(self):
        raise YAPLCProtoError("Not implemented")

    def RemoteExec(self, script, **kwargs):
        return (-1, "RemoteExec is not supported by YAPLC target!")

if __name__ == "__main__":
    """
    "C:\Program Files\Beremiz\python\python.exe" YAPLCObject.py
    """
    class TestLogger():
        def __init__(self):
            self.lock = Lock()
        def write(self,v):
            self.lock.acquire()
            print(v)
            self.lock.release()
        def writeyield(self,v):
            self.lock.acquire()
            print(v)
            self.lock.release()
        def write_warning(self,v):
            if v is not None:
                self.lock.acquire()
                msg = "Warning: " + v
                print(msg)
                self.lock.release()
        def write_error(self,v):
            if v is not None:
                self.lock.acquire()
                msg = "Warning: " + v
                print(msg)
                self.lock.release()

    class TestRoot:
        def __init__(self):
            self.logger = TestLogger()

    if os.name in ("nt", "ce"):
        lib_ext = ".dll"
    else:
        lib_ext = ".so"

    yaplc_tools_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../../yaplc"

    TstLib = yaplc_tools_dir + "/libYaPySerial" + lib_ext

    TstRoot = TestRoot()
    print "Construct PLC..."
    TstPLC = YAPLCObject(TstLib, TstRoot, "COM10")

    print "New PLC..."
    #bootloader
    yaplc_boot_loader = os.path.join(yaplc_tools_dir, "stm32flash")
    #firmware
    tst_firmware      = os.path.join(yaplc_tools_dir, "test")
    #command
    tst_cmd = "\"" + yaplc_boot_loader + "\" -w "
    tst_cmd += "\"" + tst_firmware + ".hex\"" + " -v -g 0x0 %s \r"
    #call NewPLC
    res = TstPLC.NewPLC("DeadBeaf",tst_cmd,None)
    print( res )

    print "Start PLC..."
    res = TstPLC.StartPLC()
    print( res )

    print "Get PLC status..."
    res = TstPLC.GetPLCstatus();
    print( res )

    print "MatchMD5..."
    res = TstPLC.MatchMD5("aaabbb")
    print( res )

    print "MatchMD5..."
    res = TstPLC.MatchMD5("2c2700c2c543f64e93747d21277de8fdUnknown#Uncnown#Uncnown")
    print( res )

    print "SetTraceVariablesList..."
    idxs = []
    idxs.append((0, "BOOL", 1))
    idxs.append((1, "BOOL", 1))
    res = TstPLC.SetTraceVariablesList(idxs)
    print( res )

    print "GetTraceVariables..."
    res = TstPLC.GetTraceVariables()
    print( res )

    print "GetLogMessage..."
    res = TstPLC.GetLogMessage(0,0)
    print( res )

    print "ResetLogCount..."
    TstPLC.ResetLogCount()

    TstPLC.StopPLC()

    time.sleep(3)
