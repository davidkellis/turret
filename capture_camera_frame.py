import cv2
import msgpackrpc   # see: https://github.com/msgpack-rpc/msgpack-rpc-python
import sys
import time

class LaserService:
  def __init__(self, host = "localhost", port = 10):
    self.laser_service = msgpackrpc.Client(msgpackrpc.Address(host, port))
    
  def on(self):
    self.laser_service.call("on")
    
  def off(self):
    self.laser_service.call("off")
  
  def cleanup(self):
    self.laser_service.call("cleanup")

class RangeFinder:
  def __init__(self, laser_service):
    self.laser_service = laser_service
  
  def compute_distance(self, capture_frame_fn):
    self.laser_service.on()
    time.sleep(0.2)   # it takes a short moment for the laser to turn on
    captured_frame = capture_frame_fn()
    self.laser_service.off()
    distance = self.compute_distance_from_frame(captured_frame)
    return distance

  def compute_distance_from_frame(self, image):
    pixel_distance_from_center_screen = self.find_red_dot(image)
    return 50

  def find_red_dot(self, image):
    red_image, green_image, blue_image = cv2.split(image)

class LiveVideoStream:
  def __init__(self, camera_index = 0, window_name = "Live Video", cleanup_fn = None, key_press_event_handler = None, mouse_event_handler = None):
    self.current_frame = None
    self.click_points = []
    self.camera_index = camera_index
    self.window_name = window_name
    self.camera = None
    self.cleanup_fn = cleanup_fn
    self.key_press_event_handler = key_press_event_handler
    self.mouse_event_handler = mouse_event_handler

  def cleanup(self):
    if self.cleanup_fn is not None:
      self.cleanup_fn()

  def open_window(self, name):
    return cv2.namedWindow(name)

  def open_camera(self, camera_index = 0):
    self.camera = self.get_camera(camera_index)
    return self.camera

  # returns a camera object
  def get_camera(self, camera_index = 0):
    return cv2.VideoCapture(camera_index)

  # def display_image(self, image):
  #   cv2.imshow('WindowName', image)
  # 
  # def capture_and_save_image(self):
  #   camera = self.get_camera(self.camera_index)
  #   image1 = self.capture_image(camera)
  #   self.save_image(image1, "pic.jpg")
  #   # self.display_image(image1)
  #   # c = cv2.waitKey
  # 
  #   # image2 = self.capture_image(camera)
  #   # # self.save_image(image, "pic.jpg")
  #   # self.display_image(image2)
  #   # c = cv2.cv.WaitKey()

  # returns an image object
  def capture_image(self, camera = None):
    if camera is None:
      camera = self.camera

    if camera is not None:
      status, img = camera.read()
      return img
    else:
      return None

  def save_image(self, image, filename):
    return cv2.imwrite(filename, image)

  # http://stackoverflow.com/questions/2601194/displaying-webcam-feed-using-opencv-and-python
  def display_live_video_stream(self):
    window = self.open_window(self.window_name)
    camera = self.open_camera(self.camera_index)
  
    self.capture_mouse_events(self.on_mouse_event)
  
    is_camera_open = camera.isOpened()
    while is_camera_open:
      is_camera_open, self.current_frame = camera.read()
      # print self.current_frame.shape
      self.redraw_click_points()
      cv2.imshow(self.window_name, self.current_frame)
      if self.capture_key_press() < 0:
        self.cleanup()
        break

  def capture_mouse_events(self, mouse_event_handler_fn):
    cv2.cv.SetMouseCallback(self.window_name, mouse_event_handler_fn) 

  def on_mouse_event(self, event, x, y, flags, param):
    # print(event, x, y, flags, param)
    if event == 1 or event == 2:     # mousedown
      self.on_mouse_down(event, x, y, flags, param)

  def on_mouse_down(self, event, x, y, flags, param):
    if event == 1:     # left click
      self.click_points.append((x, y))
    elif event == 2:   # right click
      del self.click_points[:]

  def redraw_click_points(self):
    if self.current_frame is not None:
      for point in self.click_points:
        self.draw_circle(self.current_frame, point, 4)

  def draw_circle(self, image, center, radius, color = (0, 0, 255), thickness = 2):
    cv2.circle(image, center, radius, color, thickness)

  def capture_key_press(self):
    key = cv2.waitKey(20)
    
    if key == 27:       # esc
      return -1
    elif key >= 0 and self.key_press_event_handler is not None:
      return self.key_press_event_handler(key)
    else:
      return 0

class TurretController:
  def __init__(self, camera_index = 0, laser_service_host = "localhost", laser_service_port = 5555):
    self.laser_service = LaserService(laser_service_host, laser_service_port)
    self.range_finder = RangeFinder(self.laser_service)
    self.video = LiveVideoStream(camera_index, cleanup_fn=self.cleanup, key_press_event_handler=self.on_key_press)

  def display_live_video_stream(self):
    self.video.display_live_video_stream()

  def cleanup(self):
    self.laser_service.off()
    # self.laser_service.cleanup()

  def on_key_press(self, key):
    if key == 63234:  # left
      print "left by 100 px"
    elif key == 63235:  # right
      print "right by 100 px"
    elif key == 108:    # l
      print "laser on"
      self.laser_service.on()
    elif key == 111:    # o
      print "laser off"
      self.laser_service.off()
    elif key == 32:     # space
      print "range find!"
      def image_capture_fn():
        frame = self.video.capture_image(self.video.camera)
        self.video.save_image(frame, "rangefind.jpg")
        frame
      distance = self.range_finder.compute_distance(image_capture_fn)
      print "Distance to target: %s" % distance
    elif key == 13:     # enter
      print "fire gun!"
    
    return 0

# argv[1] is hostname
# argv[2] is port
TurretController(1, sys.argv[1], int(sys.argv[2])).display_live_video_stream()