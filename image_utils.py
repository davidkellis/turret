import cv2

def center_point(image):
  rows = image.shape[0]
  cols = image.shape[1]
  
  x = cols / 2 - 1
  y = rows / 2 - 1
  
  return (x, y)

def save_image(image, filename):
  return cv2.imwrite(filename, image)