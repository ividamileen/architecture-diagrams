# Security Policy

## Supported Versions

Currently supported versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Measures

This project implements multiple layers of security:

### 1. Dependency Management

**Updated Dependencies:**
- All Python packages updated to latest secure versions
- All npm packages updated to latest secure versions
- Regular dependency audits via CI/CD
- Automated vulnerability scanning with Trivy and Safety

**Backend (Python):**
- `fastapi==0.109.0` (from 0.104.1)
- `aiohttp==3.9.3` (from 3.9.1) - Fixes CVE-2024-23334
- `Pillow==10.2.0` (from 10.1.0) - Security patches
- `sqlalchemy==2.0.25` (from 2.0.23)
- `cryptography==42.0.0` - Explicit version for security
- Added `safety` for dependency scanning

**Frontend (Node.js):**
- `axios==1.6.7` (from 1.6.2) - Fixes prototype pollution
- `react-router-dom==6.21.3` (from 6.20.1)
- `vite==5.0.12` (from 5.0.8) - Security patches
- `jsdom==24.0.0` (from 23.0.1)

### 2. Application Security Headers

**Implemented HTTP Security Headers:**
- `X-Content-Type-Options: nosniff` - Prevents MIME-sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Strict-Transport-Security` - Forces HTTPS
- `Content-Security-Policy` - Prevents XSS and injection attacks
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information
- `Permissions-Policy` - Restricts browser features

### 3. Rate Limiting

**Simple Rate Limiting Middleware:**
- 100 requests per 60 seconds per IP address
- Returns 429 Too Many Requests when exceeded
- Prevents brute force and DoS attacks

### 4. CORS Configuration

**Restrictive CORS Settings:**
- Explicit allowed origins (no wildcards in production)
- Explicit allowed methods: GET, POST, PUT, DELETE, OPTIONS
- Explicit allowed headers: Content-Type, Authorization, X-Requested-With
- Credentials support with proper origin validation
- Preflight cache: 10 minutes

### 5. Docker Security

**Non-Root User:**
- Backend runs as `appuser` (non-root)
- Frontend runs as `appuser` (non-root)
- Proper file permissions

**Image Optimization:**
- Minimal base images (python:3.11-slim, node:18-alpine)
- Multi-stage builds for frontend
- No development dependencies in production
- .dockerignore to exclude sensitive files

**Health Checks:**
- Backend: HTTP health endpoint check every 30s
- Frontend: HTTP availability check every 30s

### 6. API Documentation

**Production Security:**
- Swagger UI disabled in production (`docs_url=None`)
- ReDoc disabled in production (`redoc_url=None`)
- OpenAPI schema disabled in production (`openapi_url=None`)
- Only available in development mode

### 7. Secret Management

**Environment Variables:**
- All secrets stored in environment variables
- `.env.example` provided without actual secrets
- `.env` excluded from version control
- Database credentials not hardcoded
- API keys not exposed in code

### 8. CI/CD Security Scanning

**Automated Security Checks:**
- **Trivy**: Filesystem and config vulnerability scanning
- **Safety**: Python dependency vulnerability check
- **npm audit**: Node.js dependency vulnerability check
- **TruffleHog**: Secret scanning in git history
- Runs on every push and pull request

**Scan Types:**
- Container image scanning
- Dependency scanning
- Configuration scanning
- Secret detection
- SAST (Static Application Security Testing)

### 9. Input Validation

**Pydantic Models:**
- All API inputs validated with Pydantic
- Type checking enforced
- Length limits on string inputs
- Email validation
- URL validation

### 10. Database Security

**SQLAlchemy ORM:**
- Parameterized queries (prevents SQL injection)
- Connection pooling with proper timeouts
- SSL/TLS support for database connections
- No raw SQL queries without parameterization

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email security concerns to: [security@your-domain.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

**Response Time:**
- Initial response: Within 48 hours
- Status update: Within 5 business days
- Resolution: Varies by severity

**Severity Levels:**
- **Critical**: Fix within 24-48 hours
- **High**: Fix within 1 week
- **Medium**: Fix within 1 month
- **Low**: Fix in next release

## Security Best Practices for Deployment

### Production Deployment Checklist

- [ ] Generate strong `SECRET_KEY` (64+ random characters)
- [ ] Use HTTPS/TLS for all connections
- [ ] Configure firewall rules (restrict ports)
- [ ] Enable database SSL/TLS connections
- [ ] Set up monitoring and alerting
- [ ] Regular security updates (monthly)
- [ ] Backup encryption at rest
- [ ] Rotate credentials regularly (quarterly)
- [ ] Implement logging and audit trails
- [ ] Set up intrusion detection

### Environment Variables

**Required Security Configuration:**

```env
# Strong secret key (use: openssl rand -hex 32)
SECRET_KEY=<64-character-random-string>

# Database with SSL
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require

# Restrict CORS origins
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# API keys (never commit)
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>

# Production mode
API_RELOAD=false
```

### Network Security

**Recommended Setup:**
- Place backend behind reverse proxy (nginx/traefik)
- Use TLS 1.3 minimum
- Implement Web Application Firewall (WAF)
- Enable DDoS protection (Cloudflare, AWS Shield)
- Use private networks for database connections
- Implement network segmentation

### Monitoring and Logging

**Security Monitoring:**
- Log all authentication attempts
- Monitor rate limit violations
- Alert on suspicious patterns
- Track API usage patterns
- Log all errors with context
- Set up log aggregation (ELK, Datadog)

### Backup and Recovery

**Security Measures:**
- Encrypt backups at rest
- Store backups in separate location
- Test recovery procedures monthly
- Implement point-in-time recovery
- Maintain offline backups

## Compliance

This application implements security controls aligned with:

- **OWASP Top 10** (2021) - Web application security risks
- **CWE Top 25** - Most dangerous software weaknesses
- **GDPR** - Data protection (if applicable)
- **SOC 2** - Security, availability, confidentiality

## Security Updates

### Version 1.0.1 (Latest)

**Security Fixes:**
- Updated all dependencies to latest secure versions
- Added security headers middleware
- Implemented rate limiting
- Added non-root Docker users
- Enhanced CI/CD security scanning
- Disabled API docs in production
- Implemented .dockerignore files
- Added secret scanning in CI/CD

### Version 1.0.0

**Initial Security Measures:**
- CORS configuration
- Input validation with Pydantic
- Parameterized database queries
- Environment variable management
- Basic security headers

## Security Roadmap

**Planned Security Enhancements:**

### Q1 2024
- [ ] Implement OAuth2 authentication
- [ ] Add JWT token refresh mechanism
- [ ] Implement API key rotation
- [ ] Add audit logging

### Q2 2024
- [ ] Penetration testing
- [ ] Security code review
- [ ] Implement WAF rules
- [ ] Add intrusion detection

### Q3 2024
- [ ] SOC 2 Type I compliance
- [ ] Third-party security audit
- [ ] Implement SIEM integration
- [ ] Add behavioral analytics

## Resources

**Security Tools Used:**
- [Trivy](https://trivy.dev/) - Vulnerability scanner
- [Safety](https://pyup.io/safety/) - Python dependency checker
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit) - Node.js security audits
- [TruffleHog](https://github.com/trufflesecurity/trufflehog) - Secret scanner

**Security Standards:**
- [OWASP](https://owasp.org/)
- [CWE](https://cwe.mitre.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Contact

For security-related questions or concerns:
- Email: security@your-domain.com
- Security advisories: GitHub Security Advisories

---

Last updated: January 2024
