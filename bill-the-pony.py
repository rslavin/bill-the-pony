#!/usr/bin/env python3
import numpy as np
import RPi.GPIO as GPIO
import cv2
import sys

# GPIO pin numbers
LED_LEFT_PIN = 16
LED_CENTER_PIN = 20
LED_RIGHT_PIN = 21
# width and height to resize image before sending to model
# smaller => faster, larger => more accurate
FRAME_MODEL_WIDTH = 320
FRAME_MODEL_HEIGHT = 200
# width and height to resize for display
FRAME_DISPLAY_WIDTH = 540
FRAME_DISPLAY_HEIGHT = 300
# size in pixels of center region of image (IMG_MODEL_SIZE_PX)
CENTER_SIZE_PX = 15
# path to cascade classifier facial layout data
CASCADE_PATH = '/usr/share/opencv4/lbpcascades/lbpcascade_frontalface_improved.xml'


def init_rpi_pins():
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


def set_lights(light_states):
    """
    Sets left, center, and right lights to on or off.
    :param light_states: List of integers: [left, center, right] with 0 for off and 1 for on.
    :return:
    """

    GPIO.output(LED_LEFT_PIN, GPIO.HIGH if light_states[0] else GPIO.LOW)
    GPIO.output(LED_CENTER_PIN, GPIO.HIGH if light_states[1] else GPIO.LOW)
    GPIO.output(LED_RIGHT_PIN, GPIO.HIGH if light_states[2] else GPIO.LOW)


def watch(show_video=True):
    """
    Begin video stream and find people.
    :param show_video: Determines whether video window with boxes around detections should be shown. Defaults to True.
    :return:
    """

    # initialize rpi
    init_rpi_pins()

    # initialize the cascade classifierA
    classifier = cv2.CascadeClassifier(CASCADE_PATH)

    if show_video:
        cv2.startWindowThread()
    # open webcam video stream and set dimensions
    stream = cv2.VideoCapture(0)
    stream.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_MODEL_WIDTH)
    stream.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_MODEL_HEIGHT)

    while True:

        # capture frame and convert to grayscale for improved accuracy
        frame = stream.read()[1]
        # frame = cv2.flip(frame, -1)
        gray_frame = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY))

        # detect faces in the frame
        # returns the bounding boxes for the detected objects
        boxes = classifier.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=3, flags=0, minSize=(5, 5))
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        centers = []

        # generate list of box locations
        for box in boxes:
            # x coordinate of center of box
            x_pos = ((box[2] - box[0]) / 2) + box[0]
            # x distance from center
            x_pos_rel_center = x_pos - FRAME_MODEL_WIDTH / 2
            centers.append(
                {'box': box, 'x_pos_rel_center': x_pos_rel_center, 'dist_to_center_x': abs(x_pos_rel_center)})

        # if boxes are detected, do stuff
        if centers:
            sorted_boxes = sorted(centers, key=lambda b: b['dist_to_center_x'])

            # draw boxes
            for box in range(len(sorted_boxes)):
                box_color = (0, 0, 255) if box else (0, 255, 0)
                cv2.rectangle(frame, (sorted_boxes[box]['box'][0], sorted_boxes[box]['box'][1]),
                              (sorted_boxes[box]['box'][2], sorted_boxes[box]['box'][3]), box_color, 2)

            # calculate which side of the image the center-most box is on
            center_box_pos_x = sorted_boxes[0]['x_pos_rel_center']
            if -CENTER_SIZE_PX <= center_box_pos_x <= CENTER_SIZE_PX:
                print("------CENTER------")
                set_lights([0, 1, 0])
            elif center_box_pos_x >= CENTER_SIZE_PX:
                print("-------------RIGHT")
                set_lights([0, 0, 1])
            elif center_box_pos_x <= -CENTER_SIZE_PX:
                print("LEFT--------------")
                set_lights([1, 0, 0])
            print(f"Position: {center_box_pos_x} / {FRAME_MODEL_WIDTH} px")
        else:
            set_lights([0, 0, 0])
            print("------------------")

        # display the resulting frame
        if show_video:
            frame = cv2.resize(frame, (FRAME_DISPLAY_WIDTH, FRAME_DISPLAY_HEIGHT))
            # frame = cv2.flip(frame, 1)
            cv2.imshow("Bill the Pony", frame)

        # TODO fix this
        # break if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stream.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    # TODO args for everything (flip, model location, etc.)
    # if any args are passed, don't show video (i.e., command line mode)
    watch(len(sys.argv) == 1)
