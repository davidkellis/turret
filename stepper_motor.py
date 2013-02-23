import RPi.GPIO as GPIO
import time
import sys

# these pins are for the RPi revision 2 board
PIN1 = 17
PIN2 = 18
PIN3 = 27
PIN4 = 22

# single stepping
APIN1 = [1,0,0,0]
APIN2 = [0,1,0,0]
APIN3 = [0,0,1,0]
APIN4 = [0,0,0,1]

def setup():
  print "Setting up GPIO"
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(PIN1, GPIO.OUT)
  GPIO.setup(PIN2, GPIO.OUT)
  GPIO.setup(PIN3, GPIO.OUT)
  GPIO.setup(PIN4, GPIO.OUT)

def cleanup():
  print "Cleaning up GPIO"
  GPIO.cleanup()

# implements single-stepping rotation (as opposed to half-steps or double-steps)
def rotate(steps, delay = 0.003):
  if steps >= 0:
    step = 0
    while step < steps:
      i = step % 4
      GPIO.output(PIN1, APIN1[i])
      GPIO.output(PIN2, APIN2[i])
      GPIO.output(PIN3, APIN3[i])
      GPIO.output(PIN4, APIN4[i])
      time.sleep(delay)
      step = step + 1
  else:
    step = 0
    while step < -steps:
      i = -(step % 4)
      GPIO.output(PIN1, APIN1[i])
      GPIO.output(PIN2, APIN2[i])
      GPIO.output(PIN3, APIN3[i])
      GPIO.output(PIN4, APIN4[i])
      time.sleep(delay)
      step = step + 1

def main():
  setup()
  
  time.sleep(2)
  
  rotate(2048)
  time.sleep(2)

  rotate(-2048)
  time.sleep(2)

  rotate(512)
  time.sleep(2)

  rotate(-512)
  
  cleanup()

main()