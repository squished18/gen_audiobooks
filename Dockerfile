# From Powershell:
# docker build -t kokoro-1 .
# docker run -d --name kokoro-api --gpus all -p 8880:8880 -v "${PWD}:/app" kokoro-1

# Use the exact versioned tag for Ubuntu 24.04
# FROM nvidia/cuda:13.1.1-cudnn-devel-ubuntu24.04
FROM nvidia/cuda:12.6.2-cudnn-devel-ubuntu24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV ONNX_PROVIDER=CUDAExecutionProvider

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    nvtop \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install AI packages directly using the system pip
RUN pip3 install --no-cache-dir \
    kokoro-onnx \
    fastapi \
    uvicorn \
    soundfile \
    python-multipart \
    && pip3 uninstall -y onnxruntime \
    && pip3 install --no-cache-dir onnxruntime-gpu

# Copy your local code into the container
COPY . .

# Expose the API port
EXPOSE 8880

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8880"]