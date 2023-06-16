# Makefile to build and run the Docker container

# Set the Docker image name
IMAGE_NAME = flask-server

# Set the Docker container name
CONTAINER_NAME = flask-server-container

# Default target
.PHONY: all
all: build run

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker container
.PHONY: run
run: build
	docker run -p 9000:5000 --name $(CONTAINER_NAME) $(IMAGE_NAME)

# Stop the Docker container
.PHONY: stop
stop:
	docker stop $(CONTAINER_NAME)

# Remove the Docker container
.PHONY: remove
remove:
	docker rm $(CONTAINER_NAME)

# Clean up Docker artifacts
.PHONY: clean
clean: stop remove
	docker image rm $(IMAGE_NAME)
