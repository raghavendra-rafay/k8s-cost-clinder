# Kubernetes Cluster Instance Matching

This project is a Python-based server that helps identify the AWS EC2 instances or Azure VMs that best fit for a Kubernetes cluster based on their CPU and memory requirements and limits.

## Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerization)

## Installation

1. Clone the repository:

  ```bash
  git clone git@github.com:raghavendra-rafay/k8s-cost-clinder.git
  cd k8s-cost-clinder
  ```

2. (Optional) Create and activate a virtual environment:

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

3. Install the required Python dependencies:

  ```bash
  pip install -r requirements.txt
  ```

## Usage

1. Start the server:
  ```bash
  python app.py
  ```

2. Access the server:

Open your web browser and go to http://localhost:5000.
* If you see an HTML form, you can upload a kubeconfig file and click the "Identify Instance" button to get the instance information that best fits the Kubernetes cluster.
* If you see an error message or encounter any issues, please make sure the server is running correctly and check the terminal for any error logs.

## Docker Containerization (optional)

1. Build the Docker image:
  ```bash
  docker build -t flask-server .
  ```

2. Run the Docker container:
  ```bash
  docker run -p 5000:5000 --name flask-server-container flask-server
  ```

3. Access the server:

Open your web browser and go to http://localhost:9000.
