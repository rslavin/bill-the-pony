from abc import ABC, abstractmethod


class TrackingResponseInterface(ABC):
    """
    Interface that must be implemented by classes that respond to the position of the
    object tracked by the camera.
    """

    @abstractmethod
    def found_object(self, relative_coords=None):
        """
        What to do if the object is found
        :param relative_coords: [x, y] coords of object relative to center. Can be None if no object detected
        :return:
        """
        pass
