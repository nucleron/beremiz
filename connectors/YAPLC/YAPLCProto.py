#!/usr/bin/env python
# -*- coding: utf-8 -*-

#YAPLC connector, based on LPCProto.py and LPCAppProto.py
#from PLCManager

import YaPySerial
import exceptions

from threading import Lock
import os
import time
import ctypes
YAPLC_STATUS={0xaa : "Started",
              0x55 : "Stopped"}

class YAPLCProtoError(exceptions.Exception):
        """Exception class"""
        def __init__(self, msg):
                self.msg = msg

        def __str__(self):
                return "Exception in PLC protocol : " + str(self.msg)

class YAPLCProto:
    def __init__(self, libfile, port, baud, timeout):
        # serialize access lock
        self.port = port
        self.baud = baud
        self.timeout = timeout
        # open serial port
        self.SerialPort = YaPySerial.YaPySerial( libfile )
        self.Open()

    def Open(self):
        self.SerialPort.Open( self.port, self.baud, "8N1", self.timeout )
        # start with empty buffer
        self.SerialPort.Flush()

    def HandleTransaction(self, transaction):
        try:
            transaction.SetSerialPort(self.SerialPort)
            # send command, wait ack (timeout)
            transaction.SendCommand()
            current_plc_status = transaction.GetCommandAck()
            if current_plc_status is not None:
                res = transaction.ExchangeData()
            else:
                raise YAPLCProtoError("controller did not answer as expected!")
        except Exception, e:
            msg = "PLC protocol transaction error : "+str(e)
            raise YAPLCProtoError( msg )
        return YAPLC_STATUS.get(current_plc_status,"Broken"), res

    def Close(self):
        if self.SerialPort:
	    try:
                self.SerialPort.Close()
            except Exception, e:
	        msg = "PLC protocol transaction error : "+str(e)
	        raise YAPLCProtoError( msg )
	      
    def __del__(self):
        self.Close()


class YAPLCTransaction:
    def __init__(self, command):
        self.Command = command
        self.SerialPort = None

    def SetSerialPort(self, SerialPort):
        self.SerialPort = SerialPort

    def SendCommand(self):
        # send command thread
        self.SerialPort.Write(chr(self.Command))

    def GetCommandAck(self):
        res = self.SerialPort.Read(2)
        if res is None:
            return None
        if len(res) == 2:
            comm_status, current_plc_status = map(ord, res)
        else:
            raise YAPLCProtoError("YAPLC transaction error - controller did not ack order!")
        # LPC returns command itself as an ack for command
        if(comm_status == self.Command):
            return current_plc_status
        return None

    def SendData(self, Data):
        return self.SerialPort.Write(Data)

    def GetData(self):
        lengthstr = self.SerialPort.Read(4)
        if lengthstr is None:
            raise YAPLCProtoError("YAPLC transaction error - can't read data length!")
        else:
            if len(lengthstr) != 4:
                raise YAPLCProtoError("YAPLC transaction error - data length is invalid: " + str(len(lengthstr) + " !") )

        # transform a byte string into length
        length = ctypes.cast(
            ctypes.c_char_p(lengthstr),
            ctypes.POINTER(ctypes.c_uint32)
            ).contents.value
        if(length > 0):
            data = self.SerialPort.Read(length)
            if data is None:
                raise YAPLCProtoError("YAPLC transaction error - can't read data!")
                return None
            else:
                if len(lengthstr) == 0:
                    raise YAPLCProtoError("YAPLC transaction error - data is invalid!")
                    return None
            return data
        else:
            return None

    def ExchangeData(self):
        pass

class IDLETransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x6a)
    #ExchangeData = YAPLCTransaction.GetData

class STARTTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x61)

class STOPTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x62)

class BOOTTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x63)

class SET_TRACE_VARIABLETransaction(YAPLCTransaction):
    def __init__(self, data):
        YAPLCTransaction.__init__(self, 0x64)
        length = len(data)
        # transform length into a byte string
        # we presuppose endianess of LPC same as PC
        lengthstr = ctypes.string_at(ctypes.pointer(ctypes.c_uint32(length)),4)
        self.Data = lengthstr + data

    def ExchangeData(self):
        self.SendData(self.Data)

class GET_TRACE_VARIABLETransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x65)
    ExchangeData = YAPLCTransaction.GetData

class GET_PLCIDTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x66)
    ExchangeData = YAPLCTransaction.GetData

class GET_LOGCOUNTSTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x67)
    ExchangeData = YAPLCTransaction.GetData

class GET_LOGMSGTransaction(YAPLCTransaction):
    def __init__(self,level,msgid):
        YAPLCTransaction.__init__(self, 0x68)
        msgidstr = ctypes.string_at(ctypes.pointer(ctypes.c_int(msgid)),4)
        self.Data = chr(level)+msgidstr

    def ExchangeData(self):
        #pass
        self.SendData(self.Data)
        return self.GetData()

class RESET_LOGCOUNTSTransaction(YAPLCTransaction):
    def __init__(self):
        YAPLCTransaction.__init__(self, 0x69)

if __name__ == "__main__":

    import os
    __builtins__.BMZ_DBG = True

    """
    "C:\Program Files\Beremiz\python\python.exe" YAPLCProto.py
    """

    if os.name in ("nt", "ce"):
        lib_ext = ".dll"
    else:
        lib_ext = ".so"

    TestLib = os.path.dirname(os.path.realpath(__file__)) + "/../../../yaplc/libYaPySerial" + lib_ext
    TestConnection = YAPLCProto(TestLib,"COM10",57600,20)

    print "Idle transaction..."
    status,res = TestConnection.HandleTransaction(IDLETransaction())
    print status

    print "Start transaction..."
    status,res = TestConnection.HandleTransaction(STARTTransaction())
    print status

    print "Set trace vars transaction..."
    status,res = TestConnection.HandleTransaction(SET_TRACE_VARIABLETransaction(
           "\x00\x00\x00\x00"+
           "\x01"
           "\x00"

           "\x01\x00\x00\x00"+
           "\x01"
           "\x00"
           )
           )
    print status

    print "Get trace vars transaction..."
    status,res = TestConnection.HandleTransaction(GET_TRACE_VARIABLETransaction())
    print status
    print len(res)
    print "GOT : ", map(hex, map(ord, res))

    print "Get PLCID transaction..."
    status,res = TestConnection.HandleTransaction(GET_PLCIDTransaction())
    print status
    print len(res)
    print "GOT : ", map(hex, map(ord, res))

    print "Get log counts transaction..."
    status,res = TestConnection.HandleTransaction(GET_LOGCOUNTSTransaction())
    print status
    print len(res)
    print "GOT : ", map(hex, map(ord, res))

    print "Get log message transaction..."
    status,res = TestConnection.HandleTransaction(GET_LOGMSGTransaction(0,0))
    print status
    print len(res)
    print "GOT : ", map(hex, map(ord, res))

    print "Stop transaction..."
    TestConnection.HandleTransaction(STOPTransaction())

    time.sleep(3)
