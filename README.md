![GazeLogo](https://i.imgur.com/mVVScOQ.png)

![Image of EyeTracker](https://github.com/Mr0Inka/open_eye_tracking_remote/blob/master/test_7.JPG?raw=true)

![Image of EyeRoi](https://github.com/Mr0Inka/open_eye_tracking_remote/blob/master/test_8.JPG?raw=true)

What this is:  
- A ~50$ plug and play eye tracker to help quadriplegic people make decisions. Either use it as a "Yes/No" thingy or connect it to a VLC Player instance on a local computer to skip videos and control the volume using your eyes.  
- Gazing far left or far right will (by default) do a single or double beep and also send a command to VLC Player to skip or go back one position on the current playlist. Gazing straight down will toggle the left/right triggers into modifying the volume.


Dependencies face tracker:
- OpenCV (https://www.deciphertechnic.com/install-opencv-python-on-raspberry-pi/)
- dlib (pip install dlib / For Windows, use Anaconda or MiniConda)
- NumPy (pip install numpy)
- Shape_Predictor_68_face_landmarks.dat (http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)

Dependencies notifier/player:
- Growl for Windows
- ExpressJS
- VLC Player

Set up the notifier / Player:  
- Instalö Growl for Windows
- Install VLC Player, enable it's web interface and give it a lua password
- Host a wifi hotspot on your windows machine or have the RPI and Windows PC on the same network
- Add your PC's IP and the Lua password to the face tracking python script
- Start a playlist on VLC
- You're done! You can now control VLC with your eyes and see on-screen notifications about changes


Important notes: 
- The RPI version is optimized for python2, while the windows version works only with python3 (float calculation)
- A NOIR camera with additional IR blasters improves the detection quality by a lot




Icon by Gregor Cresnar
