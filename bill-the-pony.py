#!/usr/bin/env python3
import numpy as np
import cv2
import RPi.GPIO as GPIO
import sys

# GPIO pin numbers
LED_LEFT_PIN = 16
LED_CENTER_PIN = 20
LED_RIGHT_PIN = 21
# width and height to resize image before sending to model
# smaller => faster, larger => more accurate
IMG_MODEL_SZ_PX = 150
# width and height to resize for display
IMG_DISPLAY_SZ_PX = 720
# size in pixels of center region of image (IMG_MODEL_SIZE_PX)
CENTER_SIZE_PX = 15


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

    # initialize the HOG descriptor/person detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    if show_video:
        cv2.startWindowThread()
    # open webcam video stream
    stream = cv2.VideoCapture(0)

    while True:

        # capture frame and resize based on speed/accuracy preferences
        frame = cv2.resize(stream.read()[1], (IMG_MODEL_SZ_PX, IMG_MODEL_SZ_PX))

        # detect people in the image
        # returns the bounding boxes for the detected objects
        boxes = hog.detectMultiScale(frame, winStride=(1, 1), scale=1.05)[0]
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        centers = []

        # generate list of box locations
        for box in boxes:
            # x coordinate of center of box
            x_pos = ((box[2] - box[0]) / 2) + box[0]
            # x distance from center
            x_pos_rel_center = x_pos - IMG_MODEL_SZ_PX / 2
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
            print(f"Position: {center_box_pos_x} / {IMG_MODEL_SZ_PX} px")
        else:
            set_lights([0, 0, 0])
            print("------------------")

        # display the resulting frame
        if show_video:
            frame = cv2.resize(frame, (IMG_DISPLAY_SZ_PX, IMG_DISPLAY_SZ_PX))
            cv2.imshow("Bill the Pony", frame)

        # TODO fix this
        # break if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stream.release()
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    # TODO args for everything
    # if any args are passed, don't show video (i.e., command line mode)
    watch(len(sys.argv) == 1)
