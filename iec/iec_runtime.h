#include <stdio.h>
#include <pthread.h>

#include "cs104_slave.h"
#include "hal_thread.h"
#include "hal_time.h"




//
//
//    SERVER / SLAVE
//
//
#define IEC_SERVER_MEMORY_SIZE 2048
typedef struct {
    unsigned int variables[IEC_SERVER_MEMORY_SIZE];
/*
    unsigned int ro_bits [IEC_SERVER_MEMORY_SIZE];
    unsigned int rw_bits [IEC_SERVER_MEMORY_SIZE];
    unsigned int ro_words[IEC_SERVER_MEMORY_SIZE];
    unsigned int rw_words[IEC_SERVER_MEMORY_SIZE];
    */
} iec_server_mem_t;

typedef struct {
    CS104_Slave slave;
    //u8		slave_id;
    char*	local_address;
    //int		mb_nd;      // modbus library node used for this server
    //int		init_state; // store how far along the server's initialization has progressed
    pthread_t	thread_id;  // thread handling this server
    iec_server_mem_t	mem;
} iec_server_node_t;

#define NUMBER_OF_IEC_SERVERS %(number_of_servers)s

static iec_server_node_t iec_servers[NUMBER_OF_IEC_SERVERS];
char* iec_server_ip[NUMBER_OF_IEC_SERVERS] = { %(servers_ips)s };

/*******************/
/*located variables*/
/*******************/

%(loc_vars)s

