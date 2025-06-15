from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

try:
    print("Place your RFID tag near the reader...")
    while True:
        id, text = reader.read()
        print(f"RFID Tag ID: {id}, Text: {text}")
        time.sleep(2)
except KeyboardInterrupt:
    print("Stopped")
finally:
    GPIO.cleanup()
