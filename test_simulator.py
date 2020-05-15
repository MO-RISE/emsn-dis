"""
Test Simulator
~~~~~~~~~~~~~~~~

Used for testing the EMSN-DIS module.

Usage:

python test_simulator.py <local> <run time (sec)> <state_num)>

Run the simulator with multicast settings for local testing
>> python dummy_simulator.py 1 10 1

Run the simulator with multicsat settings for EMSN
>> python dummy_simulator.py 0 10 1


"""

import math
import time
import signal
import sys
import pprint

from datetime import datetime
from collections import namedtuple

from bitstring import Bits

from emsndis import EmsnDis
import emsndis.geoutils as geo

state_1 = {
    'idn': 1,
    'lat': 57.66,
    'lon': 11.76,
    'alt': 0,
    'yaw': 0,
    'pitch': 0,
    'roll': 0,
    'u': 0,
    'v': 0,
    'w': 0,
    'yaw_rot': 0,
    'pitch_rot': 0,
    'roll_rot': 0,
    'dis_entity': 'generic_ship_container_class_small',
    'text': 'Hi Reto',
}

# Details:
#   Heading South with a pitch a positive pitch of 5 deg.
state_2 = {
    'idn': 1,
    'lat': 57.66,
    'lon': 11.76,
    'alt': 0,
    'yaw': 180,
    'pitch': 5,
    'roll': 0,
    'u': 0,
    'v': 0,
    'w': 0,
    'yaw_rot': 0,
    'pitch_rot': 0,
    'roll_rot': 0,
    'dis_entity': 'generic_ship_container_class_small',
    'text': 'Hola Reto',
}

# Details;
#   Not under command/Aground (red/red)
#   Restricted ability to maneuver (Ball/Diamond/Ball)
#   Deck lights on
state_3 = {
    'idn': 1,
    'lat': 57.66,
    'lon': 11.76,
    'alt': 0,
    'yaw': 0,
    'pitch': 0,
    'roll': 0,
    'u': 0,
    'v': 0,
    'w': 0,
    'yaw_rot': 0,
    'pitch_rot': 0,
    'roll_rot': 0,
    'dis_entity': 'generic_ship_container_class_small',
    'text': 'MS Reto',
    'nav_lights':1,
    'deck_lights':2,
    'nav_shapes':2
}

pdu_types = {
    (1,1): 'ENTITY STATE PDU',
    (5,13): 'START PDU',
    (5,14): 'STOP PDU',
    (4,25): 'TRANSMITTER PDU',
    (4,26): 'SIGNAL PDU',
    (4,27): 'RECEIVER PDU',
}

def i_sent(dis, pdu):
    siteId = pdu['entityId']['site']
    applicationId = pdu['entityId']['application']
    if siteId != dis.siteId or applicationId != dis.applicationId:
        return False
    else:
        return True

def print_entity_id_pdu(pdu):
    site = pdu['entityId']['site']
    applicationId = pdu['entityId']['application']
    entityId = pdu['entityId']['entity']
    print(f' SiteId:  {site}')
    print(f' ApplicationId:  {applicationId}')
    print(f' EntityId:  {entityId}')

def print_entity_state_pdu(pdu):
    xyz = [v for v in pdu['entityLocation'].values()]
    euler = [v for v in pdu['entityOrientation'].values()]
    lla, att = geo.from_dis(xyz,euler)
    lat, lon, alt = lla
    psi, theta, phi = att
    print_entity_id_pdu(pdu)
    print(f' position: {round(lat,6)}, {round(lon,6)}, {round(alt,6)} ')
    print(f' attitude: {round(psi,6)}, {round(theta,6)}, {round(phi,6)}')
    print(f' euler: {euler}')
    print(f' xyz: {xyz}')
    characters = pdu['entityMarking']['characters']
    text = ''.join([chr(i) for i in characters])
    print(f' markings: {text}')
    ea = pdu['entityAppearance']
    print(f' entity appearance: {ea}')

def print_unknown_pdu(pdu):
    print('RECEIVED UNKNOWN PDU')
    protocolFamily = pdu['pduHeader']['protocolFamily']
    pduType = pdu['pduHeader']['pduType']
    print(f'protocolFamily: {protocolFamily}')
    print(f'pduType: {pduType}')
    print_pdus_timestamp(pdu)

class Simulator:

    def __init__(self, siteId, applicationId, excerciseId, run_time, entity_state, move, ais, **kwargs):
        self.dis = EmsnDis(siteId, applicationId, excerciseId, **kwargs)
        self.latest_state_update = time.time()
        self.entity_state = entity_state
        self.start_time = time.time()
        self.run_time = run_time
        self.ais = ais
        self.dis.send_start_pdu()
        if ais:
            self.dis.send_transmitter_pdu(
                self.entity_state['idn'],
                1,
                2,
                10, 0, 10,
                 self.entity_state['lat'],
                 self.entity_state['lon'],
                 self.entity_state['alt'],
                 self.entity_state['yaw'],
                 self.entity_state['pitch'],
                 self.entity_state['roll'])
            self.dis.send_transmitter_pdu(
                self.entity_state['idn'],
                2,
                2,
                10, 0, 10,
                 self.entity_state['lat'],
                 self.entity_state['lon'],
                 self.entity_state['alt'],
                 self.entity_state['yaw'],
                 self.entity_state['pitch'],
                 self.entity_state['roll'])
            self.dis.send_receiver_pdu(entity_state['idn'], 1, 2)
            self.dis.send_receiver_pdu(entity_state['idn'], 1, 2)
        self.move = move
        self.rstep = 0
        self.run()

    def run(self):
        while True:
            pdus = self.dis.receive_pdus()
            if len(pdus) != 0:
                for pdu in pdus:
                    self.print_pdu(pdu)
            if time.time() - self.latest_state_update > 1:
                self.dis.send_entity_state_pdu(**self.entity_state)
                self.latest_state_update = time.time()
                if self.move:
                    self.entity_state['lat'] = self.entity_state['lat'] + \
                     0.00001
                if self.ais:
                    data = (32).to_bytes(4,'big')
                    self.dis.send_signal_pdu(self.entity_state['idn'], data)
            if time.time() - self.start_time > self.run_time:
                self.dis.send_stop_pdu()
                break

    def print_pdu(self, pdu):
        protocolFamily = pdu['pduHeader']['protocolFamily']
        pduType = pdu['pduHeader']['pduType']

        if pduType == 13:
            print('START SIMULATION PDU')
        elif pduType == 14:
            print('STOP SIMULATION PDU')
        elif pduType in [1, 25, 26, 27]:
            if i_sent(self.dis, pdu):
                print(f'------------ SENT --------------')
            else:
                print(f'---------- RECEIVED ------------')
            pdu_type = pdu_types[(protocolFamily, pduType)]
            print(pdu_type)
            if not i_sent(self.dis, pdu):
                pprint.pprint(pdu)
            else:
                if pduType == 1:
                    print_entity_state_pdu(pdu)
        else:
            print_unknown_pdu(pdu)
        print('--------------------------------')
        tph = self.dis._timestamp_to_tph(pdu['pduHeader']['timestamp'])
        sph = tph*3600/(2**31 - 1) # time past the hour
        hour = datetime.now().hour
        minutes = int(sph // 60)
        seconds = int(sph % 60)
        minutes_txt = '0' + str(minutes) if minutes < 10 else str(minutes)
        seconds_txt = '0' + str(seconds) if seconds < 10 else str(seconds)
        print(f' timestamp: {hour}:{minutes_txt}:{seconds_txt}')
        print('\n')


def signal_handler(signal, frame):

    print('\nYou pressed Ctrl+C! Goodbye ...')
    sys.exit(0)

if __name__ == "__main__":


    # Handle shutdown of this program
    signal.signal(signal.SIGINT, signal_handler)

    local, run_time, state_num = sys.argv[1:5]

    ais = False
    move = False
    if int(state_num) == 1:
        entity_state = state_1
    elif int(state_num) == 2:
        entity_state = state_2
    elif int(state_num) == 3:
        entity_state = state_3
    elif int(state_num) == 4:
        entity_state = state_1
        move = True
    else:
        entity_state = state_1
        ais = True

    multicast = {
        'multicast_addr':'239.239.239.239',
        'multicast_port':20000,
        'timeout':0.2,
        'host_addr':'10.84.103.15',
    }

    # Sjöfartsverket
    siteId = 2
    applicationId = 1
    excerciseId = 1

    if int(local):
        sim = Simulator(siteId, applicationId, int(excerciseId), int(run_time), entity_state, move, ais, verbose=True)
    else:
        sim = Simulator(siteId, applicationId, int(excerciseId), int(run_time), entity_sate, move, ais,  verbose=True, **multicast)
    print('Simulation stopped.')


