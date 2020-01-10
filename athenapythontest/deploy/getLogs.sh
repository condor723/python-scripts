#!/usr/bin/env bash
#
# @file Get the logs from live instances and copy them into the logs folders.
#
# The aggregated logs from a flynn deployment can be reached using the flynn
# log command:
#
# flynn -c <cluster> -a <app> log
#
# Environment Variables:
# BVFLYNN_APP_SCOPE (ex: your ldap or jira issue)
# BVFLYNN_ENDPOINT (ex: qa-us-east-1)
#

set -o errexit
set -o nounset
set -o pipefail

# Get the logs directory
DIR="$( cd "$( dirname "$0" )" && pwd)"
PROJECT_DIR="${DIR}/.."
LOGS_DIR="${PROJECT_DIR}/logs"
# Lowercase the repo name to get the app name as that's what bvflynn does by default
APP_NAME="$(basename `git rev-parse --show-toplevel` | tr '[:upper:]' '[:lower:]')"
BVFLYNN_ENDPOINT="${BVFLYNN_ENDPOINT:-qa-us-east-1}"
BVFLYNN_APP_SCOPE="${BVFLYNN_APP_SCOPE:-}"

if [ ! -z "${BVFLYNN_APP_SCOPE}" ]; then
    APP_NAME="${BVFLYNN_APP_SCOPE}-${APP_NAME}"
fi

mkdir -p "${LOGS_DIR}"
flynn -c "${BVFLYNN_ENDPOINT}" -a "${APP_NAME}" log > "${LOGS_DIR}/${APP_NAME}-${BVFLYNN_ENDPOINT}.log" 2>/dev/null
