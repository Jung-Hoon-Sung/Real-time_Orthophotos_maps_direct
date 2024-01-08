# Use an official Ubuntu 20.04 runtime as a parent image
FROM ubuntu:20.04

# Set the timezone
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Make sure the interactive dialog is not shown during the build process
ENV DEBIAN_FRONTEND=noninteractive

# Update package list, add repositories for Python 3.8 and GIS packages, 
# install various required packages, and clean up temporary package files 
# to reduce the image size.
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    add-apt-repository -y ppa:ubuntugis/ppa && \
    apt-get update && \
    apt-get install -y python3.8 python3-pip libgl1-mesa-dev libglib2.0-0 python3-tk libgdal-dev git && \
    rm -rf /var/lib/apt/lists/* && \
    unset DEBIAN_FRONTEND

# Install GDAL Python bindings
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir numpy && \
    pip3 install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL==`gdal-config --version`

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install remaining Python packages directly in the Dockerfile
RUN pip3 install --no-cache-dir \
    llvmlite==0.39.1 \
    markdown-it-py==2.2.0 \
    mdurl==0.1.2 \
    numba==0.56.4 \
    numpy==1.23.5 \
    opencv-python==4.7.0.72 \
    pyexiv2==2.8.1 \
    Pygments==2.15.1 \
    rich==13.3.4 \
    setuptools==57.4.0 \
    wheel==0.40.0 \
    fastapi \
    uvicorn \
    python-multipart

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run main.py when the container launches
CMD ["python3", "main.py"]
