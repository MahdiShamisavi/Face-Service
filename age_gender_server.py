import grpc
from concurrent import futures
import redis
import hashlib
import datetime
import cv2
import numpy as np
import dlib
import age_gender_pb2
import age_gender_pb2_grpc
import aggregator_pb2
import aggregator_pb2_grpc

# Age & Gender Detection Models
age_model = "age_net.caffemodel"
age_proto = "age_deploy.prototxt"
gender_model = "gender_net.caffemodel"
gender_proto = "gender_deploy.prototxt"

age_net = cv2.dnn.readNet(age_model, age_proto)
gender_net = cv2.dnn.readNet(gender_model, gender_proto)


AGE_BUCKETS = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]
GENDER_LABELS = ["Male", "Female"]

# Face Detector
detector = dlib.get_frontal_face_detector()

redis_client = redis.Redis(host="localhost", port=6379, db=0)


class AgeGenderServicer(age_gender_pb2_grpc.AgeGenderServicer):
    def EstimateAgeGender(self, request, context):
        image_data = request.image_data
        image_hash = hashlib.md5(image_data).hexdigest()

        # Convert image data to OpenCV format
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid image data")
            return age_gender_pb2.AgeGenderResponse(
                image_hash=image_hash, age_gender=[]
            )

        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No faces detected")
            return age_gender_pb2.AgeGenderResponse(
                image_hash=image_hash, age_gender=[]
            )

        detected_data = []

        for face in faces:
            
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            face_roi = image[y : y + h, x : x + w]

            
            if face_roi.shape[0] == 0 or face_roi.shape[1] == 0:
                continue

          
            blob = cv2.dnn.blobFromImage(
                face_roi,
                scalefactor=1.0,
                size=(227, 227),
                mean=(78.4263377603, 87.7689143744, 114.895847746),
                swapRB=False,
            )

            # Detect Gender
            gender_net.setInput(blob)
            gender_preds = gender_net.forward()
            gender = GENDER_LABELS[gender_preds[0].argmax()]

            # Detect Age
            age_net.setInput(blob)
            age_preds = age_net.forward()
            age = AGE_BUCKETS[age_preds[0].argmax()]

            detected_data.append(f"{age}, {gender}")

        # Store results in Redis
        redis_client.hset(image_hash, "age_gender", str(detected_data))

        # Call Aggregator Service to save metadata and image
        try:
            aggregator_channel = grpc.insecure_channel("localhost:50054")
            aggregator_stub = aggregator_pb2_grpc.AggregatorStub(aggregator_channel)
            current_time = datetime.datetime.now().isoformat()
            aggregator_response = aggregator_stub.SaveFaceAttributes(
                aggregator_pb2.FaceAttributesRequest(
                    time=current_time, frame=image_data, redis_key=image_hash
                )
            )
            print("Aggregator response from AgeGender Service:", aggregator_response)
        except Exception as e:
            print("Error calling Aggregator from AgeGender Service:", e)

        return age_gender_pb2.AgeGenderResponse(
            image_hash=image_hash, age_gender=detected_data
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    age_gender_pb2_grpc.add_AgeGenderServicer_to_server(AgeGenderServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("Age/Gender Estimation Service running on port 50053...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
