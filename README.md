# EMSN-DIS

Implementation of the Distributed Interactive Simulation for the European Maritime Simulation Network.

## Procedure for testing the EMSN-DIS module

Assuming you have installed the dependencies:

1.  Connect the Ethernet cable to the EMSN LAN.
2.  Disable the WIFI in.
3.  Disable other Ethernet connections.
4.  In _Network Connections_ > _Ethernet Properties_ > _Internet Protocol Version 4 > Properties_ > _Use the following IP address and use:_

    IP address: 10.84.103.15

    Subnet mask: 255.255.255.0

5.  Ping the Transas / Wärtsila simulator to check the connection.

    ```bash
    ping 10.84.103.10
    ```

6.  Check that there are no conflicts with the Site ID, Application ID, and Exercise ID of test simulator:

    Pretending to be Sjöfartsverket:

        Site ID: 2

        Application ID: 1

        Excercise ID: 1

7.  Remember that the multicast settings in `test_simulator.py` are:

    Multicast address: 239.239.239.239

    Multicast port: 20000

    Host address: 10.84.103.15

8.  Run the test simulator:

    ```bash
    python test_simulator.py 0 10 1
    ```
