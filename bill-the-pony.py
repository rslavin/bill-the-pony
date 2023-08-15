#!/usr/bin/env python3
import numpy as np
import outputs.light_align as out
import cv2
import sys

# width and height to resize image before sending to model
# smaller => faster, larger => more accurate
FRAME_MODEL_WIDTH = 320
FRAME_MODEL_HEIGHT = 200
# width and height to resize for display
FRAME_DISPLAY_WIDTH = 540
FRAME_DISPLAY_HEIGHT = 300

# path to cascade classifier facial layout data
CASCADE_PATH = '/usr/share/opencv4/lbpcascades/lbpcascade_frontalface_improved.xml'


def watch(show_video=True):
    """
    Begin video stream and find people. Draw boxes around each person's face. The most center box is green.
    :param show_video: Determines whether video window with boxes around detections should be shown. Defaults to True.
    :return:
    """

    # initialize output hardware
    output = out.LightAlign()

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
        else:  # no boxes
            output.no_object()

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
