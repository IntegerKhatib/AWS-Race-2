# Security and public disclosure policy

This repository is a **public AWS Speed Run Race 2 reference project**, not an operational deployment and not a place for production artifacts.

## Do not contribute
- Credentials: AWS access keys, IVS stream keys, API tokens, passwords, private keys, environment files, signed URLs, or refresh tokens.
- Production configuration: real account IDs, private or public infrastructure addresses, ARNs containing actual account IDs, internal hostnames, endpoints, customer identifiers, or user information.
- Confidential application code, database dumps, media, screenshots exposing customer data, or implementation details from unrelated systems.
- Media without redistribution permission or real people's identifiable data without appropriate authorization.

Use placeholder ARNs such as `arn:aws:ivs:REGION:ACCOUNT:channel/ID`, synthetic test content, and fictional names.

## Checks
The workflow in `.github/workflows/security-check.yml` scans the **current checked-out source** for a targeted set of confidential identifiers and credentials. It does not establish that every secret is absent. It **does not scan historical Git objects**.

Before submitting the project, also enable GitHub secret scanning and push protection where available, manually review images and diagrams, and inspect prior commits for potentially sensitive content.

## Suspected exposure
If a real secret is found, **revoke/rotate it immediately** and investigate the affected service and logs. Deleting or changing a file in a new commit does not remove it from Git history or from clones.

If an internal reference is found in history, assess the exposure and arrange a history rewrite only after coordinating with repository collaborators. History rewrites invalidate old commit references and do not guarantee removal from caches or forks.

Report sensitive findings privately to the repository owner. **Do not open a public issue containing a secret.**

## Deployment and scope
The examples are educational AWS SDK references. No IAM user, stream key, existing environment configuration, or privileged AWS permission should be published in this repository. Service names such as Amazon S3 and Amazon Bedrock are public technology references, not proprietary data.
