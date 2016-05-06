
COBJ = $(SRC:.c=.o)

OBJ = $(COBJ)
#=================================================================
CROSS_TOOLS = arm-none-eabi
#=================================================================
MCC = $(CROSS_TOOLS)-gcc
MLD = $(CROSS_TOOLS)-gcc
MSIZE = $(CROSS_TOOLS)-size
MOBJCOPY = $(CROSS_TOOLS)-objcopy
#=================================================================
MCFLAGS  = $(CFLAGS)
MCFLAGS += -mthumb -mcpu=cortex-m4  -mfpu=fpv4-sp-d16 -mfloat-abi=hard
MCFLAGS += -O0 -g3 -std=gnu90 -Wall
MCFLAGS +=  -fdata-sections -ffunction-sections -fno-strict-aliasing
# defines
MCFLAGS += -DARM_MATH_CM4 -D__FPU_USED -DSTM32F4
MCFLAGS += -DPLC_MD5="\"$(MD5)\""

#=================================================================
MLDFLAGS  = $(LDFLAGS)
MLDFLAGS += -mthumb -mcpu=cortex-m4  -mfpu=fpv4-sp-d16 -mfloat-abi=hard
MLDFLAGS += -fno-strict-aliasing -std=gnu90

MLDFLAGS += -Wall -fdata-sections -ffunction-sections -O0 -g3
MLDFLAGS += -DARM_MATH_CM4 -D__FPU_USED -DSTM32F4

MLDFLAGS += -Wl,--gc-sections -nostartfiles
MLDFLAGS += -Wl,-Map=$(OUTPUT).map
#=================================================================
all: warn yaplc hex
	@echo "*** all done ***"

warn:
	@echo "*** Building target ***"

hex:
	$(MOBJCOPY) --change-address $(LOADADDR) -O ihex $(OUTPUT).elf $(OUTPUT).hex

yaplc: $(OBJ)
	$(MLD) $(MLDFLAGS) -o $(OUTPUT).elf $^
	$(MSIZE) $(OUTPUT).elf

%.o : %.c
	$(MCC) $(MCFLAGS) -c $< -o $@
