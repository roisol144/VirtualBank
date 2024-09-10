# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file and install the dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables to avoid Python buffering issues
ENV PYTHONUNBUFFERED=1

# Expose the desired port (ensure this matches the port your app will run on)
EXPOSE 8000

# Command to run the application
CMD ["python", "server.py"] 
