#ifndef EMSNDIS_H
#define EMSNDIS_H

class EmsnDis
{
public:
  int siteId;
  int applicationId;
  int exerciseId;
  EmsnDis(int i_siteId, int i_applicationId, int i_exerciseId);
  void send_start_pdu();
  void send_state_pdu();
  void send_stop_pdu();
};
#endif
