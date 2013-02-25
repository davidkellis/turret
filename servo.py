import time
import sys
import serial

# 3000 is the neutral position of the Pololu serial 8-servo controller
# 3000 = '101110111000'
# We need to split 101110111000 (3000) into 2 bytes for the Pololu servo controller.
# If we split that into two bytes s.t. the most significant bit in each byte is 0, then
# we wind up with the following two bytes: 101110111000 = 00010111 00111000
# DATA_BYTE1 = bin_to_int(int_to_bin(3000)[:-7])   # 00010111 = 23
# DATA_BYTE2 = bin_to_int(int_to_bin(3000)[-7:])   # 00111000 = 56
MICROSECONDS_PER_DEGREE = 1000 / 90.0

def int_to_bin(i):
  return "{0:b}".format(i)

def bin_to_int(binary_string):
  return int(binary_string, 2)

def a2s(arr):
  """ Array of integer byte values --> binary string
  """
  return ''.join(chr(b) for b in arr)

# angle is in degrees
# returns a pulse length in microseconds (1 millisecond = 1000 microseconds), assuming 1500 microseconds is neutral position (0 degrees)
def angle_to_normal_pulse_width(angle):
  return 1500 + angle * (MICROSECONDS_PER_DEGREE)

# angle is in degrees
# pololu servo controller maintains a servo position that is two times the pulse width, measured in microseconds.
def angle_to_servo_pololu_pulse_width(angle):
  pulse_width = angle_to_normal_pulse_width(angle)
  return 2 * pulse_width
  
# angle is in degrees
def rotate(port, servo_number = 0, angle = 0):
  pulse_width = int(round(angle_to_servo_pololu_pulse_width(angle)))
  print "pulse_width=%s" % pulse_width
  data_byte1 = bin_to_int(int_to_bin(pulse_width)[:-7])
  data_byte2 = bin_to_int(int_to_bin(pulse_width)[-7:])
  send_command(port, servo_number, 4, data_byte1, data_byte2)

def send_command(port, servo_number, command, data_byte1, data_byte2 = None):
  # first byte - a synchronization value and must be 0x80 (128)
  # second byte - 0x01 for the Pololu 8-servo serial controller
  # third byte - one of six commands - i.e. a number from 0-5
  # fouth byte - the servo to which the command should apply
  # fifth byte - data byte 1
  # sixth byte - data byte 2 (optional)
  byte_seq = [128, 1, command, servo_number, data_byte1]
  if data_byte2 is not None:
    byte_seq.append(data_byte2)
  
  print byte_seq
  
  byte_str = a2s(byte_seq)
  
  print byte_str
  
  port.write(byte_str)
  # port.puts(a2s(byte_seq))

def main():
  port = serial.Serial("/dev/ttyAMA0", 9600)
  
  raw_input("reset the servo controller")
  
  # port.open()

  rotate(port, 0, 0)
  time.sleep(2)
  
  rotate(port, 0, 45)
  time.sleep(2)

  rotate(port, 0, -45)
  time.sleep(2)
  
  # rotate(port, 0, 90)
  # time.sleep(2)
  # 
  # rotate(port, 0, -90)
  # time.sleep(2)

  rotate(port, 0, 0)
  
  port.close()

main()