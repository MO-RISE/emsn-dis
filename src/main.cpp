#include "emsndis.h"
#ifdef _WIN32
#include <Windows.h>
#else
#include <unistd.h>
#endif

int main() {
  // Create EmsnDis class instance
  int siteId = 1;
  int applicationId = 1;
  int exerciseId = 1;
  EmsnDis edis(siteId, applicationId, exerciseId);
  edis.send_start_pdu();
  for (int i = 0; i < 5; i++) {
    edis.send_state_pdu();
    sleep(1);
  }
  edis.send_stop_pdu();
  return 0;
}
