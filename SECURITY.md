# Security Policy

## Supported Versions

The following versions of Feniks are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take the security of Feniks seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email**: [grzegorz.lesniowski@gmail.com](mailto:grzegorz.lesniowski@gmail.com)
- **Subject**: `[SECURITY] Feniks Vulnerability Report`

### What to Include

To help us better understand and address the issue, please include as much of the following information as possible:

- **Type of vulnerability** (e.g., SQL injection, XSS, authentication bypass, etc.)
- **Full paths of affected source file(s)**
- **Location of the affected source code** (tag/branch/commit or direct URL)
- **Special configuration required** to reproduce the issue
- **Step-by-step instructions to reproduce** the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the issue**, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Status Update**: Within 7 days with either:
  - Confirmation of the issue and estimated timeline for a fix
  - Request for additional information
  - Explanation if the issue is not considered a vulnerability

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report
2. **Investigation**: We will investigate the issue and determine its severity
3. **Resolution**: We will work on a fix and prepare a security advisory
4. **Disclosure**: We will coordinate with you on public disclosure timing
5. **Credit**: With your permission, we will acknowledge your contribution in:
   - Security advisory
   - Release notes
   - CHANGELOG.md

### Security Disclosure Policy

When a security issue is confirmed, we will:

1. **Develop a Fix**: Work on a patch to address the vulnerability
2. **Prepare Advisory**: Create a security advisory with details
3. **Coordinate Release**: Release the fix with a new version
4. **Public Disclosure**: Publish the security advisory after the fix is available

## Security Best Practices

When using Feniks, we recommend:

### Authentication & Authorization

- **Never commit sensitive credentials** (API keys, passwords, tokens) to version control
- **Use environment variables** for all sensitive configuration (see `.env.example`)
- **Enable RBAC** when deploying in production (`AUTH_ENABLED=true`)
- **Rotate JWT secrets** regularly in production environments
- **Use HTTPS only** for API endpoints in production

### Data Protection

- **Validate all input** to prevent injection attacks
- **Sanitize user-provided data** before storage or display
- **Use parameterized queries** when interacting with databases
- **Encrypt sensitive data** at rest and in transit

### Deployment

- **Run with least privilege** - use non-root users in containers
- **Keep dependencies updated** - regularly run `pip install --upgrade`
- **Monitor for vulnerabilities** - use tools like `safety check` or `pip-audit`
- **Enable audit logging** in production environments
- **Use network segmentation** for database and internal services

### Cost Control

- **Set token budgets** to prevent unexpected AI costs
- **Enable cost monitoring** (`COST_CONTROL_ENABLED=true`)
- **Configure rate limiting** to prevent abuse
- **Monitor usage metrics** regularly

### Legacy Behavior Guard

- **Sanitize recorded snapshots** - ensure no sensitive data in behavior tests
- **Secure storage backends** - use authentication for Postgres/Qdrant
- **Limit scenario access** - use RBAC for shared scenario libraries

## Known Security Considerations

### RAE Integration

When integrating with RAE (Reflective Agent Engine):

- **Validate RAE responses** - don't blindly trust external API data
- **Use HTTPS for RAE endpoints** - never send credentials over HTTP
- **Implement timeout limits** - prevent DoS through slow RAE responses
- **Sanitize code snippets** - RAE-provided code should be reviewed before execution

### Code Refactoring

When using refactoring recipes:

- **Review all changes** - always use `--dry-run` first
- **Test thoroughly** - run full test suite after refactoring
- **Backup before refactoring** - commit or backup before applying patches
- **Limit automation scope** - don't auto-apply refactorings without review

### AngularJS Migration

When migrating legacy applications:

- **Audit migrated code** - search for TODOs and manually review
- **Test behavior contracts** - validate no regressions introduced
- **Review generated imports** - ensure no malicious packages imported
- **Sanitize user data** - don't assume legacy XSS protections still apply

## Vulnerability Disclosure Policy

We follow coordinated vulnerability disclosure:

- **Private Disclosure Period**: 90 days from initial report
- **Public Disclosure**: After fix is released or 90 days, whichever comes first
- **CVE Assignment**: We will request CVEs for confirmed vulnerabilities with CVSS >= 4.0

## Security Updates

Security updates will be:

- **Released promptly** - typically within 1-2 weeks of confirmation
- **Documented in CHANGELOG.md** - with `[SECURITY]` prefix
- **Announced via**:
  - GitHub Security Advisory
  - Release notes
  - Project README
- **Backported** to supported versions when feasible

## Scope

### In Scope

- Server-side vulnerabilities (API, CLI, workers)
- Authentication and authorization bypass
- SQL injection, XSS, CSRF
- Sensitive data exposure
- Insecure dependencies
- Code execution vulnerabilities
- DoS vulnerabilities with significant impact

### Out of Scope

- Vulnerabilities in third-party dependencies (report to upstream)
- Social engineering attacks
- Physical security
- Denial of Service requiring >1M requests
- Issues in deprecated/unsupported versions
- Theoretical vulnerabilities without practical exploit

## Security Hall of Fame

We thank the following researchers for responsibly disclosing security issues:

*No reports yet - be the first!*

## Contact

For general security questions (non-vulnerabilities):
- **Email**: grzegorz.lesniowski@gmail.com
- **GitHub Discussions**: [Security Category](https://github.com/glesniowski/feniks/discussions/categories/security)

For security vulnerabilities:
- **Email**: grzegorz.lesniowski@gmail.com
- **Subject**: `[SECURITY] Feniks Vulnerability Report`

---

**Last Updated**: 2025-11-27
**Policy Version**: 1.0
