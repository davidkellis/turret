import msgpackrpc   # see: https://github.com/msgpack-rpc/msgpack-rpc-python
import laser
import sys

class LaserService:
  def __init__(self):
    self.laser = laser.Laser()
    self.setup()
  
  def setup(self):
    self.laser.setup()
    self.laser.off()
  
  def on(self):
    self.laser.on()
  
  def off(self):
    self.laser.off()
    
  def cleanup(self):
    self.laser.cleanup()

def main(host = "localhost", port = 5555):
  try:
    laser_service = LaserService()
    server = msgpackrpc.Server(laser_service)
    server.listen(msgpackrpc.Address(host, port))
    server.start()
  finally:
    laser_service.cleanup()

# argv[1] is hostname
# argv[2] is port
main(sys.argv[1], int(sys.argv[2]))