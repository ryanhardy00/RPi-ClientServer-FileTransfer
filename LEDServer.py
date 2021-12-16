##############################
#LEDServer.py
#Author: Ryan Hardy
#This is a server designed to run on a Raspberry Pi that will send messages
#to a client machine. It also has switches that will cause LEDs to blink, and
#switch 3 will shut down the Pi. No arguments are needed.
##############################

from gpiozero import Button, LED
from time import sleep
import RPi.GPIO as gpio
import os
from subprocess import call
from socket import *
import threading

led1 = LED(16)
led2 = LED(18)

SW1 = Button(8)
SW2 = Button(10)
SW3 = Button(12)

count = 0

host = "0.0.0.0"
port = 8888

#Create socket
s = socket(AF_INET, SOCK_STREAM)
s.bind((host, port))   
s.listen(10)

#Sending messages thread
def clientThread(conn):
    data = "{SW1: Released, SW2: Released}"
    while True:
        if SW1.is_pressed and SW2.is_pressed:
            data = "{SW1: Pressed, SW2: Pressed}"
        elif SW1.is_pressed:
            data = "{SW1: Pressed, SW2: Released}"
        elif SW2.is_pressed:
            data = "{SW1: Released, SW2: Pressed}"
        else:
            data = "{SW1: Released, SW2: Released}"
        if SW3.is_pressed:
            data = "Closing connection!"
        conn.send(data)
        sleep(1)
    conn.close()

#LED functions
def setLED1():
    while(True):
        if SW1.is_pressed:
            led1.on()
            sleep(1)
            led1.off()
            sleep(1)
            
def setLED2():
    while(True):
        if SW2.is_pressed:
            led2.on()
            sleep(.5)
            led2.off()
            sleep(.5)

#Switch 3 functionality
def sw3():
    while(True):
        if SW3.is_pressed:
            count = count + 1
            sleep(1)
            if count == 3:
                call("sudo nohup shutdown -h now", shell=True)
        else:
            count = 0

#Create threads
t1 = threading.Thread(target = setLED1)
t2 = threading.Thread(target = setLED2)
t4 = threading.Thread(target = sw3)
t1.setDaemon(True)
t2.setDaemon(True)
t4.setDaemon(True)
t1.start()
t2.start()
t4.start()

print("This is a server designed to run on a Raspberry Pi that will send messages to a client machine. It also has switches that will cause LEDs to blink, and switch 3 will shut down the Pi. No arguments are needed.")

while True:
    conn, addr = s.accept()
    t3 = threading.Thread(target = clientThread, args = (conn,)).start()