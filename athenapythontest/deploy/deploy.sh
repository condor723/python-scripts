#!/usr/bin/env bash
#
# Environment Variables:
# BVFLYNN_TEAM (ex: firebird-devs@bazaarvoice.com)
# BVFLYNN_ENDPOINT (ex: qa-us-east-1|prod-us-east-1)
# BVFLYNN_APP_SCOPE (ex: qa|prod)
#

set -o errexit
set -o nounset
set -o pipefail

# Set the current working directory and the project root directory.
DIR="$( cd "$( dirname "$0" )" && pwd)"
PROJECT_DIR="${DIR}/.."

# If the bvflynn command isn't available, do nothing.
if ! command -v bvflynn; then
    >&2 echo "bvflynn not installed. Bailing."
    exit 1
fi

# --------------------------------------------------------------------------
# Set bvflynn environment variables.
# --------------------------------------------------------------------------
BVFLYNN_TEAM=""
BVFLYNN_ENDPOINT=""
BVFLYNN_APP_SCOPE="${BVFLYNN_APP_SCOPE:-}"

# --------------------------------------------------------------------------
# Run the deployment.
# --------------------------------------------------------------------------
cd "${PROJECT_DIR}"

# Actually deploy the application.
BVFLYNN_TEAM="${BVFLYNN_TEAM}" BVFLYNN_ENDPOINT="${BVFLYNN_ENDPOINT}" BVFLYNN_APP_SCOPE="${BVFLYNN_APP_SCOPE}" \
    bvflynn push

# Perform further configuration after push. The separator sandwich is meant to match the output format of flynn.
configNotice="Configuring deployment on ${BVFLYNN_ENDPOINT}"
configNoticeSeparator="$(seq -f "-" -s "" ${#configNotice})"

echo "${configNoticeSeparator}"
echo "${configNotice}"
echo "${configNoticeSeparator}"
echo "Setting flynn metadata."

branch="$(git rev-parse --abbrev-ref HEAD)"
revision="$(git rev-parse --short HEAD)"
deployer="$(whoami)"

flynn -c "${BVFLYNN_ENDPOINT}" meta set version="${branch}:${revision}" deployer="${deployer}"
