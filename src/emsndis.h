#ifndef EMSNDIS_H
#define EMSNDIS_H

#include <pybind11/embed.h>
namespace py = pybind11;

#include <string>

class EmsnDis
{
private:
  // Start the Python interpreter and keep alive
  py::scoped_interpreter guard{};
  // Instance of the EmsnDis python class
  py::object dis;

public:
  // Constructor
  EmsnDis(int siteId, int applicationId, int exerciseId);

  // Functions
  void send_start_pdu();

  void send_state_pdu(int idn, float lat, float lon, float alt,
    float yaw, float pitch, float roll, float u, float v, float w,
    float yaw_rot, float pitch_rot, float roll_rot, std::string dis_entity,
    std::string text);

  //void send_state_pdu(std::string text);
  void send_stop_pdu();
};
#endif
