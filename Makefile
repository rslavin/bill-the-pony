all: prerequisites update-upgrade configure-swap install-packages bill-daemon pigpio-daemon start-pigpiod install-opencv reset-swap

prerequisites:
	@echo "Installing prerequisites..."
	sudo apt-get install -y wget unzip cmake || (echo "Failed to install prerequisites!" && exit 1)

update-upgrade:
	@echo "Updating and upgrading system packages..."
	sudo apt-get update && sudo apt-get upgrade || (echo "Failed to update or upgrade!" && exit 1)

configure-swap:
	@echo "Configuring swap size..."
	sudo sed -I 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile || (echo "Failed to configure swap size!" && exit 1)
	sudo /etc/init.d/dphys-swapfile restart || (echo "Failed to restart swap!" && exit 1)

install-packages:
	@echo "Installing required packages..."
	sudo apt-get install -y build-essential pkg-config \
	libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev \
	libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
	libxvidcore-dev libx264-dev \
	libgtk2.0-dev libgtk-3-dev \
	libatlas-base-dev gfortran || (echo "Failed to install packages!" && exit 1)
	sudo pip3 install numpy python3-pigpio || (echo "Failed to install Python packages!" && exit 1)

pigpio-daemon:
	@echo "Configuring pigpio daemon..."
	sudo cp ./install_scripts/pigpiod /etc/init.d || (echo "Failed to copy pigpiod!" && exit 1)
	sudo update-rc.d pigpiod defaults || (echo "Failed to set pigpiod defaults!" && exit 1)
	sudo update-rc.d pigpiod enable || (echo "Failed to enable pigpiod!" && exit 1)

start-pigpiod:
	@echo "Starting pigpiod..."
	sudo /etc/init.d/pigpiod start || (echo "Failed to start pigpiod!" && exit 1)

install-opencv:
	@echo "Installing OpenCV..."
	wget -O opencv.zip https://github.com/opencv/opencv/archive/4.4.0.zip || (echo "Failed to download OpenCV!" && exit 1)
	wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.4.0.zip || (echo "Failed to download OpenCV contrib!" && exit 1)
	unzip opencv.zip || (echo "Failed to unzip OpenCV!" && exit 1)
	unzip opencv_contrib.zip || (echo "Failed to unzip OpenCV contrib!" && exit 1)
	cd ./opencv-4.4.0/ && mkdir build && cd build && \
	cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib-4.4.0/modules \
	-D BUILD_EXAMPLES=ON .. || (echo "CMake configuration failed!" && exit 1)
	make -j $(nproc) || (echo "Make failed for OpenCV!" && exit 1)
	sudo make install && sudo ldconfig || (echo "Failed to install OpenCV!" && exit 1)

reset-swap:
	@echo "Resetting swap size..."
	sudo sed -I 's/CONF_SWAPSIZE=2048/CONF_SWAPSIZE=100/' /etc/dphys-swapfile || (echo "Failed to reset swap size!" && exit 1)
	@echo "Done. Please reboot your system using the command: sudo reboot"

clean:
	@echo "Cleaning up..."
	rm -rf opencv-4.4.0 opencv.zip opencv_contrib.zip
	@echo "Cleanup complete."

.PHONY: all prerequisites update-upgrade configure-swap install-packages bill-daemon pigpio-daemon start-pigpiod install-opencv reset-swap clean
