#!/bin/sh

# Single non-interactive verification entry point for the submitted project.
set -eu

usage() {
  printf '%s\n' 'usage: tools/verify.sh [--static|--build|--strict]'
}

[ "$#" -le 1 ] || {
  usage
  exit 2
}

MODE=${1:---build}
case "$MODE" in
  --static|--build|--strict) ;;
  *)
    usage
    exit 2
    ;;
esac

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -P "$SCRIPT_DIR/.." && pwd -P)
PROJECT_PARENT=$(CDPATH= cd -P "$PROJECT_ROOT/.." && pwd -P)
cd "$PROJECT_ROOT"

export PYTHONDONTWRITEBYTECODE=1
printf '%s\n' 'stage=contract_check'
python3 tools/contract_check.py --manifest migration-manifest.json
printf '%s\n' 'stage=unit_tests'
python3 -m unittest discover -s tools/tests -p 'test_*.py' -v

if [ "$MODE" = --static ]; then
  printf '%s\n' 'stage=completed' 'status=passed' 'mode=static'
  exit 0
fi

printf '%s\n' 'stage=preflight'
if [ "$MODE" = --strict ]; then
  tools/preflight.sh --strict
else
  tools/preflight.sh --build-only
fi

sdk_root_has_metadata() {
  candidate_root=$1
  [ -n "$candidate_root" ] || return 1
  [ -d "$candidate_root" ] || return 1
  for metadata_file in \
    "$candidate_root/ets/oh-uni-package.json" \
    "$candidate_root"/*/ets/oh-uni-package.json \
    "$candidate_root"/*/*/ets/oh-uni-package.json \
    "$candidate_root"/*/*/*/ets/oh-uni-package.json \
    "$candidate_root/openharmony/ets/oh-uni-package.json" \
    "$candidate_root/harmonyos/ets/oh-uni-package.json" \
    "$candidate_root/sdk/ets/oh-uni-package.json" \
    "$candidate_root/sdk"/*/ets/oh-uni-package.json
  do
    if [ -f "$metadata_file" ]; then
      return 0
    fi
  done
  return 1
}

find_sdk_root() {
  for candidate in \
    "${DEVECO_SDK_HOME:-}" \
    "${OHOS_BASE_SDK_HOME:-}" \
    "$PROJECT_ROOT/sdk" \
    "$PROJECT_ROOT/.toolchains/openharmony-api20/sdk" \
    "$PROJECT_ROOT/.toolchains/harmony-cli/sdk" \
    "$PROJECT_PARENT/.toolchains/openharmony-api20/sdk" \
    "$PROJECT_PARENT/.toolchains/harmony-cli/sdk" \
    "${DEVECO_HOME:-}/sdk" \
    "${HOME:-}/Library/Huawei/Sdk" \
    "${HOME:-}/Library/Huawei/HarmonyOS/Sdk" \
    "${HOME:-}/Library/OpenHarmony/Sdk" \
    "${HOME:-}/Huawei/Sdk" \
    "${HOME:-}/DevEco-Studio/sdk" \
    '/Applications/DevEco-Studio.app/Contents/sdk' \
    '/Applications/DevEco Studio.app/Contents/sdk' \
    '/opt/DevEco-Studio/sdk' \
    '/opt/deveco-studio/sdk'
  do
    if sdk_root_has_metadata "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

normalize_executable() {
  executable=$1
  case "$executable" in
    /*) printf '%s\n' "$executable" ;;
    *)
      executable_dir=$(CDPATH= cd -P "$(dirname "$executable")" && pwd -P)
      printf '%s/%s\n' "$executable_dir" "$(basename "$executable")"
      ;;
  esac
}

find_hvigor() {
  for candidate in \
    "${HVIGORW:-}" \
    "$PROJECT_ROOT/hvigorw" \
    "$PROJECT_ROOT/hvigor/bin/hvigorw" \
    "$PROJECT_ROOT/bin/hvigorw" \
    "$PROJECT_ROOT/.toolchains/harmony-cli/bin/hvigorw" \
    "$PROJECT_ROOT/.toolchains/harmony-cli/hvigor/bin/hvigorw" \
    "$PROJECT_ROOT/../.toolchains/harmony-cli/bin/hvigorw" \
    "$PROJECT_ROOT/../.toolchains/harmony-cli/hvigor/bin/hvigorw" \
    "${DEVECO_HOME:-}/tools/hvigor/bin/hvigorw" \
    "${HOME:-}/Applications/DevEco-Studio.app/Contents/tools/hvigor/bin/hvigorw" \
    "${HOME:-}/Applications/DevEco Studio.app/Contents/tools/hvigor/bin/hvigorw" \
    '/Applications/DevEco-Studio.app/Contents/tools/hvigor/bin/hvigorw' \
    '/Applications/DevEco Studio.app/Contents/tools/hvigor/bin/hvigorw' \
    "${HOME:-}/DevEco-Studio/tools/hvigor/bin/hvigorw" \
    '/opt/DevEco-Studio/tools/hvigor/bin/hvigorw' \
    '/opt/deveco-studio/tools/hvigor/bin/hvigorw'
  do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      normalize_executable "$candidate"
      return 0
    fi
  done
  if path_candidate=$(command -v hvigorw 2>/dev/null); then
    normalize_executable "$path_candidate"
    return 0
  fi
  return 1
}

if [ -z "${DEVECO_SDK_HOME:-}" ]; then
  DEVECO_SDK_HOME=$(find_sdk_root) || {
    printf '%s\n' 'status=failed' 'reason=missing_sdk'
    exit 1
  }
  export DEVECO_SDK_HOME
fi

if [ -z "${DEVECO_NODE_HOME:-}" ]; then
  NODE_BIN=$(command -v node 2>/dev/null || true)
  if [ -n "$NODE_BIN" ]; then
    DEVECO_NODE_HOME=$(CDPATH= cd -P "$(dirname "$NODE_BIN")/.." && pwd -P)
    export DEVECO_NODE_HOME
  fi
fi

HVIGOR_BIN=$(find_hvigor) || {
  printf '%s\n' 'status=failed' 'reason=missing_hvigor'
  exit 1
}

printf '%s\n' 'stage=build'
BUILD_TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/jetsnack-build.XXXXXX")
cleanup_build_root() {
  if [ -n "${BUILD_TEMP_ROOT:-}" ] && [ -d "$BUILD_TEMP_ROOT" ]; then
    rm -rf "$BUILD_TEMP_ROOT"
  fi
}
trap cleanup_build_root 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

BUILD_ROOT=$BUILD_TEMP_ROOT/project
python3 - "$PROJECT_ROOT" "$BUILD_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
shutil.copytree(
    source,
    destination,
    ignore=shutil.ignore_patterns(
        ".git",
        ".hvigor",
        "build",
        "oh_modules",
        "__pycache__",
    ),
)
PY

BUILD_SCOPE=harmonyos
public_api_base_for_sdk() {
  sdk_root=$1
  metadata=$sdk_root/ets/oh-uni-package.json
  [ -f "$metadata" ] || return 1
  api_version=$(python3 - "$metadata" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    print(json.load(stream).get("apiVersion", ""))
PY
  )
  [ -n "$api_version" ] || return 1
  sdk_parent=$(CDPATH= cd -P "$(dirname "$sdk_root")" && pwd -P)
  [ -d "$sdk_parent/base/$api_version" ] || return 1
  CDPATH= cd -P "$sdk_parent/base" && pwd -P
}

if PUBLIC_API_BASE=$(public_api_base_for_sdk "$DEVECO_SDK_HOME"); then
    python3 - "$BUILD_ROOT/build-profile.json5" "$BUILD_ROOT/entry/src/main/module.json5" <<'PY'
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
    DEVECO_SDK_HOME=$PUBLIC_API_BASE
    OHOS_BASE_SDK_HOME=$PUBLIC_API_BASE
    export DEVECO_SDK_HOME OHOS_BASE_SDK_HOME
    BUILD_SCOPE=public_api_compatibility
fi

if [ -z "${HVIGOR_USER_HOME:-}" ]; then
  if [ -d "$PROJECT_PARENT/.toolchains/hvigor-home" ]; then
    HVIGOR_USER_HOME=$PROJECT_PARENT/.toolchains/hvigor-home
  elif [ -n "${HOME:-}" ] && { [ -d "${HOME:-}/.hvigor" ] || [ -w "${HOME:-}" ]; }; then
    HVIGOR_USER_HOME=${HOME:-}/.hvigor
  else
    HVIGOR_USER_HOME=$BUILD_TEMP_ROOT/.hvigor-user-home
  fi
  export HVIGOR_USER_HOME
fi

HAP_PATH=entry/build/default/outputs/default/entry-default-unsigned.hap
FORMAL_HAP=$PROJECT_ROOT/$HAP_PATH
TEMP_HAP=$BUILD_ROOT/$HAP_PATH
rm -f "$FORMAL_HAP"

# Allow slow CI/agent-backed toolchains ample time while still reclaiming a
# genuinely wedged Hvigor process.  The platform may override this explicitly.
BUILD_TIMEOUT_SECONDS=${VERIFY_BUILD_TIMEOUT_SECONDS:-1800}
case "$BUILD_TIMEOUT_SECONDS" in
  ''|*[!0-9]*)
    printf '%s\n' 'status=failed' 'reason=invalid_build_timeout'
    exit 2
    ;;
esac
[ "$BUILD_TIMEOUT_SECONDS" -gt 0 ] || {
  printf '%s\n' 'status=failed' 'reason=invalid_build_timeout'
  exit 2
}

set +e
(
  cd "$BUILD_ROOT"
  python3 "$PROJECT_ROOT/tools/run_with_timeout.py" \
    --timeout "$BUILD_TIMEOUT_SECONDS" -- \
    "$HVIGOR_BIN" clean assembleHap --mode module \
    -p product=default \
    -p module=entry@default \
    -p buildMode=debug \
    --no-daemon
)
BUILD_EXIT_CODE=$?
set -e
if [ "$BUILD_EXIT_CODE" -eq 124 ]; then
  printf '%s\n' 'status=failed' 'reason=build_timeout' \
    "timeout_seconds=$BUILD_TIMEOUT_SECONDS"
  exit 1
fi
if [ "$BUILD_EXIT_CODE" -ne 0 ]; then
  printf '%s\n' 'status=failed' 'reason=hvigor_failed'
  exit 1
fi

[ -s "$TEMP_HAP" ] || {
  printf '%s\n' "status=failed" "reason=missing_hap" "expected=$HAP_PATH"
  exit 1
}
mkdir -p "$(dirname "$FORMAL_HAP")"
cp "$TEMP_HAP" "$FORMAL_HAP"

if [ "$MODE" = --strict ]; then
  printf '%s\n' 'stage=codelinter'
  find_codelinter() {
    for candidate in \
      "${CODELINTER:-}" \
      "$PROJECT_ROOT/codelinter" \
      "$PROJECT_ROOT/bin/codelinter" \
      "$PROJECT_ROOT/codelinter/bin/codelinter" \
      "$PROJECT_ROOT/.toolchains/harmony-cli/bin/codelinter" \
      "$PROJECT_ROOT/.toolchains/harmony-cli/codelinter/bin/codelinter" \
      "$PROJECT_ROOT/../.toolchains/harmony-cli/bin/codelinter" \
      "$PROJECT_ROOT/../.toolchains/harmony-cli/codelinter/bin/codelinter" \
      "${DEVECO_HOME:-}/tools/codelinter/bin/codelinter" \
      "${HOME:-}/Applications/DevEco-Studio.app/Contents/tools/codelinter/bin/codelinter" \
      "${HOME:-}/Applications/DevEco Studio.app/Contents/tools/codelinter/bin/codelinter" \
      '/Applications/DevEco-Studio.app/Contents/tools/codelinter/bin/codelinter' \
      '/Applications/DevEco Studio.app/Contents/tools/codelinter/bin/codelinter' \
      "${HOME:-}/DevEco-Studio/tools/codelinter/bin/codelinter" \
      '/opt/DevEco-Studio/tools/codelinter/bin/codelinter' \
      '/opt/deveco-studio/tools/codelinter/bin/codelinter'
    do
      if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        normalize_executable "$candidate"
        return 0
      fi
    done
    if path_candidate=$(command -v codelinter 2>/dev/null); then
      normalize_executable "$path_candidate"
      return 0
    fi
    return 1
  }

  CODELINTER_BIN=$(find_codelinter) || {
    printf '%s\n' 'status=failed' 'reason=missing_codelinter'
    exit 1
  }
  LINTER_REPORT=$PROJECT_ROOT/build/reports/codelinter.json
  mkdir -p "$(dirname "$LINTER_REPORT")"
  rm -f "$LINTER_REPORT"
  if ! "$CODELINTER_BIN" \
    -f json \
    -o "$LINTER_REPORT" \
    -e error,warn,suggestion \
    "$PROJECT_ROOT"
  then
    printf '%s\n' 'status=failed' 'reason=codelinter_failed' "report=build/reports/codelinter.json"
    exit 1
  fi
  [ -s "$LINTER_REPORT" ] || {
    printf '%s\n' 'status=failed' 'reason=missing_codelinter_report' 'expected=build/reports/codelinter.json'
    exit 1
  }
fi

printf '%s\n' \
  'stage=completed' \
  'status=passed' \
  "mode=${MODE#--}" \
  "build_scope=$BUILD_SCOPE" \
  "hap=$HAP_PATH"
