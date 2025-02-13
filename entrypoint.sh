#!/bin/bash
set -e  # Exit immediately if a command fails

# Set default subscription if not provided
SUBSCRIPTION="${SUBSCRIPTION:-XTD_PLATFORM}"

# Run vmx-aps command
vmx-aps -l=DEBUG \
  --api-key "$API_SECRET" \
  --api-gateway-url "$API_GATEWAY_URL" \
  --access-token-url "$ACCESS_TOKEN_URL" \
  protect --subscription-type "$SUBSCRIPTION" \
  --file "$APP_FILE"

# Check for protect_result.txt and output to GitHub Actions
RESULT_FILE="protect_result.txt"
if [[ -f "$RESULT_FILE" ]]; then
  PROTECTED_FILE="$(cat "$RESULT_FILE")"
  echo "PROTECTED_FILE=$PROTECTED_FILE" >> "$GITHUB_OUTPUT"
fi
