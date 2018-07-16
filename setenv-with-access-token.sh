#!/bin/sh
set -e

python auth.py

export ACCESS_TOKEN="$(grep -oE "(?:\"access_token\":\s?\")(.*?)(?:\")" tokens.json | cut -c 18- | rev | cut -c 2- | rev)"

echo ""
echo "Your access token is set in ACCESS_TOKEN environment variable, and can be used as following:"
echo "> curl -H \"Authorization: Bearer \$ACCESS_TOKEN\" \"http://localhost:8080/my-protected-resource\""

