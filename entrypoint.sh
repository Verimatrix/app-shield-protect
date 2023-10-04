#!/bin/sh -l

# retrieving account info for getting subscription_type if it's not provided
if [[ -z ${SUBSCRIPTION_TYPE}]]; then
  python3 /aps-cli/aps.py -v -c "$API_KEY_ID" -s "$API_SECRET"  --api-gateway-url "$API_GATEWAY_URL" --access-token-url "$ACCESS_TOKEN_URL" get-account-info > account.info
  cat account.info
  SUBSCRIPTION_TYPE = jq '.["customer"]["subscriptions"][0]["type"]'
  echo "Subscription Type retrieved [$SUBSCRIPTION_TYPE]"
fi

python3 /aps-cli/aps.py -v -c "$API_KEY_ID" -s "$API_SECRET"  --api-gateway-url "$API_GATEWAY_URL" --access-token-url "$ACCESS_TOKEN_URL" protect --subscription-type "$SUBSCRIPTION_TYPE" --file "$APP_FILE"

RESULT_FILE=protect_result.txt
if [ -f "$RESULT_FILE" ]; then
  protected_file="$(cat protect_result.txt)"
  echo "::set-output name=protected-file::$protected_file"
fi

