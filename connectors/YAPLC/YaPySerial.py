#!/usr/bin/env python
# -*- coding: utf-8 -*-

import exceptions
from threading import Timer, Thread, Lock, Semaphore
import ctypes, os, commands, types, sys
import time

if os.name in ("nt", "ce"):
    from _ctypes import LoadLibrary as dlopen
    from _ctypes import FreeLibrary as dlclose
elif os.name == "posix":
    from _ctypes import dlopen, dlclose

class YaPySerialError(exceptions.Exception):
        """Exception class"""
        def __init__(self, msg):
                self.msg = msg

        def __str__(self):
                return "Exception in YaPySerial : " + str(self.msg)

class YaPySerial:
    def __init__(self, LibFile):
        self.port = None
        self._DlibraryHandle = None
        self.DlibraryHandle = None
        try:
            """
            Load library
            """
            self._DlibraryHandle = dlopen(LibFile)
            self.DlibraryHandle = ctypes.CDLL(LibFile, handle=self._DlibraryHandle)
            """
            Attach functions
            """
            self._SerialOpen = self.DlibraryHandle.yapy_serial_open;
            self._SerialOpen.restype = ctypes.c_int
            self._SerialOpen.argtypes = [ctypes.POINTER( ctypes.c_void_p ), ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]

            self._SerialClose = self.DlibraryHandle.yapy_serial_close;
            self._SerialClose.restype = ctypes.c_int
            self._SerialClose.argtypes = [ctypes.POINTER( ctypes.c_void_p )]

            self._SerialRead = self.DlibraryHandle.yapy_serial_read;
            self._SerialRead.restype = ctypes.c_int
            self._SerialRead.argtypes = [ctypes.POINTER( ctypes.c_void_p ), ctypes.c_void_p, ctypes.c_size_t]

            self._SerialWrite = self.DlibraryHandle.yapy_serial_write;
            self._SerialWrite.restype = ctypes.c_int
            self._SerialWrite.argtypes = [ctypes.POINTER( ctypes.c_void_p ), ctypes.c_void_p, ctypes.c_size_t]

            self._SerialGPIO = self.DlibraryHandle.yapy_serial_gpio;
            self._SerialGPIO.restype = ctypes.c_int
            self._SerialGPIO.argtypes = [ctypes.POINTER( ctypes.c_void_p ), ctypes.c_int, ctypes.c_int]
        except:
            raise YaPySerialError("Could'n t load dynamic library!")

    def Open(self, device, baud, modestr, timeout):
        self.port = ctypes.c_void_p(0)
        try:
            res = int( self._SerialOpen( ctypes.byref( self.port ), ctypes.c_char_p( device ), ctypes.c_int( baud ), ctypes.c_char_p( modestr ), ctypes.c_int( timeout )))
        except:
            raise YaPySerialError("Runrtime error on serial open!")
        if res > 0:
            msg = "Couldn't open serial port, error: " + str( res ) + "!"
            raise YaPySerialError( msg )

    def Close(self):
        try:
            res = int(self._SerialClose( ctypes.byref( self.port ) ))
        except:
            raise YaPySerialError("Runrtime error on serial close!")
        if res > 0:
            msg = "Couldn't close serial port, error: " + str( res ) + "!"
            raise YaPySerialError( msg )
        self.port = None

    def Read(self, nbytes):
        try:
            buf = ctypes.create_string_buffer( int(nbytes) )
            res = int(self._SerialRead( ctypes.byref( self.port ), ctypes.cast( buf, ctypes.c_void_p ), ctypes.c_size_t( nbytes ) ))
        except:
            raise YaPySerialError("Runrtime error on serial read!")
        if res > 0:
            if res == 2:
                return None
            else:
                msg = "Couldn't read serial port, error: " + str( res ) + "!"
                raise YaPySerialError( msg )
        else:
            return buf.raw

    def Write(self, buf):
        try:
            nbytes = len( buf )
            strbuf = ctypes.create_string_buffer( buf )
            res = int(self._SerialWrite( ctypes.byref( self.port ), ctypes.cast( ctypes.byref( strbuf ), ctypes.c_void_p ), ctypes.c_size_t( nbytes ) ))
        except:
            raise YaPySerialError("Runrtime error on serial write!")
        if res > 0:
            msg = "Couldn't write to serial port, error: " + str( res ) + "!"
            raise YaPySerialError( msg )

    def Flush(self):
        try:
            buf = ctypes.create_string_buffer(1);
            res = 0
            while res == 0:
                res = int(self._SerialRead( ctypes.byref( self.port ), ctypes.cast( buf, ctypes.c_void_p ), ctypes.c_size_t(1) ))
        except:
            raise YaPySerialError("Runrtime error on serial flush!")
        if res != 2:
            msg = "Couldn't write to serial port, error: " + str( res ) + "!"
            raise YaPySerialError( msg )

    def GPIO(self, n, level):
        try:
            res = int(self._SerialGPIO( ctypes.byref( self.port ), ctypes.c_int(n), ctypes.c_int( level ) ))
        except:
            raise YaPySerialError("Runrtime error on serial gpio!")
        if res > 0:
            msg = "Couldn't write to serial port, error: " + str( res ) + "!"
            raise YaPySerialError( msg )

    def __del__(self):
        if self._DlibraryHandle is not None:
            if self.port is not None:
                try:
                    self.Close()
                except:
                    raise YaPySerialError("Could'n t close serial port!")
            dlclose(self._DlibraryHandle)
            self._DlibraryHandle = None
            self.DlibraryHandle = None

if __name__ == "__main__":

    """
    "C:\Program Files\Beremiz\python\python.exe" YaPySerial.py
    """
    if os.name in ("nt", "ce"):
        lib_ext = ".dll"
    else:
        lib_ext = ".so"

    TestLib = os.path.dirname(os.path.realpath(__file__)) + "/../../../yaplc/libYaPySerial" + lib_ext

    TestSerial = YaPySerial( TestLib )
    TestSerial.Open( "COM256", 9600, "8N1", 2 )

    TestSerial.Flush()

    send_str = "Hello World!!!"
    TestSerial.Write( send_str )

    receive_str = TestSerial.Read( len( send_str ) )

    print( "Received:" )
    print( receive_str )

    TestSerial.Close()

    time.sleep(1)
