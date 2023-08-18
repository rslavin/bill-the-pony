import pigpio
from .tracking_response_interface import TrackingResponseInterface

HORIZ_PIN = 17
VERT_PIN = 27
FREQUENCY = 50
# size in pixels of center region of image
CENTER_TOLERANCE_X = 30
CENTER_TOLERANCE_Y = 30
SERVO_START_X = 1300
SERVO_START_Y = 800
SERVO_MIN = 500
SERVO_MAX = 2500
SERVO_INCREMENT_X = 20
SERVO_INCREMENT_Y = 20


class Gimbal(TrackingResponseInterface):

    def __init__(self):
        self.pwm = pigpio.pi()
        self.pwm.set_mode(HORIZ_PIN, pigpio.OUTPUT)
        self.pwm.set_mode(VERT_PIN, pigpio.OUTPUT)
        self.pwm.set_PWM_frequency(HORIZ_PIN, FREQUENCY)
        self.pwm.set_PWM_frequency(VERT_PIN, FREQUENCY)
        self.horiz_current_duty = SERVO_START_X
        self.vert_current_duty = SERVO_START_Y
        self.pwm.set_servo_pulsewidth(HORIZ_PIN, self.horiz_current_duty)
        self.pwm.set_servo_pulsewidth(VERT_PIN, self.vert_current_duty)

    def found_object(self, relative_coords=None):
        if not relative_coords:
            return

        if relative_coords[0] < -CENTER_TOLERANCE_X:
            self.horiz_current_duty = min(self.horiz_current_duty + SERVO_INCREMENT_X, SERVO_MAX)
        elif relative_coords[0] > CENTER_TOLERANCE_X:
            self.horiz_current_duty = max(self.horiz_current_duty - SERVO_INCREMENT_X, SERVO_MIN)
        self.pwm.set_servo_pulsewidth(HORIZ_PIN, self.horiz_current_duty)

        if relative_coords[1] > CENTER_TOLERANCE_Y:
            self.vert_current_duty = min(self.vert_current_duty + SERVO_INCREMENT_Y, SERVO_MAX)
        elif relative_coords[1] < -CENTER_TOLERANCE_Y:
            self.vert_current_duty = max(self.vert_current_duty - SERVO_INCREMENT_Y, SERVO_MIN)
        self.pwm.set_servo_pulsewidth(VERT_PIN, self.vert_current_duty)
