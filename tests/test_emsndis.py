
import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pytest import approx

import time
from bitstring import Bits

from emsndis import EmsnDis
from emsndis import geoutils
from datetime import datetime
from collections import namedtuple

# Gateway for simulator 1 (siteId 1, applicationId 1, excerciseId 99)
dis1 = EmsnDis(1,1,99)

# Gateway for simulator 2 (siteId 2, applicationId 1, excerciseId 99)
dis2 = EmsnDis(2,1,99)

# Dummy entityType
dummy_entity_type = {
	'entityKind': 1,
	'domain': 3,
	'country': 0,
	'category': 61,
	'subcategory': 2,
	'specific': 1,
	'extra': 2,
}

# Dummy entity
Entity = namedtuple('Entity','id position attitude lin_vel ang_vel')
dummy_entity = Entity(1, [57.66, 11.76, 0],[0,0,0], [0,0,0], [0,0,0])

def get_tph():
	"""Get synthetic time past the hour.
	"""
	return int((datetime.utcnow().timestamp() % 3600)*((2**31) - 1)/3600)

def get_h():
	"""Get hours since 00:00 UTC January 1, 1970
	"""
	return int(datetime.utcnow().timestamp() // 3600)

def assert_tph(tph_a, tph_b):
	if tph_a > tph_b:
		tph_ratio = tph_b / tph_a
	else:
		tph_ratio = tph_a / tph_b
	assert tph_ratio > 0.98 and tph_ratio < 1.00

def timestamp_to_tph(t):
	return int('0' + Bits(uintbe=t,length=32).bin[:-1],2)


# TESTS
# -----

def test_timestamp():
	t = dis1.timestamp
	tph = timestamp_to_tph(t)
	assert_tph(tph, get_tph())
	assert type(t) is int

def test_clocktime():
	h, t = dis1.clocktime
	assert type(h) is int
	assert type(t) is int
	assert h == get_h()
	tph = timestamp_to_tph(t)
	assert_tph(tph, get_tph())

def test_datetime_to_clocktime():
	now = datetime.now()
	h, t = dis1.datetime_to_clocktime(now.strftime('%Y-%m-%d %H:%M:%S'))
	assert type(h) is int
	assert type(t) is int
	assert h == get_h()
	tph = timestamp_to_tph(t)
	assert_tph(tph, int((now.timestamp() % 3600)*(2**31 - 1)/3600))


def test_send_start_pdu():
	dis1.send_start_pdu()
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	assert pdu['pduHeader']['pduType'] == 13
	assert_tph(timestamp_to_tph(pdu['pduHeader']['timestamp']), get_tph())
	assert pdu['realWorldTime']['hour'] == get_h()
	assert_tph(timestamp_to_tph(pdu['realWorldTime']['timePastHour']), get_tph())
	assert pdu['receivingEntityId']['site'] == 65535
	assert pdu['receivingEntityId']['application'] == 65535
	assert pdu['receivingEntityId']['entity'] == 65535


def test_send_entity_state_pdu():
	idn = 989
	lat = 19
	lon = 12.1
	alt = 0
	yaw = 1.1
	pitch = 1.2
	roll = 1.3
	u = 10
	v = 0.1
	w = 0
	yaw_rot = 0.1
	pitch_rot = 0.3
	roll_rot = 0.2
	text = 'Hello'
	dis_entity = 'generic_ship_container_class_small'

	# Without lights and shapes
	dis1.send_entity_state_pdu(idn, lat, lon, alt, yaw, pitch, roll,
		u, v, w, yaw_rot, pitch_rot, roll_rot, dis_entity, text)
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	XYZ, euler = geoutils.to_dis([lat, lon, alt], [yaw, pitch, roll])
	X, Y, Z = XYZ
	psi, theta, phi = euler
	assert pdu['entityLocation']['x'] == approx(X)
	assert pdu['entityLocation']['y'] == approx(Y)
	assert pdu['entityLocation']['z'] == approx(Z)
	assert pdu['entityOrientation']['psi'] == approx(psi)
	assert pdu['entityOrientation']['theta'] == approx(theta)
	assert pdu['entityOrientation']['phi'] == approx(phi)
	assert pdu['entityMarking']['characters'] == [ord(i) for i in text] + \
		[0]*(11 - len(text))
	assert pdu['entityAppearance'] == '0'*32

	# With light and shapes
	dis1.send_entity_state_pdu(idn, lat, lon, alt, yaw, pitch, roll,
		u, v, w, yaw_rot, pitch_rot, roll_rot, dis_entity, text, deck_lights=True,
		nav_lights=1, nav_shapes=3)
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	XYZ, euler = geoutils.to_dis([lat, lon, alt], [yaw, pitch, roll])
	X, Y, Z = XYZ
	psi, theta, phi = euler
	ea = ['0']*32
	ea[29] = '1' # Deck lights
	ea[16:19] = ['0','0','1'] # Navigation lights
	ea[24:27] = ['0','1','1'] # Navigation shapes
	ea = ''.join(ea)
	print(ea)
	print(pdu['entityAppearance'])
	assert pdu['entityAppearance'] == ea

def test_send_stop_pdu():
	dis1.send_stop_pdu()
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	assert pdu['realWorldTime']['hour'] == get_h()
	assert_tph(timestamp_to_tph(pdu['realWorldTime']['timePastHour']), get_tph())

def test_send_transmitter_pdu():
	idn = 1
	ridn = 1
	state = 2
	x, y, z = (10,10,10)
	lat, lon, alt = (0,0,0)
	yaw, pitch, roll = (3.1416,0,0)
	dis1.send_transmitter_pdu(idn, ridn, state, x, y, z, lat, lon, alt, yaw,
		pitch, roll)
	pdus = dis2.receive_pdus()
	pdu = pdus[0]
	assert pdu['pduHeader']['pduType'] == 25
	assert pdu['frequency'] == 161975000

def test_send_signal_pdu():
	idn = 1
	data = (1).to_bytes(4,'big')
	dis1.send_signal_pdu(idn, data)
	pdus = dis2.receive_pdus()
	pdu = pdus[0]
	assert pdu['pduHeader']['pduType'] == 26
	assert pdu['dataLength'] == len(data)*8
	assert pdu['data'] == data

def test_send_receiver_pdu():
	idn = 1
	ridn = 1
	state = 2
	dis1.send_receiver_pdu(idn, ridn, state)
	pdus = dis2.receive_pdus()
	pdu = pdus[0]
	assert pdu['pduHeader']['pduType'] == 27
	assert pdu['receiverState'] == state
	assert pdu['radioId'] == 1












