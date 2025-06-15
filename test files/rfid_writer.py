from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    text = input("Enter vehicle number to write to tag: ").replace(" ", "")
    print("Now place your RFID tag near the reader...")
    reader.write(text)
    print(f"? Written to tag: {text}")
finally:
    import RPi.GPIO as GPIO
    GPIO.cleanup()
