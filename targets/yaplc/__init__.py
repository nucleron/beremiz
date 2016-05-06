import os, sys, shutil
from ..toolchain_yaplc import toolchain_yaplc

target_load_addr    = "0x08008000"
target_runtime_addr = "0x080001ac"

base_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
#base_dir = os.path.split(sys.path[0])[0]
libopencm3_dir = os.path.join(base_dir, "libopencm3")

class yaplc_target(toolchain_yaplc):
    def __init__(self, CTRInstance):
        toolchain_yaplc.__init__(self, CTRInstance)
        #
        libopencm3_inc_dir = os.path.join(libopencm3_dir, "include")
        self.cflags.append("-I\""+libopencm3_inc_dir+"\"")
        #Needed for plc_main.c
        plc_yaplc_dir = os.path.join(base_dir, "yaplc")
        plc_src_dir   = os.path.join(plc_yaplc_dir, "src")
        plc_rt_dir    = os.path.join(plc_src_dir, "plc_runtime")
        self.cflags.append("-I\"" + plc_rt_dir + "\"")
        self.cflags.append("-DPLC_RTE_ADDR=" + target_runtime_addr)
        #Add linker script to ldflags
        plc_linker_script = os.path.join(plc_rt_dir, "bsp/stm32f4/stm32f4disco-app.ld")
        #Target specific build options
        self.target_options.append("LDFLAGS=-Wl,-script=\""+plc_linker_script+"\" ")
        self.target_options.append("OUTPUT="+self.exe)
        self.target_options.append("LOADADDR="+target_load_addr)
    def build(self):
        #Copy make file
        beremiz_dir = os.path.join(base_dir, "beremiz")
        tagtets_dir = os.path.join(beremiz_dir, "targets")
        yaplc_target_dir = os.path.join(tagtets_dir, "yaplc")
        shutil.copy(os.path.join(yaplc_target_dir, "Makefile"), os.path.join(self.buildpath, "Makefile"))

        #Build project
        return toolchain_yaplc.build(self)

    def GetBinaryCode(self):

        yaplc_tools_dir = os.path.join(base_dir, "yaplc")
        yaplc_boot_loader = os.path.join(yaplc_tools_dir, "stm32flash")
        #
        #command  = "\"" + yaplc_boot_loader + "\" -w "
        #command += "\"" + toolchain_yaplc.GetBinaryCode(self) + ".hex\""
        #command += " -v -g 0x0 -S " + target_load_addr + " %s"
        command = []
        command.append(yaplc_boot_loader)
        command.append("-w")
        command.append(toolchain_yaplc.GetBinaryCode(self) + ".hex")
        command.append("-v")
        command.append("-g")
        command.append("0x0")
        command.append("-S")
        command.append(target_load_addr)
        command.append("%(serial_port)s")
        #
        return command
        #return toolchain_yaplc.GetBinaryCode(self) + ".hex"
