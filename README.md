# AWS Race 2 — LiveMedia Intelligence

A **public-safe technical case study** and reference examples for an EC2-hosted microservices-based live media intelligence platform.

> This repository is **not** the private production platform, its source code, nor a fully deployable replacement. It is an independent educational companion for the AWS Community Builders Speed Run 2 article.

## Scope

- **Amazon EC2** hosts web frontend, backend API, and media/AI orchestration microservices.
- **Amazon IVS (Low-Latency Streaming)** provides channels, ingest, and playback; channel creation is initiated in the Events UI.
- **Amazon S3** stores optional recordings and generated subclips.
- **Amazon Rekognition** performs face detection on sampled video frames and supports a storyboard assembled by the application.
- **Amazon Transcribe** processes extracted or separately captured audio into speech-to-text.
- **Amazon Translate** translates transcript text between English and Arabic.
- **AWS Elemental MediaConvert** generates and transcodes selected subclips from supported S3 media inputs.

An **AI Provider settings** screen lets operators configure a chosen model/provider. This configurable LLM integration is an application extension; no additional hosted AWS model service is asserted as part of the seven-service architecture.

## Architecture

See the [architecture graphic (SVG)](architecture/live-media-intelligence.svg), [editable Mermaid diagram](architecture/live-media-intelligence.mmd), and [article draft](docs/article.md).

## Example code

- [IVS channel creation, with optional recording](examples/create_ivs_channel.py)
- [Rekognition face detection from an S3 frame](examples/detect_faces.py)
- [Transcribe / Translate / MediaConvert integration pseudocode](docs/integration-contracts.md)

Examples are illustrative, require an authorized AWS account and configured IAM permissions, and have **not** been validated end-to-end against the private product.

## Privacy and security

Do not commit the original application's code, private endpoints, stream keys, user emails, API tokens, account identifiers, identifiable faces, or copyrighted source media. Use synthetic demonstration assets. See [publication checklist](docs/publication-checklist.md).

## References

- [Amazon IVS CreateChannel API](https://docs.aws.amazon.com/ivs/latest/LowLatencyAPIReference/API_CreateChannel.html)
- [Amazon IVS recording to S3](https://docs.aws.amazon.com/ivs/latest/LowLatencyUserGuide/record-to-s3.html)
- [Amazon Rekognition DetectFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectFaces.html)
- [Amazon Transcribe supported languages](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [AWS Elemental MediaConvert input clips](https://docs.aws.amazon.com/mediaconvert/latest/ug/specifying-inputs.html)

## License

Documentation and examples are provided as an educational draft. The owner should choose an explicit license before public publication.
