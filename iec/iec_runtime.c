
#include <stdio.h>
#include "IEC_%(locstr)s.h"

static bool running = true;

//
//
//    SERVER / SLAVE
//
//

static void rawMessageHandler(void* parameter, IMasterConnection conneciton, uint8_t* msg, int msgSize, bool sent)
{
    if (sent)
        printf("SEND: ");
    else
        printf("RCVD: ");

    printf("\n");
}

static bool clockSyncHandler (void* parameter, IMasterConnection connection, CS101_ASDU asdu, CP56Time2a newTime)
{
    uint64_t newSystemTimeInMs = CP56Time2a_toMsTimestamp(newTime);

    /* Set time for ACT_CON message */
    CP56Time2a_setFromMsTimestamp(newTime, Hal_getTimeInMs());

    /* update system time here */

    return true;
}

static bool interrogationHandler(void* parameter, IMasterConnection connection, CS101_ASDU asdu, uint8_t qoi)
{
    //printf("interrogationHandler\n");
    return true;
}

bool asduHandler(void* parameter, IMasterConnection connection, CS101_ASDU asdu)
{
    //printf("Received asdu with type %%d\n", CS101_ASDU_getTypeID(asdu));
    iec_server_node_t* server = (iec_server_node_t*)parameter;
    /*
    IEC60870_5_TypeID id = CS101_ASDU_getTypeID(asdu);
    if(id == C_RD_NA_1) { //Read value code
        if  (CS101_ASDU_getCOT(asdu) == CS101_COT_REQUEST) {
            InformationObject io = CS101_ASDU_getElement(asdu, 0);
            int value_idx = InformationObject_getObjectAddress(io);
            int value = server->mem.variables[value_idx];
            CS101_ASDU_setCOT(asdu, CS101_COT_ACTIVATION_CON);
            IMasterConnection_sendASDU(connection, asdu);
            InformationObject_destroy(io);
        }
    }*/
    return true;
}

static bool connectionRequestHandler(void* parameter, const char* ipAddress)
{
#if 0
    if (strcmp(ipAddress, "127.0.0.1") == 0) {
        printf("Accept connection\n");
        return true;
    }
    else {
        printf("Deny connection\n");
        return false;
    }
#else
    return true;
#endif
}

static void connectionEventHandler(void* parameter, IMasterConnection con, CS104_PeerConnectionEvent event)
{
    if (event == CS104_CON_EVENT_CONNECTION_OPENED) {
        printf("Connection opened\n");
    }
    else if (event == CS104_CON_EVENT_CONNECTION_CLOSED) {
        printf("Connection closed\n");
    }
    else if (event == CS104_CON_EVENT_ACTIVATED) {
        printf("Connection activated\n");
    }
    else if (event == CS104_CON_EVENT_DEACTIVATED) {
        printf("Connection deactivated\n");
    }
}

static void* run_iec_slave(void* _server)
{
    iec_server_node_t* server = (iec_server_node_t*)_server;
    server->slave = CS104_Slave_create(10, 10);
    CS104_Slave slave = server->slave;

	CS104_Slave_setLocalAddress(slave, "0.0.0.0");
	CS104_Slave_setServerMode(slave, CS104_MODE_SINGLE_REDUNDANCY_GROUP);
    CS104_Slave_setClockSyncHandler(slave, clockSyncHandler, NULL);
    CS104_Slave_setInterrogationHandler(slave, interrogationHandler, NULL);
    CS104_Slave_setASDUHandler(slave, asduHandler, _server);
    CS104_Slave_setConnectionRequestHandler(slave, connectionRequestHandler, NULL);
    CS104_Slave_setConnectionEventHandler(slave, connectionEventHandler, NULL);

    CS104_Slave_start(slave);

    if (CS104_Slave_isRunning(slave) == false) {
        printf("Starting server failed!\n");
        CS104_Slave_destroy(slave);
        return 0;
    }

    while (running) {
		Thread_sleep(500);
		//printf("log...\n");
		//printf("%%d\n", server->mem.variables[0]);
		/*
		CS101_ASDU newAsdu = CS101_ASDU_create(alParams, false, CS101_COT_PERIODIC, 0, 1, false, false);
		InformationObject io = (InformationObject) MeasuredValueScaled_create(NULL, 110, scaledValue, IEC60870_QUALITY_GOOD);
		CS101_ASDU_addInformationObject(newAsdu, io);
		InformationObject_destroy(io);
		CS104_Slave_enqueueASDU(slave, newAsdu);
		CS101_ASDU_destroy(newAsdu);
		*/
	}

	CS104_Slave_stop(slave);
	CS104_Slave_destroy(slave);

	Thread_sleep(500);

	return 0;
}


//
//
//Beremiz interfaces
//
//
int __init_%(locstr)s (int argc, char **argv){
    for(uint32_t i = 0; i < NUMBER_OF_IEC_SERVERS; i++)
    {
        //set server's parameters
        iec_servers[i].local_address = iec_server_ip[i];

        int res = 0;
        pthread_t thread_id;
        pthread_attr_t attr;
        res |= pthread_attr_init(&attr);
        res |= pthread_create(&(iec_servers[i].thread_id), &attr, &run_iec_slave, (void *)&(iec_servers[i]));
        if (res !=  0) {
            fprintf(stderr, "IEC plugin: Error starting server.\n");
        }

        //run_iec_slave(slaves[i]);
    }
	return 0;
}

void __publish_%(locstr)s (){
    //printf("Pulbish iec call!\n");
}

void __retrieve_%(locstr)s (){
    //printf("retrieve iec call!\n");
}

int __cleanup_%(locstr)s (){
	int res = 0;
    //printf("cleanup iec call!\n");
	return res;
}
