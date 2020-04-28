
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
	dis1.send_entity_state_pdu(dummy_entity)
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	XYZ, euler = geoutils.to_dis(dummy_entity.position, dummy_entity.attitude)
	X, Y, Z = XYZ
	psi, theta, phi = euler
	assert pdu['entityLocation']['x'] == approx(X)
	assert pdu['entityLocation']['y'] == approx(Y)
	assert pdu['entityLocation']['z'] == approx(Z)
	assert pdu['entityOrientation']['psi'] == approx(psi)
	assert pdu['entityOrientation']['theta'] == approx(theta)
	assert pdu['entityOrientation']['phi'] == approx(phi)

def test_send_stop_pdu():
	dis1.send_stop_pdu()
	pdus = dis2.receive_pdus()
	assert len(pdus) == 1
	pdu = pdus[0]
	assert pdu['realWorldTime']['hour'] == get_h()
	assert_tph(timestamp_to_tph(pdu['realWorldTime']['timePastHour']), get_tph())















