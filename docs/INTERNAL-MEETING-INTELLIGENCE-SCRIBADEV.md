# Internal Meeting Intelligence

Status: Approved architectural reference for future PNS internal tooling

Upstream project: https://github.com/allanrmartins/ScribaDev

## Purpose

Build a private PNS meeting assistant that records authorized meetings, creates a local transcript, extracts decisions and follow-ups, and connects approved results to the CRM. This is an internal operations tool, not part of Never Miss and not a customer-facing product.

## Why ScribaDev is relevant

ScribaDev already demonstrates the hardest desktop components:

1. Detection of Teams, Zoom, Google Meet, Webex, and browser meetings
2. Separate microphone and system-audio capture
3. Local transcription with faster-whisper
4. Optional local speaker diarization with pyannote
5. Structured Markdown notes and complete transcripts
6. Local search and machine-readable JSON output
7. Audio compression and configurable retention
8. Recovery of interrupted processing

## Integration decision

Use ScribaDev as a pinned upstream dependency or selectively reuse modules after a code and security review. Do not copy the repository directly into the CRM or allow it to write to production automatically.

The desktop capture agent should remain local. It should send an approved structured meeting record to a narrow authenticated CRM ingestion endpoint. Raw audio should remain local by default. Transcript upload must be opt-in per meeting.

## Proposed PNS workflow

1. The operator joins a meeting and explicitly starts or confirms recording.
2. The desktop agent records microphone and system audio locally.
3. Whisper transcribes locally.
4. The operator reviews the transcript, title, participants, and consent status.
5. A PNS-specific summarizer extracts decisions, objections, commitments, follow-ups, and CRM entities.
6. The operator approves the result.
7. The CRM attaches the meeting to the correct company and contacts, creates approved tasks, and records an audit event.
8. Local audio follows a configurable deletion period. CRM transcript retention follows PNS policy.

## Required controls before integration

1. Visible recording indicator and explicit operator action
2. Recorded confirmation that participants were informed when required
3. Meeting-level discard and do-not-upload controls
4. Encryption in transit and at rest for any uploaded transcript
5. Short-lived scoped credentials for the desktop agent
6. Company and contact matching that requires human confirmation when ambiguous
7. No automatic email, task assignment, or CRM mutation without review during the first release
8. Audit log for upload, edit, approval, export, and deletion
9. Configurable raw-audio and transcript retention
10. Dependency, installer, model, and supply-chain security review

## Licensing

ScribaDev is published under the MIT License. PNS may use, modify, and distribute covered code, but any copied or substantial portions must retain the upstream copyright and permission notice. Preserve its license and review `THIRD-PARTY-LICENSES.md` before shipping an internal installer.

## Legal boundary

Recording laws and client policies vary. The tool must not silently decide that recording is permitted. The operator is responsible for obtaining required consent, and the interface must make that responsibility visible before capture starts.

## Delivery phases

### Phase 1: local internal trial

Install upstream ScribaDev on one PNS Windows machine. Use manual recording confirmation, local transcription, no CRM upload, and a seven-day audio retention period. Validate audio quality and meeting detection.

### Phase 2: reviewed CRM import

Create a narrow CRM endpoint for reviewed Markdown or JSON notes. Add company matching, meeting timeline records, task suggestions, consent metadata, and an approval screen.

### Phase 3: PNS desktop agent

Pin a reviewed upstream revision, apply PNS branding and prompts, package a signed installer, add secure device enrollment, and support updates with rollback.

## Acceptance criteria

1. A Google Meet, Teams, and Zoom session can be captured with clear consent handling.
2. Microphone and remote participants are intelligible and correctly separated.
3. Local transcription completes reliably after interruption and restart.
4. The operator can discard a meeting before any upload.
5. Approved notes reach the correct CRM company without exposing raw credentials.
6. Decisions and follow-ups are accurate enough for human approval.
7. Deletion and retention controls are verifiable.

