# AWS Race 2 — MediaFlux AI

A **public-safe technical case study** and reference examples for an EC2-hosted microservices-based live media intelligence platform.

> This repository contains an independent architectural reference and educational examples for AWS Speed Run Race 2. It is not a complete deployable application.

## Scope

- **Amazon EC2** hosts web frontend, backend API, and media/AI orchestration microservices.
- **Amazon IVS (Low-Latency Streaming)** provides channels, ingest, and playback; channel creation is initiated in the Events UI.
- **Amazon S3** stores optional recordings and generated subclips.
- **Amazon Rekognition** performs face detection on sampled video frames and supports a storyboard assembled by the application.
- **Amazon Transcribe** processes extracted or separately captured audio into speech-to-text.
- **Amazon Translate** translates transcript text between English and Arabic.
- **AWS Elemental MediaConvert** generates and transcodes selected subclips from supported S3 media inputs.
- **Amazon Bedrock** runs a supported foundation model for recording summaries and evidence-grounded questions in the Ask MediaFlux AI assistant.

An **AI Provider settings** screen lets operators configure a chosen model/provider. Amazon Bedrock is the default AWS foundation-model inference service for Ask MediaFlux AI. Provider configuration allows a model to be selected or configured; supported models, credentials, and API access must be validated in deployment.

## Architecture

See the [architecture graphic (SVG)](architecture/mediaflux-ai.svg), [editable Mermaid diagram](architecture/mediaflux-ai.mmd), and [article draft](docs/article.md).

## Amazon Bedrock integration

The reference design describes authorized transcript retrieval, model invocation, and recording-grounded question answering. See [integration contracts](docs/integration-contracts.md) for public integration boundaries.


## Example code

- [IVS channel creation, with optional recording](examples/create_ivs_channel.py)
- [Rekognition face detection from an S3 frame](examples/detect_faces.py)
- [Transcribe / Translate / MediaConvert integration pseudocode](docs/integration-contracts.md)

Examples are illustrative, require an authorized AWS account and configured IAM permissions, and have **not** been validated end-to-end as a deployable platform.

## Privacy and security

Do not commit confidential source code, private endpoints, stream keys, user emails, API tokens, account identifiers, identifiable faces, or copyrighted source media. Use synthetic demonstration assets. See [publication checklist](docs/publication-checklist.md).

## References

- [Amazon IVS CreateChannel API](https://docs.aws.amazon.com/ivs/latest/LowLatencyAPIReference/API_CreateChannel.html)
- [Amazon IVS recording to S3](https://docs.aws.amazon.com/ivs/latest/LowLatencyUserGuide/record-to-s3.html)
- [Amazon Rekognition DetectFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectFaces.html)
- [Amazon Transcribe supported languages](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [AWS Elemental MediaConvert input clips](https://docs.aws.amazon.com/mediaconvert/latest/ug/specifying-inputs.html)

## License

Documentation and examples are provided as an educational draft. The owner should choose an explicit license before public publication.
