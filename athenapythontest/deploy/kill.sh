#!/usr/bin/env bash
#
# Environment Variables:
# BVFLYNN_ENDPOINT (ex: qa-us-east-1|prod-us-east-1)
# BVFLYNN_APP_SCOPE (ex: qa|prod)
#

set -o errexit
set -o nounset
set -o pipefail

# Lowercase the repo name to get the app name as that's what bvflynn does by default
APP_NAME="$(basename `git rev-parse --show-toplevel` | tr '[:upper:]' '[:lower:]')"
BVFLYNN_ENDPOINT="${BVFLYNN_ENDPOINT:-qa-us-east-1}"
BVFLYNN_APP_SCOPE="${BVFLYNN_APP_SCOPE:-}"

if [ ! -z "${BVFLYNN_APP_SCOPE}" ]; then
    APP_NAME="${BVFLYNN_APP_SCOPE}-${APP_NAME}"
fi

flynn -c "${BVFLYNN_ENDPOINT}" -a "${APP_NAME}" delete
