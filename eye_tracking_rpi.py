import time
import keyboard

import cv2
import numpy as np
import dlib
from math import hypot
from playsound import playsound

from picamera.array import PiRGBArray
from picamera import PiCamera

import os
import RPi.GPIO as GPIO
import requests

import sys

vlcPass = "helloWorld" #The Lua password you set in the VLC Player settings
vlcIp = "192.168.123.1" #Your PC's ip adress in the local network

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21,GPIO.OUT)

camera = PiCamera()    #Initiate the rpi camera
camera.resolution = (640, 480)    #Base image resolution
#camera.rotation = 180
camera.framerate = 30    #Base image FPS
rawCapture = PiRGBArray(camera, size=(640,480))    #Camera setup and base image resolution

time.sleep(0.1)    #Warm up camera

totalWidth = 640    #Image Width
totalHeight = 480    #Image Height
divider = 2    #Divide full image by X for faster face detection

shutDownTime = 3 #Shutdown after holding button for X seconds

maxThresh = 130
minThresh = 0

thresh_r = 80    #Default threshold for detecting the darkest spot on the right eye
thresh_l = 80    #Default threshold for detecting the darkest spot on the right eye
lowLimit = 0.32    #Lower boundary for triggering
highLimit = 0.68    #Higher boundary for triggering
faceTimer = 30    #Perform full re-calibration after 30 frames without a face

autoCorrect = True    #Toggle the use of automatic threshold correction

threshHigh = 35    #Automatically correct threshold towards this value
leftCalib = False    #Internal variable for the left eye (full) calibration status
rightCalib = False    #Internal variable for the right eye (full) calibration status

textSize = 2    #Default text size

triggerLim = 3;    #Trigger after X frames over or under the high- and lowLimit

firstRun = True    #Internal variable to identify a first-run
leftRoi = 0    #Internal variable holding the left eye coordinates
rightRoi = 0    #Internal variable holding the right eye coordinates

triggerL = 0    #Internal variable holding the left eye trigger frame count
triggerR = 0    #Internal variable holding the right eye trigger frame count
triggerV = 0

faceless = 0    #Internal variable holding the "face missing" frame count befor full calibration

pause = False

lWidth = 0
rWidth = 0

vertRateL = 50;
vertRateR = 50;

keyboardCheck = 0;

nofacemode = True

playCalib = True

mode = "channel"

currentVolume = 125

buttonHold = 0 #Timestamp for when the button was pressed
buttonState = 0 #Current status of the button
shuttingDown = 0 #Are we shutting down already?

GPIO.setup(4, GPIO.IN) #Capacitive Button bin
GPIO.add_event_detect(4, GPIO.BOTH) #Capacitive Button interrupt

def key_press(key):
    print key.name
    global lowLimit
    global highLimit
    #print event.Ascii
    if key.name == "z":
        print "> SenseUp"
        lowLimit += 0.02
        highLimit -= 0.02
        print "Limits: " + str(lowLimit) + "/" + str(highLimit)
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=sense_" + str(lowLimit) + "-" + str(highLimit), timeout=0.1)
        except: 
            print("Sense Request Failed!")
    elif key.name == "t":
        print "> SenseDown"
        lowLimit -= 0.02
        highLimit += 0.02
        print "Limits: " + str(lowLimit) + "/" + str(highLimit)
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=sense_" + str(lowLimit) + "-" + str(highLimit), timeout=0.1)
        except: 
            print("Sense Request Failed!")
    elif key.name == "w":
        print "> Up"
        lowLimit = 0.32    #Lower boundary for triggering
        highLimit = 0.68 
        print "Limits: " + str(lowLimit) + "/" + str(highLimit)
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=sense_" + str(lowLimit) + "-" + str(highLimit), timeout=0.1)
        except: 
            print("Sense Request Failed!")
    elif key.name == "s":
        print "> Down"
        modeTrigger()
    elif key.name == "a":
        print "> Left"
        lTrigger()
    elif key.name == "d":
        print "> Right"
        rTrigger()

def on_error(error):
    print error

def modeTrigger():
    global mode
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    if mode == "channel":
        mode = "volume"
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=mode_volume", timeout=0.1)
        except: 
            print("Notify Request Failed!")
    elif mode == "volume":
        mode = "channel"
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=mode_channel", timeout=0.1)
        except: 
            print("Notify Request Failed!")
    print(" > Mode = " + mode)

def lTrigger():
    global currentVolume
    print("LEFT Triggered")
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    if mode == "channel":
        try:
            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=pl_previous", timeout=0.1)
        except:
            print("VLC Request Failed!")
                        
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=ChannelDown", timeout=0.1)
        except: 
            print("Notify Request Failed!")
                            
    elif mode == "volume":
        currentVolume -= 25
        if currentVolume < 0:
            currentVolume = 0
        print("Current volume: " + str(currentVolume))
        try:
            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=volume&val=" + str(currentVolume), timeout=0.1)
        except:
            print("VLC Request Failed!")
                        
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=Volume_" + str(currentVolume), timeout=0.1)
        except: 
            print("Notify Request Failed!")
            
def rTrigger():
    global currentVolume
    print("Right Triggered")
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(21, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(21, GPIO.LOW)
    if mode == "channel":
        try:
            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=pl_next", timeout=0.1)
        except:
            print("VLC Request Failed!")
                        
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=ChannelUp", timeout=0.1)
        except: 
            print("Notify Request Failed!")
                            
    elif mode == "volume":
        currentVolume += 25
        if currentVolume >= 249:
            currentVolume = 255 
        print("Current volume: " + str(currentVolume))
        try:
            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=volume&val=" + str(currentVolume), timeout=0.1)
        except:
            print("VLC Request Failed!")
                        
        try:
            requests.get("http://" + vlcIp + ":3000/notify/?message=Volume_" + str(currentVolume), timeout=0.1)
        except: 
            print("Notify Request Failed!")

def triggered(arg): #Capacitive button callback
    global keyboard
    global buttonHold
    global buttonState
    global pause
    buttonState = GPIO.input(4)
    if buttonState:
        #print("Pressed")
        buttonHold = time.time()
    else:
        releaseTime = time.time() - buttonHold
        #print("Released after " + str(releaseTime))
        if releaseTime < shutDownTime:
            if not pause:
                print("Paused!")
                try:
                    requests.get("http://" + vlcIp + ":3000/notify/?message=paused", timeout=0.1)
                except:
                    print("Pause Request Failed!")
                GPIO.output(21, GPIO.HIGH)
                time.sleep(0.3)
                GPIO.output(21, GPIO.LOW)
                time.sleep(0.5)
                pause = not pause
            else: 
                print("Resumed!")
                keyboard.on_press(key_press)
                try:
                    requests.get("http://" + vlcIp + ":3000/notify/?message=resumed", timeout=0.1)
                except:
                    print("Pause Request Failed!")
                GPIO.output(21, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(21, GPIO.LOW)
                time.sleep(0.1)                
                GPIO.output(21, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(21, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(21, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(21, GPIO.LOW)
                time.sleep(0.5)
                pause = not pause
                
GPIO.add_event_callback(4, triggered) #Capacitive button add callback


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_5_face_landmarks.dat")
#predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
font = cv2.FONT_HERSHEY_PLAIN

def midpoint(p1 ,p2):    #Gets the eye bounding box middle point
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)

def rescale_img(frame, percent=75):    #Scales the full res image by divider value
    width = int(totalWidth / divider)
    height = int(totalHeight / divider)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)

def getRoi(eye_points, facial_landmarks):    #Get the eye's region of interest
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(eye_points[1]).y)
    eyeWidth = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
    leftTop = (int(facial_landmarks.part(eye_points[0]).x), int(facial_landmarks.part(eye_points[0]).y - eyeWidth / 4))
    rightBot = (int(facial_landmarks.part(eye_points[1]).x), int(facial_landmarks.part(eye_points[1]).y + eyeWidth / 5))

    cv2.rectangle(gray,leftTop,rightBot,(0,255,255),1)

    return [leftTop, rightBot]



def getRate(box, thresh):    #Get the current viewpoint angle
    roi = frame[box[2]:box[3], box[0]:box[1]]
    rows, cols, _ = roi.shape
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray_roi = cv2.GaussianBlur(gray_roi, (7, 7), 0)
    
    _, threshold = cv2.threshold(gray_roi, thresh, 255, cv2.THRESH_BINARY_INV)
    _, contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    
    #print(str(cols) + " | " + box[4]) //Display current eye difference

    global lWidth
    global rWidth

    if box[4] == "right":
        rWidth = cols
    elif box[4] == "left":
        lWidth = cols

    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
    
        leftright = x + int(w/2)
        vert = y + int(h/2)
        #print(box[4] + str(rows))
        vertAngle = (vert / (float(rows) / 100))

        global leftCalib
        global rightCalib

        global vertRateL
        global vertRateR

        if box[4] == "right":
            vertRateR = vertAngle
        elif box[4] == "left":
            vertRateL = vertAngle

        angle = (leftright / (float(cols) / 100))
        
        if leftCalib and rightCalib:
            if autoCorrect:
                correct(box[4], int(w / (float(cols) / 100)), int(h / (float(cols) / 100)))
        else:
            fullCalib(box[4], (w / (float(cols) / 100)))
        

        cv2.rectangle(roi, (x, y), (x + w, y + h), (255, 0, 255), 1)
        
        cv2.line(roi, (x + int(float(w)/2), 0), (x + int(float(w)/2), rows), (255, 255,0), 1)
        cv2.line(roi, (0, y + int(float(h)/2)), (cols, y + int(float(h)/2)), (0, 255,0), 1)

        cv2.line(roi, (int(cols*0.3), 0), (int(cols*0.3), rows), (255, 255,255), 1)
        cv2.line(roi, (int(cols*0.7), 0), (int(cols*0.7), rows), (255, 255,255), 1)

        #####cv2.imshow(("Eye_" + box[4]), roi)
        #####cv2.imshow(("Threshold_" + box[4]), threshold)

        return (leftright / (float(cols) / 100)) / 100

    global thresh_r
    global thresh_l

    if box[4] == "right":
        thresh_r = thresh_r + 1
    elif box[4] == "left":
        thresh_l = thresh_l + 1

def correct(eye, value, valueH):    #Auto correct towards the threshHigh value
    global thresh_r
    global thresh_l

    #print(str(valueH) + " | " + str(value))

    if eye == "right":
        if value > threshHigh and thresh_r > minThresh:
            thresh_r = thresh_r - 1
        elif value < threshHigh and thresh_r < maxThresh:
            thresh_r = thresh_r + 1

    elif eye == "left":
        if value > threshHigh and thresh_l > minThresh:
            thresh_l = thresh_l - 1
        elif value < threshHigh and thresh_l < maxThresh:
            thresh_l = thresh_l + 1

def init():    #Initialize the script
    cv2.namedWindow("Frame",cv2.WINDOW_NORMAL)
    cv2.namedWindow("Threshold_left",cv2.WINDOW_NORMAL)
    cv2.namedWindow("Threshold_right",cv2.WINDOW_NORMAL)
    cv2.namedWindow("Eye_left",cv2.WINDOW_NORMAL)
    cv2.namedWindow("Eye_right",cv2.WINDOW_NORMAL)

    #cv2.setWindowProperty('Frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.moveWindow("Threshold_left", int(totalWidth * 0.82), 80)
    cv2.moveWindow("Threshold_right", int(totalWidth * 0.82), 220)
    cv2.moveWindow("Eye_left", int(totalWidth * 0.82), 360)
    cv2.moveWindow("Eye_right",int(totalWidth * 0.82), 500)
    cv2.moveWindow("Frame", 0,0)

def fullCalib(eye, value):    #Perform one step towards thefull calibration
    global thresh_r
    global thresh_l

    if eye == "right":
        if value >= threshHigh:
            thresh_r = thresh_r - 3
        else:
            global rightCalib
            rightCalib = True
            print("RIGHT CALIBRATED")
    elif eye == "left":
        if value >= threshHigh:
            thresh_l = thresh_l - 3
        else:
            global leftCalib
            leftCalib = True
            print("LEFT CALIBRATED")


def getWDiff():
    if rWidth > lWidth:
        return lWidth / (float(rWidth) / 100)
    elif lWidth > rWidth:
        return rWidth / (float(lWidth) / 100)
    else:
        return 100

for piFrame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    try:
        frame = piFrame.array
        
        #sys.stdout.write(frame.tostring())
    
        if firstRun:
            firstRun = False
            #init()
           
        if buttonState and time.time() > (buttonHold + shutDownTime) and not shuttingDown:
            shuttingDown = 1
            GPIO.output(21, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(21, GPIO.LOW)
            os.system("sudo shutdown -h now")
            print("Shutting down")
           
        if pause:
            #print("Paused")
            rawCapture.truncate(0)    #Empty the buffer
            leftCalib = False
            rightCalib = False
            thresh_l = 80
            thresh_r = 80
            continue
            
            
        if rightCalib == False or leftCalib == False:
            GPIO.output(21, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(21, GPIO.LOW)
    
        small = rescale_img(frame, percent=500)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    
    
        faces = detector(gray)
    
        #####cv2.imshow("Frame", frame)
    
        faceCount = len(faces)
    
        if faceCount == 0:
            faceless = faceless + 1
        else:
            faceless = 0
    
        if faceless == faceTimer:    #Perform full calibration after not having a face for X frames
            nofacemode = True
            faceless = 0
            try:
                requests.get("http://" + vlcIp + ":3000/notify/?message=noface", timeout=0.1)
            except:
                print("Pause Request Failed!")
    
        for face in faces:
            leftRoi = 0
            landmarks = predictor(gray, face)
            #leftRoi = getRoi([36, 39], landmarks)    #36,39 for 68-Point landmarks
            #rightRoi = getRoi([42,45], landmarks)    #42,45 for 68-Point landmarks
            leftRoi = getRoi([1,0], landmarks)     #2,3 for 5-point landmarks
            rightRoi = getRoi([2,3], landmarks)    #1,3 for 5-point landmarks
    
        if faceCount != 0:
            if nofacemode:
                print("Found face")
                nofacemode = False
                try:
                    requests.get("http://" + vlcIp + ":3000/notify/?message=facefound", timeout=0.1)
                except:
                    print("face Request Failed!")
                
            oneX, oneY = leftRoi[0]
            twoX, twoY = leftRoi[1]
        
            oneX = oneX * divider
            twoX = twoX * divider
            oneY = oneY * divider
            twoY = twoY * divider
        
            leftRate = getRate([oneX, twoX, oneY, twoY, "left"], thresh_l)
        
            oneX, oneY = rightRoi[0]
            twoX, twoY = rightRoi[1]
        
            oneX = oneX * divider
            twoX = twoX * divider
            oneY = oneY * divider
            twoY = twoY * divider
            
            rightRate = getRate([oneX, twoX, oneY, twoY, "right"], thresh_r)
        
            widthDiff = getWDiff()
        
    
            #print(widthDiff)
    
            currentRate = 50
            currentVert = 50
    
            
            if leftRate is not None and rightRate is not None and faceCount == 1:
                currentRate = (leftRate + rightRate) / 2
                #print("AVG : " + str(currentRate))
                currentVert = (vertRateR + vertRateL) / 2
            
            elif leftRate is not None and rightRate is None and faceCount == 1:
                #print("Left : " + str(leftRate))
                currentRate = leftRate
                currentVert = vertRateL
            
            elif leftRate is None and rightRate is not None and faceCount == 1:
                #print("Right : " + str(rightRate))
                currentRate = rightRate
                currentVert = vertRateR
            #else:
            #    cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,0,255),30)
            #    cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 0,255), 15)
            #    cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 0,255), 15)
            
            #print triggerV
            
            if currentVert > 60 and currentRate < highLimit and currentRate > lowLimit and int(widthDiff) > 85:
                triggerV += 1
                triggerR = 0
                triggerL = 0
                if triggerV == triggerLim:
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    if mode == "channel":
                        mode = "volume"
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=mode_volume", timeout=0.1)
                        except: 
                            print("Notify Request Failed!")
                    elif mode == "volume":
                        mode = "channel"
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=mode_channel", timeout=0.1)
                        except: 
                            print("Notify Request Failed!")
                    print(" > Mode = " + mode)
    
            elif currentRate > highLimit and int(widthDiff) > 85:
                cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 0,255), 15)
                triggerL += 1
                triggerR = 0
                if triggerL == triggerLim:
                    print("LEFT Triggered")
                    cv2.putText(frame, "> LEFT", (30, int(totalHeight * 0.8)), font, 10, (0, 255, 0), 10)
                    cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,255,0),30)
                    #playsound('clickOn.mp3')
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    if mode == "channel":
                        try:
                            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=pl_previous", timeout=0.1)
                        except:
                            print("VLC Request Failed!")
                            
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=ChannelDown", timeout=0.1)
                        except: 
                            print("Notify Request Failed!")
                            
                    elif mode == "volume":
                        currentVolume -= 25
                        if currentVolume < 0:
                            currentVolume = 0
                        print("Current volume: " + str(currentVolume))
                        try:
                            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=volume&val=" + str(currentVolume), timeout=0.1)
                        except:
                            print("VLC Request Failed!")
                            
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=Volume_" + str(currentVolume), timeout=0.1)
                        except: 
                            print("Notify Request Failed!")
    
            elif currentRate < lowLimit and int(widthDiff) > 85:
                cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 0,255), 15)
                triggerR += 1
                triggerL = 0
                if triggerR == triggerLim:
                    print("RIGHT Triggered")
                    cv2.putText(frame, "> RIGHT", (30, int(totalHeight * 0.8)), font, 10, (0, 255, 0), 10)
                    cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,255,0),30)
                    #playsound('clickOff.mp3')
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(21, GPIO.LOW)
                    if mode == "channel":
                        try:
                            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=pl_next", timeout=0.3)
                        except:
                            print("VLC Request Failed!")
                            
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=ChannelUp", timeout=0.3)
                        except: 
                            print("Notify Request Failed!")
                    elif mode == "volume":
                        currentVolume += 25
                        if currentVolume >= 249:
                            currentVolume = 255 
                        print("Current volume: " + str(currentVolume))
                        try:
                            requests.get("http://" + vlcPass + "@" + vlcIp + ":8080/requests/status.xml?command=volume&val=" + str(currentVolume), timeout=0.3)
                        except:
                            print("VLC Request Failed!")
                            
                        try:
                            requests.get("http://" + vlcIp + ":3000/notify/?message=Volume_" + str(currentVolume), timeout=0.3)
                        except: 
                            print("Notify Request Failed!")
            else: 
                triggerL = 0
                triggerR = 0
                triggerV = 0
    
            if leftCalib == False and rightCalib == False:
                cv2.putText(frame, "Calibrating...", (30, int(totalHeight * 0.9)), font, (textSize * 2), (0, 255, 0), 3)
    
            if widthDiff < 85:
                cv2.putText(frame, "Turn towards camera!", (30, int(totalHeight * 0.9)), font, (textSize * 1.5), (255, 255, 255), 4)
                cv2.putText(frame, "Turn towards camera!", (30, int(totalHeight * 0.9)), font, (textSize * 1.5), (0, 0, 255), 3)
    
    
            #cv2.line(gray, (int(480 * currentRate), 0), (int(480 * currentRate), 270) , (0, 0,255), 4)
        
            cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 255,255), 2)
            cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 255,255), 2)
        
            cv2.putText(frame, "Focus position: {:.2f}".format(currentRate), (30, 50), font, textSize, (0, 0, 0), 3)
            cv2.putText(frame, "Threshhold_L: {}".format(thresh_l), (30, 120), font, textSize, (0, 0, 0), 3)
            cv2.putText(frame, "Threshhold_R: {}".format(thresh_r), (30, 190), font, textSize, (0, 0, 0), 3)
            #cv2.putText(frame, "Faces: {}".format(faceCount), (30, 260), font, textSize, (0, 0, 0), 3)
            cv2.putText(frame, "Diff: {:.1f} %".format(widthDiff), (30, 260), font, textSize, (0, 0, 0), 3)
        
        
            cv2.line(frame, (0, int(totalHeight * 0.6)), (totalWidth,int(totalHeight * 0.6)) , (0, 0,255), 2)
            cv2.circle(frame, (int(totalWidth * currentRate), int(totalHeight * 0.6)), 50, (0, 0, 255), 15)
        
            #cv2.imshow("Threshold", threshold)
            #####cv2.imshow("Frame", frame)
            #cv2.imshow("gray roi", gray_roi)
            #cv2.imshow("gray", gray)
            #roi = rescale_frame(roi, percent=500)
            #cv2.imshow("Roi", roi)
    
        else:
            #print("No faces")
            cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 255,255), 2)
            cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 255,255), 2)
            cv2.line(frame, (0, int(totalHeight * 0.6)), (totalWidth,int(totalHeight * 0.6)) , (0, 0,255), 2)
            cv2.circle(frame, (int(totalWidth * 0.5), int(totalHeight * 0.6)), 50, (0, 0, 255), 15)
    
    
        key = cv2.waitKey(30)
        if key == 27:
            hookman.start()
            break
        elif key == 38:
            print("+1 threshR")
            thresh_r = thresh_r + 1
        elif key == 40:
            print("-1 threshR")
            thresh_r = thresh_r - 1
        elif key == 39:
            print("+1 threshL")
            thresh_l = thresh_l + 1
        elif key == 37:
            print("-1 threshL")
            thresh_l = thresh_l - 1
        elif key == 99:
            thresh_l = 100
            thresh_r = 100
            leftCalib = False
            rightCalib = False
        
        rawCapture.truncate(0)    #Empty the buffer
        
    except:
        print("Error converting image")
        rawCapture.truncate(0)    #Empty the buffer

cv2.destroyAllWindows()
