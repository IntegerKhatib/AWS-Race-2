"""Reference only: create IVS channel; recording is OPT-IN by recording config ARN.

Requires boto3, valid AWS credentials, and permission for ivs:CreateChannel.
Never log, publish, or commit the stream key returned by this API.
"""
import os
import boto3


def create_event_channel(event_name: str, record: bool = False):
    client = boto3.client("ivs", region_name=os.environ["AWS_REGION"])
    args = {"name": event_name, "type": "STANDARD", "latencyMode": "LOW"}
    if record:
        recording_arn = os.environ.get("IVS_RECORDING_CONFIGURATION_ARN")
        if not recording_arn:
            raise ValueError("A recording configuration ARN is required for recording")
        args["recordingConfigurationArn"] = recording_arn
    response = client.create_channel(**args)
    channel = response["channel"]
    # The response also includes streamKey; keep it in secure application storage.
    return {"channelArn": channel["arn"], "playbackUrl": channel["playbackUrl"],
            "ingestEndpoint": channel["ingestEndpoint"], "recordingEnabled": record}


if __name__ == "__main__":
    print(create_event_channel("public-demo", record=False))
