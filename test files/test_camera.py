from picamera2 import Picamera2
import time

picam = Picamera2()
picam.start()
time.sleep(2)
picam.capture_file("captured_images/test.jpg")
picam.stop()

print("Image saved as test.jpg")
