#Python runtime based on Alpine Linux as a base image
FROM python:3.11.5-alpine

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache build-base libffi-dev
# Installing any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Current directory contents into the container at /app
COPY . .
# Assuming Dockerfile is in the root and for_dot is the main project directory
#COPY for_dot /app

# Copy fonts directory to Docker container
COPY fonts /app/fonts

EXPOSE 50

# Environment variable to specify the Python file to run
ENV FLASK_APP=appdot.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=50  
#Ensure Flask runs on port 50

# Running appdot.py when the container launches
CMD ["flask", "run"]
