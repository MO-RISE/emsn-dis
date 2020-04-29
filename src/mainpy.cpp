// main.cpp
#include <pybind11/embed.h>
namespace py = pybind11;
int main() {
    // Start interpreter and keep alive
    py::scoped_interpreter guard{};

    // Modify the systems path:
    //  sys.path.append(os.path.dirname(os.getcwd()))
    py::module os = py::module::import("os");
    py::module sys = py::module::import("sys");
    py::object cwd = os.attr("getcwd")();
    py::object cwdpath = os.attr("path").attr("dirname")(cwd);
    py::none none = sys.attr("path").attr("append")(cwdpath);

    //py::print(cwdpath);
    //sys.path.append(os.path.dirname(os.getcwd()))
    // from dummy import Dummy
    py::object EmsnDis = py::module::import("emsndis").attr("EmsnDis");
    //py::module p = py::module::import("potato2");
    // Construct a Dummy instance
    py::object dis = EmsnDis(1,1,1);
    // Call the class method "send_start_pdu" that returns None.
    py::none o_a = dis.attr("send_start_pdu")();
    // Call the class method "stop_start_pdu" that returns None.
    //py::none o_b = dis.attr("send_start_pdu")();
    // Call the class method "recall" that returns a string.
    //py::object result = p.attr("add")(2,4);
    // Print the string.
    //py::print(result);
}
