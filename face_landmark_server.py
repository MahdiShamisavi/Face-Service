import grpc
from concurrent import futures
import redis
import hashlib
import datetime
import dlib
import cv2
import numpy as np
import face_landmark_pb2
import face_landmark_pb2_grpc
import aggregator_pb2
import aggregator_pb2_grpc

# Load face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    "shape_predictor_68_face_landmarks.dat"
) 

redis_client = redis.Redis(host="localhost", port=6379, db=0)


class FaceLandmarkServicer(face_landmark_pb2_grpc.FaceLandmarkServicer):
    def DetectLandmarks(self, request, context):
        image_data = request.image_data

        
        image_hash = hashlib.md5(image_data).hexdigest()

        
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid image data")
            return face_landmark_pb2.LandmarkResponse(
                image_hash=image_hash, landmarks=""
            )

        # Detect faces
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        print("Number of faces :", len(faces))

        if len(faces) == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No faces detected")
            return face_landmark_pb2.LandmarkResponse(
                image_hash=image_hash, landmarks=""
            )

        detected_landmarks = []

        for face in faces:
            shape = predictor(gray, face)
            landmarks = [(p.x, p.y) for p in shape.parts()]
            detected_landmarks.append(landmarks)

        # Store landmarks in Redis
        redis_client.hset(image_hash, "landmarks", str(detected_landmarks))

       
        try:
            aggregator_channel = grpc.insecure_channel("localhost:50054")
            aggregator_stub = aggregator_pb2_grpc.AggregatorStub(aggregator_channel)
            current_time = datetime.datetime.now().isoformat()
            aggregator_response = aggregator_stub.SaveFaceAttributes(
                aggregator_pb2.FaceAttributesRequest(
                    time=current_time, frame=image_data, redis_key=image_hash
                )
            )
            print("Aggregator response from FaceLandmark Service:", aggregator_response)
        except Exception as e:
            print("Error calling Aggregator from FaceLandmark Service:", e)

        return face_landmark_pb2.LandmarkResponse(
            image_hash=image_hash, landmarks=str(detected_landmarks)
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    face_landmark_pb2_grpc.add_FaceLandmarkServicer_to_server(
        FaceLandmarkServicer(), server
    )
    server.add_insecure_port("[::]:50052")
    server.start()
    print("Face Landmark Detection Service running on port 50052...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
