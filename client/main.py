import RPi.GPIO as GPIO
from time import sleep
import gnsq
import json
import os.path
from datetime import datetime
import pytz
import sys

local_tz = pytz.timezone("Asia/Jakarta")

GPIO.setwarnings(False)

NSQ_HOST = "localhost"

nsqd = None
reader = None

USED_PINS = [7,11,13,15]
CURRENT_STATE_FILE_PATH = "current_state.json"
_current_state = {}


def activate(pin):
    global _current_state
    GPIO.output(pin, GPIO.HIGH)
    _current_state[str(pin)] = GPIO.HIGH
    save_state()

def deactivate(pin):
    global _current_state
    GPIO.output(pin, GPIO.LOW)
    _current_state[str(pin)] = GPIO.LOW
    save_state()

def save_state():
    global _current_state
    _csjson = json.dumps(_current_state)
    text_file = open(CURRENT_STATE_FILE_PATH, "w")
    text_file.write(_csjson)
    text_file.close()

def load_state():
    global _current_state
    if os.path.exists(CURRENT_STATE_FILE_PATH):
        with open(CURRENT_STATE_FILE_PATH, "r") as text_file:
            _csjson = text_file.read().strip()
            if len(_csjson) > 0:
                _current_state = json.loads(_csjson)
    if len(_current_state) == 0:
        for pin in USED_PINS:
            _current_state[pin] = GPIO.HIGH

_processed = []

def sync():
    try:
        nsqd.publish("sinyu_server", json.dumps(_current_state))
    except Exception, e:
         pass


import threading

class TimeScheduler(threading.Thread):
    def run(self):
        print "time scheduler started."
        while True:
            sleep(5)
            _now = datetime.now().replace(tzinfo=pytz.utc).astimezone(local_tz)
            print ("    time: ", _now)
            if _now.hour == 18 and _now.minute == 0:
#         if _now.hour == 10 and _now.minute == 18:
#                nsqd.publish("sinyu", "lampu_jalan:on")
#                nsqd.publish("sinyu", "lampu_garasi:on")
                activate(13)
                activate(15)
                sync()
            if _now.hour == 5 and _now.minute == 30:
                print "deactivate lampu depan"
#            if _now.hour == 10 and _now.minute == 15:
#                nsqd.publish("sinyu", "lampu_jalan:on")
#                nsqd.publish("sinyu", "lampu_garasi:on")
                deactivate(13)
                deactivate(15)
                sync()

def setup_nsq_handler():
    global NSQ_HOST
    global reader


    reader = gnsq.Reader("sinyu","all", NSQ_HOST + ":4150")

    @reader.on_message.connect
    def handler(reader, message):
        global _processed
        global _current_state

        if message.id in _processed:
            return
        print "got message:",message.body,", id:", message.id
        _processed.insert(0, message.id)
        if len(_processed) > 5:
            _processed.pop()
        msg = message.body.strip()
        state = "off"
        if msg.endswith(":on"):
            state = "on"

        if msg.startswith("lampu_jalan"):
            if state == "on":
                print "nyalain lampu jalan..."
                activate(13)
            else:
                deactivate(13)
            sync()
        elif msg.startswith("lampu_garasi"):
            if state == "on":
                print "nyalain lampu garasi..."
                activate(15)
            else:
                print "matiin lampu garasi..."
                deactivate(15)
            sync()
        elif msg.startswith("lampu_1_r_tamu"):
            if state == "on":
                print "nyalain lampu tengah..."
                activate(11)
            else:
                print "matiin lampu tengah..."
                deactivate(11)
            sync()
        elif msg.startswith("terminal_r_tamu"):
            if state == "on":
                print "nyalain stop kontak ruang tengah..."
                activate(7)
            else:
                print "matiin stop kontak ruang tengah..."
                deactivate(7)
            sync()

        if msg == "sync":
            sync()

    reader.start()


def main():
    global _current_state
    global USED_PINS
    global NSQ_HOST
    global nsqd
    global reader

    print "SinyuPi client v0.1"


    if len(sys.argv) < 2:
        print "usage: %s [NSQ-HOST]" % sys.argv[0]
        return

    print "starting..."

    NSQ_HOST = sys.argv[1]

    print "using nsq host:", NSQ_HOST

    load_state()
    print "current state:", json.dumps(_current_state)

    sleep(2)

    print "setup GPIO..."

    GPIO.setmode(GPIO.BOARD)

    for pin in USED_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=_current_state.get(pin,GPIO.HIGH))

    # pre-setup
    for pin, state in _current_state.iteritems():
        GPIO.output(int(pin), state)

    nsqd = gnsq.Nsqd(address = NSQ_HOST, http_port=4151)

    save_state()
    nsqd.publish("sinyu_server", json.dumps(_current_state))

    print "starting time scheduler..."
    tsc = TimeScheduler()
    tsc.daemon = True
    tsc.start()

    print "running..."

    setup_nsq_handler()

    print "  done."



if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt, e:
        print e
    finally:
        GPIO.cleanup()
        print "done."
