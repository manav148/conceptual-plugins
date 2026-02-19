#!/usr/bin/env bash
# Google Ads OAuth Token Exchange
# Exchanges a refresh token for an access token
# Usage: gads-token.sh <client_id> <client_secret> <refresh_token>
# Returns: access_token on success, ERROR message on failure

CLIENT_ID="$1"
CLIENT_SECRET="$2"
REFRESH_TOKEN="$3"

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ] || [ -z "$REFRESH_TOKEN" ]; then
  echo "ERROR: Usage: gads-token.sh <client_id> <client_secret> <refresh_token>"
  exit 1
fi

RESPONSE=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
  -d "grant_type=refresh_token" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "refresh_token=${REFRESH_TOKEN}")

ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  ERROR=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error_description','Unknown error'))" 2>/dev/null)
  echo "ERROR: ${ERROR}"
  exit 1
fi

echo "$ACCESS_TOKEN"
