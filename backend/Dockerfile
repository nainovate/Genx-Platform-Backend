# Use the Python 3.9.6 Alpine image as the base for our Docker image
FROM python:3.9.6


# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory into the container at /app
COPY . .

# Start the Flask application when the container starts
CMD ["python", "main.py"]

# FROM python:3.8-alpine: This sets the base image to the official Python 3.8 image with the Alpine Linux distribution.
# WORKDIR /app: This sets the working directory inside the container to /app, where we will copy our application files.
# COPY requirements.txt .: This copies the requirements.txt file from our local directory to the /app directory in the container.
# RUN pip install --no-cache-dir -r requirements.txt: This installs the Python dependencies specified in requirements.txt using pip. The --no-cache-dir option ensures that pip does not use the cache and saves disk space.
# COPY . .: This copies the entire local directory into the /app directory in the container.
# CMD ["python", "app.py"]: This sets the command that will run when the container starts, which is to run the app.py file using the python interpreter.
