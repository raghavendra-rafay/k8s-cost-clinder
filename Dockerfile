# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask server files into the container
COPY app.py app.py
COPY templates ./templates
COPY aws ./aws
COPY azure ./azure
COPY notebook ./notebook

# Expose the port on which the Flask server will run
EXPOSE 5000

# Set the environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV OPENAI_API_KEY=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

# Start the Flask server
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
