##############################################
# ViewData.py
# Author: Ryan Hardy
#
# This program transfers a file from a raspberry Pi and plots the data using matplotlib.
# Call the program using python ViewData.py [ip] [mode] [filename]
# ip is the IP of the RPi, the mode is 0 or 1
# The filename is optional, depending on the mode
#
# In mode 0, the file is only transferred and nothing is plotted. If no filename is given, 
# all files in home/pi/Documents/ are transferred to ./DataFiles on the local machine.
# In mode 1, a filename must be given for the data to be plotted. If the file is not 
# already on the host machine, it will be downloaded from the RPi and then plotted.
# You will be asked to enter your RPi's password if the file needs to be transferred.
# It is assumed your pi is named "pi".
# If this is not the case you will need to change the "username" in the ssh.connect lines
#
# Required libraries listed below. All were pre-installed on my version of Anaconda for Windows, but
# your results may be different.
#############################################

import sys
import os
import argparse
from paramiko import SSHClient
from scp import SCPClient
import paramiko
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import numpy as np
import platform

# Check # of args
if len(sys.argv) != 3:
	if len(sys.argv) != 4:
		print("Too few or too many arguments were entered, try again!")
		exit()
	else:
		pass

# Get args
filename = ""
rpiIP = str(sys.argv[1])
mode = int(sys.argv[2])

# Define vars
xSound = []
ySound = []
xPot = []
yPot = []
deltaTimeSound = 0
xSoundDelta = []
deltaTimePot = 0
xPotDelta = []

if len(sys.argv) == 4:
	filename = str(sys.argv[3])

if mode == 1 and len(sys.argv) == 3:
	print("Please add the file to plot to your argument after entering your mode select.")
	exit()

# Create ./DataFiles if it does not already exist
if not os.path.exists("DataFiles"):
	os.makedirs("DataFiles")
if mode == 0 and filename == "":
	# Transfer all files
	piPass = input("Enter you Pi's password:")
	# Check OS for file structure
	if platform.system() == "Windows":
		localFilePath = r'.\DataFiles'
	else:
		localFilePath = './DataFiles'
	ssh = SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=rpiIP, port = '22', username='pi', password=piPass)
	scp = SCPClient(ssh.get_transport(), sanitize = lambda x: x)
	scp.get('/home/pi/Documents/*', localFilePath)
	scp.close()

elif mode == 0:
	# Transfer entered file
	piPass = input("Enter you Pi's password:")
	# Check OS for file structure
	if platform.system() == "Windows":
		localFilePath = r'.\DataFiles'
		localFilePath = localFilePath + "\\" + filename
	else:
		localFilePath = './DataFiles'
		localFilePath = localFilePath + "/" + filename
	remoteFilePath = "/home/pi/Documents/*" + filename
	if os.path.exists(localFilePath):
		print("File already exists on your local host, ending program!")
	ssh = SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=rpiIP, port = '22', username='pi', password=piPass)
	scp = SCPClient(ssh.get_transport(), sanitize = lambda x: x)
	scp.get(remoteFilePath, localFilePath)
	scp.close()

if mode == 1:
	# Plot mode
	localPath = ".\\DataFiles\\" + filename
	if not os.path.exists(localPath):
		piPass = input("The file you entered is not on your local host. Enter you Pi's password to download it and then plot the data:")
		# Check OS for file structure
		if platform.system() == "Windows":
			localFilePath = r'.\DataFiles'
			localFilePath = localFilePath + "\\" + filename
		else:
			localFilePath = './DataFiles'
			localFilePath = localFilePath + "/" + filename
		remoteFilePath = "/home/pi/Documents/*" + filename
		ssh = SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(hostname = rpiIP, port = '22', username='pi', password=piPass)
		scp = SCPClient(ssh.get_transport(), sanitize = lambda x: x)
		scp.get(remoteFilePath, localFilePath)
		scp.close()

	# Read .csv, separate data into lists based on sensor
	with open(localPath, "r") as csvfile:
		reader = csv.reader(csvfile, delimiter = ",")
		next(reader)
		for row in reader:
			if row[1] == "Ultrasonic":
				xSound.append(row[0])
				ySound.append(float(row[2]))
			if row[1] == "Potentiometer":
				xPot.append(row[0])
				yPot.append(float(row[2]))

	# Strip datetime to be a timedelta, where 0 is the first time data was taken and time progresses from there
	for i in range(len(xSound)):
		xSoundStripped = datetime.strptime(xSound[0], "%H:%M:%S.%f")
		xSoundStripped2 = datetime.strptime(xSound[i], "%H:%M:%S.%f")
		deltaTimeSound = xSoundStripped2 - xSoundStripped
		deltaTimeSoundSec = deltaTimeSound.total_seconds()
		xSoundDelta.append(deltaTimeSoundSec)
	for i in range(len(xPot)):
		xPotStripped = datetime.strptime(xPot[0], "%H:%M:%S.%f")
		xPotStripped2 = datetime.strptime(xPot[i], "%H:%M:%S.%f")
		deltaTimePot = xPotStripped2 - xPotStripped
		deltaTimePotSec = deltaTimePot.total_seconds()
		xPotDelta.append(deltaTimePotSec)

	saveInput = input("Would you like to save the plot as a jpg? Press s to save, any other key to plot without saving!")
	print("Plotting the data, this may take a while!")

	# Plot
	fig, axs = plt.subplots(2)
	fig.suptitle('Plotted Data')
	axs[0].plot(xSoundDelta, ySound)
	axs[0].set_xlabel('Elapsed time from first recorded entry (seconds)')
	axs[0].set_ylabel('Distance (cenitimeters)')
	axs[1].plot(xPotDelta, yPot)
	axs[1].set_xlabel('Elapsed time from first recorded entry (seconds)')
	axs[1].set_ylabel('Potentiometer Value (Percentage)')
	axs[1].set_ylim([0,100])

	# Save if requested
	if saveInput == "s":
		newFilename = os.path.splitext(filename)[0] + ".jpg"
		fig.savefig(newFilename)
		print("File saved in current directory as " + newFilename)

	plt.show()