import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from emsndis import multicast

def test_send_and_receive():
	message = 'Bananas'
	ms1 = multicast.Socket()
	ms2 = multicast.Socket()
	ms3 = multicast.Socket()
	ms1.send(message.encode())
	data2 = ms2.receive()
	data3 = ms3.receive()
	assert data2.decode() == message
	assert data3.decode() == message
