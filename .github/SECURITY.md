# Security Policy

## Reporting a Vulnerability

Please do **NOT** open a public issue for security vulnerabilities.

Instead, use one of these methods:

1. **GitHub Private Reporting:** [Report a vulnerability](https://github.com/burakcanpolat/med-guide/security/advisories/new)
2. **Email:** Open a private advisory via the link above

We will respond within 72 hours and coordinate a fix before public disclosure.

## Scope

This policy covers security vulnerabilities in the codebase, such as:

- Code injection or command injection in scripts
- Path traversal in file handling (ZIP extraction, DICOM processing)
- Secrets exposure (API keys, tokens)
- Dependency vulnerabilities

## Out of Scope

- **AI output accuracy** — Med-Guide is not a medical device. AI-generated medical analysis may contain errors by design. This is not a security vulnerability.
- **Medical advice quality** — See the disclaimer in the README.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (main branch) | Yes |
| Older commits | No |
