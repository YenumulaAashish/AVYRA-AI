# AVYRA roadmap

- **V1 - AI Brain:** text interaction, OpenAI Responses integration, session memory, modular architecture and automated tests. Completed foundation.
- **V1.1 - Voice Interaction:** implemented Enter-controlled microphone input, local Faster-Whisper, Edge TTS and automatic playback using the existing brain.
- **V1.2 - Wake Word:** local detection, custom AVYRA activation phrase and microphone state management.
- **V2 - Computer Automation:** application launching, system monitoring, permission-based tool execution and safeguarded file operations.
- **V3 - Vision:** screenshot capture, screen understanding, camera input and multimodal integration.
- **V4 - Persistent Memory:** SQLite, long-term memory, retrieval and user-controlled inspection/deletion.
- **V5 - Advanced AI Agent:** multi-step planning, tool orchestration, task execution and human approval for sensitive actions.
- **V6 - Hardware Integration:** Raspberry Pi, ESP32, sensors, MAVLink telemetry and hardware monitoring. Initial drone integration must be read-only and must never bypass flight-controller safety checks.

V1 and V1.1 are implemented. Each later milestone needs its own tests, permission design and explicit scope review.
