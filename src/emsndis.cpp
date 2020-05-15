#include <pybind11/embed.h>
namespace py = pybind11;
#include <iostream>
#include <string>
#include "emsndis.h"

EmsnDis::EmsnDis(int siteId, int applicationId, int exerciseId)
{
  // Start the Python interpreter and keep alive
  //py::scoped_interpreter guard{};

  // Modify the systems path:
  //  sys.path.append(os.path.dirname(os.getcwd()))

  py::module os = py::module::import("os");
  py::module sys = py::module::import("sys");
  py::object cwd = os.attr("getcwd")();
  py::object cwdpath = os.attr("path").attr("dirname")(cwd);
  py::none none = sys.attr("path").attr("append")(cwdpath);

  // Import the class object from the emsndis Python module.
  py::object EmsnDis = py::module::import("emsndis").attr("EmsnDis");

  // Construct an instance
  dis = EmsnDis(siteId, applicationId, exerciseId);

}
void EmsnDis::send_start_pdu()
{
    dis.attr("send_start_pdu")();
    //std::cout << "Start Pdu\n";
}

void EmsnDis::send_state_pdu(int idn, float lat, float lon, float alt,
float yaw, float pitch, float roll, float u, float v, float w, float yaw_rot,
float pitch_rot, float roll_rot, std::string dis_entity, std::string text)
{
    py::none o_a = dis.attr("send_entity_state_pdu")(idn, lat, lon, alt,
      yaw, pitch, roll, u, v, w, yaw_rot, pitch_rot, roll_rot, dis_entity,
      text);
}


void EmsnDis::send_stop_pdu()
{
    dis.attr("send_stop_pdu")();
    //py::none o_a = dis.attr("send_stop_pdu")();
    //std::cout << "Start Pdu\n";
}

