#!/usr/bin/env python

"""
emsndis.multicast
~~~~~~~~~~~~~~~~~
A module for UDP multicasting.

Usage:
------

>> sock = Socket(multicast_addr='239.239.239.239', multicast_port=20000, timeout=0.2, host_addr='10.84.103.15')
>> sent_data = struct.pack('>I',1234)
>> sock.send(sent_data)
>> sock.send(f'Hello from {name}'.encode())
>> received_data = sock.receive()

References:
	https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html
	https://docs.python.org/3.7/library/socket.html
"""

import socket
import signal
import time
import sys


class Socket:

	def __init__(self,
		multicast_addr='224.10.10.10', 
		multicast_port=9999,
		timeout=0.2,
		host_addr='0.0.0.0',
		bufsize=1024,
		verbose=False,
		**kwargs):
		"""Initiate multicast socket
		"""
		self.host_addr = host_addr
		self.multicast_port = multicast_port
		self.multicast_groups = []
		self.bufsize = bufsize

		# Create an UDP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set timeout to 'receive data'
		self.sock.settimeout(timeout)
		
		# Allow the reuse of local addresses
		self.sock.setsockopt(
			socket.SOL_SOCKET,
			socket.SO_REUSEADDR,
			1
		)

		# Bind to the server address
		self.sock.bind((host_addr, multicast_port))

		# Add membership to a multicast group
		self.join_multicast_group(multicast_addr)

		# Verbose
		if verbose:
			print('Created a UDP multicast socket:')
			print(f' Multicast address: {multicast_addr}')
			print(f' Multicast port: {multicast_port}')
			print(f' Host address: {host_addr}')
			print('\n')


	def join_multicast_group(self, multicast_addr):
		"""Add a membership to a multicast group.
		"""
		self.multicast_groups.append(multicast_addr)
		membership = socket.inet_aton(multicast_addr) + \
			socket.inet_aton(self.host_addr)
		self.sock.setsockopt(
			socket.IPPROTO_IP, # Layer to handle the option
			socket.IP_ADD_MEMBERSHIP,
			membership
		)

	def send(self, data):
		for mc in self.multicast_groups:
			self.sock.sendto(data, (mc, self.multicast_port))

	def receive(self):
		try:
			data = self.sock.recv(self.bufsize)
		except socket.timeout:
			pass
		else:
			return data