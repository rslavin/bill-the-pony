import RPi.GPIO as GPIO
from .tracking_response_interface import TrackingResponseInterface

# GPIO pin numbers
LED_LEFT_PIN = 16
LED_CENTER_PIN = 20
LED_RIGHT_PIN = 21
# size in pixels of center region of image
CENTER_SIZE_PX = 15


def set_lights(light_states):
    """
    Sets left, center, and right lights to on or off.
    :param light_states: List of integers: [left, center, right] with 0 for off and 1 for on.
    :return:
    """

    GPIO.output(LED_LEFT_PIN, GPIO.HIGH if light_states[0] else GPIO.LOW)
    GPIO.output(LED_CENTER_PIN, GPIO.HIGH if light_states[1] else GPIO.LOW)
    GPIO.output(LED_RIGHT_PIN, GPIO.HIGH if light_states[2] else GPIO.LOW)


class LightAlign(TrackingResponseInterface):
    def __init__(self):
        """
        Initialize Raspberry Pi pins
        :return:
        """
        # initialize Raspberry Pi pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LED_LEFT_PIN, GPIO.OUT)
        GPIO.setup(LED_RIGHT_PIN, GPIO.OUT)
        GPIO.setup(LED_CENTER_PIN, GPIO.OUT)

    def found_object(self, relative_coords):
        """
        Calculates what region the object is in the frame based on CENTER_SIZE_PX, which
        specifies the center region and partitions the left and right regions.
        :param relative_coords: [x, y] coords of object relative to center
        :return:
        """
        # calculate which side of the image the center-most box is on
        if -CENTER_SIZE_PX <= relative_coords[0] <= CENTER_SIZE_PX:
            print("------CENTER------")
            set_lights([0, 1, 0])
        elif relative_coords[0] >= CENTER_SIZE_PX:
            print("-------------RIGHT")
            set_lights([0, 0, 1])
        elif relative_coords[0] <= -CENTER_SIZE_PX:
            print("LEFT--------------")
            set_lights([1, 0, 0])

    def no_object(self):
        """
        If no object is found, the lights are turned off.
        :return:
        """
        set_lights([0, 0, 0])
        print("------------------")
