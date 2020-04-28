"""
Test Simulator
~~~~~~~~~~~~~~~~

Used for testing the EMSN-DIS module.

Usage:

python test_simulator.py <exercise ID> <run time (sec)> <entity (1-3)> <local>

Run the simulator with multicast settings for local testing
>> python dummy_simulator.py 1 10 1 1

Run the simulator with multicsat settings for EMSN
>> python dummy_simulator.py 1 10 1 0


"""

import math
import time
import signal
import sys

from datetime import datetime
from collections import namedtuple

from bitstring import Bits

from emsndis import EmsnDis
import emsndis.geoutils as geo

# Dummy entities
Entity = namedtuple('Entity','id position attitude lin_vel ang_vel')
entity_1 = Entity(1, [57.66, 11.76, 0],[0,0,0], [0,0,0], [0,0,0])

class Simulator:

    def __init__(self, siteId, applicationId, excerciseId, run_time, entity,**kwargs):
        self.dis = EmsnDis(siteId, applicationId, excerciseId, **kwargs)
        self.latest_state_update = time.time()
        self.entity = entity
        self.start_time = time.time()
        self.run_time = run_time
        self.dis.send_start_pdu()
        self.rstep = 0
        self.run()

    def run(self):
        while True:
            pdus = self.dis.receive_pdus()
            if len(pdus) != 0:
                for pdu in pdus:
                    self.print_pdu(pdu)
            if time.time() - self.latest_state_update > 1:
                #self.entity.attitude[0] += 5
                #self.entity.attitude[2] += self.rstep
                #if self.entity.attitude[0] > 360:
                #    self.entity.attiude[0] = 0
                #if abs(self.entity.attitude[2]) > 45:
                #    self.rstep *= -1
                #print('attitude', self.entity.attitude)
                self.dis.send_entity_state_pdu(self.entity)
                self.latest_state_update = time.time()
            if time.time() - self.start_time > self.run_time:
                self.dis.send_stop_pdu()
                break

    def print_pdu(self, pdu):
        pduType = pdu['pduHeader']['pduType']
        protocolFamily = pdu['pduHeader']['protocolFamily']
        tph = self.dis._timestamp_to_tph(pdu['pduHeader']['timestamp'])
        sph = tph*3600/(2**31 - 1) # time past the hour
        hour = datetime.now().hour
        minutes = int(sph // 60)
        seconds = int(sph % 60)
        minutes_txt = '0' + str(minutes) if minutes < 10 else str(minutes)
        seconds_txt = '0' + str(seconds) if seconds < 10 else str(seconds)
        if pduType == 1 and protocolFamily == 1:
            # Entity State PDU
            siteId = pdu['entityId']['site']
            applicationId = pdu['entityId']['application']
            entityId = pdu['entityId']['entity']
            if siteId != self.dis.siteId or applicationId != self.dis.applicationId:
                print('RECEIVED Entity State PDU:')
            else:
                print('SENT Entity State PDU')
            xyz = [v for v in pdu['entityLocation'].values()]
            euler = [v for v in pdu['entityOrientation'].values()]
            lla, att = geo.from_dis(xyz,euler)
            lat, lon, alt = lla
            #att = [geo.rad2deg(v) for v in att]
            psi, theta, phi = att
            #lat, lon = self.dis.dis2latlon(pdu['entityLocation'])
            print(f' SiteId:  {siteId}')
            print(f' ApplicationId:  {applicationId}')
            print(f' EntityId:  {entityId}')
            print(f' EntityType:')
            print(f"    entityKind: {pdu['entityType']['entityKind']}"),
            print(f"    domain: {pdu['entityType']['domain']}"),
            print(f"    country: {pdu['entityType']['country']}"),
            print(f"    category: {pdu['entityType']['category']}"),
            print(f"    subcategory: {pdu['entityType']['subcategory']}"),
            print(f"    specific: {pdu['entityType']['specific']}"),
            print(f"    extra: {pdu['entityType']['extra']}"),

            print(f' timestamp: {hour}:{minutes_txt}:{seconds_txt}')
            print(f' position: {round(lat,6)}, {round(lon,6)}, {round(alt,6)} ')
            print(f' attitude: {round(psi,6)}, {round(theta,6)}, {round(phi,6)}')
            print(f' euler: {euler}')
            print(f' xyz: {xyz}')
            #print(pdu)
            print('\n')
        else:
            print('SENT / RECEIVED Entity State PDU')
            print(f' timestamp: {hour}:{minutes_txt}:{seconds_txt}')
            print(f' PDU type: {pduType}')
            print(f' Protocol Family: {protocolFamily}')
            #print(pdu)
            print('\n')



def signal_handler(signal, frame):

    print('\nYou pressed Ctrl+C! Goodbye ...')
    sys.exit(0)

if __name__ == "__main__":


    # Handle shutdown of this program
    signal.signal(signal.SIGINT, signal_handler)

    excerciseId, run_time, entityId, local = sys.argv[1:5]

    if int(entityId) == 1:
        entity = entity_1
    elif int(entityId) == 2:
        entity = entity_2
    else:
        entity = Entity(int(entityId), (57.68, 11.76, 3.1416), (0,0,0))

    multicast = {
        'multicast_addr':'239.239.239.239',
        'multicast_port':20000,
        'timeout':0.2,
        'host_addr':'10.84.103.15',
    }

    # Sjöfartsverket
    siteId = 2
    applicationId = 1

    if int(local):
        sim = Simulator(siteId, applicationId, int(excerciseId), int(run_time), entity, verbose=True)
    else:
        sim = Simulator(siteId, applicationId, int(excerciseId), int(run_time), entity, verbose=True, **multicast)
    print('Simulation stopped.')


