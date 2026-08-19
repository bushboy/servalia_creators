#!/bin/sh
set -e

# PII_ENCRYPTION_KEY must be injected from a secret manager (e.g. K8s secret,
# Vault, SSM). The application will fail to start if it is not set.
if [ -z "$PII_ENCRYPTION_KEY" ]; then
  echo "ERROR: PII_ENCRYPTION_KEY is not set. Provide it from your secret manager."
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec uvicorn thebe_core.api:app --host 0.0.0.0 --port 8000
else
  exec "$@"
fi
