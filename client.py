##############################
#client.py
#Author: Ryan Hardy
#This program receives data from a server running on a Raspberry Pi. 
#To establish a connection with the Pi, please enter an IP address and Port number. 
#Hint: Use 8888 for the Port.
##############################
from socket import *
import sys
import argparse

#Check args
if len(sys.argv) < 2:
	print("This program receives data from a server running on a Raspberry Pi. To establish a connection with the Pi, please enter an IP address and Port number. Hint: Use 8888 for the Port.")
	exit()
else:
	#Create socket to read data
	host = sys.argv[1]
	port = int(sys.argv[2])

	with socket(AF_INET, SOCK_STREAM) as s:
		try: 
			s.connect((host, port))
		except error:
			print("No connection was found, closing the program! Make sure the server is running and the IP and Port is correct.")
			exit()
		while True:
			data = s.recv(1024)
			print(data)
