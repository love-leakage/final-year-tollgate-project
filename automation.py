# -*- coding: utf-8
import time
import sqlite3
import pytesseract
import cv2
import numpy as np
import torch
from picamera2 import Picamera2
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import lgpio
from mfrc522 import SimpleMFRC522
import smtplib
from email.message import EmailMessage

# OLED imports
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C

# === Configuration ===
MODEL_PATH = 'best.pt'
DATABASE_PATH = 'tollgate.db'
BUZZER_PIN = 18
SERVO_PIN = 17

# === Initialize hardware ===
i2c = busio.I2C(board.SCL, board.SDA)
oled = SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.show()

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, BUZZER_PIN)
lgpio.gpio_claim_output(chip, SERVO_PIN)

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

rfid = SimpleMFRC522()
model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH, force_reload=True)

# === Functions ===
def oled_show(text):
    oled.fill(0)
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((0, 0), text, font=font, fill=255)
    oled.image(image)
    oled.show()

def capture_image(filename="captured.jpg"):
    picam2.capture_file(filename)
    return filename

def crop_plate(img_path):
    img = Image.open(img_path)
    results = model(img)
    for det in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = map(int, det[:6])
        cropped = img.crop((x1, y1, x2, y2))
        cropped_path = "plate_crop.jpg"
        cropped.save(cropped_path)
        return cropped_path
    return None

def ocr_plate(crop_path):
    img = cv2.imread(crop_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(resized, -1, kernel)
    config = '--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(sharpened, config=config)
    return ''.join(e for e in text if e.isalnum()).upper()

def read_rfid():
    oled_show("Waiting for RFID")
    print("Waiting for RFID...")
    id, text = rfid.read()
    return text.strip().replace(" ", "")

def send_email(subject, body, image_path=None):
    EMAIL_ADDRESS = "rylyoga@gmail.com"
    EMAIL_PASSWORD = "xlqzhziphrdhksjw"
    TO_EMAIL = "rylyoga4229@gmail.com"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content(body)

    if image_path:
        with open(image_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename='plate.jpg')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def activate_buzzer():
    lgpio.gpio_write(chip, BUZZER_PIN, 1)
    time.sleep(1)
    lgpio.gpio_write(chip, BUZZER_PIN, 0)

def move_servo(degree):
    pulse = 500 + int((degree / 180) * 2000)
    duty_percent = pulse / 20000 * 100
    lgpio.tx_pwm(chip, SERVO_PIN, 50, duty_percent)
    time.sleep(1)
    lgpio.tx_pwm(chip, SERVO_PIN, 0, 0)

# === Main loop ===
while True:
    try:
        rfid_number = read_rfid()
        oled_show("Capturing Image")
        image_path = capture_image()

        oled_show("Detecting Plate")
        crop_path = crop_plate(image_path)
        if not crop_path:
            oled_show("No Plate Found")
            continue

        oled_show("Extracting Number")
        extracted_number = ocr_plate(crop_path)

        rfid_number = rfid_number.strip().replace(" ", "").upper()
        extracted_number = extracted_number.strip().replace(" ", "").upper()
        print(f"Comparing RFID: '{rfid_number}' with OCR: '{extracted_number}'")

        if rfid_number != extracted_number:
            oled_show("Not Match!")
            print("Mismatch Detected")
            activate_buzzer()
            move_servo(0)
            send_email("Not Match", f"RFID: {rfid_number}\nOCR: {extracted_number}", crop_path)
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute("INSERT INTO not_match (rfid_number, extracted_number) VALUES (?, ?)",
                         (rfid_number, extracted_number))
            conn.commit()
            conn.close()
            time.sleep(5)
            continue

        oled_show("Checking Stolen DB")
        print("MATCHED - Checking stolen DB")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stolen_vehicles WHERE vehicle_number = ?", (rfid_number,))
        stolen = cursor.fetchone()
        conn.close()

        if stolen:
            oled_show("Stolen Detected")
            print("STOLEN DETECTED")
            activate_buzzer()
            move_servo(0)
            send_email("Stolen Detected", f"Vehicle Number: {rfid_number}", crop_path)
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute("INSERT INTO log_entry (vehicle_number, status) VALUES (?, ?)",
                         (rfid_number, "Stolen"))
            conn.commit()
            conn.close()
        else:
            oled_show("Vehicle Allowed")
            print("VEHICLE ALLOWED")
            move_servo(90)
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute("INSERT INTO log_entry (vehicle_number, status) VALUES (?, ?)",
                         (rfid_number, "Allowed"))
            conn.commit()
            conn.close()
            time.sleep(5)
            move_servo(0)

        time.sleep(5)

    except KeyboardInterrupt:
        oled_show("System Stopped")
        break
