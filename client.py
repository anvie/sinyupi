import RPi.GPIO as GPIO
from time import sleep
import gnsq


GPIO.setmode(GPIO.BOARD)

reader = gnsq.Reader("sinyu","all","my.cool.server.net:4150")


def activate(pin):
    GPIO.output(pin, GPIO.LOW)

def deactivate(pin):
    GPIO.output(pin, GPIO.HIGH)


_processed = []

@reader.on_message.connect
def handler(reader, message):
    global _processed
    if message.id in _processed:
        return
    print "got message:",message.body,", id:", message.id
    _processed.insert(0, message.id)
    if len(_processed) > 5:
        _processed.pop()
    msg = message.body.strip()
    if msg == "lampu_teras_1_on":
        print "nyalain lampu teras..."
        activate(7)
    elif msg == "lampu_teras_1_off":
        print "matiin lampu teras..."
        deactivate(7)
    elif msg == "lampu_teras_2_on":
        print "nyalain lampu teras..."
        activate(11)
    elif msg == "lampu_teras_2_off":
        print "matiin lampu teras..."
        deactivate(11)

        


def main():
    print "starting..."

    GPIO.setup(7, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)
    
    reader.start()

    print "  done."
    


if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt, e:
        print e
        GPIO.cleanup()
    finally:
        print "done."

