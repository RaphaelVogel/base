from bottle import route, static_file, HTTPResponse
from access_modules import solar, weather
import random
import json
import subprocess
import logging
import requests
import time
import wit


@route('/')
def index():
    return static_file('index.html', root='/home/pi/base/web')


# ------------------------------------------------------------------------------------------
# Sound, Radio and Speech Recognition API
# ------------------------------------------------------------------------------------------
access_token = ""
logger = logging.getLogger("base_logger")

was_machen = ['Wir könnten heute ins Freibad oder Hallenbad gehen',
              'Wir könnten heute Fahrrad fahren',
              'Wir könnten heute ins Kino gehen',
              'Wir könnten heute ganz viele Süßigkeiten essen',
              'Wir könnte heute Fussball spielen',
              'Die Kinder sollten heute ihr Zimmer aufräumen',
              'Die Kinder können jetzt Mathe und Deutsch üben',
              'Wir könnten jetzt Fernsehen schauen']
radio = 1


@route('/playsound/<file>')
def play_sound(file):
    subprocess.call(["amixer", "sset", "PCM,0", "65%"])
    filename = "/home/pi/base/sounds/" + file + ".wav"
    subprocess.call(["aplay", filename])
    return dict(status="OK")


@route('/playRadio')
def play_radio():
    global radio
    if radio > 6:
        radio = 1
    subprocess.call("mpc -q play " + str(radio), shell=True)
    radio += 1
    return dict(status="OK", playing=str(radio - 1))


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


@route('/recognize')
def speech_recognizer():
    logger.info("In speech_recognizer method")
    stop_radio()
    return dict(recognized_intent="")


# ----------------------------------------------------------------------------------------------
# Solar and weather API
# ----------------------------------------------------------------------------------------------
@route('/solar/current')
def current_solarproduction():
    current_data = solar.read_data(False)  # returns a dictionary, will be transformed to JSON by bottle
    if current_data:
        return current_data
    else:
        return HTTPResponse(dict(error="Could not read solar production values"), status=500)


@route('/weather/current')
def current_weather():
    current_data = weather.read_data(False)
    if current_data:
        return current_data
    else:
        return HTTPResponse(dict(error="Could not read weather data values"), status=500)


# ----------------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------------
def say(text):
    subprocess.call(["amixer", "sset", "PCM,0", "75%"])
    subprocess.call('pico2wave --lang=de-DE --wave=/tmp/test.wav "' + text + '" && aplay /tmp/test.wav && rm /tmp/test.wav', shell=True)
    subprocess.call(["amixer", "sset", "PCM,0", "50%"])


def evaluate_speech_intent():
    pass
