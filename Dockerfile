FROM python:3.8-slim as build


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app/
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. age_gender.proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. aggregator.proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. face_landmark.proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_input.proto


FROM python:3.8-slim


RUN apt-get update && apt-get install -y \
    python3-pip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY --from=build /app /app


COPY models /app/models


EXPOSE 50051 50052 50053 50054

ENV PYTHONUNBUFFERED=1

# Run all services
CMD ["sh", "-c", "python image_input_server.py & python face_landmark_server.py & python age_gender_server.py & python data_storage_server.py"]
