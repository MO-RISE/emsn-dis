#include "emsndis.h"
// libray for sleep function
#ifdef _WIN32
#include <Windows.h>
#else
#include <unistd.h>
#endif

#include <string>

int main() {
  // Create EmsnDis class instance
  int siteId = 1;
  int applicationId = 1;
  int exerciseId = 1;
  std::string dis_entity;
  dis_entity = "generic_ship_container_class_small";
  std::string text;
  text = "Hi Reto";

  EmsnDis dis(siteId, applicationId, exerciseId);
  dis.send_start_pdu();
  /*
  for (int i = 0; i < 5; i++) {

    edis.send_state_pdu(
      1,
      57.66, 11.76, 0, // position
      0., 0., 0., // attitude
      0., 0., 0., // linear vel.
      0., 0., 0., // angular vel.
      dis_entity,
      text
    );
    sleep(1);

    dis.send_state_pdu();
  }
  */
  dis.send_state_pdu(dis_entity);
  dis.send_stop_pdu();
  return 0;
}
