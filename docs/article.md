# Building a Microservices-Based Live Media Intelligence Platform on AWS

*How Amazon IVS, EC2 microservices, Rekognition, Transcribe, Translate, S3, and MediaConvert can power live events from creation to searchable recordings and subclips.*

> **Article draft for AWS Community Builders Speed Run 2.** “LiveMedia Intelligence” is the public reference name. This article shares engineering patterns, not private platform source code. Validate deployment-specific claims and measurements before publication.

## Why we built it

In a broadcast operation, bringing a live feed online is only the first step. Operators need to prepare an event, provision a streaming endpoint, monitor incoming video, transcribe speech, translate it, inspect visual moments, extract a selected clip, and securely deliver the result. When the event ends, they may need to return to a recording and ask questions about its contents.

Our design uses **an EC2-hosted microservices platform** to coordinate specialized AWS services, giving operators a single browser-based workspace. We do not build our own live-video delivery network or media transcoding engine. Application microservices own the user workflow, authorization, event records, metadata, and orchestration; AWS managed services perform specialized media processing.

We call this reference design **LiveMedia Intelligence**. It has five user-facing areas: **Events**, **Live Operations**, **Media Library**, **AI Providers**, and **User Management**.

## Architecture: orchestration on EC2, specialized processing through AWS

The application frontend, backend API, event/channel service, live operations service, AI orchestration workers, media library service, and clip/export workers run as separate components on Amazon EC2. Containerization allows independent updates. The API enforces access controls and maps user actions to AWS SDK calls. The application's internal database and persistence are intentionally not presented as an additional AWS service in this architecture.

| AWS service | Application responsibility |
| --- | --- |
| **Amazon EC2** | Hosts frontend, backend, and media/AI orchestration microservices |
| **Amazon IVS (Low-Latency Streaming)** | Creates channels, ingests and delivers streams, and optionally records |
| **Amazon S3** | Stores opted-in recordings, generated subclips, and related media |
| **Amazon Rekognition** | Detects faces in sampled frames; our application assembles storyboards |
| **Amazon Transcribe** | Produces speech-to-text from a streaming audio adapter or recorded media |
| **Amazon Translate** | Translates transcript text between Arabic and English |
| **AWS Elemental MediaConvert** | Selects media ranges and transcodes resulting video clips |

The browser's Ask Assistant can use a configured LLM provider with relevant transcript and metadata context. We intentionally keep that provider abstract rather than claiming an eighth named AWS service.

[View the editable architecture diagram](../architecture/live-media-intelligence.mmd). The diagram's layout was independently designed for this live-event workflow, taking general inspiration from AWS Media2Cloud architecture guidance.

## 1. Events: a UI action provisions an Amazon IVS channel

An operator clicks **Create Event**, enters a name and details, and chooses whether to record the stream. The backend checks authorization, creates an application event record, calls the Amazon IVS **CreateChannel** API, and maps the new channel ARN to the event.

Recording is opt-in: attach an IVS recording configuration ARN only when requested. That configuration points to the authorized S3 destination and must be in a supported Region. The channel creation response includes an ingest endpoint, playback URL, and a sensitive stream key.

A minimal SDK sample:

~~~python
import boto3

ivs = boto3.client("ivs", region_name="eu-west-1")
request = {
    "name": "Live-Demo-Event",
    "type": "STANDARD",
    "latencyMode": "LOW"
}
if record_to_s3:
    request["recordingConfigurationArn"] = recording_configuration_arn

result = ivs.create_channel(**request)
channel_arn = result["channel"]["arn"]
playback_url = result["channel"]["playbackUrl"]
~~~

**Never display or log the stream key publicly.** The backend should securely manage publishing credentials and handle partial failures, such as a successfully created IVS channel followed by a failed event-database write. Idempotency and reconciliation help avoid orphaned resources.

The operator now has a prepared event and an authorized broadcaster can publish a compatible stream to the ingest endpoint.

## 2. Live Operations: playback and AI analysis take different paths

A source encoder publishes video to **Amazon IVS**, which supplies a low-latency playback URL for live monitoring. The platform's Live Operations screen provides stream status, playback, and operator actions. Crucially, AI inference must never be placed on the critical path of video delivery.

### Speech-to-text with Amazon Transcribe

An EC2-hosted audio adapter captures or extracts audio and sends it to **Amazon Transcribe** using a supported streaming or batch workflow. Transcripts should retain media-relative timing and source language. Configure supported English and Arabic dialects explicitly; supported features vary by language and API mode.

### Arabic ↔ English translation with Amazon Translate

The orchestration service passes transcript text to **Amazon Translate**. The application stores original and translated text alongside the same media context. Translate does not itself return video timestamps, so the application must preserve transcript-to-media alignment.

### Face detection and storyboards with Amazon Rekognition

A frame-sampling component extracts approved JPEG/PNG images from an authorized media path. **Rekognition DetectFaces** identifies visible faces and returns bounding boxes and related observations. The platform builds the storyboard from images, timestamps, and AI responses. **Face detection is not person identification.** A frame-based approach also avoids relying on older Rekognition streaming-video capabilities unavailable to new customers.

### Smart subclips and transcoding

Operators select a start and end position. A clip microservice validates those positions against actual available media, maps them to the recording timebase, submits an **AWS Elemental MediaConvert** job using supported inputs and input clipping settings, and writes the output to **Amazon S3**.

A live stream cannot automatically be clipped from media that has not yet been made available. During an active event, the application needs a deliberate media-availability and capture design. Amazon IVS itself is not a frame-accurate editing API.

### Secure sharing and export

The application checks whether the requested user can view or export an asset. MediaConvert can generate required output variants, and controlled delivery links can be generated for authorized S3 objects. Do not make the S3 bucket public simply to enable download.

### Ask questions about recordings

Users may ask the configured assistant questions against available transcripts and enriched media metadata. Application code retrieves only authorized content and supplies that evidence to the configured LLM provider. Responses should refer back to recording positions and sources where possible. Neither IVS nor Transcribe natively exposes a complete media-specific Q&A assistant.

### A critical integration boundary

**IVS provides managed streaming; it is not a generic raw-video-frame inference interface.** For near-live AI, an independent authorized frame/audio capture adapter feeds the AI worker. For post-event analysis, the worker can operate on finalized S3 recordings. This choice strongly affects processing latency and must be stated explicitly.

## 3. Media Library: optional S3 recording and replay

If the operator enabled recording, Amazon IVS stores HLS media and recording metadata in the configured **S3 bucket**. Depending on configuration, thumbnails and multiple renditions may be present. Do not assume the recording is a single MP4 object or hardcode the exact HLS paths.

For complete post-processing, handle recording-finalization status rather than assuming every file is complete the moment the source goes offline.

The **Media Library** connects recorded assets to event metadata. An operator can replay a session, review transcripts and translations, inspect storyboard observations, and access generated clips. S3 stores the media objects; the EC2 application manages the asset catalog, associations, indexing, and authorization.

An illustrative metadata record is:

~~~json
{
  "eventId": "event-demo-001",
  "ivsChannelArn": "arn:aws:ivs:REGION:ACCOUNT:channel/ID",
  "recordingEnabled": true,
  "recordingPrefix": "ivs/v1/...",
  "language": "en",
  "transcript": "metadata/transcript.json",
  "translation": "metadata/translation-ar.json",
  "storyboard": "metadata/storyboard.json",
  "clips": ["clips/selected-moment.mp4"]
}
~~~

This is a conceptual public example, not the private application's database schema.

## 4. AI Providers: a configurable model integration

The **AI Providers** administration screen allows authorized operators to configure a language-model provider for the assistant and check its connectivity. The public reference architecture deliberately avoids publishing proprietary provider details, private endpoints, or credentials.

Keeping the assistant provider-independent lets the media pipeline produce reusable transcripts and enrichment metadata. Administrators can manage model governance separately from IVS channel operations and media processing.

The assistant must always check access permissions **before** fetching transcript or media context.

## 5. User Management: enforce roles in backend services

**User Management** lets administrators provision accounts and assign access profiles. Administrators may manage users or AI providers, while operators are limited to relevant event and live production workflows.

The backend must enforce role-based access control (RBAC) on event creation, playback, transcript retrieval, exporting, sharing, and configuration—not merely hide unsupported UI buttons. The same principle applies across event and asset boundaries.

## 6. Why microservices on Amazon EC2?

EC2 hosts long-running application processes and media/AI integration workers with distinct deployment lifecycles. The application can evolve its event service, streaming dashboard, clipping workers, and assistant independently.

Each layer has a clear responsibility:

- **Application microservices:** workflows, identity, authorization, event records, metadata, retries, and timeline mapping.
- **Amazon IVS:** ingest and managed low-latency viewer distribution, with optional S3 recording.
- **Rekognition, Transcribe, and Translate:** specialized AI processing, with results interpreted and coordinated by the application.
- **MediaConvert:** managed media conversion and time-range extraction for supported media inputs.
- **S3:** recordings, clip outputs, and media objects.

Microservices do not automatically deliver high availability. Instance recovery, deployment strategy, monitoring, scaling, service authentication, and resilience still require engineering effort.

## 7. Reproducible demo workflow

Use owned or licensed demonstration video, synthetic identities, and AWS credentials with narrowly scoped permissions.

1. Prepare an EC2-based test environment with a sample backend integration and IAM role.
2. Configure IVS recording to a dedicated S3 bucket if recording is required.
3. Create a channel through the Events workflow or [sample IVS SDK script](../examples/create_ivs_channel.py).
4. Publish test video from OBS or a supported encoder and observe it in Live Operations.
5. Capture authorized frames/audio and run Transcribe and [Rekognition DetectFaces](../examples/detect_faces.py) through the processing adapters.
6. Translate selected transcript portions between English and Arabic; preserve time alignment.
7. Stop streaming, identify the finalized S3 recording and its actual media paths.
8. Submit an appropriate MediaConvert clip job with supported input and valid timecodes; verify the S3 output.
9. Ask the configured assistant a question supported by the authorized transcript and inspect the evidence.
10. Test different user profiles, verifying backend authorization for both media and administration.

**Important:** The companion repository provides standalone SDK examples and architecture contracts. It is **not** a one-click deployment or a public copy of the production system. Integration adapters and real AWS setup are still required.

## 8. What to measure

For a valuable engineering report, gather **measured** data rather than estimates:

| Metric | Interpretation |
| --- | --- |
| Event provisioning delay | Time from Create Event to channel-ready state |
| Live playback latency | Difference between source capture and viewer playback |
| Speech transcription lag | Difference between audio time and transcript availability |
| Translation delay | Time from submitted transcript text to translated output |
| Frame sampling rate | Frames analyzed per stream per minute |
| Rekognition usage | Images processed per event |
| MediaConvert job duration | Time from clip request to completed output |
| S3 footprint | Stored recording and subclip sizes |

Cost dimensions are separate: EC2 runtime, IVS live input/viewer hours, S3 requests and storage, Rekognition image processing, Transcribe audio, Translate characters, and MediaConvert output. Configured LLM services may incur separate charges.

## 9. Lessons learned

**Own the user journey, not every engine.** The application can offer one operational experience while using specialized AWS APIs for video, transcription, visual analysis, translation, and transcoding.

**Make recording a deliberate decision.** A prepared live event and a persisted recording are not the same thing.

**Keep media and AI timing consistent.** A transcript line, storyboard image, and selected clip become useful when reliably anchored to the same recording timeline.

**Never block the live path on AI.** Inference failures should not interrupt ingest or playback. Near-live analysis requires an explicit authorized capture adapter.

**Treat roles and model governance as architecture.** Secure metadata access and model configuration are first-class workflows, not cosmetic administrative screens.

## Conclusion

Live media operations involve event preparation, ingest, AI processing, optional recording, media review, and clip delivery. The challenge is to make this a coherent operator workflow without reimplementing the underlying media services.

**LiveMedia Intelligence** demonstrates how an EC2-hosted microservices control plane can coordinate **Amazon IVS, Amazon S3, Amazon Rekognition, Amazon Transcribe, Amazon Translate, and AWS Elemental MediaConvert**. Operators can prepare a channel, monitor a stream, enrich its content, and return to resulting media assets as needed.

The transferable engineering principle is to **start with the operator journey, define clean service boundaries, and use AWS managed services where their specialized capabilities make the most difference**.

## AWS references

- [Amazon IVS CreateChannel API](https://docs.aws.amazon.com/ivs/latest/LowLatencyAPIReference/API_CreateChannel.html)
- [Amazon IVS Auto-Record to S3](https://docs.aws.amazon.com/ivs/latest/LowLatencyUserGuide/record-to-s3.html)
- [Amazon Rekognition DetectFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectFaces.html)
- [Rekognition streaming video availability](https://docs.aws.amazon.com/rekognition/latest/dg/streaming-video.html)
- [Amazon Transcribe language support](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [MediaConvert input clipping](https://docs.aws.amazon.com/mediaconvert/latest/ug/specifying-inputs.html)
- [Guidance for Media2Cloud on AWS](https://docs.aws.amazon.com/solutions/media2cloud-on-aws/)
