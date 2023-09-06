#!/bin/sh -l

python3 /aps-cli/aps.py -v -c "$API_KEY_ID" -s "$API_SECRET"  --api-gateway-url "$API_GATEWAY_URL" --access-token-url "$ACCESS_TOKEN_URL" protect --file "$APP_FILE"

RESULT_FILE=protect_result.txt
if [ -f "$RESULT_FILE" ]; then
  protected_file="$(cat protect_result.txt)"
  echo "::set-output name=protected-file::$protected_file"
fi

