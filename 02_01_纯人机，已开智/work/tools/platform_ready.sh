#!/bin/sh

# Read-only, deterministic handoff for the platform reproduction Agent.
set -eu

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd -P)
WORK_ROOT=$(CDPATH= cd -P "$SCRIPT_DIR/.." && pwd -P)

for required in \
  AppScope/app.json5 \
  build-profile.json5 \
  entry/build-profile.json5 \
  entry/src/main/module.json5 \
  entry/src/main/ets/pages/Index.ets \
  migration-report.md \
  migration-manifest.json \
  source-facts/android-facts.json \
  journeys/core.yaml \
  skills/android-to-harmonyos/SKILL.md
do
  if [ ! -f "$WORK_ROOT/$required" ]; then
    printf '%s\n' 'artifact_status=failed' "missing=$required"
    exit 1
  fi
done

printf '%s\n' \
  'artifact_status=ready' \
  'artifact_type=harmonyos_stage_repository' \
  'source_commit=23e1421b72b602d80486777efbf24dd248abf3bb' \
  'artifact_path=work'
