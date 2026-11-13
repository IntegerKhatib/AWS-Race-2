# Integration boundaries and sample contracts

These are explanatory interfaces, not a deployed integration.

## Event creation

```json
{"eventName":"Demo Conference", "recordToS3":true, "region":"eu-west-1"}
```

Backend responsibilities: validate user authorization, validate the event, call IVS CreateChannel, persist event-to-channel mapping, protect stream key, and return safe ingest/playback metadata. Enable recording only if the user selected it and a compatible recording configuration exists.

## Live operations

The application renders IVS playback and stream state separately from AI tasks. Speech-to-text requires audio capture/extraction and a Transcribe streaming connection or post-recording batch job. Frame analysis requires an image adapter; pass sampled PNG/JPEG images to Rekognition DetectFaces. Persist timestamped observations with media timeline positions.

## Transcription and translation

Amazon Transcribe language codes are dialect-specific: choose supported `en-US`, `ar-AE`, or `ar-SA` configuration as appropriate. Amazon Translate uses `en` and `ar`. Word-level timestamp output and any language-dependent feature availability need testing.

## Storyboard

A storyboard is an **application output** assembled from timestamped sampled frames, associated detected faces, and optional captions. Rekognition DetectFaces does not generate a storyboard UI by itself, and detection does not prove a person's identity.

## Clip / transcode

The user selects recording and start/end timecodes; a worker validates available media and maps timestamps to the actual recording timeline. Submit a MediaConvert job with an S3-readable supported source and `InputClippings` (`StartTimecode`, `EndTimecode`); configure an S3 output destination and the job's IAM role. IVS recording paths/renditions must be read from recording metadata; don't invent a fixed MP4. For fragmented HLS sources, verify MediaConvert input support and prepare a supported mezzanine when needed.

## Ask assistant

Use the transcript and AI metadata as retrieval context. The configurable LLM provider answers questions subject to authorization and grounded evidence. A configured provider is *not* a proof that every model/provider or every retrieval feature is implemented.

## Access control

Model permissions for event creation, live operation, media viewing, exports, AI configuration, and account management. Enforce authorization in backend services, not only hidden UI buttons.
