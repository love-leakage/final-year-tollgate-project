import cv2
import pytesseract
from picamera2 import Picamera2
from time import sleep

# Initialize Picamera2
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
sleep(2)  # allow camera to warm up

# Capture image
frame = picam2.capture_array()

# Optional: save image for debugging
cv2.imwrite("capture.jpg", frame)

# Convert to grayscale for better OCR results
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# OCR with Tesseract
text = pytesseract.image_to_string(gray)

# Print the result
print("Extracted Text:")
print(text)

# Optionally show the image
cv2.imshow("Captured Image", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
