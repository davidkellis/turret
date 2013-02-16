import RPi.GPIO as GPIO
from time import sleep

class Laser:
  LASER_PIN = 25

  def setup(self):
    print "Setting up GPIO"
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.LASER_PIN, GPIO.OUT)

  def cleanup(self):
    print "Cleaning up GPIO"
    GPIO.cleanup()

  def on(self):
    self.power_on(True)

  def off(self):
    self.power_on(False)

  def power_on(self, enable):
    status = "ON" if enable else "OFF"
    print "Laser is %s" % status
    GPIO.output(self.LASER_PIN, not enable)

def main():
  try:
    laser = Laser()
    
    laser.setup()
  
    for i in range(1, 2):
      laser.power_on(False)
      sleep(5)
  
      laser.power_on(True)
      sleep(5)

  finally:
    laser.cleanup()

# main()