from bottle import route, static_file, HTTPResponse
from access_modules import solar, weather, pushover, alarmlog
import subprocess
import logging
import time
import urllib
import requests
import configparser

cfg = configparser.ConfigParser()
cfg.read('/home/pi/base/tools/config.txt')

logger = logging.getLogger("base_logger")
radio = 1


# ------------------------------------------------------------------------------------------
# Sound, Radio API
# ------------------------------------------------------------------------------------------
@route('/')
def index():
    return static_file('index.html', root='/home/pi/base/web')


@route('/playsound/<file>')
def play_sound(file, volume=80):
    stop_radio()
    subprocess.call("amixer sset PCM,0 " + str(volume) + "%", shell=True)
    filename = "/home/pi/base/sounds/" + file + ".wav"
    subprocess.call(["aplay", filename])
    return dict(status="OK")


@route('/playRadio')
def play_radio():
    global radio
    if radio > 6:
        radio = 1

    subprocess.call(["mpc", "stop"])
    if radio == 1:
        say("HR 3", 75)
    elif radio == 2:
        say("SWR 3", 75)
    elif radio == 3:
        say("SWR 1", 75)
    elif radio == 4:
        say("SWR 2", 75)
    elif radio == 5:
        say("Bayern 3", 75)
    elif radio == 6:
        say("Das Ding", 75)

    time.sleep(0.4)
    out = subprocess.check_output("mpc play " + str(radio), shell=True)
    out = out.split(b'\n')[0].decode('utf-8')
    radio += 1
    return dict(playing=out)


@route('/stopRadio')
def stop_radio():
    subprocess.call(["mpc", "stop"])
    return dict(status="OK")


@route('/increaseVolume')
def increase_volume():
    subprocess.call(["mpc", "volume", "+10"])
    return dict(status="OK")


@route('/decreaseVolume')
def decrease_volume():
    subprocess.call(["mpc", "volume", "-10"])
    return dict(status="OK")


# ----------------------------------------------------------------------------------------------
# Solar and weather API
# ----------------------------------------------------------------------------------------------
@route('/solar/current')
def current_solarproduction():
    current_data = solar.read_data()  # returns a dictionary, will be transformed to JSON by bottle
    if current_data:
        return current_data
    else:
        return HTTPResponse(dict(error="Could not read solar production values"), status=500)


@route('/weather/current')
def current_weather():
    current_data = weather.read_data()
    if current_data:
        return current_data
    else:
        return HTTPResponse(dict(error="Could not read weather data values"), status=500)


# ----------------------------------------------------------------------------------------------
# Alarm control
# ----------------------------------------------------------------------------------------------
@route('/alarmOn')
def alarm_on():
    subprocess.call(["sudo", "systemctl", "start", "alarm.service"])
    # update the E Paper alarm display
    try:
        requests.get(cfg['ccu2']['update_alarm_on'], timeout=3)
    except Exception:
        pass
    return dict(status="OK")


@route('/alarmOff')
def alarm_off():
    subprocess.call(["sudo", "systemctl", "stop", "alarm.service"])
    # update the E Paper alarm display
    try:
        requests.get(cfg['ccu2']['update_alarm_off'], timeout=3)
    except Exception:
        pass
    return dict(status="OK")


@route('/alarmStatus')
def alarm_status():
    try:
        subprocess.check_call(["systemctl", "status", "alarm.service"])  # if $? is != 0 raises CalledProcessError
        return dict(status="started")
    except subprocess.CalledProcessError:
        return dict(status="stopped")


@route('/alarmLog')
def alarm_log():
    log_data = alarmlog.get_log()
    if log_data:
        return log_data
    else:
        return HTTPResponse(dict(error="Could not read log data from alarm service"), status=500)


# ----------------------------------------------------------------------------------------------
# Pushover API
# ----------------------------------------------------------------------------------------------
@route('/pushOver/<message_type>/<message>')  # message_type = alarm | standard
def send_pushover_message(message_type, message):
    message = urllib.parse.unquote_plus(message)
    ret_value = pushover.send_message(message_type, message)  # returns a dictionary, will be transformed to JSON by bottle
    if ret_value:
        return ret_value
    else:
        return HTTPResponse(dict(error="Could not send pushover message"), status=500)


# ----------------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------------
def say(text, volume):
    subprocess.call("amixer sset PCM,0 " + str(volume) + "%", shell=True)
    subprocess.call('pico2wave --lang=de-DE --wave=/tmp/test.wav "' + text + '" && aplay /tmp/test.wav && rm /tmp/test.wav', shell=True)
    subprocess.call(["amixer", "sset", "PCM,0", "65%"])
