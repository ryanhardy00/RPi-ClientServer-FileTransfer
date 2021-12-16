##############################################
# MonitoringApp.py
# Author: Ryan Hardy
# This program monitors a potentiometer and sonic sensor, reads their values, and
# depending on the mode adds the data to a .csv file or prints the data to the console.
# The distance is measured in cm and will show  as 0 if the data is out of range.
# The potentiometer is measured as a percentage of the value.
#Change the mode by commenting/un-commenting the lines below!
# Required libraries listed below, BCM pins used.
# File will be names sensorDataHH_MM_SS_MS.csv, where HH is the hou, MM is the minute, SS is the second,
# and MS is the millisecond that the file was created. EX: sensorData14_21_44_47.csv
# File will be saved in home/pi/Documents/
#############################################

import RPi.GPIO as GPIO
import time
from datetime import datetime
from time import sleep
import csv
import spidev

#################
# BUTTON SELECT
# Button Mode select not implemented!
# Comment/uncomment and rerun to change modes!
mode = "MS"
#mode = "ORD"
#mode = "RDM"
################

print("This program monitors a potentiometer and sonic sensor, reads their values, and ")
print("depending on the mode adds the data to a file or prints the data to the console.")
print("IMPORTANT: Button functionality is NOT implemented! Change the mode by commenting/un-commenting the mode lines!")
print("Current mode: " + mode)

# Check mode to create file
if mode == "ORD" or mode == "RDM":
    filename = "/home/pi/Documents/" + "sensorData" + datetime.now().strftime("%H_%M_%S_%f")[:-4] + ".csv"
    print("Recording data to " + filename)
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        writer.writerow(["Time", "Sensor", "Value"])

# Define pins
BuzzerPin = 18
LEDPin = 14
timer = 0
LEDTimer = 0
LEDState = 0
buttonPin = 16
GPIO_TRIGGER = 25
GPIO_ECHO = 24
green = 6
red = 5
blue = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# GPIO Setups
GPIO.setup(red, GPIO.OUT) 
GPIO.setup(green, GPIO.OUT)
GPIO.setup(blue, GPIO.OUT)

Freq = 100

RED = GPIO.PWM(red, Freq)  
GREEN = GPIO.PWM(green, Freq)
BLUE = GPIO.PWM(blue, Freq)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(BuzzerPin, GPIO.OUT)
GPIO.setup(LEDPin, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

global Buzz 
Buzz = GPIO.PWM(BuzzerPin, 100) 
Buzz.start(50)

buzzFreq = 0
rate = 0

RBG = "Red: 255, Green: 0, Blue: 0"

# Start RGB LED if mode selected
if mode == "MS" or mode == "RDM":
    RED.start(100)
    GREEN.start(100)
    BLUE.start(100)

# Return RGB value and turn on LED
def getRGBVal(percentage):
    if percentage < 8.33:
        RED.ChangeDutyCycle(100)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 255, Green: 0, Blue: 0"
    elif percentage >= 8.33 and percentage < 16.66:
        RED.ChangeDutyCycle(75)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(25)
        RBG = "Red: 191, Green: 65, Blue: 0"
    elif percentage >= 16.66and percentage < 24.99:
        RED.ChangeDutyCycle(50)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(50)
        RBG = "Red: 128, Green: 127, Blue: 0"
    elif percentage >= 24.99 and percentage < 33.32:
        RED.ChangeDutyCycle(25)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(75)
        RBG = "Red: 64, Green: 191, Blue: 0"
    elif percentage >= 33.32 and percentage <= 41.65:
        RED.ChangeDutyCycle(1)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(100)
        RBG = "Red: 0, Green: 255, Blue: 0"
    elif percentage >= 41.65 and percentage <= 49.98:
        RED.ChangeDutyCycle(1)
        BLUE.ChangeDutyCycle(25)
        GREEN.ChangeDutyCycle(75)
        RBG = "Red: 0, Green: 191, Blue: 64"
    elif percentage >= 49.98 and percentage <= 58.31:
        RED.ChangeDutyCycle(1)
        BLUE.ChangeDutyCycle(50)
        GREEN.ChangeDutyCycle(50)
        RBG = "Red: 0, Green: 128, Blue: 127"
    elif percentage >= 58.31 and percentage <= 66.64:
        RED.ChangeDutyCycle(1)
        BLUE.ChangeDutyCycle(75)
        GREEN.ChangeDutyCycle(25)
        RBG = "Red: 0, Green: 64, Blue: 191"
    elif percentage >= 66.64 and percentage <= 74.97:
        RED.ChangeDutyCycle(1)
        BLUE.ChangeDutyCycle(100)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 0, Green: 0, Blue: 255"
    elif percentage >= 74.97 and percentage <= 83.3:
        RED.ChangeDutyCycle(25)
        BLUE.ChangeDutyCycle(75)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 64, Green: 0, Blue: 191"
    elif percentage >= 83.3 and percentage <= 91.63:
        RED.ChangeDutyCycle(50)
        BLUE.ChangeDutyCycle(50)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 127, Green: 0, Blue: 128"
    elif percentage >= 91.63 and percentage <= 100:
        RED.ChangeDutyCycle(75)
        BLUE.ChangeDutyCycle(25)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 191, Green: 0, Blue: 64"
    else:
        RED.ChangeDutyCycle(100)
        BLUE.ChangeDutyCycle(1)
        GREEN.ChangeDutyCycle(1)
        RBG = "Red: 255, Green: 0, Blue: 0"
    return RBG

# Enable SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # open spi port 0, device (CS) 0
spi.max_speed_hz=1000000

def ReadChannel(channel):
    response = spi.xfer2([1,(8+channel)<<4,0])   #1000 0000    Start byte 00000001, channel selection: end byte
    data = ((response[1]&3) << 8) + response[2]         #011
    return data
 
# Function to convert data to voltage level,
# rounded to specified number of decimal places.
# Fucntions below taken from example code on Moodle
def ConvertVolts(data, places):
    volts = (data * 3.3) / float(1023)
    volts = round(volts, places)
    return volts
 
pot_channel = 0

def getPotPercentage():
    pot_level = ReadChannel(pot_channel)
    pot_volts = ConvertVolts(pot_level, 2)
    potPercentage= round((pot_volts / 3.3) * 100, 2)
    
    return potPercentage

# Return distance from sonic sensor
def distance(): 
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    StartTime = time.time()
    StopTime = time.time()
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
    TimeElapsed = StopTime - StartTime
    distance = (TimeElapsed * 34300) / 2 # Sonis speed / 2 (measured val is roundtrip, / 2 to get one-way distance)
 
    return distance

while True:
    try:
        if(mode == "MS"):
            # MS mode
            GPIO.output(LEDPin, False)
            dist = distance()
            if dist > 20:
                print("Distance is out of range ( >20 cm), value will be stored as a zero!")
                dist = 0
            print("Distance = " + str(round(dist,2)) + " cm Buzzer Frequency: " + str(round(buzzFreq,0)) + "Hz")
            time.sleep(.1)
            timer = timer + 1
            # Run sonic sensor every .1 sec, pot sensor ever .5 sec
            if timer == 5:
                potPercentage = getPotPercentage()
                RGBValue = getRGBVal(potPercentage)
                print("Pot Percentage: " + str(potPercentage) + "% RGB Values: " + RGBValue)
                timer = 0
            # Change buzzer freq. based on distance
            if dist > 20:
                buzzFreq = 4000
                Buzz.stop()
            elif dist < 20 and dist > 4:
                buzzFreq = 100 + ((dist - 4) * 118.75)
                Buzz.start(50)
            elif dist < 4:
                buzzFreq = 100
                Buzz.start(50)
                sleep(.5)
                Buzz.stop()
            Buzz.ChangeFrequency(buzzFreq)
           
        elif(mode == "RDM"):
            # RDM Mode
            GPIO.output(LEDPin, True)
            dist = distance()
            if dist > 20:
                print("Distance is out of range ( >20 cm), value will be stored as a zero!")
                dist = 0
            print("Distance = " + str(round(dist,2)) + " cm Buzzer Frequency: " + str(round(buzzFreq,0)) + "Hz")
            time.sleep(.1)
            timer = timer + 1
            if timer == 5:
                potPercentage = getPotPercentage()
                getRGBVal(potPercentage)
                print("Pot Percentage: " + str(potPercentage) + "%")
                potPercentageField = [str(datetime.now().time()), "Potentiometer", str(potPercentage)]
                timer = 0
                # Store pot value in file
                with open(filename, "a") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(potPercentageField)
            field = [str(datetime.now().time()), "Ultrasonic", str(round(dist,2))]
            # Store sonic sensor in file
            with open(filename, "a") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(field)
            if dist > 20:
                buzzFreq = 4000
                Buzz.stop()
            elif dist < 20 and dist > 4:
                buzzFreq = 100 + ((dist - 4) * 118.75)
                Buzz.start(50)
            elif dist < 4:
                buzzFreq = 100
                Buzz.start(50)
                sleep(.5)
                Buzz.stop()
            Buzz.ChangeFrequency(buzzFreq)
        
        elif(mode == "ORD"):
            # ORD Mode
            # Same as RDM except without monitoring
            Buzz.stop()
            dist = distance()
            if dist > 20:
                dist = 0
            time.sleep(.1)
            timer = timer + 1
            if timer == 5:
                potPercentage = getPotPercentage()
                getRGBVal(potPercentage)
                potPercentageField = [str(datetime.now().time()), "Potentiometer", str(potPercentage)]
                timer = 0
                with open(filename, "a") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(potPercentageField)
            field = [str(datetime.now().time()), "Ultrasonic", str(round(dist,2))]
            with open(filename, "a") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(field)  
            # Toggle LED  
            LEDTimer = LEDTimer + 1
            if LEDTimer == 10:
                if LEDState == 0:
                    LEDState = 1
                    GPIO.output(LEDPin, True)
                elif LEDState == 1:
                    LEDState = 0
                    GPIO.output(LEDPin, False)
                LEDTimer = 0
        elif(mode == "OFF"):
            # Turn off all pins
            GPIO.output(LEDPin, False)
            GPIO.cleanup()
            Buzz.stop()
            spi.close()
            exit()
    except KeyboardInterrupt:
        print("Keyboard interrupt triggered, exiting program!")
        mode = "OFF"
