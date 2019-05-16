const Growl = require('node-notifier/notifiers/growl');
var path = require('path');
var notifier = new Growl();

const express = require('express');
const app = express();
app.get('/notify', function(req, res){
   const {id, since, fields, anotherField} = req.query;
   let message = req.query.message
   notify(message)
   console.log(message)
});

app.listen(3000);

console.log("Server running")

function notify(message, icon){
    if(message.indexOf("Volume") >= 0){
    	let vol = parseInt(message.replace("Volume_", ""))
    	let volNow = map(vol, 0, 254, 0, 11);
    	let iconName;
    	let volMessage;
    	if(volNow == 0){
    		iconName = "./icon/zero.png"
    		volMessage = "Muted"
        } else if(volNow == 1){
    		iconName = "./icon/ten.png"
    		volMessage = "10%"
    	} else if(volNow == 2){
    		iconName = "./icon/twenty.png"
    		volMessage = "20%"
    	} else if(volNow == 3){
    		iconName = "./icon/thirty.png"
    		volMessage = "30%"
    	} else if(volNow == 4){
     		iconName = "./icon/forty.png"
    		volMessage = "40%"
    	} else if(volNow == 5){
     		iconName = "./icon/fifty.png"
    		volMessage = "50%"
    	} else if(volNow == 6){
     		iconName = "./icon/sixty.png"
    		volMessage = "60%"
    	} else if(volNow == 7){
     		iconName = "./icon/seventy.png"
    		volMessage = "70%"
    	} else if(volNow == 8){
     		iconName = "./icon/eighty.png"
    		volMessage = "80%"
    	} else if(volNow == 9 && vol != 255){
    		iconName = "./icon/ninety.png"
    		volMessage = "90%"
    	} else if(vol == 255){
    		iconName = "./icon/hundred.png"
    		volMessage = "100%"
    	} 
        notifier.notify({
        	title: "Adjusted volume: ",
        	message: volMessage,
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: iconName
  	    });
    } else if(message == "ChannelUp"){
        notifier.notify({
        	title: "[+] Channel",
        	message: "Moved up one channel",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/right.png"
  	    });
    } else if(message == "ChannelDown"){
        notifier.notify({
        	title: "[-] Channel",
        	message: "Moved down one channel",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/left.png"
  	    });
    } else if(message == "mode_channel"){
        notifier.notify({
        	title: "Mode: Channel",
        	message: "Gaze left/right to control the channels",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/channel.png"
  	    });
    } else if(message == "mode_volume"){
        notifier.notify({
        	title: "Mode: Volume",
        	message: "Gaze left/right to control the volume",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/volume.png"
  	    });
    } else if(message == "resumed"){
        notifier.notify({
        	title: "Tracking active",
        	message: "Gaze left/right/down",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/resume.png"
  	    });
    } else if(message == "paused"){
        notifier.notify({
        	title: "Stopped tracking",
        	message: "Please re-activate the tracker",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/pause.png"
  	    });
    } else if(message == "noface"){
        notifier.notify({
        	title: "Can't find a face",
        	message: "Try a distance of ~70cm",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/noface.png"
  	    });
    } else if(message == "facefound"){
        notifier.notify({
        	title: "I can see you",
        	message: "Gaze left/right/down to control",
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/facefound.png"
  	    });
    } else if(message.indexOf("sense_") != -1){
    	let lowLim = message.replace("sense_", "").split("-")[0]
    	let highLim = message.replace("sense_", "").split("-")[1]
        notifier.notify({
        	title: "Changed setting:",
        	message: "Sense: " + lowLim + "/" + highLim,
        	sound: false, // true | false.
        	time: 1000, // How long to show balloon in ms
        	icon: "./icon/setting.png"
  	    });
    }
}


function map (thisNum, in_min, in_max, out_min, out_max) {
  return parseInt((thisNum - in_min) * (out_max - out_min) / (in_max - in_min) + out_min);
}



