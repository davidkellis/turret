import cv2
import msgpackrpc   # see: https://github.com/msgpack-rpc/msgpack-rpc-python
import sys
import time
import numpy as np
import image_utils as img

class LaserService:
  def __init__(self, host = "localhost", port = 10):
    self.laser_service = msgpackrpc.Client(msgpackrpc.Address(host, port))
    
  def on(self):
    try:
      self.laser_service.call("on")
    except msgpackrpc.error.TimeoutError:
      pass
    
  def off(self):
    try:
      self.laser_service.call("off")
    except msgpackrpc.error.TimeoutError:
      pass
  
  def cleanup(self):
    try:
      self.laser_service.call("cleanup")
    except msgpackrpc.error.TimeoutError:
      pass

class RangeFinder:
  def __init__(self, laser_service):
    self.laser_service = laser_service
  
  def compute_distance(self, capture_frame_fn):
    self.laser_service.on()
    time.sleep(0.2)   # it takes a short moment for the laser to turn on
    captured_frame = capture_frame_fn()
    self.laser_service.off()
    # distance = self.compute_distance_from_frame(captured_frame)
    distance = 50
    return distance

  def compute_distance_from_frame(self, image):
    (x, y) = self.find_red_dot_coords(image)
    distance_in_feet = 50
    return 50
  # 
  # def find_red_dot_coords(self, image):
  #   rows = image.shape[0]
  #   cols = image.shape[1]
  #   max_red_coord = (0, 0)
  #   blue, green, max_red_value = image[0][0]
  #   
  #   for row in range(rows):
  #     for col in range(cols):
  #       x, y = col, row
  #       pixel = image[row][col]
  #       blue, green, red = pixel
  #       
  #       # TODO: need to make this smarter, so that it checks the surrounding pixels and concludes that 
  #       #       a #fff value is "red" if it is sufficiently surrounded by red pixels
  #       # red must be 50% brighter than the blue and 50% brighter than the green
  #       if red >= round(blue * 1.50) and red >= round(green * 1.50) and red > max_red_value:
  #         max_red_coord = (x, y)
  #         max_red_value = red
  # 
  #   return max_red_coord

  # def find_red_dot_circles(self, image):
  #   rows, cols, depth = image.shape
  #   gray_img = cv2.cvtColor(image, cv2.cv.CV_BGR2GRAY)
  #   # gray_img = cv2.GaussianBlur(gray_img, (0, 0), 2, gray_img, 2)
  #   # circles = cv2.HoughCircles(gray_img, cv2.cv.CV_HOUGH_GRADIENT, 1, rows / 8, param1=200, param2=100, minRadius=0, maxRadius=30)
  #   circles = cv2.HoughCircles(gray_img, cv2.cv.CV_HOUGH_GRADIENT, 1, 10, param1=50, param2=50, minRadius=0, maxRadius=50)
  #   circles = np.uint16(np.around(circles))[0]
  #   # print "circles="
  #   # print circles
  #   return circles
  
  # extracts a rectangular sub-region of the image where: 
  # the top-left of the rectangle is 10 pixels to the left of the image's center point
  # the bottom-right of the rectangle is the bottom-most pixel in the image appearing 10 pixels to the right of the image's center point
  def extract_laser_channel_rect(self, image):
    rows = image.shape[0]
    
    # since the Logitech C270 resolution is 1280x960, the center point will never be exact, 
    # it will be offset to the left and up by 1 px in both directions
    x, y = img.center_point(image)
    
    rect_width = 20   # width must be even
    rect_half_width = rect_width / 2
    
    # top-left and bottom-right are (x,y) coordinate pairs where the top-left of the image is the origin (0,0)
    top_left = (x - (rect_half_width - 1), y)
    bottom_right = (x + rect_half_width, rows - 1)
    
    # image is a matrix, so we extract the rows and columns we want (which we derive from the x,y coordinate range)
    top_row_index = top_left[1]
    left_col_index = top_left[0]
    right_col_index = bottom_right[0] + 1   # + 1 because the : operator includes the min and excludes the max
    rect_image = image[top_row_index : , left_col_index : right_col_index]
    # img.save_image(rect_image, "rect.jpg")
    
    return (rect_image, top_left)

  def find_red_dot_circles(self, image):
    rect_region, coord_offset = self.extract_laser_channel_rect(image)
    
    template = cv2.imread("laserdotbrown.png")
    template_rows = template.shape[0]
    template_cols = template.shape[1]
    
    result = cv2.matchTemplate(rect_region, template, cv2.TM_CCOEFF_NORMED)
    # normal_result = cv2.normalize(result, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=-1)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
    match_rect_top_left = maxLoc    # For SQDIFF and SQDIFF_NORMED, the best matches are lower values. For all the other methods, the higher the better
    
    circle = (coord_offset[0] + match_rect_top_left[0] + (template_cols / 2), 
              coord_offset[1] + match_rect_top_left[1] + (template_rows / 2))
    return [circle]

class LiveVideoStream:
  def __init__(self, camera_index = 0, window_name = "Live Video", cleanup_fn = None, key_press_event_handler = None, mouse_event_handler = None):
    self.current_frame = None
    self.click_points = []
    self.rectangles = []
    self.camera_index = camera_index
    self.window_name = window_name
    self.camera = None
    self.cleanup_fn = cleanup_fn
    self.key_press_event_handler = key_press_event_handler
    self.mouse_event_handler = mouse_event_handler

  def add_click_point(self, point):
    self.click_points.append(point)

  def add_rectangle(self, top_left, bottom_right):
    self.rectangles.append((top_left, bottom_right))

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
  #   img.save_image(image1, "pic.jpg")
  #   # self.display_image(image1)
  #   # c = cv2.waitKey
  # 
  #   # image2 = self.capture_image(camera)
  #   # # img.save_image(image, "pic.jpg")
  #   # self.display_image(image2)
  #   # c = cv2.cv.WaitKey()

  # returns a BGR-image matrix
  def capture_image(self, camera = None):
    if camera is None:
      camera = self.camera

    if camera is not None:
      status, image = camera.read()   # returns a BGR-image matrix
      return image
    else:
      return None

  # http://stackoverflow.com/questions/2601194/displaying-webcam-feed-using-opencv-and-python
  def display_live_video_stream(self):
    window = self.open_window(self.window_name)
    camera = self.open_camera(self.camera_index)
  
    self.capture_mouse_events(self.on_mouse_event)
  
    is_camera_open = camera.isOpened()
    while is_camera_open:
      is_camera_open, self.current_frame = camera.read()   # returns a BGR-image matrix
      # print self.current_frame.shape

      # this block of code displays only the red channel of each video frame
      # blue_ch, green_ch, red_ch = cv2.split(self.current_frame)
      # blueimg = np.zeros((self.current_frame.shape[0], self.current_frame.shape[1]), dtype=self.current_frame.dtype)
      # greenimg = blueimg
      # redimg = red_ch
      # self.current_frame = cv2.merge([blueimg, greenimg, redimg])
      
      self.redraw_click_points()
      self.redraw_rectangles()
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
      print "pixel at (%s, %s) = %s" % (x, y, self.current_frame[y][x])
    elif event == 2:   # right click
      del self.click_points[:]
      del self.rectangles[:]

  def redraw_click_points(self):
    if self.current_frame is not None:
      for point in self.click_points:
        x, y = 0, 0
        radius = 0
        if len(point) == 3:
          x, y, radius = point
        elif len(point) == 2:
          x, y = point
          radius = 4
        point = (x, y)
        self.draw_circle(self.current_frame, point, radius)
  
  def redraw_rectangles(self):
    if self.current_frame is not None:
      for rect in self.rectangles:
        top_left = rect[0]
        bottom_right = rect[1]
        self.draw_rectangle(self.current_frame, top_left, bottom_right)

  def draw_circle(self, image, center, radius, color = (0, 0, 255), thickness = 2):
    cv2.circle(image, center, radius, color, thickness)
  
  def draw_rectangle(self, image, top_left, bottom_right, color = (0, 0, 255), thickness = 2):
    cv2.rectangle(image, top_left, bottom_right, color, thickness)

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
        img.save_image(frame, "rangefind.jpg")
        return frame
      # distance = self.range_finder.compute_distance(image_capture_fn)
      # print "Distance to target: %s" % distance
    elif key == 97:     # a
      frame = self.video.current_frame
      img.save_image(frame, "frame.jpg")
    elif key == 114:    # r
      # draw rect
      image = self.video.current_frame
      rows = image.shape[0]
      cols = image.shape[1]
      top_left = ((cols / 2 - 1) - 10, rows / 2 - 1)
      bottom_right = ((cols / 2 - 1) + 10, rows - 1)
      self.video.add_rectangle(top_left, bottom_right)
      # self.range_finder.extract_laser_channel_rect(image)
    elif key == 102:    # f
      frame = self.video.current_frame
      circles = self.range_finder.find_red_dot_circles(frame)
      print "circles:"
      for circle in circles:
        print circle
        self.video.add_click_point(circle)
      # print "coords: (x=%s, y=%s)" % coords
    elif key == 13:     # enter
      print "fire gun!"
    
    return 0

# argv[1] is hostname
# argv[2] is port
TurretController(1, sys.argv[1], int(sys.argv[2])).display_live_video_stream()