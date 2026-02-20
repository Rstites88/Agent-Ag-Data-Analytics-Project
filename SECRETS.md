# Secrets & Environment Setup

> **NEVER commit credentials to the repository.** This file documents which secrets are needed and where to configure them.

---

## GitHub Actions Secrets

Add these in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

| Secret Name          | Where to Get It                                                                        | Used By                                |
| -------------------- | -------------------------------------------------------------------------------------- | -------------------------------------- |
| `NVIDIA_API_KEY`     | [build.nvidia.com/moonshotai/kimi-k2.5](https://build.nvidia.com/moonshotai/kimi-k2.5) | CrewAI code review (primary provider)  |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys)                                       | CrewAI code review (fallback provider) |

### Authentication Secrets (Google OAuth)

| Secret Name            | Where to Get It                                                                         | Used By                          |
| ---------------------- | --------------------------------------------------------------------------------------- | -------------------------------- |
| `GOOGLE_CLIENT_ID`     | [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) | OAuth login flow                 |
| `GOOGLE_CLIENT_SECRET` | Same as above — created with the OAuth 2.0 Client ID                                    | OAuth token exchange             |
| `ALLOWED_EMAILS`       | You define this — comma-separated list of authorized email addresses                    | Access control (email allowlist) |

### Authentication Variables (non-secret)

Add under **Settings → Secrets and variables → Actions → Variables tab**:

| Variable Name         | Example Value                           | Used By            |
| --------------------- | --------------------------------------- | ------------------ |
| `GOOGLE_REDIRECT_URI` | `https://your-domain.com/auth/callback` | OAuth callback URL |

### Optional Secrets (Cloudflare Deployment)

| Secret Name             | Where to Get It                                                                     | Used By                               |
| ----------------------- | ----------------------------------------------------------------------------------- | ------------------------------------- |
| `CLOUDFLARE_API_TOKEN`  | [Cloudflare Dashboard → API Tokens](https://dash.cloudflare.com/profile/api-tokens) | Preview + production deploy workflows |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → Overview (right sidebar)                                     | Preview + production deploy workflows |

### Optional Secrets (Enhanced Memory)

| Secret Name    | Where to Get It                     | Used By                                  |
| -------------- | ----------------------------------- | ---------------------------------------- |
| `MEM0_API_KEY` | [app.mem0.ai](https://app.mem0.ai/) | Persistent AI review memory (mem0 Cloud) |

---

## Google OAuth Setup (Step by Step)

This project uses Google OAuth 2.0 for authentication. A public-facing website exists, but protected sections require login. Only email addresses listed in `ALLOWED_EMAILS` can access protected content.

### 1. Create OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Select **Web application**
6. Add your authorized redirect URIs:
   - Production: `https://your-domain.com/auth/callback`
   - Local dev: `http://localhost:8788/auth/callback`
7. Copy the **Client ID** and **Client Secret**

### 2. Configure the email allowlist

The `ALLOWED_EMAILS` secret controls who can log in. Set it as a comma-separated list:

```text
alice@example.com,bob@example.com,charlie@example.com
```

When a user authenticates via Google, the auth worker checks their email against this list. If their email is not in the list, they are denied access with a 403 response.

### 3. Add secrets to GitHub

| Where     | Name                   | Value                                      |
| --------- | ---------------------- | ------------------------------------------ |
| Secrets   | `GOOGLE_CLIENT_ID`     | `123456789-abc.apps.googleusercontent.com` |
| Secrets   | `GOOGLE_CLIENT_SECRET` | `GOCSPX-xxxxxxxxxxxx`                      |
| Secrets   | `ALLOWED_EMAILS`       | `alice@example.com,bob@example.com`        |
| Variables | `GOOGLE_REDIRECT_URI`  | `https://your-domain.com/auth/callback`    |

### 4. How the auth flow works

```text
User clicks "Login with Google"
  → Redirected to Google's consent screen
  → User authenticates with their Google account (2FA if enabled)
  → Google redirects back to /auth/callback with an authorization code
  → Auth worker exchanges code for tokens
  → Auth worker fetches user's email from Google
  → Email checked against ALLOWED_EMAILS list
  → If allowed: session created, cookie set, redirected to protected area
  → If denied: 403 Forbidden response
```

The auth worker runs on Cloudflare Workers, so sessions are stored in KV and user records in D1. No passwords are stored — Google handles all credential management and 2FA.

---

## How to Add a Secret

1. Go to your GitHub repository
2. Click **Settings** (top nav, far right)
3. In the left sidebar, expand **Secrets and variables**
4. Click **Actions**
5. Click **New repository secret**
6. Enter the **Name** exactly as shown in the table above
7. Paste the **Value** (your actual key/token)
8. Click **Add secret**

> Secrets are encrypted and only exposed to workflows at runtime. They are never visible in logs (GitHub masks them automatically).

---

## Local Development (.env)

For running locally (outside GitHub Actions):

```bash
# Copy the root template
cp .env.example .env

# And/or the CrewAI template
cp .crewai/.env.example .crewai/.env

# Edit with your actual values
nano .env
```

The `.env` file is gitignored — it will never be committed.

---

## What Each Secret Does

### `NVIDIA_API_KEY`

Primary key for CrewAI review runs. When this key is present, all crews use `moonshotai/kimi-k2-5` via NVIDIA NIM.

- Endpoint: `https://integrate.api.nvidia.com/v1`
- Current policy in this repo: NVIDIA first, OpenRouter fallback
- Cost: currently free-tier trial on NVIDIA API catalog

### `OPENROUTER_API_KEY`

Fallback key for CrewAI review runs when `NVIDIA_API_KEY` is absent. Routes AI model requests through [OpenRouter](https://openrouter.ai/), which provides access to multiple models from a single API key.

- **Free tier**: 20 requests/minute, access to free models (Gemini Flash, etc.)
- **Paid tier**: Higher rate limits, access to premium models (GPT-4o, Claude, etc.)
- **Cost**: The default configuration uses models that cost ~$0.01-0.05 per review

### `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`

OAuth 2.0 credentials from Google Cloud Console. The Client ID is sent to the browser (public). The Client Secret is server-side only — it exchanges authorization codes for access tokens.

- Create at [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
- Must be a **Web application** type OAuth client
- Redirect URIs must match exactly (production + localhost for dev)

### `ALLOWED_EMAILS`

Comma-separated list of email addresses permitted to access protected sections of the site. Checked server-side by the auth worker after Google authentication succeeds.

- Only Google accounts with emails in this list can log in
- Update this secret to add or remove authorized users
- No wildcard support (each email must be explicit)

### `CLOUDFLARE_API_TOKEN`

Required only if you're deploying your website to Cloudflare Pages. Create a token with these permissions:

- **Cloudflare Pages**: Edit
- **Zone**: DNS Edit (if using custom preview domains)
- **Account**: Cloudflare Pages Read
- **Workers Scripts**: Edit (for auth worker)
- **Workers KV**: Edit (for session storage)
- **D1**: Edit (for user records)

### `CLOUDFLARE_ACCOUNT_ID`

Your Cloudflare account identifier. Found on the Overview page of any zone in your Cloudflare dashboard (right sidebar, "Account ID").

### `MEM0_API_KEY`

Optional. Enables [mem0 Cloud](https://mem0.ai/) for persistent semantic memory across CI runs. Without this, the system uses local JSON files in `.crewai/memory/` (which works great — mem0 is an upgrade, not a requirement).

---

## Credential Validation

Run the validation script to check all credentials at once:

```bash
# Locally
bash scripts/validate-credentials.sh

# In CI — runs automatically via validate-environment workflow
```

The script tests each credential against its service's API and outputs a formatted report.

---

## Security Checklist

- [ ] `.env` is in `.gitignore` (**required** — already configured in this template)
- [ ] No API keys, tokens, or passwords in any committed file
- [ ] GitHub secrets are set at the repository level, not organization level (unless intentional)
- [ ] Cloudflare API token uses minimum required permissions
- [ ] Team members each have their own provider keys (NVIDIA/OpenRouter; never share keys)
- [ ] `ALLOWED_EMAILS` contains only authorized personnel
- [ ] Google OAuth redirect URIs are limited to your domains only
- [ ] Auth worker validates email against allowlist server-side (never client-side only)
- [ ] Sessions have reasonable TTL (default: 24 hours)
