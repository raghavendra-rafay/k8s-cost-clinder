import os
import requests
import pandas as pd
import csv
import re
import json

from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from kubernetes import client, config
from flask import Flask, request, jsonify, render_template
from notebook.main import OpenApiModel
app = Flask(__name__)

def fetch_aws_instance_data():
    # Fetch AWS instance specifications

    instance_data = []
    with open('aws/aws_data.csv') as file_obj:
        reader_obj = csv.reader(file_obj)
        next(reader_obj)
        for row in reader_obj:
            instance_data.append({
                'InstanceType': row[0],
                'vCPU': row[1],
                'Memory': row[2],
                'Price': row[3]
            })
    return instance_data

    '''
    instance_spec_url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json"
    instance_specs = requests.get(instance_spec_url).json()

    # Retrieve AWS instance data
    instance_data = []
    for sku, details in instance_specs['products'].items():
        if details['productFamily'] == 'Compute Instance':
            instance_data.append({
                'InstanceType': details['attributes']['instanceType'],
                'vCPU': details['attributes']['vcpu'],
                'Memory': details['attributes']['memory'],
                'Storage': details['attributes']['storage'],
                'Price': details['priceDimensions'][''].get('pricePerUnit', 'N/A')
            })

    return instance_data
    '''

def fetch_azure_instance_data():
    # Fetch Azure instance specifications
    instance_data = []
    with open("azure/azure.json", 'r') as json_file:
        data = json.load(json_file)
        for item in data:
            #print(item)
            if item.get("CPU") is None or item.get("Memory") == None or item.get("Cost") == None:
                print("A parameter is not present", item)
                continue
            instance_data.append({
                'InstanceType': item["InstanceType"],
                'vCPU': item["CPU"],
                'Memory': str(item["Memory"]) + " GiB",
                'Price': item["Cost"]
            })
    return instance_data

    '''
    instance_spec_url = "https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and priceType eq 'Consumption' and armRegionName eq 'your_region'"
    instance_specs = requests.get(instance_spec_url).json()

    # Retrieve Azure instance data
    instance_data = []
    for item in instance_specs['Items']:
        if item['productType'] == 'Virtual Machines':
            instance_data.append({
                'InstanceType': item['productName'],
                'vCPU': item['vCPUs'],
                'Memory': item['memory'],
                'Storage': item['storage'],
                'Price': item['unitPrice']
            })

    return instance_data
    '''

def get_total_resource_requests_and_limits():
    # Load Kubernetes configuration from the provided kubeconfig file
    kubeconfig_file = request.files['kubeconfig']
    kubeconfig_path = '/tmp/kubeconfig'
    kubeconfig_file.save(kubeconfig_path)
    config.load_kube_config(config_file=kubeconfig_path)

    # Create Kubernetes API client
    api_instance = client.CoreV1Api()

    # Get all pods in the cluster
    pods = api_instance.list_pod_for_all_namespaces(watch=False)

    total_requests_cpu = 0
    total_requests_memory = 0
    total_limits_cpu = 0
    total_limits_memory = 0

    for pod in pods.items:
        # Retrieve the container specifications for the pod
        containers = pod.spec.containers

        for container in containers:
            # Retrieve the resource requirements and limits for the container
            resources = container.resources

            # Retrieve CPU requests and limits
            if resources.requests and 'cpu' in resources.requests:
                cpu_request = resources.requests['cpu']
                total_requests_cpu += parse_quantity(cpu_request)

            if resources.limits and 'cpu' in resources.limits:
                cpu_limit = resources.limits['cpu']
                total_limits_cpu += parse_quantity(cpu_limit)

            # Retrieve memory requests and limits
            if resources.requests and 'memory' in resources.requests:
                memory_request = resources.requests['memory']
                total_requests_memory += parse_quantity(memory_request)

            if resources.limits and 'memory' in resources.limits:
                memory_limit = resources.limits['memory']
                total_limits_memory += parse_quantity(memory_limit)

    # Delete the temporary kubeconfig file
    os.remove(kubeconfig_path)

    return total_requests_cpu, total_requests_memory, total_limits_cpu, total_limits_memory


def extract_value_and_unit(string):
    pattern = r'(\d+(\.\d+)?)\s*([a-zA-Z]+)?'
    match = re.search(pattern, string)

    if match:
        value = float(match.group(1))
        unit = match.group(3) or ''
        return value, unit
    else:
        return None

def parse_quantity(quantity):
    # Parse the quantity value and convert it to CPU or memory value
    value, unit = extract_value_and_unit(quantity)

    if unit == 'n':
        return value / 1000000
    if unit == '':
        return value
    if unit == 'm':
        return value / 1000
    elif unit == 'Ki':
        return value / 1024
    elif unit == 'Mi':
        return value / 1024
    elif unit == 'Gi':
        return value
    elif unit == 'Ti':
        return value * 1024
    elif unit == 'Pi':
        return value * 1024 * 1024
    else:
        return 0

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/scikit-learn/identify", methods=["POST"])
def scikit_learn_identify():
    # Call the function to fetch total CPU and memory requests and limits
    total_requests_cpu, total_requests_memory, total_limits_cpu, total_limits_memory = get_total_resource_requests_and_limits()

    # Create a DataFrame for the cluster requests and limits
    cluster_data = pd.DataFrame([
        {'vCPU': total_requests_cpu, 'Memory': total_requests_memory, 'Price': 0},
        {'vCPU': total_limits_cpu, 'Memory': total_limits_memory, 'Price': 0}
    ])

    # Predict the common neighbor instance type for the cluster
    predicted_instance_type = knn.predict(cluster_data)

    response = {
        'predicted_instance_type': predicted_instance_type[0],
        'total_cpu_requests': total_requests_cpu,
        'total_memory_requests': total_requests_memory,
        'total_cpu_limits': total_limits_cpu,
        'total_memory_limits': total_limits_memory
    }

    return jsonify(response)

@app.route("/openapi/identify", methods=["POST"])
def openapi_identify():
    # Call the function to fetch total CPU and memory requests and limits
    total_requests_cpu, total_requests_memory, total_limits_cpu, total_limits_memory = get_total_resource_requests_and_limits()
    return openapi_model.get_instance(total_requests_cpu, total_requests_memory)

def build_scikit_model(knn):
    # Fetch AWS EC2 instance data
    # aws_instance_data = fetch_aws_instance_data()

    # Fetch Azure VM instance data
    azure_instance_data = fetch_azure_instance_data()

    # Combine AWS and Azure instance data
    # instance_data = aws_instance_data + azure_instance_data
    instance_data = azure_instance_data

    # Create a pandas DataFrame
    df = pd.DataFrame(instance_data)

    # Preprocess the data
    df['Memory'] = df['Memory'].str.extract('(\d+)').astype(float)  # Extract memory value in GB
    df['Price'] = df['Price'].astype(float)  # Convert price to float

    # Split the data into training and test sets
    X = df[['vCPU', 'Memory', 'Price']]
    y = df['InstanceType']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    knn.fit(X_train, y_train)



if __name__ == '__main__':
    # Create and train the KNN classifier
    knn = KNeighborsClassifier(n_neighbors=3)
    build_scikit_model(knn=knn)
    openapi_model = OpenApiModel("aws/aws_data.csv")

    app.run(debug=True)
