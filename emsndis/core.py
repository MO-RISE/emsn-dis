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


	def _make_pdu_header(self, pduType, protocolFamily, length):
		"""Make a PDU header

		Used by all the PDUs sent by the EMSN-DIS interface.
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
		print('Sent Start / Resume PDU')

	#def latlon2dis(self,lat,lon):
	#	return geo.lla2ecef((lat,lon,0))

	#def dis2latlon(self, entityLocation):
 	#	ecef = [v for v in entityLocation.values()]
	#	lat, lon, height = gps.ecef2lla(ecef)
	#	return [lat, lon]

	def send_entity_state_pdu_old(self, entity, dis_entity='generic_ship_container_class_medium'):
		"""Send the state of an entity.

		Arguments:

			entity (object)
				The entity is an object with the following properties:

					id: unique identification number for the entity.

					position: (lon, lat, altitude) in WGS84.

					attitude: (yaw, pitch, roll) angles in radians.

					lin_vel: (u, v, w) in m/s.

					ang_vel: () in rad/s

			dis_entity (str):

				Text used as a key for the dictionary containing the custom DIS
				entities for the EMSN (default value = 'generic_ship_contianer_class_medium').

		Output:

			None
		"""
		position = entity.position
		attitude = entity.attitude
		XYZ, euler = geo.to_dis(position, attitude)
		X, Y, Z = XYZ
		psi, theta, phi = euler
		# print([geo.rad2deg(v) for v in euler])
		#dis_position = self.latlon2dis(entity.position[0],entity.position[1])
		entity_state_pdu = {
		    'pduHeader': self._make_pdu_header(1,1,144),
		    'entityId': {
		        'site': self.siteId,
		        'application':self.applicationId,
		        'entity':entity.id,
		    },
		    'forceId':1,
		    'numberOfArticulationParameters':0,
		    'entityType': emsn_dis_entities[dis_entity],
		    'alternativeEntityType': emsn_dis_entities[dis_entity],
		    'entityLinearVelocity': {
		        'x':entity.lin_vel[0],
		        'y':entity.lin_vel[1],
		        'z':entity.lin_vel[2],
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
		        'characterSet':1,
		        'characters':[79, 83, 32, 50, 0, 0, 0, 0, 0, 0, 0],
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
		            'psi':entity.ang_vel[0],
		            'theta':entity.ang_vel[1],
		            'phi':entity.ang_vel[2],
		        },
		    },
		    'entityAppearance':'0'*32,
		    'capabilities':[False]*32,
		}
		self._send_pdu(entity_state_pdu)

	def send_entity_state_pdu(self, idn, lat, lon, alt, yaw, pitch,
		roll, u, v, w, yaw_rot, pitch_rot, roll_rot, dis_entity, text):
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
				Yaw angle (rad)
			pitch:
				Pitch angle (rad)
			roll:
				Roll anlge (rad)
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

		Output:

			NONE

		"""
		position = [lat, lon, alt]
		attitude = [yaw, pitch, roll]
		XYZ, euler = geo.to_dis(position, attitude)
		X, Y, Z = XYZ
		psi, theta, phi = euler
		if len(text) > 11:
			raise Exception('The text cannot have more than 11 characters.')
		characters = [ord(i) for i in text] + [0]*(11 - len(text))
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
		        'characterSet':1,
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
		    'entityAppearance':'0'*32,
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

	def create_entity(self, entity):
		pass

	def _make_entity_pdu(self):
		pass

	def send_transmitter_pdu(self):
		pass

	def send_receiver_pdu(self):
		pass

	def send_signal_pdu(self):
		pass

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
