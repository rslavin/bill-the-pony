#!/usr/bin/env python3
import numpy as np
import RPi.GPIO as GPIO
import outputs.light_align as lights_out
import outputs.gimbal as gimbal_out
import cv2
from argparse import ArgumentParser
from time import sleep

# width and height to resize image before sending to model
# smaller => faster, larger => more accurate
FRAME_MODEL_WIDTH = 320
FRAME_MODEL_HEIGHT = 320
# width and height to resize for display
FRAME_DISPLAY_WIDTH = 540
FRAME_DISPLAY_HEIGHT = 540
BUTTON_PIN = 22
ON_LIGHT_PIN = 23

# path to cascade classifier facial layout data
CASCADE_PATH_DEFAULT = '/usr/share/opencv4/lbpcascades/lbpcascade_frontalface.xml'


def watch(show_video=True, flip=False, cascade_path=CASCADE_PATH_DEFAULT):
    """
    Begin video stream and find people. Draw boxes around each person's face. The most center box is green.
    :param show_video: Determines whether video window with boxes around detections should be shown. Defaults to True.
    :param flip: Whether to flip the video vertically
    :param cascade_path: Path to cascade xml file. lbcascade_frontalface.xml used by default
    :return:
    """

    # initialize output hardware
    output = lights_out.LightAlign()
    output_gimbal = gimbal_out.Gimbal()

    # turn on light
    GPIO.output(ON_LIGHT_PIN, GPIO.HIGH)

    # initialize the cascade classifierA
    classifier = cv2.CascadeClassifier(cascade_path)

    if show_video:
        cv2.startWindowThread()
    # open webcam video stream and set dimensions
    stream = cv2.VideoCapture(0)
    stream.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_MODEL_WIDTH)
    stream.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_MODEL_HEIGHT)

    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        # capture frame and convert to grayscale for improved accuracy
        frame = stream.read()[1]
        if flip:
            frame = cv2.flip(frame, -1)
        gray_frame = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY))

        # detect faces in the frame
        # returns the bounding boxes for the detected objects
        boxes = classifier.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=3, flags=0, minSize=(5, 5))
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        centers = []

        # generate list of box locations
        for box in boxes:
            # coordinates of center of box
            x_pos = ((box[2] - box[1]) / 2) + box[0]
            y_pos = ((box[3] - box[1]) / 3) + box[1]

            # distance from center
            x_pos_rel_center = x_pos - FRAME_MODEL_WIDTH / 2
            y_pos_rel_center = y_pos - FRAME_MODEL_HEIGHT / 2
            centers.append(
                {'box': box, 'pos_rel_center': (x_pos_rel_center, y_pos_rel_center),
                 'dist_to_center': (abs(x_pos_rel_center), abs(y_pos_rel_center))})

        if centers:
            sorted_boxes = sorted(centers, key=lambda b: b['dist_to_center'][0])

            # draw boxes
            for box in range(len(sorted_boxes)):
                box_color = (0, 0, 255) if box else (0, 255, 0)
                cv2.rectangle(frame, (sorted_boxes[box]['box'][0], sorted_boxes[box]['box'][1]),
                              (sorted_boxes[box]['box'][2], sorted_boxes[box]['box'][3]), box_color, 2)

            # output
            output.found_object(sorted_boxes[0]['pos_rel_center'])
            output_gimbal.found_object(sorted_boxes[0]['pos_rel_center'])
        else:  # no boxes
            output.found_object()
            output_gimbal.found_object()

        # display the resulting frame
        if show_video:
            frame = cv2.resize(frame, (FRAME_DISPLAY_WIDTH, FRAME_DISPLAY_HEIGHT))
            if flip:
                frame = cv2.flip(frame, 1)
            cv2.imshow("Bill the Pony", frame)

    stream.release()
    cv2.destroyAllWindows()


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-n", "--no-video", action="store_true",
                        help="disable video playback -- for command-line invocation")
    parser.add_argument("-f", "--flip", action="store_true",
                        help="flip the video vertically -- use mounting camera upside down")
    parser.add_argument("-c", "--cascade-path", action="store",
                        help="custom location of cascade xml file for face detection")

    return parser.parse_args()


def main():
    # setup button
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ON_LIGHT_PIN, GPIO.OUT)

    # block until button is pressed
    while GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING):
        args = parse_args()
        sleep(0.5)
        watch(show_video=not args.no_video, flip=args.flip,
              cascade_path=args.cascade_path if args.cascade_path else CASCADE_PATH_DEFAULT)
        lights_out.set_lights([0, 0, 0])
        GPIO.output(ON_LIGHT_PIN, GPIO.LOW)
        sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
