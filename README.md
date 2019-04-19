# open_eye_tracking_remote

![Image of EyeTracker](https://github.com/Mr0Inka/open_eye_tracking_remote/blob/master/test_7.JPG?raw=true)

Dependencies:
- OpenCV (https://www.deciphertechnic.com/install-opencv-python-on-raspberry-pi/)
- dlib (pip install dlib / For Windows, use Anaconda or MiniConda)
- NumPy (pip install numpy)
- Shape_Predictor_68_face_landmarks.dat (http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)


Important notes: 
- The RPI version is optimized for python2, while the windows version works only with python3 (float calculation)
- The RPI version currently only works with an RPI camera, not a usb camera
- Using a NOIR camera with IR blasters should technically enhance the detection quality (needs readjusting in detecting black/white)
