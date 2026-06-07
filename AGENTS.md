\# WAI\_chat Coding Instructions



\## Project purpose

This repository powers the Workfriend.ai / WAI chatbot and related tools hosted on Hugging Face Spaces.



\## Current priority

Improve chatbot retrieval so structured documents are not flattened into generic embedding soup.



The target pattern is:

1\. domain-aware routing

2\. structured metadata

3\. exact/keyword search for IDs, headings and source names

4\. vector retrieval as fallback, not the whole retrieval strategy

5\. source-aware answers with uncertainty shown clearly



\## Engineering rules

\- Make small changes.

\- Preserve existing Hugging Face deployment behaviour.

\- Do not rewrite the whole app.

\- Do not replace the vector store unless specifically asked.

\- Do not add paid services unless approved.

\- Prefer simple readable Python.

\- Add smoke tests or simple test scripts for retrieval changes.

\- Keep changes easy to review.



\## Deployment constraints

\- This app runs on Hugging Face Spaces.

\- Do not break `asgi.py`, Dockerfile, requirements.txt, or app startup without explaining why.

\- Avoid creating objects like LLM clients at import time if doing so can crash the whole app.



\## Retrieval principles

\- Preserve document structure where possible.

\- Exact IDs, screen names, headings, process names, and filenames should be searchable without relying only on embeddings.

\- Metadata such as domain, document type, process, source file, heading path, and confidence level should be preserved.

\- Answers should distinguish confirmed facts, inferred facts, assumptions, and open questions.

