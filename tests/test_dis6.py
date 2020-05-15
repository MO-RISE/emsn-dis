import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from emsndis import dis6

def assert_pdus(pdu_a, pdu_b):
    for k, v in pdu_a.items():
        if type(v) is dict:
            assert_pdus(v, pdu_b[k])
        elif type(v) is float:
            assert v == pytest.approx(pdu_b[k])
        else:
            assert v == pdu_b[k]

def test_send_receive_start_pdu():
    pdu_start = {
        'pduHeader':{
            'protocolVersion':5,
            'excerciseId':1,
            'pduType':13,
            'protocolFamily':2,
            'timestamp':10,
            'length':10,
            'padding':0,
        },
        'originatingEntityId':{
            'site': 1,
            'application':2,
            'entity':1,
        },
        'receivingEntityId':{
            'site': 1,
            'application':2,
            'entity':1,
        },
        'realWorldTime': {
            'hour':1213323,
            'timePastHour':233,
        },
        'simulationTime':{
            'hour':12122,
            'timePastHour':234,
        },
        'requestId':111,
    }
    pdu_size = int(352/8)
    s = dis6.serialize(pdu_start)
    data = s.getvalue()
    assert len(data) == pdu_size
    pdu_rec = dis6.deserialize(data)
    assert_pdus(pdu_start, pdu_rec)

def test_send_receive_stop_pdu():
    pdu_stop = {
        'pduHeader':{
            'protocolVersion':5,
            'excerciseId':1,
            'pduType':14,
            'protocolFamily':2,
            'timestamp':10,
            'length':10,
            'padding':0,
        },
        'originatingEntityId':{
            'site': 1,
            'application':2,
            'entity':1,
        },
        'receivingEntityId':{
            'site': 1,
            'application':2,
            'entity':1,
        },
        'realWorldTime': {
            'hour':1213323,
            'timePastHour':233,
        },
        'reason':2,
        'frozenBehavior':2,
        'padding':'1'*16,
        'requestId':111,
    }
    pdu_size = int(320/8)
    s = dis6.serialize(pdu_stop)
    data = s.getvalue()
    assert len(data) == pdu_size
    pdu_rec = dis6.deserialize(data)
    assert_pdus(pdu_stop, pdu_rec)

def test_send_receive_entity_state_pdu():

    pdu_state = {
    'pduHeader': {
        'protocolVersion': 5,
        'excerciseId': 1,
        'pduType':1,
        'protocolFamily': 2,
        'timestamp': 10,
        'length': 10,
        'padding':0,
    },
    'entityId': {
        'site': 1,
        'application':2,
        'entity':1,
    },
    'forceId':1,
    'numberOfArticulationParameters':0,
    'entityType': {
        'entityKind':1,
        'domain':2,
        'country':1,
        'category':3,
        'subcategory':2,
        'specific':1,
        'extra':1
    },
    'alternativeEntityType': {
        'entityKind':1,
        'domain':2,
        'country':1,
        'category':3,
        'subcategory':2,
        'specific':1,
        'extra':1
    },
    'entityLinearVelocity': {
        'x':1,
        'y':2,
        'z':3,
    },
    'entityLocation': {
        'x':1.99,
        'y':2,
        'z':3,
    },
    'entityOrientation': {
        'psi':1,
        'theta':2,
        'phi':3.1,
    },
    'entityMarking': {
        'characterSet':1,
        'characters':[33]*11,
    },
    'deadReckoningParameters':{
        'deadReckoningAlgorithm':1,
        'otherParameters': '1'*120,
        'entityLinearAcceleration': {
            'x':1,
            'y':2,
            'z':3,
        },
        'entityAngularVelocity':{
            'psi':1,
            'theta':2,
            'phi':3,
        },
    },
    'entityAppearance':'1'*32,
    'capabilities':[False]*32,
    }
    stream = dis6.serialize(pdu_state)
    data = stream.getvalue()
    assert len(data) == 144
    pdu_deserialized = dis6.deserialize(data)
    assert_pdus(pdu_state, pdu_deserialized)

def test_send_receive_transmitter_pdu():
    trans_pdu = {
        'pduHeader': {
        'protocolVersion': 5,
        'excerciseId': 1,
        'pduType':25,
        'protocolFamily': 1,
        'timestamp': 10,
        'length': 10,
        'padding':0,
        },
        'entityId': {
            'site': 1,
            'application':2,
            'entity':1,
        },
        'radioId':33,
        'radioEntityType': {
            'entityKind': 1,
            'domain': 2,
            'country': 3,
            'category':2,
            'nomenclatureVersion': 3,
            'nomenclature': 4,
        },
        'transmitState': 3,
        'inputSource': 2,
        'padding':'0'*16,
        'antennaLocation': {
            'X': 0,
            'Y': 3,
            'Z': 3
        },
        'relativeAntennaLocation': {
            'x': 2,
            'y': 5,
            'z': 6
        },
        'antennaPatternType': 6,
        'antennaPatternLength': 0,
        'frequency': 23233,
        'transmitFrequencyBandwidth':33.22,
        'power': 32.233,
        'modulationType': {
            'spreadSpectrum': [False]*16,
            'major': 14,
            'detail': 12,
            'system': 12
        },
        'cryptoSystem': 3,
        'cryptoKeyId': 14,
        'lengthOfModulationParameters': 0,
        'padding2':'0'*24,
    }
    stream = dis6.serialize(trans_pdu)
    data = stream.getvalue()
    assert len(data) == 832/8
    pdu_deserialized = dis6.deserialize(data)
    assert_pdus(trans_pdu, pdu_deserialized)

def test_send_receive_signal_pdu():
    signal_pdu =  {
        'pduHeader': {
            'protocolVersion': 5,
            'excerciseId': 1,
            'pduType':26,
            'protocolFamily': 1,
            'timestamp': 10,
            'length': 10,
            'padding':0,
        },
        'entityId': {
            'site': 1,
            'application':2,
            'entity':1,
        },
        'radioId':1,
        'encodingScheme':'0'*16,
        'TDLtype':2,
        'sampleRate':1,
        'dataLength':32,
        'samples':1,
        'data':(32).to_bytes(4,'big')
    }
    stream = dis6.serialize(signal_pdu)
    data = stream.getvalue()
    assert len(data) == (256 + signal_pdu['dataLength'])/8
    pdu_deserialized = dis6.deserialize(data)
    assert_pdus(signal_pdu, pdu_deserialized)

def test_send_receive_receiver_pdu():
    receiver_pdu = {
        'pduHeader': {
        'protocolVersion': 5,
        'excerciseId': 1,
        'pduType':27,
        'protocolFamily': 1,
        'timestamp': 10,
        'length': 10,
        'padding':0,
        },
        'entityId': {
            'site': 1,
            'application':2,
            'entity':1,
        },
        'radioId':1,
        'receiverState': 2,
        'padding':'0'*16,
        'receivedPower': 40.0,
        'transmitterEntityId': {
            'site': 1,
            'application':2,
            'entity':1,
        },
        'transmitterRadioId': 1,
    }
    stream = dis6.serialize(receiver_pdu)
    data = stream.getvalue()
    assert len(data) == 288/8
    pdu_deserialized = dis6.deserialize(data)
    assert_pdus(receiver_pdu, pdu_deserialized)

