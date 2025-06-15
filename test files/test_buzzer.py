import RPi.GPIO as GPIO
import time

BUZZER_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

GPIO.output(BUZZER_PIN, GPIO.HIGH)
print("Buzzer ON")
time.sleep(2)
GPIO.output(BUZZER_PIN, GPIO.LOW)
print("Buzzer OFF")
GPIO.cleanup()
