# AI Prompts & Conversations Log

**Project**: Real-Time Network Telemetry Framework (RFC 9232)  
**Course**: CS331 Computer Networks | **Team ID**: T018  

---

## Overview

In accordance with course integrity and project submission guidelines, this directory contains the complete and transparent documentation of all AI assistance used during the project. It includes both high-level learning documentation matching the submission appendix format, curated learning progression logs, and the complete unsummarized raw conversation history.

---

## Files in this Directory

### 1. Formal Submission Documentation
- **[`AI_Usage_Documentation.pdf`](./AI_Usage_Documentation.pdf)** (2 Pages, A4 PDF):
  - Formatted to match the standard academic AI usage documentation template.
  - **Section 1**: *How I Used AI During the Project* (learning assistant, ground-truth verification, local execution).
  - **Section 2**: *Prompts I Used During Development* (10 representative student inquiries covering RFC 9232 scope, gRPC push streaming, dual collectors, TCP latency, SQLite WAL batching, hysteresis state machines, and scalability testing).
  - **Section 3**: *How I Worked With the AI Suggestions* (verifying terminal outputs, diagnosing Windows port conflicts, rejecting ML complexity in favor of explainable fundamentals).
  - **Section 4**: *What AI Contributed vs. What I Did* (detailed matrix mapping Planning, Implementation, Environment setup, Debugging, Testing, Evaluation, and Documentation).
- **[`AI_Usage_Documentation.md`](./AI_Usage_Documentation.md)**: Markdown version of the above.

### 2. Pedagogical Learning Prompts & Ground-Truth Inquiries
- **[`AI_Learning_Prompts.pdf`](./AI_Learning_Prompts.pdf)** (3 Pages, A4 PDF):
  - Curated compilation of prompts organized across 9 chronological learning phases.
  - Highlights the student's questions, underlying network concepts explored, and concrete technical outcomes.
- **[`AI_Learning_Prompts.md`](./AI_Learning_Prompts.md)**: Markdown version of the learning prompts.

### 3. Full Unsummarized Raw Conversation Archives
- **[`raw_conversations.md`](./raw_conversations.md)**:
  - Verbatim, chronological transcript of every prompt submitted to and response received from AI assistants across the entire project lifecycle (all turns).
- **[`prompts_and_responses.json`](./prompts_and_responses.json)**:
  - Machine-readable JSON dump of all prompts, timestamps, tool actions, and raw model responses.
- **[`raw_transcript_full.jsonl`](./raw_transcript_full.jsonl)**:
  - Cryptographic system-level log file containing raw turn tokens, timestamps, tool invocations, and step indexes.

### 4. Reproducible Generator Scripts
- **`generate_ai_usage_pdf.py`**: Python script using PyMuPDF to regenerate `AI_Usage_Documentation.pdf`.
- **`generate_learning_prompts_pdf.py`**: Python script using PyMuPDF to regenerate `AI_Learning_Prompts.pdf`.
