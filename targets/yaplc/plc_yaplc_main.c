/**
 * Newlib stubs.
 **/

#include <sys/stat.h>

int _close(int file)
{
    (void)file;
    return -1;
}

int _fstat(int file, struct stat *st)
{
    (void)file;
    st->st_mode = S_IFCHR;
    return 0;
}

int _isatty(int file)
{
    (void)file;
    return 1;
}

int _lseek(int file, int ptr, int dir)
{
    (void)file;
    (void)ptr;
    (void)dir;
    return 0;
}

int _open(const char *name, int flags, int mode)
{
    (void)name;
    (void)flags;
    (void)mode;
    return -1;
}

int _read(int file, char *ptr, int len)
{
    (void)file;
    (void)ptr;
    (void)len;
    return 0;
}

char *heap_end = 0;
caddr_t _sbrk(int incr)
{
    (void)incr;
    return (caddr_t) 0;
}

int _write(int file, char *ptr, int len)
{
    (void)file;
    (void)ptr;
    (void)len;
    return 0;
}

/**
 * YAPLC specific code.
 **/

#include <string.h>
#include <iec_std_lib.h>
#include <plc_abi.h>

/**
 * YAPLC ABI.
 **/

void fake_start(void)
{
    while(1);
}

#ifndef PLC_MD5
#error "PLC_MD5 must be defined!!!"
#endif
//App ABI, placed after .plc_app_abi_sec
__attribute__ ((section(".plc_md5_sec"))) char plc_md5[] = PLC_MD5;
//App ABI, placed at the .text end
__attribute__ ((section(".plc_check_sec"))) char plc_check_md5[] = PLC_MD5;

//Linker added symbols
extern uint32_t _plc_data_loadaddr, _plc_data_start, _plc_data_end, _plc_bss_end, _plc_sstart;

extern app_fp_t _plc_pa_start, _plc_pa_end;
extern app_fp_t _plc_ia_start, _plc_ia_end;
extern app_fp_t _plc_fia_start,_plc_fia_end;

extern int startPLC(int argc,char **argv);
extern int stopPLC();
extern void runPLC(void);

extern void resumeDebug(void);
extern void suspendDebug(int disable);

extern void FreeDebugData(void);
extern int GetDebugData(unsigned long *tick, unsigned long *size, void **buffer);

extern void ResetDebugVariables(void);
extern void RegisterDebugVariable(int idx, void* force);

extern void ResetLogCount(void);
extern uint32_t GetLogCount(uint8_t level);
extern uint32_t GetLogMessage(uint8_t level, uint32_t msgidx, char* buf, uint32_t max_size, uint32_t* tick, uint32_t* tv_sec, uint32_t* tv_nsec);

//App ABI, placed at the .text start
__attribute__ ((section(".plc_app_abi_sec"))) plc_app_abi_t plc_yaplc_app =
{
    .sstart = (uint32_t *)&_plc_sstart,
    .entry  = fake_start,
    //Startup interface
    .data_loadaddr = &_plc_data_loadaddr,

    .data_start    = &_plc_data_start,
    .data_end      = &_plc_data_end,

    .bss_end       = &_plc_bss_end,

    .pa_start  = &_plc_pa_start,
    .pa_end    = &_plc_pa_end,

    .ia_start  = &_plc_ia_start,
    .ia_end    = &_plc_ia_end,

    .fia_start = &_plc_fia_start,
    .fia_end   = &_plc_fia_end,

    .check_id  = plc_check_md5,

    //Must be run on compatible RTE
    .rte_ver_major = 1,
    .rte_ver_minor = 0,
    .rte_ver_patch = 0,

    //App interface
    .id   = plc_md5,

    .start = startPLC,
    .stop  = stopPLC,
    .run   = runPLC,

    .dbg_resume    = resumeDebug,
    .dbg_suspend   = suspendDebug,

    .dbg_data_get  = GetDebugData,
    .dbg_data_free = FreeDebugData,

    .dbg_vars_reset   = ResetDebugVariables,
    .dbg_var_register = RegisterDebugVariable,

    .log_cnt_get   = GetLogCount,
    .log_msg_get   = GetLogMessage,
    .log_cnt_reset = ResetLogCount,
    .log_msg_post  = LogMessage
};

//Redefine LOG_BUFFER_SIZE
#define LOG_BUFFER_SIZE (1<<10) /*1Ko*/
#define LOG_BUFFER_ATTRS

#define PLC_RTE ((plc_rte_abi_t *)(PLC_RTE_ADDR))

void PLC_GetTime(IEC_TIME *CURRENT_TIME)
{
    PLC_RTE->get_time( CURRENT_TIME );
}

void PLC_SetTimer(unsigned long long next, unsigned long long period)
{
    PLC_RTE->set_timer( next, period );
}

long AtomicCompareExchange(long* atomicvar,long compared, long exchange)
{
	/* No need for real atomic op on LPC,
	 * no possible preemption between debug and PLC */
	long res = *atomicvar;
	if(res == compared){
		*atomicvar = exchange;
	}
	return res;
}

long long AtomicCompareExchange64(long long* atomicvar,long long compared, long long exchange)
{
	/* No need for real atomic op on LPC,
	 * no possible preemption between debug and PLC */
	long long res = *atomicvar;
	if(res == compared){
		*atomicvar = exchange;
	}
	return res;
}

static int debug_locked = 0;
static int _DebugDataAvailable = 0;
static unsigned long __debug_tick;

int TryEnterDebugSection(void)
{
    if(!debug_locked && __DEBUG){
        debug_locked = 1;
		return 1;
    }
    return 0;
}

void LeaveDebugSection(void)
{
        debug_locked = 0;
}

void InitiateDebugTransfer(void)
{
    /* remember tick */
    __debug_tick = __tick;
    _DebugDataAvailable = 1;
}

void suspendDebug(int disable)
{
    /* Prevent PLC to enter debug code */
    __DEBUG = !disable;
    debug_locked = !disable;
}

void resumeDebug(void)
{
    /* Let PLC enter debug code */
    __DEBUG = 1;
    debug_locked = 0;
}

int WaitDebugData(unsigned long *tick)
{
    if(_DebugDataAvailable && !debug_locked){
        /* returns 0 on success */
        *tick = __debug_tick;
        _DebugDataAvailable = 0;
        return 0;
    }
    return 1;
}

void ValidateRetainBuffer(void)
{
    PLC_RTE->validate_retain_buf();
}
void InValidateRetainBuffer(void)
{
    PLC_RTE->invalidate_retain_buf();
}
int CheckRetainBuffer(void)
{
    return PLC_RTE->check_retain_buf();
}

void InitRetain(void)
{
}

void CleanupRetain(void)
{
}

void Retain(unsigned int offset, unsigned int count, void *p)
{
    PLC_RTE->retain( offset, count, p );
}
void Remind(unsigned int offset, unsigned int count, void *p)
{
    PLC_RTE->remind( offset, count, p );
}

int startPLC(int argc,char **argv)
{
	if(__init(argc,argv) == 0){
		PLC_SetTimer(0, common_ticktime__);
		return 0;
	}else{
		return 1;
	}
}

int stopPLC(void)
{
    __cleanup();
    return 0;
}

BOOL ix1 = 0;
BOOL ix2 = 0;
BOOL ix3 = 0;
BOOL ix4 = 0;
BOOL ix5 = 0;
BOOL ix6 = 0;
BOOL ix7 = 0;
BOOL ix8 = 0;
BOOL * __IX1 = &ix1;
BOOL * __IX2 = &ix2;
BOOL * __IX3 = &ix3;
BOOL * __IX4 = &ix4;
BOOL * __IX5 = &ix5;
BOOL * __IX6 = &ix6;
BOOL * __IX7 = &ix7;
BOOL * __IX8 = &ix8;

static void PLC_GetInputs(void)
{
    ix1 = PLC_RTE->get_din(1);
    ix2 = PLC_RTE->get_din(2);
    ix3 = PLC_RTE->get_din(3);
    ix4 = PLC_RTE->get_din(4);
    ix5 = PLC_RTE->get_din(5);
    ix6 = PLC_RTE->get_din(6);
    ix7 = PLC_RTE->get_din(7);
    ix8 = PLC_RTE->get_din(8);
}

BOOL qx1 = 0;
BOOL qx2 = 0;
BOOL qx3 = 0;
BOOL qx4 = 0;
BOOL * __QX1 = &qx1;
BOOL * __QX2 = &qx2;
BOOL * __QX3 = &qx3;
BOOL * __QX4 = &qx4;

static void PLC_SetOutputs(void)
{
    PLC_RTE->set_dout(1, qx1);
    PLC_RTE->set_dout(2, qx2);
    PLC_RTE->set_dout(3, qx3);
    PLC_RTE->set_dout(4, qx4);
}

void runPLC(void)
{
    PLC_GetInputs();
    PLC_GetTime( &__CURRENT_TIME );
    __run();
    PLC_SetOutputs();
}
