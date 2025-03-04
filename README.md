

# **Face Processing gRPC Services with Redis**
This project consists of multiple **gRPC-based microservices** for **face detection, landmark detection, age/gender estimation, and data storage**. It uses **Redis** for caching detected results.

## **🚀 Features**
- **Face Landmark Detection** using `dlib`
- **Age & Gender Estimation** using OpenCV DNN models
- **Data Storage Service** for saving images and metadata
- **Redis Integration** for caching results
- **gRPC Communication** between services


## **🛠 Installation & Setup**

### **1️⃣ Requirement files

Download the necessary models:

- shape_predictor_68_face_landmarks.dat
- age_net.caffemodel
- age_deploy.prototxt
- gender_net.caffemodel
- gender_deploy.prototxt


### **2️⃣ Start Redis**
Run Redis using Docker:

```bash
docker run -it -p 6379:6379 redis
```

---

### **3️⃣ Compile gRPC Protobuf Files**
Before running the services, compile the `.proto` files:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. age_gender.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. aggregator.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. face_landmark.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_input.proto
```

---

### **4️⃣ Run gRPC Services**
Each service runs on a different port.

#### **Start Face Landmark Detection Service (Port 50052)**
```bash
python face_landmark_server.py
```

#### **Start Age/Gender Detection Service (Port 50053)**
```bash
python age_gender_server.py
```

#### **Start Data Storage Service (Port 50054)**
```bash
python data_storage_server.py
```

#### **Start Image Input Service (Port 50051)**
```bash
python image_input_server.py
```

---

## **🔹 How to Use**
### **Send an Image for Processing**
To send an image for processing, use the `image_input_client.py` script:

```bash
python image_input_client.py path/to/image.jpg
```

## **🔹 Docker**

docker-compose build --no-cache


docker-compose up -d

