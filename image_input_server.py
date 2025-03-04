import grpc
from concurrent import futures
import image_input_pb2
import image_input_pb2_grpc
import face_landmark_pb2_grpc
import age_gender_pb2_grpc
import aggregator_pb2_grpc
import face_landmark_pb2
import age_gender_pb2
import aggregator_pb2
import hashlib
import datetime


class ImageInputServicer(image_input_pb2_grpc.ImageInputServicer):
    def ProcessImage(self, request, context):
        image_data = request.image_data
        image_hash = hashlib.md5(image_data).hexdigest()

        # Call Face Landmark Detection Service
        try:
            landmark_channel = grpc.insecure_channel("localhost:50052")
            landmark_stub = face_landmark_pb2_grpc.FaceLandmarkStub(landmark_channel)
            landmark_response = landmark_stub.DetectLandmarks(
                face_landmark_pb2.LandmarkRequest(image_data=image_data)
            )
            print("Face Landmark Service response:", landmark_response)
        except Exception as e:
            print("Error calling Face Landmark Service:", e)

        # Call Age/Gender Estimation Service
        try:
            age_gender_channel = grpc.insecure_channel("localhost:50053")
            age_gender_stub = age_gender_pb2_grpc.AgeGenderStub(age_gender_channel)
            age_gender_response = age_gender_stub.EstimateAgeGender(
                age_gender_pb2.ImageRequest(image_data=image_data)
            )
            print("Age/Gender Service response:", age_gender_response)
        except Exception as e:
            print("Error calling Age/Gender Service:", e)

        return image_input_pb2.ImageResponse(
            message=f"Image processed with hash: {image_hash}"
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_input_pb2_grpc.add_ImageInputServicer_to_server(ImageInputServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Image Input Service running on port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
