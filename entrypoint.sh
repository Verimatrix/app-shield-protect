#!/bin/sh -l

python3 /aps-cli/aps.py -v -c "$API_KEY_ID" -s "$API_SECRET" protect --file "$APP_FILE"

RESULT_FILE=protect_result.txt
if [ -f "$RESULT_FILE" ]; then
  protected_file="$(cat protect_result.txt)"
  echo "::set-output name=protected-file::$protected_file"
fi

