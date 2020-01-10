#!/usr/bin/env bash
#
# Start the the app via `flask`.
#
# Note: Parts of this script are *very* bvflynn-specific. We assume this app will be running either locally or in a
# bvflynn cluster.
#
# Environment Variables:
# PORT - the port to bind flask to
# BVFLYNN_VPC - the VPC within which the container is running (e.g. 'qa' or 'prod')
# BVFLYNN_ENDPOINT_SCOPE - the scope within which the cluster is running (e.g. 'sbx')
# FLASK_APP - the file to be run by `flask` (e.g. 'app.py')
# FLASK_DEBUG - enable or disable debugging options in `flask` (e.g. '1' or '0')

set -o errexit
set -o nounset
set -o pipefail
# debug
# set -o xtrace

PORT="${PORT:-}"
BVFLYNN_VPC="${BVFLYNN_VPC:-}"
BVFLYNN_ENDPOINT_SCOPE="${BVFLYNN_ENDPOINT_SCOPE:-}"
FLASK_APP="${FLASK_APP:-./app.py}"
FLASK_ENV="${FLASK_ENV:-}"

flask_options=

# if PORT was provided in the environment, use it; otherwise, allow flask to choose a default port (flynn provides a
# PORT env var)
if [[ -n "${PORT}" ]]; then
    flask_options="${flask_options} --port ${PORT}"
fi

# when deployed, allow binding to an external ip address and disable the reloader and debugger
if [[ -n "${BVFLYNN_VPC}" ]]; then
    flask_options="${flask_options} --host 0.0.0.0 --no-reload --no-debugger"
fi

# if the dev environment has not been explicitly set and we're running locally or in sandbox, tell flask we're in a dev
# environment
# when FLASK_ENV=development and `--no-reload --no-debugger` are mixed (i.e. in sandbox), we get DEBUG-level logging
# without running the python debugger or flask reloader
if [[ -z "${FLASK_ENV}" ]] && [[ -z "${BVFLYNN_VPC}" || "sbx" = "${BVFLYNN_ENDPOINT_SCOPE}" ]]; then
    FLASK_ENV="development"
fi

echo "starting app with command \`FLASK_APP="${FLASK_APP}" FLASK_ENV="${FLASK_ENV}" flask run ${flask_options}\`"
FLASK_APP="${FLASK_APP}" FLASK_ENV="${FLASK_ENV}" flask run ${flask_options}
