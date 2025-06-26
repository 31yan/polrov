from adafruit_pca9685 import PCA9685
import board
import busio
import random
import time

class MotorControl:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pwm = PCA9685(i2c)
        self.pwm.frequency = 50

        self.MOTOR_CHANNELS = {
            "motor_1": 1,
            "motor_2": 14,
            "motor_3": 3,
            "motor_4": 12,
            "motor_5": 5,
            "motor_6": 10
        }

        self.PWM_MIN = 700
        self.PWM_MAX = 2000
        self.PWM_MEDIUM = 1300
        self.PWM_SLOW = 1000

    def set_motor_throttle(self, channel, throttle_us):
        pwm_value = int((throttle_us / 20000) * 65535)
        self.pwm.channels[channel].duty_cycle = pwm_value

    def move_forward(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_5"], self.PWM_MEDIUM)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_6"], self.PWM_MEDIUM)

    def move_backward(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_1"], self.PWM_MEDIUM)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_2"], self.PWM_MEDIUM)

    def move_left(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_1"], self.PWM_MEDIUM)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_5"], self.PWM_MEDIUM)

    def move_right(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_2"], self.PWM_MEDIUM)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_6"], self.PWM_MEDIUM)

    def move_up(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_3"], self.PWM_MIN)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_4"], self.PWM_MIN)

    def move_down(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_3"], self.PWM_MEDIUM)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_4"], self.PWM_MEDIUM)

    def stop_all_motors(self):
        for ch in self.MOTOR_CHANNELS.values():
            self.set_motor_throttle(ch, self.PWM_MIN)

    def move_based_on_confidence(self, cylinder_confidence, gate_confidence, Cylinder_CONFIDENCE_THRESHOLD, Gate_CONFIDENCE_THRESHOLD):
        """Kontrol pergerakan robot berdasarkan confidence dari objek yang terdeteksi."""
        if cylinder_confidence >= Cylinder_CONFIDENCE_THRESHOLD:
            print(f"Cylinder terdeteksi (confidence {cylinder_confidence:.2f})")
            print("Robot bergerak ke kiri atau kanan...")
            if random.choice([True, False]):
                self.move_left()
                arah = "kiri"
            else:
                self.move_right()
                arah = "kanan"
            print(f"Robot bergerak ke {arah}")
            time.sleep(2)  # Durasi gerakan
            self.stop_all_motors()

        elif gate_confidence >= Gate_CONFIDENCE_THRESHOLD:
            print(f"Gate terdeteksi (confidence {gate_confidence:.2f})")
            # Gerakan ketika Gate terdeteksi
            self.set_motor_throttle(self.MOTOR_CHANNELS["motor_3"], self.PWM_MAX)
            self.set_motor_throttle(self.MOTOR_CHANNELS["motor_4"], self.PWM_MAX)
            self.set_motor_throttle(self.MOTOR_CHANNELS["motor_5"], self.PWM_SLOW)
            self.set_motor_throttle(self.MOTOR_CHANNELS["motor_6"], self.PWM_SLOW)

        else:
            print("Tidak ada objek yang terdeteksi, robot bergerak maju dan turun")
            self.move_forward()
            self.move_down()
