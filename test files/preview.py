from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
picam2.start_preview(Preview.QTGL)  # Use QTGL for OpenGL accelerated preview

picam2.configure(picam2.create_preview_configuration())
picam2.start()
time.sleep(0)  # Keep running; you can use Ctrl+C to stop
input("Press Enter to stop preview...")
picam2.stop_preview()
picam2.close()
