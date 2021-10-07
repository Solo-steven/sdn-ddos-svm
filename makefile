.PHONY: mininet-start, controller-conllect, controller-detect

controller-install:
	cd controller && pipenv install
controller-collect: controller-install
	cd controller && pipenv run ryu-manager ./collect.py
controller-detect: controller-install
	cd controller && pipenv run ryu-manager ./detect.py

mininet-build:
	docker build -t test/docker ./mininet
mininet-start: mininet-build
	docker run --rm -it --privileged -e DISPLAY \
             -v /tmp/.X11-unix:/tmp/.X11-unix \
             -v /lib/modules:/lib/modules \
		test/docker

clean: 
	docker image rm test/docker