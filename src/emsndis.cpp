//#include <pybind11/embed.h>
//namespace py = pybind11;
#include <iostream>
#include "emsndis.h"

EmsnDis::EmsnDis(int i_siteId, int i_applicationId, int i_exerciseId)
{
  siteId = i_siteId;
  applicationId = i_applicationId;
  exerciseId = i_exerciseId;
}
void EmsnDis::send_start_pdu()
{
    std::cout << "Start Pdu\n";
}
void EmsnDis::send_state_pdu()
{
    std::cout << "State Pdu\n";
}
void EmsnDis::send_stop_pdu()
{
    std::cout << "Stop Pdu\n";
}

