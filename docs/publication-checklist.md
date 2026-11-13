# Before sharing publicly

- [ ] Select a GitHub account and create repository `AWS-Race-2` (GitHub repository names cannot contain spaces as normal URL slugs; use `AWS-Race-2`, display title “AWS Race 2”).
- [ ] Validate diagrams and AWS SDK examples against a clean sandbox account.
- [ ] Replace screenshots with sanitized crops: no server IP address, account names, private emails, private identifiers, stream keys, or copyrighted media frames.
- [ ] Verify whether actual live Transcribe and Rekognition processing uses a parallel capture path versus post-recording analysis.
- [ ] Verify MediaConvert source packaging and timecode mapping.
- [ ] Verify Amazon Bedrock model ID/inference profile, AWS Region, backend IAM permission, Converse API behavior, and measured token usage.
- [ ] Specify precisely how Ask LiveMedia retrieves authorized transcript and metadata context, associates citations/timestamps, and calls Bedrock.
- [ ] Record measured results: IVS setup time, AI processing delay, sample transcript, translation, clip job duration, and final object key.
- [ ] Add repository license chosen by the owner and ensure rights to publish examples.
- [ ] Review all details against private source before claiming implemented behavior.
