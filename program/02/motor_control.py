import time
from adafruit_pca9685 import PCA9685
import busio
import board

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

        self.PWM_MIN = 700      # Motor mati / idle
        self.PWM_MAX = 2000     # Motor full speed
        self.PWM_MEDIUM = 1300  # Kecepatan sedang
        self.PWM_SLOW = 1000    # Kecepatan lambat

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

    def move_down(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_3"], self.PWM_MAX)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_4"], self.PWM_MAX)

    def move_up(self):
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_3"], self.PWM_MIN)
        self.set_motor_throttle(self.MOTOR_CHANNELS["motor_4"], self.PWM_MIN)

    def stop_all_motors(self):
        for ch in self.MOTOR_CHANNELS.values():
            self.set_motor_throttle(ch, self.PWM_MIN)
