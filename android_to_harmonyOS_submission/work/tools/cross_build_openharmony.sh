#!/bin/sh

# Compile the authored Harmony project against the public OpenHarmony API 20
# surface in a temporary copy. This is a compatibility check, not a substitute
# for the official HarmonyOS build or Code Linter.
set -eu

case "${1:-}" in
  '') BUILD_MODE=debug ;;
  --debug) BUILD_MODE=debug ;;
  --release) BUILD_MODE=release ;;
  *)
    printf '%s\n' 'usage: tools/cross_build_openharmony.sh [--debug|--release]'
    exit 2
    ;;
esac
[ "$#" -le 1 ] || {
  printf '%s\n' 'usage: tools/cross_build_openharmony.sh [--debug|--release]'
  exit 2
}

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -P "$SCRIPT_DIR/.." && pwd -P)
PROJECT_PARENT=$(CDPATH= cd -P "$PROJECT_ROOT/.." && pwd -P)
SDK_ROOT=${OHOS_CROSS_SDK_HOME:-$PROJECT_PARENT/.toolchains/openharmony-api20/base}
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/jetsnack-cross-build.XXXXXX")
if [ "$BUILD_MODE" = debug ]; then
  OUTPUT_RELATIVE=build/cross/entry-default-unsigned.hap
else
  OUTPUT_RELATIVE=build/cross/release/entry-default-unsigned.hap
fi
OUTPUT_PATH=$PROJECT_ROOT/$OUTPUT_RELATIVE

# A failed compatibility check must not leave a previous HAP looking current.
rm -f "$OUTPUT_PATH"

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup 0 HUP INT TERM

[ -d "$SDK_ROOT" ] || {
  printf '%s\n' 'status=failed' 'reason=missing_public_api_sdk'
  exit 1
}

find_hvigor() {
  for candidate in \
    "${HVIGORW:-}" \
    "$PROJECT_PARENT/.toolchains/harmony-cli/bin/hvigorw" \
    "$PROJECT_ROOT/hvigorw"
  do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  command -v hvigorw
}

HVIGOR_BIN=$(find_hvigor) || {
  printf '%s\n' 'status=failed' 'reason=missing_hvigor'
  exit 1
}

rsync -a \
  --exclude .git \
  --exclude .hvigor \
  --exclude build \
  --exclude entry/build \
  --exclude oh_modules \
  --exclude entry/oh_modules \
  "$PROJECT_ROOT/" "$TEMP_ROOT/"

python3 - "$TEMP_ROOT/build-profile.json5" "$TEMP_ROOT/entry/src/main/module.json5" <<'PY'
import json
import sys

profile_path, module_path = sys.argv[1:]
with open(profile_path, encoding="utf-8") as stream:
    profile = json.load(stream)
product = profile["app"]["products"][0]
product["compileSdkVersion"] = 20
product["compatibleSdkVersion"] = 20
product["targetSdkVersion"] = 20
product["runtimeOS"] = "OpenHarmony"
with open(profile_path, "w", encoding="utf-8") as stream:
    json.dump(profile, stream, ensure_ascii=False, indent=2)
    stream.write("\n")

with open(module_path, encoding="utf-8") as stream:
    module = json.load(stream)
module["module"]["deviceTypes"] = ["default"]
with open(module_path, "w", encoding="utf-8") as stream:
    json.dump(module, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
PY

export DEVECO_SDK_HOME=$SDK_ROOT
export OHOS_BASE_SDK_HOME=$SDK_ROOT
export HVIGOR_USER_HOME=${HVIGOR_USER_HOME:-$PROJECT_PARENT/.toolchains/hvigor-home}

if [ -z "${DEVECO_NODE_HOME:-}" ]; then
  NODE_BIN=$(command -v node 2>/dev/null || true)
  if [ -n "$NODE_BIN" ]; then
    DEVECO_NODE_HOME=$(CDPATH= cd -P "$(dirname "$NODE_BIN")/.." && pwd -P)
    export DEVECO_NODE_HOME
  fi
fi

cd "$TEMP_ROOT"
"$HVIGOR_BIN" assembleHap --mode module \
  -p product=default \
  -p module=entry@default \
  -p buildMode="$BUILD_MODE" \
  --no-daemon

SOURCE_HAP=entry/build/default/outputs/default/entry-default-unsigned.hap
[ -s "$SOURCE_HAP" ] || {
  printf '%s\n' 'status=failed' 'reason=missing_hap'
  exit 1
}

mkdir -p "$(dirname "$OUTPUT_PATH")"
cp "$SOURCE_HAP" "$OUTPUT_PATH"

printf '%s\n' \
  'status=passed' \
  'scope=public_api_cross_build' \
  "build_mode=$BUILD_MODE" \
  "hap=$OUTPUT_RELATIVE"
