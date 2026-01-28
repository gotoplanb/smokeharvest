# Authentication Patterns for SmokeHarvest

This guide covers how to handle different authentication scenarios when running SmokeHarvest against your application.

## No Authentication

The simplest case. Set `auth.type: none` in your config.

```yaml
auth:
  type: none
```

## Username/Password

The most common case. Credentials are stored in environment variables for security.

```yaml
auth:
  type: username_password
  username_env: MY_APP_TEST_USER
  password_env: MY_APP_TEST_PASS
  login_url: /login  # optional, defaults to /login
```

**Setup:**
```bash
export MY_APP_TEST_USER="testuser@example.com"
export MY_APP_TEST_PASS="testpassword123"
```

**Best practice:** Create a dedicated test account with limited permissions. Don't use real user credentials.

## One-Time Password (OTP) / MFA

For applications requiring a one-time code sent via email or SMS.

### Interactive Mode (Human in the Loop)

For demos or manual runs, Claude will pause and prompt for the OTP:

```yaml
auth:
  type: otp
  username_env: MY_APP_TEST_USER
  password_env: MY_APP_TEST_PASS
  otp_method: prompt  # Claude will ask you to paste the code
```

When Claude reaches the OTP screen:
```
SmokeHarvest: I've submitted your credentials and triggered OTP.
              Paste the code when you receive it:
              
You:          847293

SmokeHarvest: Continuing authentication flow...
```

### Automated Mode (API Integration)

For fully automated pipelines, integrate with an email API to fetch OTP codes programmatically.

```yaml
auth:
  type: otp
  username_env: MY_APP_TEST_USER
  password_env: MY_APP_TEST_PASS
  otp_method: email_api
  otp_config:
    provider: resend  # or mailgun, sendgrid, etc.
    api_key_env: RESEND_API_KEY
    inbox: test-otp@yourdomain.com
    # Pattern to extract OTP from email body
    otp_pattern: "Your verification code is: (\\d{6})"
```

**Note:** Automated OTP handling requires additional setup:
1. A dedicated test email inbox
2. An email API that can read incoming mail
3. The OTP pattern for your application

This is more complex and may not be worth it for occasional smoke tests. The interactive mode works fine for most use cases.

## OAuth / SSO

OAuth flows are tricky because they involve redirects to third-party providers.

### Option 1: Test Account with Password Auth

Many OAuth providers allow password authentication for test accounts. Check if your provider supports this.

### Option 2: Pre-authenticated Session

For CI/CD pipelines, you might:
1. Manually authenticate once
2. Export the session cookies
3. Load those cookies at the start of each test

```yaml
auth:
  type: session_cookie
  cookie_file: ./test-session.json
```

**Warning:** Session cookies expire. This approach requires periodic manual re-authentication.

### Option 3: Skip Auth in Tests

If your application supports it, use a test mode or feature flag that bypasses authentication for known test accounts.

```yaml
auth:
  type: none
  # Add a header or query param that your app recognizes
  test_mode:
    header: X-Test-Mode
    value: "smokeharvest"
```

## API Key Authentication

For applications that use API keys instead of session-based auth.

```yaml
auth:
  type: api_key
  api_key_env: MY_APP_API_KEY
  # How to send the key
  method: header  # or query_param
  header_name: Authorization
  header_format: "Bearer {key}"  # or "Api-Key {key}", etc.
```

## Handling Auth in Critical Paths

If authentication is a critical path itself (you want to test the login flow), define it as a step:

```yaml
critical_paths:
  - name: authentication
    description: Test the login flow
    steps:
      - action: navigate
        target: /login
        
      - action: fill_form
        fields:
          - name: email
            selector: input[name="email"]
            value_env: MY_APP_TEST_USER
          - name: password
            selector: input[name="password"]
            value_env: MY_APP_TEST_PASS
            
      - action: click
        selector: button[type="submit"]
        
      - action: verify
        assertions:
          - type: url_contains
            value: "/dashboard"
          - type: element_visible
            selector: "[data-testid='user-menu']"
```

## Security Reminders

1. **Never commit credentials** - Always use environment variables
2. **Use test accounts** - Don't use real user credentials
3. **Limit permissions** - Test accounts should have minimal access
4. **Rotate credentials** - Change test passwords periodically
5. **Don't test against production with destructive actions** - Use staging when possible
