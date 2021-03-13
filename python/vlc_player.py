# ============================================
# Virtual Window Player
# 2021 Resinchem Tech
# Licensed under Creative Commons Attribution 4.0 - Free for reuse
# =============================================

# ======================
#  Import Libraries
# ======================
import time
import threading
import json
import vlc                        # https://pypi.org/project/python-vlc/
import RPi.GPIO as GPIO           # https://pypi.org/project/RPi.GPIO/
import paho.mqtt.client as mqtt   # https://pypi.org/project/paho-mqtt/

# ***** UPDATE THE GLOBAL VARS IN THIS SECTION TO MATCH YOUR ENVIRONMENT / INSTALL *****
# ======================
#  Define global vars
# ======================
mqtt_server = "YOUR_SERVER_IP"
mqtt_user = "MQTT_USER"
mqtt_pw = "MQTT_PASSWORD"
mqtt_port = 1883
mqtt_keepalive = 60
mqtt_topic = "winpi/window/cmnd"  # application will subscribe to this topic

# First cam and first vid will be default shown when switching sources
# First cam will be shown by default at launch
# Each addition requires a URL and name, in the same order within each list
# ======================================
# Sample Cameras - update to match yours
# ======================================
cam_name = [
    "Backyard",
    "Front Yard",
    "Back Porch",
    "Family Room",
    "Garage"
    ]
cameras = [
    "rtsp://userid:password@192.168.1.100:554//h264Preview_01_sub",      # Reolink Exampes
    "rtsp://userid:password@192.168.1.101:554//h264Preview_01_sub",
    "rtsp://userid:password@192.168.1.102/live",                         # Wyze cam Examples
    "rtsp://userid:password@192.168.1.103/live",
    "rtsp://userid:password0@192.168.1.104/live"
    ]
# ===========================================
# Sample Video Loops - update to match yours
# ===========================================
vid_name = [
    "Beach 01",
    "Beach 02",
    "Beach 03",
    "Caribbean Dock",
    "Forest Stream",
    "Mountain Flowers",
    "Ocean Water",
    "Snowy Scene",
    "Waterfall 01",
    "Waterfall 02"
    ]
videos = [
    "/home/pi/vlc_player/vids/beach_sh03.mp4",    # for best performance, videos should be local on Pi
    "/home/pi/vlc_player/vids/beach_sh04.mp4",
    "/home/pi/vlc_player/vids/tropbeach01.mp4",
    "/home/pi/vlc_player/vids/carib_dock.mp4",
    "/home/pi/vlc_player/vids/river01.mp4",
    "/home/pi/vlc_player/vids/mountain.mp4",
    "/home/pi/vlc_player/vids/water_sea.mp4",
    "/home/pi/vlc_player/vids/snowscene.mp4",
    "/home/pi/vlc_player/vids/falls01.mp4",
    "/home/pi/vlc_player/vids/falls02.mp4"
    ]

cam_loop_sec = 25       # how often, in seconds, the camera changes when in loop mode
cur_cam_count = 0       # First camera to show (from array - zero based) when switching modes
vid_loop_sec = 120      # how ofent, in seconds, to show each video when in loop mode
cur_vid_count = 0       # First video to show (from array - zero based) when switching modes
cur_play_mode = "cam"   # Initial launch mode. Vaild values are "cam" and "vid"

Instance = vlc.Instance('--fullscreen', '--input-repeat=9999', '--network-caching=4000', '--no-audio')
player = Instance.media_player_new()
player.video_set_aspect_ratio("16:9")

# ======================
#  Functions and classes
# ======================
# MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(mqtt_topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # json message format: {"mode":"cam","title":"my_title"}
    global cur_play_mode
    cmnd = msg.payload.decode()
    json_cmnd = json.loads(cmnd)
    mode = json_cmnd["mode"]
    title = json_cmnd["title"]
    
    if mode == "play_cam":
      url = GetCam_URL(title)
    elif mode == "play_vid":
      url = GetVid_URL(title)
    else:
      url = ""
      
    print("mode: " + mode)
    print("title: " + title)
    print("url: " + url)
    
    if mode == "play_cam" and url != "":
      cur_play_mode = "cam"
      play_stream(url)
    elif mode == "next_cam":
      cur_play_mode = "cam"
      play_cam_next()
    elif mode == "cam_loop":
      cur_play_mode = "cam_loop"
      play_cam_loop()
    elif mode == "play_vid" and url != "":
      cur_play_mode = "vid"
      play_stream(url)
    elif mode == "next_vid":
      cur_play_mode = "vid"
      play_vid_next()
    elif mode == "vid_loop":
      cur_play_mode = "vid_loop"
      play_vid_loop()
    elif mode == "play_stop":
      play_stop()
    else:
      pass

# BUTTON PRESSES - Update here and in main loop if you use different GPIO pins
def button_press(channel):
#  print("Button callback " + str(channel) + "  pressed")
    global cur_cam_count
    global cur_vid_count
    global cur_play_mode
    if channel == 29:   # Next Cam
      if cur_play_mode != "cam" and cur_play_mode != "cam_loop":  # reset to first cam on mode switch
        cur_cam_count = -1
      cur_play_mode = "cam"
      play_cam_next()
    elif channel == 31:  # Cam Loop
      cur_play_mode = "cam_loop"
      play_cam_loop()
    elif channel == 33:  # Next Vid
      if cur_play_mode != "vid" and cur_play_mode != "vid_loop":  # reset to first vid on mode switch
        cur_vid_count = -1
      cur_play_mode = "vid"
      play_vid_next()
    elif channel == 35:  # Vid Loop
      cur_play_mode = "vid_loop"
      play_vid_loop()
    elif channel == 37:
      #pass
      launch_web()
    else:
      pass

def launch_web():
    #response = subprocess.run("/usr/bin/startx /home/pi/startbrowser.sh", shell=False, stderr=subprocess.PIPE)
    pass
def play_stream(url):
    Media = Instance.media_new(url)
    Media.get_mrl()
    player.set_media(Media)
    player.play()

def GetCam_URL(title):
    try:
      title_idx = cam_name.index(title)
    except ValueError:
      url = ""
      print("Cam title not found")
    else:
      try:
        url = cameras[title_idx]
      except:
        url = ""
        print("Cam URL not found from title index")
    return url

def play_cam_next():
    global cur_cam_count
    cur_cam_count = cur_cam_count + 1
    if cur_cam_count > len(cameras) - 1:
      cur_cam_count = 0
    next_url = cameras[cur_cam_count]
    play_stream(next_url)

def play_cam_loop():
  def run():
    global cur_cam_count
    cur_cam_count = -1
    try:
      while cur_play_mode == "cam_loop":
        play_cam_next()
        time.sleep(cam_loop_sec)
        if cur_play_mode != "cam_loop":
          break
    except KeyboardInterrupt:
        GPIO.cleanup()
  thread = threading.Thread(target=run)  # run in thread to allow button press to break loop
  thread.start()

def GetVid_URL(title):
    try:
      title_idx = vid_name.index(title)
    except ValueError:
      url = ""
      print("Vid title not found")
    else:
      try:
        url = videos[title_idx]
      except:
        url = ""
        print("Vid URL not found from title index")
    return url


def play_vid_next():
    global cur_vid_count
    cur_vid_count = cur_vid_count + 1
    if cur_vid_count > len(videos) - 1:
      cur_vid_count = 0
    next_url = videos[cur_vid_count]
    play_stream(next_url)

def play_vid_loop():
  def run2():
    global cur_vid_count
    cur_vid_count = -1
    try:
      while cur_play_mode == "vid_loop":
        play_vid_next()
        time.sleep(vid_loop_sec)
        if cur_play_mode != "vid_loop":
          break
    except KeyboardInterrupt:
        GPIO.cleanup()
  thread = threading.Thread(target=run2)  # run in thread to allow button press to break loop
  thread.start()

def play_stop():
    player.stop


# ======================
#  MAIN ROUTINE
# ======================

def main():
    print("Starting main...")
    GPIO.setmode(GPIO.BOARD)
    # Cam Next - Pin 29
    GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(29,GPIO.FALLING,callback=button_press, bouncetime=200)
    # Cam Loop - Pin 31
    GPIO.setup(31, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(31,GPIO.FALLING,callback=button_press, bouncetime=200)
    # Vid Next - Pin 33
    GPIO.setup(33, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(33,GPIO.FALLING,callback=button_press, bouncetime=200)
    # Vid Loop - Pin 35
    GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(35,GPIO.FALLING,callback=button_press, bouncetime=200)
    # Other - Pin 37
    GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(37,GPIO.FALLING,callback=button_press, bouncetime=200)
    # MQTT Initialize
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_user, mqtt_pw)
    client.connect(mqtt_server, mqtt_port, mqtt_keepalive)
    client.loop_start()
    
    url = cameras[0]
    play_stream(url)
# ======================
# Start Main Loop Here
# ======================
    try: 
      while True:
#          time.sleep(10)
#          play_cam_next()
          pass    
    except KeyboardInterrupt:
        GPIO.cleanup()
# -------------------------------------------------------------
# Main call - this executes if executed as script from cmd line
# -------------------------------------------------------------
if __name__ == "__main__":
    main() 
