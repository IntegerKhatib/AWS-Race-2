# Building MediaFlux AI on AWS: Live Streaming, AI Analysis, and Smart Media Workflows with EC2 Microservices

*AWS Community Builders — Speed Run Race 2 | Engineering case study and reference design*

A live streaming event is not finished when the video reaches the player. Production teams also need to understand what happened, convert speech into searchable text, translate content, identify visual moments, create clips, share approved outputs, and return to a recording to ask specific questions. These tasks frequently require separate interfaces and manual handoffs.

**MediaFlux AI** combines them in one web application. Rather than replacing AWS media services, the application runs as **containerized microservices on Amazon EC2** and connects specialized AWS APIs to the decisions made by producers, operators, and administrators. This article focuses on seven managed AWS media/AI services plus EC2: **Amazon IVS, Amazon S3, Amazon Rekognition, Amazon Transcribe, Amazon Translate, AWS Elemental MediaConvert, Amazon Bedrock, and Amazon EC2**. It deliberately excludes unrelated platform capabilities and any private product source.

## What users see: five application areas

The interface is organized around the actual production journey, not a catalog of AWS APIs:

1. **Events** — create a live event in the web UI. A backend service validates permissions, creates the event record, and provisions an **Amazon IVS** channel behind the scenes. Recording is optional.
2. **Live** — receive and monitor the stream, initiate speech-to-text and English/Arabic translation, analyze selected video frames, create a subclip, and securely share or export an approved result. An AI assistant can answer questions about accessible event or recording metadata.
3. **Media Library** — if recording was enabled, browse the **Amazon S3** recording associated with an event; review transcripts, translations, storyboards, and generated clips.
4. **AI Providers** — let administrators configure supported LLM providers/models. **Amazon Bedrock** supplies the AWS-hosted model inference used in the reference assistant. Not every configurable provider necessarily has the same capabilities or connection-testing support.
5. **User Management** — assign users different roles and profiles. The backend enforces access to events, media, exports, AI configuration, and administrative actions.

## Architecture: EC2 owns workflow orchestration; AWS services do specialized work

The application layer runs on Amazon EC2 with separate frontend, backend/API, and background processing containers. Conceptually the microservices cover event provisioning, live operations, audio/frame analysis orchestration, media-library management, clipping/export, AI assistance, and administration. Some responsibilities may share a deployable service or worker; logical boundaries do not imply a dedicated EC2 instance per feature.

| AWS service | Specific responsibility |
| --- | --- |
| **Amazon EC2** | Host the containerized web frontend, backend APIs, background workers, and application control plane |
| **Amazon IVS** | Create ingest/playback channels, accept encoded live streams, and optionally record to S3 |
| **Amazon S3** | Store opted-in IVS recordings, transcoded subclips, and associated objects |
| **Amazon Rekognition** | Detect faces or other supported observations in sampled frames; the application assembles the storyboard |
| **Amazon Transcribe** | Convert live-accessible audio or recorded audio into timestamped text |
| **Amazon Translate** | Translate text between Arabic and English |
| **AWS Elemental MediaConvert** | Process supported recorded media, extract selected time ranges, and create/transcode clips |
| **Amazon Bedrock** | Perform model inference and reasoning over authorized transcripts and enrichment metadata |

**Architecture diagram:** [MediaFlux AI — SVG](../architecture/live-media-intelligence.svg) · [Editable flow](../architecture/mediaflux-ai.mmd)

This is a deliberately different architecture from the AWS Media2Cloud guidance. Media2Cloud principally describes serverless asset ingestion and analysis. Here, an **EC2-hosted microservices application** begins with a live event and controls IVS channel lifecycle, near-live operator workflows, optional recording, and interactive review. Media2Cloud informed the diagramming approach, not the service inventory.

## 1. Events: creating an event provisions an IVS channel

The operator selects **Create Event** and enters the event name, relevant details, and a recording choice. The event microservice checks user permissions and issues an IVS `CreateChannel` request. It stores the new channel ARN and permitted playback details against the event so the operator can start a broadcast using an authorized encoder.

When the user enables recording, the service attaches a valid IVS recording configuration connected to an authorized S3 bucket. **Recording is opt-in**, not an implicit side effect of every channel. The returned stream key is a credential: keep it out of browser logs, screenshots, repositories, and general application telemetry.

Engineering requirements include checking API failures, avoiding duplicate channel creation on retry, and reconciling a channel that was created in AWS but not successfully written to the application's event database. The reference SDK example demonstrates `CreateChannel` and optional recording configuration; deployments must validate their own implementation.

## 2. Live: the stream stays available while AI runs independently

An encoder sends a compatible stream to IVS. IVS serves the live playback experience; the **Live** screen shows the session and provides AI and media controls.

The most important architecture choice is to **decouple playback from AI processing**. Video delivery must not wait for a transcript, a model answer, or a finished MediaConvert job.

### Speech-to-text — Amazon Transcribe

An application-managed audio adapter obtains an authorized audio feed and passes it to an appropriate Transcribe streaming workflow. For a recorded event, post-event transcription is another option. The transcript is associated with the correct event and media time offsets; operator-facing text appears alongside the live or recorded content. Whether a particular audio capture path qualifies as near-live must be verified in the deployed system—IVS playback alone is not an automatic raw-audio source for Transcribe.

### Translation — Amazon Translate

The application sends transcript text to Amazon Translate and stores **Arabic and English** versions against the same event timeline. Transcription and translation are distinct steps: Transcribe produces words from audio; Translate processes text. Each result is paired with the original time reference so an editor can navigate back to the relevant moment. Exact dialects and language-mode support require an AWS Region and API validation.

### Frame and face analysis — Amazon Rekognition

A sampling worker extracts frames from an accessible media feed or recording and calls supported Rekognition image-analysis operations, including face detection. Each result is tied to a frame timestamp. The application—not Rekognition—then builds a **storyboard** of keyframes, annotations, and timeline navigation. Face detection identifies the presence and attributes of a face; it does not by itself establish who that person is.

Because IVS is a managed streaming service rather than a raw-frame inference interface, near-live image analysis needs an independent frame capture/sampling path. Alternatively, the worker can analyze footage after it becomes available in S3.

### Subclips, transcoding, secure sharing, and export

A user chooses start and end timestamps in the Live timeline. The clip worker maps those positions to the actual available recording/media timeline, validates the source format, and submits a **MediaConvert** job to produce a clip or transcoded output. The resulting file is stored in **S3** and associated with the event/media item.

IVS recordings are typically HLS assets and metadata, not automatically one MP4. The implementation must discover the actual recording renditions and supply MediaConvert with a supported input or prepare an intermediate asset. A clip cannot be generated before its required source media is available. A live operator interface can accept a clip request early, but completion depends on media availability and processing latency.

Sharing and export are authorized application operations. The backend checks permissions before issuing a time-limited delivery link or another controlled export mechanism. The S3 bucket should not be publicly exposed merely to make sharing easy.

### Ask MediaFlux AI — questions answered using Amazon Bedrock

The operator asks a question such as **“What did the presenter say about the deployment strategy?”** The assistant first verifies access to the selected event or recording and retrieves relevant transcript passages, translations, and storyboard metadata. It provides that bounded context to an available model through **Amazon Bedrock**, then returns a response with supporting time references where available.

The reasoning model does not inherently understand arbitrary S3 video files. Accurate answers depend on the application's transcript and enrichment pipeline, retrieval logic, authorization checks, and timestamp alignment. This separation is central to the design: **the application assembles evidence; Bedrock interprets it**.

## 3. Media Library: the recording exists only when storage is enabled

If the operator enables recording, Amazon IVS writes the recorded stream and its metadata to the configured S3 destination. The Media Library uses the event/channel association and recording metadata to present the correct media asset for replay and later analysis.

For each stored event, the interface can group the recording, transcripts, translated text, storyboard frames, and subclips under one media record. If recording is disabled, the platform must not imply that a durable full-session archive exists. It may still retain separately generated metadata or clips if those were explicitly created and stored.

## 4. AI Providers: bring a supported language model

The **AI Providers** administration page separates model configuration from the core media pipeline. An administrator can register and manage supported provider settings. The reference workflow uses **Amazon Bedrock** for generative-AI inference and reasoning; provider-specific authentication, model identifiers, Regions, and available features must be validated individually.

This separation means IVS, transcription, translation, and clip production can continue operating regardless of the chosen LLM. It also prevents sensitive model credentials from being sent directly from browser code to inference endpoints.

## 5. User Management: permissions follow the media

An administrator adds users and assigns profiles such as an event operator, media reviewer, or platform administrator. Permission checks must run in backend APIs for channel creation, playback access, clip creation, export, sharing, provider configuration, and user changes. Hiding a button in the frontend is not authorization.

Especially for the AI assistant, retrieval must be permission-scoped: a user cannot ask a model about a recording they are not allowed to access.

## Engineering choices and trade-offs

**Why EC2 microservices?** Some live/media operations require long-lived application processes and workers, while frontend/backend features change independently. Containerized components on EC2 offer control over runtime, job scheduling, and deployment, while managed AWS services remove the need to build the streaming, transcription, translation, transcoding, and model-inference engines.

**What determines latency?** IVS playback has its own latency. Audio/frame capture adds delay; AI inference adds more; S3 recording availability and MediaConvert processing determine when a finalized clip can be exported. Measure each stage separately rather than claiming the whole pipeline is “real-time.”

**What belongs in the application?** Event-to-channel mapping, access control, clip timecode validation, transcript alignment, storyboard assembly, job retry/reconciliation, and secure sharing. These are not automatically provided by an AWS API.

**What must be verified before a public demo?** IVS channel/recording configuration, supported Arabic/English transcription modes, the near-live capture adapter, a real Rekognition frame sample, S3 recording rendition discovery, MediaConvert clipping against an actual supported source, Bedrock model access and evidence-grounded answers, and role enforcement. Do not publish performance figures without measuring them.

## End-to-end demonstration

1. An operator signs in and uses **Events** to create a live event.
2. The Events service provisions its **Amazon IVS** channel. The operator chooses whether to enable S3 recording.
3. An authorized encoder begins streaming; the user watches it in **Live**.
4. The audio processing path generates a transcript with **Amazon Transcribe**; **Amazon Translate** produces Arabic/English text.
5. Sampled frames are analyzed with **Amazon Rekognition**, and the application assembles a storyboard.
6. An operator chooses a segment; **MediaConvert** builds a supported subclip and stores it in **S3**.
7. The operator shares or exports an approved clip using backend authorization.
8. When recording was enabled, the event is accessible in **Media Library** along with its enrichment metadata.
9. The user asks **Ask MediaFlux AI** a recording-specific question; **Bedrock** answers using only the authorized context retrieved by the application.
10. An administrator uses **AI Providers** and **User Management** to control model access and user privileges.

## Conclusion

**MediaFlux AI** demonstrates how **microservices on Amazon EC2** can deliver a coherent live-media production workspace by orchestrating exactly the AWS services needed for ingest, optional recording, analysis, translation, clip creation, and generative-AI-assisted review. The engineering value is not another video player or AI endpoint: it is the consistent workflow, event/time synchronization, permissions, and media lifecycle connecting them.

*This repository documents an AWS architectural reference and standalone examples; it has not been validated as a complete production deployment.*

## References

- [AWS Guidance for Media2Cloud on AWS](https://docs.aws.amazon.com/solutions/media2cloud-on-aws/) — diagram organization/reference, not a service-by-service implementation template
- [Amazon IVS recording to S3](https://docs.aws.amazon.com/ivs/latest/LowLatencyUserGuide/record-to-s3.html)
- [Amazon IVS CreateChannel API](https://docs.aws.amazon.com/ivs/latest/LowLatencyAPIReference/API_CreateChannel.html)
- [Amazon Rekognition DetectFaces API](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectFaces.html)
- [Amazon Transcribe supported languages](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html)
- [Amazon Translate documentation](https://docs.aws.amazon.com/translate/latest/dg/what-is.html)
- [AWS Elemental MediaConvert input clipping](https://docs.aws.amazon.com/mediaconvert/latest/ug/setting-up-input-clipping.html)
- [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html)
