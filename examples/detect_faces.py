"""Detect faces in a sampled frame already uploaded to S3.

This uses Rekognition Images (DetectFaces), not legacy Rekognition stream processing.
Do not equate face detection with face identification.
"""
import os
import boto3


def detect_faces(bucket: str, key: str):
    client = boto3.client("rekognition", region_name=os.environ["AWS_REGION"])
    result = client.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}},
                                 Attributes=["DEFAULT"])
    return [{"box": face["BoundingBox"], "confidence": face["Confidence"]}
            for face in result.get("FaceDetails", [])]
