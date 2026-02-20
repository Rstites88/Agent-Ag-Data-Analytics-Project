#!/bin/bash
# =============================================================================
# Credential Validation Script
# =============================================================================
# Tests all environment variables and secrets required for the project.
# Outputs formatted markdown table to GitHub Actions summary.
#
# Usage:
#   bash scripts/validate-credentials.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SUMMARY_FILE="/tmp/credential-validation-summary.md"
RESULT_FILE="/tmp/credential-validation-result"
OVERALL_RESULT=0

cat > "$SUMMARY_FILE" << 'EOF'
### Credential status

| Service | Credential | Type | Value | Status |
|---------|------------|------|-------|--------|
EOF

log_info()  { echo -e "${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

add_row() {
  echo "| $1 | $2 | $3 | $4 | $5 |" >> "$SUMMARY_FILE"
}

validate_cloudflare() {
  local token_status="" account_status=""

  echo ""
  echo "=== Validating Cloudflare Credentials ==="

  if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
    log_warn "CLOUDFLARE_API_TOKEN not set (optional — deploy will be skipped)"
    token_status="⚠️ Not Set"
  else
    log_info "CLOUDFLARE_API_TOKEN is set"
    if command -v wrangler &>/dev/null && wrangler whoami > /dev/null 2>&1; then
      log_info "Cloudflare API token verified via wrangler"
      token_status="✅ Valid"
    else
      token_status="✅ Set (wrangler not available for live check)"
    fi
  fi

  if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
    log_warn "CLOUDFLARE_ACCOUNT_ID not set (optional — deploy will be skipped)"
    account_status="⚠️ Not Set"
  else
    log_info "CLOUDFLARE_ACCOUNT_ID is set: ${CLOUDFLARE_ACCOUNT_ID:0:8}..."
    account_status="✅ Set"

    if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
      ACCOUNT_RESPONSE=$(curl -s \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID" 2>/dev/null || echo '{"success":false}')

      if echo "$ACCOUNT_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); exit(0 if d.get('success') else 1)" 2>/dev/null; then
        log_info "Cloudflare account access verified"
        account_status="✅ Valid"
      else
        log_warn "Cannot verify Cloudflare account access"
        account_status="⚠️ Cannot Verify"
      fi
    fi
  fi

  add_row "**Cloudflare**" "API Token" "Secret" "•••••••" "$token_status"
  add_row "" "Account ID" "Secret" "${CLOUDFLARE_ACCOUNT_ID:+${CLOUDFLARE_ACCOUNT_ID:0:8}•••}" "$account_status"
}

validate_google() {
  local client_id_status="" client_secret_status="" redirect_status="" emails_status=""

  echo ""
  echo "=== Validating Google OAuth Credentials ==="

  if [ -z "${GOOGLE_CLIENT_ID:-}" ]; then
    log_warn "GOOGLE_CLIENT_ID not set (auth will be disabled)"
    client_id_status="⚠️ Not Set"
  else
    log_info "GOOGLE_CLIENT_ID is set"
    if [[ "$GOOGLE_CLIENT_ID" =~ apps\.googleusercontent\.com$ ]]; then
      log_info "GOOGLE_CLIENT_ID format is valid"
      client_id_status="✅ Valid Format"
    else
      log_warn "GOOGLE_CLIENT_ID format may be invalid (expected: *.apps.googleusercontent.com)"
      client_id_status="⚠️ Invalid Format"
    fi
  fi

  if [ -z "${GOOGLE_CLIENT_SECRET:-}" ]; then
    log_warn "GOOGLE_CLIENT_SECRET not set (auth will be disabled)"
    client_secret_status="⚠️ Not Set"
  else
    log_info "GOOGLE_CLIENT_SECRET is set"
    if [[ "$GOOGLE_CLIENT_SECRET" =~ ^GOCSPX- ]]; then
      client_secret_status="✅ Valid Format"
    else
      client_secret_status="✅ Set"
    fi
  fi

  if [ -z "${GOOGLE_REDIRECT_URI:-}" ]; then
    log_warn "GOOGLE_REDIRECT_URI not set"
    redirect_status="⚠️ Not Set"
  else
    log_info "GOOGLE_REDIRECT_URI is set: $GOOGLE_REDIRECT_URI"
    if [[ "$GOOGLE_REDIRECT_URI" =~ ^https?:// ]]; then
      redirect_status="✅ Valid URL"
    else
      redirect_status="⚠️ Invalid URL"
    fi
  fi

  if [ -z "${ALLOWED_EMAILS:-}" ]; then
    log_warn "ALLOWED_EMAILS not set (no users will be able to access protected content)"
    emails_status="⚠️ Not Set"
  else
    local email_count
    email_count=$(echo "$ALLOWED_EMAILS" | tr ',' '\n' | grep -c '@' || echo "0")
    log_info "ALLOWED_EMAILS is set: $email_count email(s) configured"
    emails_status="✅ $email_count email(s)"
  fi

  # Live validation: test OAuth token endpoint if both client ID and secret are set
  if [ -n "${GOOGLE_CLIENT_ID:-}" ] && [ -n "${GOOGLE_CLIENT_SECRET:-}" ]; then
    OAUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "https://oauth2.googleapis.com/token" \
      -d "client_id=${GOOGLE_CLIENT_ID}&client_secret=${GOOGLE_CLIENT_SECRET}&grant_type=authorization_code&code=FAKE_CODE&redirect_uri=http://localhost" \
      2>/dev/null || echo "000")

    if [ "$OAUTH_RESPONSE" = "400" ]; then
      log_info "Google OAuth credentials are valid (bad code expected, credentials accepted)"
    elif [ "$OAUTH_RESPONSE" = "401" ]; then
      log_error "Google OAuth credentials are invalid (401 Unauthorized)"
      client_id_status="❌ Invalid"
      OVERALL_RESULT=1
    else
      log_warn "Google OAuth endpoint returned HTTP $OAUTH_RESPONSE"
    fi
  fi

  add_row "**Google OAuth**" "Client ID" "Secret" "${GOOGLE_CLIENT_ID:+${GOOGLE_CLIENT_ID:0:20}•••}" "$client_id_status"
  add_row "" "Client Secret" "Secret" "•••••••" "$client_secret_status"
  add_row "" "Redirect URI" "Variable" "${GOOGLE_REDIRECT_URI:-not set}" "$redirect_status"
  add_row "" "Allowed Emails" "Secret" "${ALLOWED_EMAILS:+$email_count email(s)}" "$emails_status"
}

validate_ai_provider_keys() {
  local nvidia_status=""
  local openrouter_status=""

  echo ""
  echo "=== Validating AI Provider Credentials ==="

  if [ -z "${NVIDIA_API_KEY:-}" ] && [ -z "${NVIDIA_NIM_API_KEY:-}" ]; then
    log_warn "NVIDIA_API_KEY not set (preferred for CrewAI review)"
    nvidia_status="⚠️ Not Set"
  else
    local nvidia_key="${NVIDIA_API_KEY:-${NVIDIA_NIM_API_KEY:-}}"
    log_info "NVIDIA API key is set"

    NIM_MODELS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $nvidia_key" \
      "https://integrate.api.nvidia.com/v1/models" 2>/dev/null || echo "000")

    if [ "$NIM_MODELS_RESPONSE" = "200" ]; then
      log_info "NVIDIA API key verified (models endpoint accessible)"
      nvidia_status="✅ Valid"
    elif [ "$NIM_MODELS_RESPONSE" = "401" ]; then
      log_error "NVIDIA API key is invalid (401 Unauthorized)"
      nvidia_status="❌ Invalid"
      OVERALL_RESULT=1
    else
      log_warn "NVIDIA API returned HTTP $NIM_MODELS_RESPONSE"
      nvidia_status="⚠️ HTTP $NIM_MODELS_RESPONSE"
    fi
  fi

  if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    log_warn "OPENROUTER_API_KEY not set (used as fallback)"
    openrouter_status="⚠️ Not Set"
  else
    log_info "OPENROUTER_API_KEY is set"

    MODELS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $OPENROUTER_API_KEY" \
      "https://openrouter.ai/api/v1/models" 2>/dev/null || echo "000")

    if [ "$MODELS_RESPONSE" = "200" ]; then
      log_info "OpenRouter API key verified (models endpoint accessible)"
      openrouter_status="✅ Valid"
    elif [ "$MODELS_RESPONSE" = "401" ]; then
      log_error "OpenRouter API key is invalid (401 Unauthorized)"
      openrouter_status="❌ Invalid"
      OVERALL_RESULT=1
    else
      log_warn "OpenRouter returned HTTP $MODELS_RESPONSE"
      openrouter_status="⚠️ HTTP $MODELS_RESPONSE"
    fi
  fi

  add_row "**NVIDIA NIM**" "API Key" "Secret" "${NVIDIA_API_KEY:+${NVIDIA_API_KEY:0:12}•••}${NVIDIA_NIM_API_KEY:+${NVIDIA_NIM_API_KEY:0:12}•••}" "$nvidia_status"
  add_row "**OpenRouter**" "API Key" "Secret" "${OPENROUTER_API_KEY:+${OPENROUTER_API_KEY:0:12}•••}" "$openrouter_status"
}

validate_optional() {
  echo ""
  echo "=== Checking Optional Credentials ==="

  if [ -n "${GITHUB_TOKEN:-}" ]; then
    log_info "GITHUB_TOKEN is available"
    add_row "**GitHub**" "Token" "Auto-provided" "•••••••" "✅ Available"
  else
    log_warn "GITHUB_TOKEN not available (expected in Actions context)"
    add_row "**GitHub**" "Token" "Auto-provided" "-" "⚠️ Not Available"
  fi

  if [ -n "${MEM0_API_KEY:-}" ]; then
    log_info "MEM0_API_KEY is set (cloud memory enabled)"
    add_row "**mem0**" "API Key" "Secret" "•••••••" "✅ Set"
  else
    log_info "MEM0_API_KEY not set (using local JSON memory — this is fine)"
    add_row "**mem0**" "API Key" "Secret" "-" "⏭️ Using Local"
  fi
}

echo "========================================"
echo "Credential Validation"
echo "========================================"
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

validate_cloudflare
validate_google
validate_ai_provider_keys
validate_optional

cat >> "$SUMMARY_FILE" << 'EOF'

<details>
<summary><strong>Legend</strong></summary>

- ✅ **Valid**: Credential is properly configured and verified via API
- ⚠️ **Warning**: Credential is set but format may be invalid, or is optional and not set
- ❌ **Invalid**: Credential is missing or invalid (required)
- ⏭️ **Skipped**: Using alternative (e.g., local memory instead of cloud)

</details>

---

<details>
<summary><strong>Validation methods</strong></summary>

- **Cloudflare**: Verified via wrangler CLI and account access API
- **Google OAuth**: Verified via OAuth2 token endpoint (400 = creds valid, 401 = creds invalid)
- **NVIDIA NIM**: Verified via models endpoint (200 = key valid)
- **OpenRouter**: Verified via models endpoint (200 = key valid)

</details>

---

<details>
<summary><strong>If credentials fail</strong></summary>

1. **Cloudflare**: Regenerate at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. **Google OAuth**: Update at [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
3. **NVIDIA NIM**: Regenerate at [build.nvidia.com/moonshotai/kimi-k2.5](https://build.nvidia.com/moonshotai/kimi-k2.5)
4. **OpenRouter**: Regenerate at [openrouter.ai/keys](https://openrouter.ai/keys)
5. **Allowed Emails**: Update the `ALLOWED_EMAILS` secret with comma-separated addresses
6. Update secrets in repo: Settings → Secrets and variables → Actions

</details>
EOF

echo ""
echo "========================================"
if [ $OVERALL_RESULT -eq 0 ]; then
  log_info "All credentials validated successfully!"
else
  log_error "Credential validation failed. Check the summary for details."
fi
echo "========================================"

echo "$OVERALL_RESULT" > "$RESULT_FILE"
exit $OVERALL_RESULT
