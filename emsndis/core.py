#!/usr/bin/env python

"""
core.py
~~~~~~~~

Wrapper for DIS following the
Implementation of the European Maritime Simulation Network.

References:
[1] STM Validation. 2017. European Maritime Simulator Network -
  Technical Description for STM Validation. https://go.aws/2RA4Vse
  (viewed 20 January 2020)
[2] IEEE. 1995. 1278.1-1995 Standard for Distributed Interactive Simulation.
[3] Simulation Interoperability Standards Organization. 2015. SISO-REF-010-2015
  Reference for Enumerations for Simulation Interoperability, Version 21.
  https://cutt.ly/qyQp53G (viewed 14 May 2020).

"""

import sys
import signal

from datetime import datetime

from . import multicast
from . import dis6

#from opendis.RangeCoordinates import GPS
from . import geoutils as geo

from bitstring import Bits

#gps = GPS()

# Folllowing Section 5.1.4 in Ref. [2]
ALL_APPLIC = 65535
ALL_ENTITIES = 65535
ALL_SITES = 65535
NO_APPLIC = 0
NO_ENTITY = 0
NO_SITE = 0

# Custom DIS entities for EMSN as described in section 3.1.4.1
# in Ref. [1]

# Generic Ship Container Class medium (3.000 - 10.000 TEU)
emsn_dis_entities = {
  'generic_ship_container_class_medium': {
    'entityKind': 1,
    'domain': 3,
    'country': 0,
    'category': 61,
    'subcategory': 2,
    'specific': 1,
    'extra': 0,
  },
  'generic_ship_container_class_small': {
    'entityKind': 1,
    'domain': 3,
    'country': 0,
    'category': 61,
    'subcategory': 1,
    'specific': 3,
    'extra': 0,
  }
}


class EmsnDis:

  def __init__(self, siteId, applicationId, excerciseId,**kwargs):
    self.sock = multicast.Socket(**kwargs)
    self.latest_entity_state_update = {}
    self.excerciseId = excerciseId
    self.requests = 0
    self.siteId = siteId
    self.applicationId = applicationId
    self.simulationManagementEntityId = {
      'site': siteId,
      'application': applicationId,
      'entity':0,
    }

  def hello(self):
    print(f'Hello, my applicationId is {self.applicationId}')

  def _make_pdu_header(self, pduType, protocolFamily, length):
    """Make a PDU header

    Used by all the PDUs sent by the EMSN-DIS interface.

    Args:
    -----

      pduType (enum):
        Incomplete list of PDU types from in Ref. [3] Sec. A.2:
          1: Entity State
          13: Start / Resume
          14: Stop / Freeze
          18: Data query
          19: Set data
          20: Data
          25: Transmitter
          26: Signal
          27: Receiver

      protocolFamily (enum):
        Incomplete list of protocol families from Ref. [3] Sec. A.3:
          1: Entity information (e.g. Entity State PDU)
          4: Radio communication (e.g. Transmitter PDU)
          5: Simulation management (e.g. Start PDU)

      Length (int):
        Length of the PDU in bytes (aka. octets).

    Output:
    -------

      PDU header dict

    """
    return {
      'protocolVersion': 6,
      'excerciseId': self.excerciseId,
      'pduType': pduType,
      'protocolFamily': protocolFamily,
      'timestamp': self.timestamp,
      'length': length,
      'padding':0,
    }

  def _send_pdu(self, pdu):
    """Send a single PDU
    """
    stream = dis6.serialize(pdu)
    data = stream.getvalue()
    self.sock.send(data)

  def receive_pdus(self):
    """Receive PDUs.
        """
    pdus = []
    while True:
        data = self.sock.receive()
        if data:
          pdus.append(dis6.deserialize(data))
        else:
            break
    return pdus

  def _get_tph(self, datetime):
    """Get time past the hour.
    One hour is equal to (2^31 - 1) time units.
      Defined in section 5.2.31.3 in Ref. [2].
    """
    return int((datetime.timestamp() % 3600)*((2**31) -1)/3600)

  def _get_h(self, datetime):
    """Get hours since 00:00 UTC January 1, 1970.
    Defined in section 5.2.31.3 in Ref. [2].
    """
    return int(datetime.timestamp() // 3600)

  def _tph_to_timestamp(self, tph):
    """Transform time past the hour (tph) to timestamp
    Timestamp is an 32 bit big endian integer encoding in its
    first 31 bits the time past the hour and in the last one
    the type of timestamp (0: relative, 1:absolute).
    Defined in section 5.2.31 in Ref. [2]
    """
    return int(Bits(uintbe=tph,length=32).bin[1:] + '0',2)

  def _timestamp_to_tph(self, t):
    """Transform a timestamp to time past the hour
    See description of "_tph_to_timestamp"
    """
    return int('0' + Bits(uintbe=t,length=32).bin[:-1],2)

  @property
  def timestamp(self):
    """Current timestamp
    """
    tph = self._get_tph(datetime.utcnow())
    return self._tph_to_timestamp(tph)

  @property
  def clocktime(self):
    """Current clocktime.
    Defined in section 5.2.8 in Ref. [2]
    """
    utcnow = datetime.utcnow()
    return (self._get_h(utcnow), self.timestamp)

  def send_start_pdu(self, real_wold_time=None, simulation_time=None):
    """Send a Start / Resume PDU.
    """
    self.requests += 1
    if type(real_wold_time) is str:
      rwt_h, rwt_tph = self.datetime_to_disclocktime(real_wold_time)
    else:
      rwt_h, rwt_tph = self.clocktime

    if type(simulation_time) is str:
      st_h, st_tph = self.datetime_to_disclocktime(simulation_time)
    else:
      st_h, st_tph = self.clocktime

    pdu_start = {
          'pduHeader':self._make_pdu_header(13,5,88),
          'originatingEntityId':self.simulationManagementEntityId,
          'receivingEntityId':{
              'site': ALL_SITES,
              'application':ALL_APPLIC,
              'entity': ALL_ENTITIES,
          },
          'realWorldTime': {
              'hour':rwt_h,
              'timePastHour':rwt_tph,
          },
          'simulationTime':{
              'hour':st_h,
              'timePastHour':st_tph,
          },
          'requestId':self.requests,
      }
    self._send_pdu(pdu_start)

  def send_entity_state_pdu(self, idn, lat, lon, alt, yaw, pitch,
    roll, u, v, w, yaw_rot, pitch_rot, roll_rot, dis_entity, text,
    nav_lights=0, deck_lights=False, nav_shapes=0):
    """Send the state of an entity.

    Arguments:

      id:
        Unique identification number for the entity.
      lat:
        Latitude in WGS84 (deg).
      lon:
        Longitude in WGS84 (deg).
      alt:
        Altitude in WGS84 (m).
      yaw:
        Yaw angle (deg)
      pitch:
        Pitch angle (deg)
      roll:
        Roll anlge (deg)
      u:
        Longitudinal speed (m/s).
      v:
        Transverse speed (m/s).
      w:
        Upward speed (m/s).
      yaw_rot:
        Yaw angle rate of turn (rad/s).
      pitch_rot:
        Pitch angle rate of turn (rad/s).
      roll_rot:
        Roll angle rate of turn (rad/s).
      dis_entity (str):
        Text used as a key for the dictionary containing the custom DIS
        entities for the EMSN (default value = 'generic_ship_contianer_class_medium').
      text (str):
        Text for identifying the entity (max 11 characters).
      nav_lights (enum):
        Enum value that describes if additional navigational lights are set:
          0: None
          1: Not under command/Aground (red/red)
          2: Restricted ability to maneuver (red/white/red)
          3: Constrained by her draught (red/red/red)
          4: Fishing with Trawler (green/white)
          5: Fishing (red/white)
          6: Pilot (white/red)
          7: Anchor (white)
          8: Power driven vessel underway
      deck_lights (bool):
        True corresponds to deck lights on.
      nav_shapes (enum):
        Enum value that describes if additional navigational shapes are set:
          0: None
          1: Not under command (Ball/Ball)
          2: Restricted ability to maneuver (Ball/Diamond/Ball)
          3: Constrained by her draught (Cylinder)
          4: Fishing with or without Trawler (Cone down/Cone up)
          5: Aground (ball/ball/ball)
          7: Anchor (ball)


    Output:

      NONE

    """

    # Entity Location and Orientation
    # Transformation to DIS coordinate System
    position = [lat, lon, alt]
    attitude = [yaw, pitch, roll]
    XYZ, euler = geo.to_dis(position, attitude)
    X, Y, Z = XYZ
    psi, theta, phi = euler

    # Entity Markings
    if len(text) > 11:
      raise Exception('The text cannot have more than 11 characters.')
    characters = [ord(i) for i in text] + [0]*(11 - len(text))

    # Lights and shapes (Entity Appearance)
    # Ref: [1] (3.1.1.2)
    ea = ['0']*32
    if nav_lights != 0:
      if nav_lights == 8:
        ea[12] = '1'
      elif nav_lights == 7:
        ea[16:19] = ['1','1','1']
      elif nav_lights == 6:
        ea[16:19] = ['1','1','0']
      elif nav_lights == 5:
        ea[16:19] = ['1','0','1']
      elif nav_lights == 4:
        ea[16:19] = ['1','0','0']
      elif nav_lights == 3:
        ea[16:19] = ['0','1','1']
      elif nav_lights == 2:
        ea[16:19] = ['0','1','0']
      elif nav_lights == 1:
        ea[16:19] = ['0','0','1']
      else:
        raise Exception('Navigation lights must be an integer between 0 and 8')
    if deck_lights:
      ea[29] = '1'
    if nav_shapes != 0:
      if nav_shapes == 7:
        ea[24:27] = ['1','1','1']
      elif nav_shapes == 6:
        ea[24:27] = ['1','1','0']
      elif nav_shapes == 5:
        ea[24:27] = ['1','0','1']
      elif nav_shapes == 4:
        ea[24:27] = ['1','0','0']
      elif nav_shapes == 3:
        ea[24:27] = ['0','1','1']
      elif nav_shapes == 2:
        ea[24:27] = ['0','1','0']
      elif nav_shapes == 1:
        ea[24:27] = ['0','0','1']
      else:
        raise Exception('Navigation shapes must be an integer between 0 and 7')
    ea = ''.join(ea)

    entity_state_pdu = {
        'pduHeader': self._make_pdu_header(1,1,144),
        'entityId': {
            'site': self.siteId,
            'application':self.applicationId,
            'entity':idn,
        },
        'forceId':1,
        'numberOfArticulationParameters':0,
        'entityType': emsn_dis_entities[dis_entity],
        'alternativeEntityType': emsn_dis_entities[dis_entity],
        'entityLinearVelocity': {
            'x':u,
            'y':v,
            'z':w,
        },
        'entityLocation': {
            'x':X,
            'y':Y,
            'z':Z,
        },
        'entityOrientation': {
            'psi':psi,
            'theta':theta,
            'phi':phi,
        },
        'entityMarking': {
            'characterSet':1, # Value of 1 means ASCII
            'characters':characters,
        },
        'deadReckoningParameters':{
            'deadReckoningAlgorithm':4, # High Speed or Maneuvering Entity with Extrapolation of Orientation
            'otherParameters': '0'*120, # Zero indicates "None"
            'entityLinearAcceleration': {
                'x':0,
                'y':0,
                'z':0,
            },
            'entityAngularVelocity':{
                'psi':yaw_rot,
                'theta':pitch_rot,
                'phi':roll_rot,
            },
        },
        'entityAppearance': ea,
        'capabilities':[False]*32,
    }
    self._send_pdu(entity_state_pdu)

  def send_stop_pdu(self):
    self.requests += 1
    rwt_h, rwt_tph = self.clocktime
    pdu_stop = {
      'pduHeader':self._make_pdu_header(14,5,320),
      'originatingEntityId':self.simulationManagementEntityId,
      'receivingEntityId':{
        'site': ALL_SITES,
        'application': ALL_APPLIC,
        'entity': ALL_ENTITIES,
      },
      'realWorldTime': {
        'hour':rwt_h,
        'timePastHour':rwt_tph,
      },
      'reason':2,
      'frozenBehavior':2,
      'padding':'1'*16,
      'requestId':self.requests,
    }
    self._send_pdu(pdu_stop)

  def send_transmitter_pdu(self, idn, ridn, state, x, y, z, lat, lon, alt, yaw, pitch, roll):
    """

    Args:
    -----

    idn (integer):
      Entity Id of the sending entity.

    ridn (integer):
      Radio Id within the sending entity (idn).

    state (enum):
      0: Off
      1: On but not transmitting
      2: On and transmitting

    x, y, z:
      Coordinates in meters for the top of the AIS antenna in the
      DIS local coordinate system: (i.e. origo at the centre of the
      bounding volume of the vessel; +x towards the bow; +y towards
      starboard; +z downwards).

    lat (float):
      Latitude of the vessel in WGS84 (deg).

    lon (float):
      Longitude of the vessel in WGS84 (deg).

    alt (float):
      Altitude of the vessel in WGS84 (m).

    loa (float):
      Lenght Overall of the vessel in meters.

    b (float):
      Beam (aka. breadth) of the vessel in meters.

    yaw, pitch, roll:
      Rotation angles in degrees for the vessel.

    All preassigned values for the Transmitter PDU are defined in
    Ref. [1] Section 3.1.1.5

    """

    if ridn == 1:
      frequency = 161975000
    elif ridn == 2:
      frequency = 162025000
    else:
      raise Exeption(f'No pre-assigned frequency for Radio Id {ridn}')

    # Transformation to DIS coordinate System
    X, Y, Z = geo.xyz2XYZ((lat, lon, alt), (yaw, pitch, roll), (x, y, z))

    transmitter_pdu = {
        'pduHeader': self._make_pdu_header(25,4,104),
        'entityId': {
            'site': self.siteId,
            'application':self.applicationId,
            'entity':idn,
        },
        'radioId':1,
        'radioEntityType': {
            'entityKind': 7,
            'domain': 3,
            'country': 0,
            'category':0,
            'nomenclatureVersion': 0,
            'nomenclature': 0,
        },
        'transmitState': state,
        'inputSource': 0,
        'padding':'0'*16,
        'antennaLocation': {
            'X': X,
            'Y': Y,
            'Z': Z,
        },
        'relativeAntennaLocation': {
            'x': x,
            'y': y,
            'z': z,
        },
        'antennaPatternType': 0,
        'antennaPatternLength': 0,
        'frequency': frequency,
        'transmitFrequencyBandwidth':25000,
        'power':40.0,
        'modulationType': {
            'spreadSpectrum': [False]*16,
            'major': 0,
            'detail': 0,
            'system': 0,
        },
        'cryptoSystem': 0,
        'cryptoKeyId': 0,
        'lengthOfModulationParameters': 0,
        'padding2':'0'*24,
    }
    self._send_pdu(transmitter_pdu)

  def send_receiver_pdu(self, idn, ridn, state):
    """pduType = 27
    """
    receiver_pdu = {
      'pduHeader': self._make_pdu_header(27,4,36),
      'entityId': {
        'site': self.siteId,
        'application':self.applicationId,
        'entity':idn,
      },
      'radioId': ridn,
      'receiverState': state,
      'padding':'0'*16,
      'receivedPower': 0.0,
      'transmitterEntityId': {
          'site': 0,
          'application':0,
          'entity':0,
      },
      'transmitterRadioId': 0,
    }
    self._send_pdu(receiver_pdu)

  def send_signal_pdu(self, idn, data):
    """
    pduType = 26
    """
    signal_pdu =  {
      'pduHeader': self._make_pdu_header(26,4,36),
      'entityId': {
            'site': self.siteId,
            'application':self.applicationId,
            'entity':idn,
       },
      'radioId':1,
      'encodingScheme':'1000000000000000',
      'TDLtype':0,
      'sampleRate':1,
      'dataLength':int(len(data)*8),
      'samples':0,
      'data':data
    }
    self._send_pdu(signal_pdu)

  def send_data_pdu(self):
    pass

  def send_data_query_pdu(self):
    pass

  def datetime_to_clocktime(self, datetime_str):
    """Transforms an ISO datetime string in LOCAL TIME to
    to DIS UTC clocktime.
    """
    dt = datetime.fromisoformat(datetime_str)
    offset = datetime.utcnow() - datetime.now()
    dt_utc = dt + offset
    return (self._get_h(dt_utc), self._tph_to_timestamp(self._get_tph(dt_utc)))
