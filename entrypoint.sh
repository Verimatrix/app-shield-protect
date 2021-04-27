#!/bin/sh -l

python3 /aps-cli/aps.py -v -c "$APS_KEY" -s "$APS_SECRET" protect --file "$APP_FILE"

RESULT_FILE=protect_result.txt
if [ -f "$RESULT_FILE" ]; then
  protected_file="$(cat protect_result.txt)"
  echo "::set-output name=protected-file::$protected_file"
fi

