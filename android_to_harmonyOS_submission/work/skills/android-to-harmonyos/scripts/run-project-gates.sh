#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -P "$SCRIPT_DIR/../../.." && pwd -P)

exec "$PROJECT_ROOT/tools/verify.sh" "${1:---build}"
