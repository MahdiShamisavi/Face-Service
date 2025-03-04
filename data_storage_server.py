import grpc
from concurrent import futures
import redis
import json
import os
import aggregator_pb2
import aggregator_pb2_grpc

redis_client = redis.Redis(host="localhost", port=6379, db=0)


class AggregatorServicer(aggregator_pb2_grpc.AggregatorServicer):
    def SaveFaceAttributes(self, request, context):
        redis_key = request.redis_key
        timestamp = request.time  
        image_data = request.frame  

        # Get data from Redis
        metadata = redis_client.hgetall(redis_key)
        decoded_metadata = {
            key.decode(): value.decode() for key, value in metadata.items()
        }

        json_data = {"timestamp": timestamp, "face_data": decoded_metadata}
        print("Data Storage Service: Saving metadata:", json_data)

        
        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"{redis_key}.json")

        with open(json_path, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

        # Save image
        image_dir = os.path.join(output_dir, "images")
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, f"{redis_key}.jpg")
        with open(image_path, "wb") as image_file:
            image_file.write(image_data)

        print("Data Storage Service: Saved image to", image_path)

        return aggregator_pb2.FaceResultResponse(response=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    aggregator_pb2_grpc.add_AggregatorServicer_to_server(AggregatorServicer(), server)
    server.add_insecure_port("[::]:50054")
    server.start()
    print("Data Storage Service running on port 50054...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
