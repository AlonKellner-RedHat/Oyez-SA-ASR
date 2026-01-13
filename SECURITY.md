# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security
vulnerability in Oyez SA-ASR, please follow these steps:

### 1. **DO NOT** create a public GitHub issue

Security vulnerabilities should not be disclosed publicly until they are
resolved.

### 2. **DO** report the vulnerability privately

Please report security vulnerabilities by emailing us at
**<me@alonkellner.com>** with the subject line
`[SECURITY] Oyez SA-ASR Vulnerability Report`.

### 3. **Include the following information** in your report

- **Description**: A clear description of the vulnerability
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Affected versions**: Which versions of Oyez SA-ASR are affected
- **Suggested fix**: If you have a suggested fix (optional)

### 4. **Response timeline**

- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Resolution**: As quickly as possible, typically within 30 days

### 5. **Disclosure policy**

- Vulnerabilities will be disclosed publicly after they are fixed
- A security advisory will be published on GitHub
- CVE numbers will be requested for significant vulnerabilities
- Users will be notified through GitHub releases and security advisories

## Security Best Practices

### For Users

- Always use the latest stable version of Oyez SA-ASR
- Keep your dependencies updated
- Review configuration files before applying them
- Use environment variables for sensitive information
- Run Oyez SA-ASR in a controlled environment

### For Contributors

- Follow secure coding practices
- Validate all user inputs
- Use secure file handling methods
- Avoid hardcoding sensitive information
- Review code for potential security issues

## Security Features

Oyez SA-ASR includes several security features:

- **Input validation**: All file paths and configurations are validated
- **Safe file operations**: File operations are performed safely with proper
  error handling
- **Environment variable protection**: Sensitive information can be stored in
  environment variables
- **Audit trail**: File synchronization operations can be logged for audit
  purposes

## Security Updates

Security updates are released as patch versions (e.g., 0.1.1, 0.1.2) and
should be applied immediately.

### Updating Oyez SA-ASR

```bash
# Update to latest version
git pull
```

## Responsible Disclosure

We believe in responsible disclosure and will:

- Acknowledge all security reports
- Work with reporters to understand and fix issues
- Credit reporters in security advisories (unless they prefer anonymity)
- Provide reasonable time for users to update before public disclosure

## Security Team

The security team consists of:

- **Primary contact**: Alon Kellner (<me@alonkellner.com>)
- **Backup contact**: GitHub Issues (for non-sensitive security discussions)

## Security History

This section will be updated with resolved security issues:

- **No security vulnerabilities reported yet**

---

## Thank you for helping keep Oyez SA-ASR secure! 🔒

For general questions about Oyez SA-ASR security, please use
[GitHub Issues](https://github.com/AlonKellner/oyez_sa_asr/issues).
