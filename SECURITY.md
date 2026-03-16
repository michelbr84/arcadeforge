# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in ArcadeForge, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: **security@arcadeforge.io**

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)

We will acknowledge receipt within 48 hours and provide a timeline for the fix.

## Scope

The following areas are in scope for security reports:

- Authentication bypass or session hijacking
- Sandbox escape (game code accessing host resources)
- SQL injection, command injection, or XSS
- Unauthorized access to other users' data
- API rate limit bypass
- Credential exposure

## Security Model

ArcadeForge executes user-generated code. Our security model includes:

- **Sandbox isolation**: Games run in Docker containers with no network, limited CPU/memory, read-only filesystem, non-root user, and seccomp profiles.
- **Code scanning**: All game code is scanned for dangerous patterns (import os, subprocess, eval, exec, etc.) before execution.
- **Authentication**: Argon2id password hashing, server-side sessions with HttpOnly cookies, session rotation on login.
- **Rate limiting**: Redis-backed rate limiting on all auth and play endpoints.
- **Input validation**: Strict Pydantic schemas on all API inputs.

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |

## Dependencies

We monitor dependencies via `pip-audit` (Python) and `pnpm audit` (Node.js).
