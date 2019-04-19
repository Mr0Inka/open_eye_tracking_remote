import cv2
import numpy as np
import dlib
from math import hypot
#from playsound import playsound

from picamera.array import PiRGBArray
from picamera import PiCamera
import time

camera = PiCamera()    #Initiate the rpi camera
camera.resolution = (1280, 720)    #Base image resolution
camera.framerate = 30    #Base image FPS
rawCapture = PiRGBArray(camera, size=(1280,720))    #Camera setup and base image resolution

time.sleep(0.1)    #Warm up camera

totalWidth = 1280    #Image Width
totalHeight = 720    #Image Height
divider = 6    #Divide full image by X for faster face detection

thresh_r = 80    #Default threshold for detecting the darkest spot on the right eye
thresh_l = 80    #Default threshold for detecting the darkest spot on the right eye
lowLimit = 0.35    #Lower boundary for triggering
highLimit = 0.65    #Higher boundary for triggering
faceTimer = 15    #Perform full re-calibration after 30 frames without a face

autoCorrect = True    #Toggle the use of automatic threshold correction

threshHigh = 40    #Automatically correct threshold towards this value
leftCalib = False    #Internal variable for the left eye (full) calibration status
rightCalib = False    #Internal variable for the right eye (full) calibration status

textSize = 2    #Default text size

triggerLim = 3;    #Trigger after X frames over or under the high- and lowLimit

firstRun = True    #Internal variable to identify a first-run
leftRoi = 0    #Internal variable holding the left eye coordinates
rightRoi = 0    #Internal variable holding the right eye coordinates

triggerL = 0    #Internal variable holding the left eye trigger frame count
triggerR = 0    #Internal variable holding the right eye trigger frame count

leftRate = None   #Internal variable for view angle left
rightRate = None   #Internal variable for view angle left

faceless = 0    #Internal variable for counting the frames without a face

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
font = cv2.FONT_HERSHEY_PLAIN

def midpoint(p1 ,p2):   #Gets the midpoint
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)

def rescale_img(frame, percent=75):    #Rescales raw image by divider value
    width = int(totalWidth / divider)
    height = int(totalHeight / divider)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation =cv2.INTER_AREA)

def getRoi(eye_points, facial_landmarks):    #Gets the region of interes (eye coordinates)
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(eye_points[1]).y)
    eyeWidth = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
    leftTop = (int(facial_landmarks.part(eye_points[0]).x - eyeWidth / 10), int(facial_landmarks.part(eye_points[0]).y - eyeWidth / 4))
    rightBot = (int(facial_landmarks.part(eye_points[1]).x + eyeWidth / 10), int(facial_landmarks.part(eye_points[1]).y + eyeWidth / 5))

    cv2.rectangle(gray,leftTop,rightBot,(0,255,255),1)

    return [leftTop, rightBot]



def getRate(box, thresh):    #gets the current view angle
    roi = frame[box[2]:box[3], box[0]:box[1]]
    rows, cols, _ = roi.shape
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray_roi = cv2.GaussianBlur(gray_roi, (7, 7), 0)
    
    _, threshold = cv2.threshold(gray_roi, thresh, 255, cv2.THRESH_BINARY_INV)
    _, contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    

    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
    
        leftright = x + int(w/2)

        global leftCalib
        global rightCalib

        if cols < 3:
            return None

        angle = (float(leftright) / (float(cols) / 100))
        
        
        
        if leftCalib and rightCalib:
        	if autoCorrect:
        	    correct(box[4], int(w / (float(cols) / 100)))
        else:
        	fullCalib(box[4], (w / (float(cols) / 100)))
        

        cv2.rectangle(roi, (x, y), (x + w, y + h), (255, 0, 255), 1)
        
        cv2.line(roi, (x + int(w/2), 0), (x + int(w/2), rows), (255, 255,0), 1)
        cv2.line(roi, (0, y + int(h/2)), (cols, y + int(h/2)), (0, 255,0), 1)

        cv2.line(roi, (int(cols*0.3), 0), (int(cols*0.3), rows), (255, 255,255), 1)
        cv2.line(roi, (int(cols*0.7), 0), (int(cols*0.7), rows), (255, 255,255), 1)

        cv2.imshow(("Eye_" + box[4]), roi)
        cv2.imshow(("Threshold_" + box[4]), threshold)

        print(float(leftright) / (float(cols) / 100))

        return float(leftright) / (float(cols) / 100) / 100

    global thresh_r
    global thresh_l

    if box[4] == "right":
    	thresh_r = thresh_r + 1
    elif box[4] == "left":
    	thresh_l = thresh_l + 1

def correct(eye, value):   #Auto correct step
    global thresh_r
    global thresh_l

    if eye == "right":
        if value > threshHigh:
            thresh_r = thresh_r - 1
        elif value < threshHigh:
            thresh_r = thresh_r + 1

    elif eye == "left":
        if value > threshHigh:
            thresh_l = thresh_l - 1
        elif value < threshHigh:
            thresh_l = thresh_l + 1

def init():    #Initiate the script on startup
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

def fullCalib(eye, value):    #Perform a full calib step
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




for piFrame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    
    frame = piFrame.array

    if firstRun:
        firstRun = False
        init()

    small = rescale_img(frame, percent=500)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    faces = detector(gray)

    cv2.imshow("Frame", frame)    #Show camera image directly on startup

    faceCount = len(faces)

    if faceCount == 0:
    	faceless = faceless + 1
    else:
    	faceless = 0

    # if faceless == faceTimer:    #Perform full calib after empty face frames
    # 	leftCalib = False
    # 	rightCalib = False
    # 	thresh_l = 100
    # 	thresh_r = 100
    # 	print("Recalibrating")

    for face in faces:
        leftRoi = 0
        landmarks = predictor(gray, face)
        leftRoi = getRoi([36, 39], landmarks)
        rightRoi = getRoi([42,45], landmarks)

    if faceCount != 0:
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
    
        
    
        currentRate = 50
        
        if leftRate is not None and rightRate is not None and faceCount == 1:
            currentRate = (leftRate + rightRate) / float(2)
            #print("AVG : " + str(currentRate))
        
        elif leftRate is not None and rightRate is None and faceCount == 1:
            #print("Left : " + str(leftRate))
            currentRate = leftRate
        
        elif leftRate is None and rightRate is not None and faceCount == 1:
            #print("Right : " + str(rightRate))
            currentRate = rightRate
        else:
            cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,0,255),30)
            cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 0,255), 15)
            cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 0,255), 15)
    
        if currentRate > highLimit:
            cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 0,255), 15)
            triggerL += 1
            triggerR = 0
            if triggerL == triggerLim:
                print("LEFT Triggered")
                cv2.putText(frame, "> LEFT", (30, int(totalHeight * 0.8)), font, 10, (0, 255, 0), 10)
                cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,255,0),30)
                #playsound('clickOn.mp3')

        elif currentRate < lowLimit:
            cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 0,255), 15)
            triggerR += 1
            triggerL = 0
            if triggerR == triggerLim:
                print("RIGHT Triggered")
                cv2.putText(frame, "> RIGHT", (30, int(totalHeight * 0.8)), font, 10, (0, 255, 0), 10)
                cv2.rectangle(frame,(int(totalWidth * 0.01), int(totalHeight * 0.01)),(int(totalWidth * 0.99), int(totalHeight * 0.99)),(0,255,0),30)
                #playsound('clickOff.mp3')
        else: 
            triggerL = 0
            triggerR = 0

        if leftCalib == False and rightCalib == False:
        	cv2.putText(frame, "Calibrating...", (30, int(totalHeight * 0.9)), font, (textSize * 2), (0, 255, 0), 3)


        #cv2.line(gray, (int(480 * currentRate), 0), (int(480 * currentRate), 270) , (0, 0,255), 4)
    
        cv2.line(frame, (int(totalWidth * lowLimit), 0), (int(totalWidth * lowLimit), totalHeight) , (0, 255,255), 2)
        cv2.line(frame, (int(totalWidth * highLimit), 0), (int(totalWidth * highLimit), totalHeight) , (0, 255,255), 2)
    

    
        cv2.putText(frame, "Focus position: {:.2f}".format(currentRate), (30, 50), font, textSize, (0, 0, 0), 3)
        cv2.putText(frame, "Threshhold_L: {}".format(thresh_l), (30, 120), font, textSize, (0, 0, 0), 3)
        cv2.putText(frame, "Threshhold_R: {}".format(thresh_r), (30, 190), font, textSize, (0, 0, 0), 3)
        cv2.putText(frame, "Faces: {}".format(faceCount), (30, 260), font, textSize, (0, 0, 0), 3)
    
    
        cv2.line(frame, (0, int(totalHeight * 0.6)), (totalWidth,int(totalHeight * 0.6)) , (0, 0,255), 2)
        cv2.circle(frame, (int(totalWidth * currentRate), int(totalHeight * 0.6)), 50, (0, 0, 255), 15)
    
        #cv2.imshow("Threshold", threshold)
        cv2.imshow("Frame", frame)
        #cv2.imshow("gray roi", gray_roi)
        #cv2.imshow("gray", gray)
        #roi = rescale_frame(roi, percent=500)
        #cv2.imshow("Roi", roi)

    else:
        print("No faces")



    key = cv2.waitKey(30)
    if key == 27:
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

cv2.destroyAllWindows()
