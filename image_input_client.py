import grpc
import image_input_pb2
import image_input_pb2_grpc
import sys


def send_image(image_path):

    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        sys.exit(1)

    channel = grpc.insecure_channel("localhost:50051")
    stub = image_input_pb2_grpc.ImageInputStub(channel)

    try:
        response = stub.ProcessImage(
            image_input_pb2.ImageRequest(image_data=image_data)
        )
        print("Response from Image Input Service:", response.message)
    except grpc.RpcError as e:
        print(f"gRPC Error: {e.details()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    image_path = sys.argv[1]
    send_image(image_path)
