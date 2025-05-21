# Use a Python base image suitable for AWS Lambda (e.g., Amazon Linux based)
# python:3.9-slim-buster is a good starting point for smaller images,
# but for Lambda, a specific Amazon Linux base might be more aligned if not using layers.
# For simplicity and common Docker usage, we'll use a standard Python slim image.
FROM python:3.13-slim

# Install poppler-utils and other necessary dependencies
# poppler-utils is required by pdf2image to convert PDFs
RUN apt-get update && \
    apt-get install -y \
    poppler-utils \
    libpoppler-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY app.py .
COPY lambda_function.py .
COPY templates templates/

# Expose the port Flask runs on (for local testing, not directly used by Lambda)
EXPOSE 5000

# Define the command to run the application using Gunicorn (a WSGI HTTP Server)
# Gunicorn is a common choice for deploying Flask apps in production.
# For AWS Lambda with wsgi_lambda, the handler is usually invoked directly by Lambda.
# This CMD is more for local Docker testing or if you were running this on EC2/ECS.
# For Lambda, you'd typically use the lambda_function.py as the handler.
# However, for a complete Docker setup, Gunicorn is good practice.
# If you are deploying to Lambda via a container image, Lambda will use the ENTRYPOINT/CMD
# to start your application, and wsgi_lambda will handle the event translation.
# The `wsgi_lambda` library is designed to work with the Lambda runtime interface.
# The `lambda_function.py` file is the entry point for Lambda.
# When building a Docker image for Lambda, the Lambda runtime will execute the handler
# specified in your Lambda function configuration (e.g., `lambda_function.lambda_handler`).
# This Dockerfile is more for a general Flask deployment.

# For AWS Lambda container images, you typically don't need a CMD that runs Gunicorn
# unless you're using a custom runtime or a specific base image that expects it.
# The Lambda runtime itself will invoke your handler.

# Let's adjust this Dockerfile to be explicitly for AWS Lambda Container Image.
# AWS Lambda provides a Runtime Interface Client (RIC) to handle the invocation.
# We need to install `aws-lambda-wsgi` and `aws-lambda-python-runtime-interface-client`
# and then use the correct entrypoint for the Lambda runtime.

# Update requirements.txt to include aws-lambda-wsgi and aws-lambda-python-runtime-interface-client
# For this Dockerfile, let's assume the requirements.txt has been updated.

# Install the AWS Lambda Python Runtime Interface Client and aws-lambda-wsgi
RUN pip install --no-cache-dir \
    aws-lambda-wsgi \
    aws-lambda-python-runtime-interface-client

# Command to run the application for AWS Lambda
# This is the entrypoint for the Lambda runtime, which will invoke your handler.
# The handler is specified in the Lambda function configuration (e.g., lambda_function.lambda_handler)
# For container images, the Lambda runtime will use the entrypoint/cmd to start the application.
# The `aws-lambda-wsgi` package provides the necessary integration.
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdawsgicli.main" ]
CMD [ "lambda_function.lambda_handler" ]

