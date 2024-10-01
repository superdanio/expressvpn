#!/usr/bin/env bash

set -e

TARGET=${HEALTHCHECK_TARGET:-http://ifconfig.me}

echo -n "Calling $TARGET: "
curl -fsL --get --data-urlencode "url=$TARGET" "http://localhost:5000/api/test"
