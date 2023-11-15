#!/bin/sh

# retrieving account info for getting subscription_type if it's not provided


ENABLE_PLATFORM=""
if [ "${PLATFORM}" != "" ] ; then
  ENABLE_PLATFORM="-P"
fi

if [ -z "${SUBSCRIPTION_TYPE}" ]; then
  python3 /aps-cli/aps.py -l=DEBUG ${ENABLE_PLATFORM} -c "$API_KEY_ID" -s "$API_SECRET" --api-gateway-url "$API_GATEWAY_URL" --access-token-url "$ACCESS_TOKEN_URL" get-account-info  > account.info
  SUBSCRIPTION=$(cat account.info | jq -r '.["customer"]["subscriptions"][0]["type"]')
  echo "Subscription Type retrieved [${SUBSCRIPTION}]"
else
  SUBSCRIPTION="${SUBSCRIPTION_TYPE}";
fi

if [ -n "${SUBSCRIPTION}" ]; then
  python3 /aps-cli/aps.py -l=DEBUG ${ENABLE_PLATFORM} -c "$API_KEY_ID" -s "$API_SECRET"  --api-gateway-url "$API_GATEWAY_URL" --access-token-url "$ACCESS_TOKEN_URL" protect --subscription-type "$SUBSCRIPTION" --file "$APP_FILE"
  if [ $? != 0 ] ; then
    exit 1
  fi
else
  echo "Error: Cannot resolve SUBSCRIPTION type"
fi



RESULT_FILE=protect_result.txt
if [ -f "$RESULT_FILE" ]; then
  protected_file="$(cat protect_result.txt)"
  echo "PROTECTED_FILE=$protected_file" >> "$GITHUB_OUTPUT"
fi

