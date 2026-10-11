# Requirement (verbatim from the customer brief)

Agentic Cybersecurity – Prompt Injection Firewall:

AI agents are used to take care of multiple standard activities in today's time. However, access to external content and tools also exposes them to malicious attempts to extract private information, perform unauthorized tasks, or trigger other unwanted behavior. One such technique is direct and indirect prompt injection.

A Prompt Injection Firewall is one of the most relevant cybersecurity problems today because many AI systems (LLM-based agents, copilots, and chatbots) can access external content and tools. The firewall's role is to detect and neutralize malicious instructions embedded in user input or retrieved data before they influence the AI's behavior.

Design a Prompt Injection Firewall that intercepts all incoming content before it influences the AI's behavior. The solution should detect and neutralize malicious prompt injections while allowing legitimate content to pass with minimal disruption.

## Input Sources

The firewall may receive:

- User messages
- Web pages
- PDFs
- Emails
- Markdown
- HTML
- Word documents
- API responses
- OCR text
- Source code
- Images (via OCR)

## Attack types

The solution should try to detect the following types of attack across the input sources listed above:

1. Instruction Override
2. Role Change
3. Secret Extraction
4. Tool Abuse
5. Credential Theft
6. Context Poisoning
7. Multi-Step Jailbreaks
8. Encoded Instructions
9. Indirect Prompt Injection

## Solution depth requirements

- D1: Mostly structured and textual data as input. Should generate acceptable outputs in a majority of situations.
- D2: Mostly structured and textual data as input. High degree of demonstrable reliability.
- D3: Highly heterogeneous multimodal input. High degree of demonstrable reliability.

# Product context

The product to be specified is named **COSMAC**. It is to be built by reusing, refactoring and renaming the existing open-source codebase `prompt-shield` (v0.8.1, Apache 2.0) checked out at
`/Users/lokeshkumarmittal/Desktop/Hackathon/ET/prompt-shield`.
