#!/bin/sh

# Portable, read-only toolchain discovery for the Jetsnack HarmonyOS project.
# The script deliberately does not install tools or alter shell profiles.
set -eu

print_invalid_argument() {
  printf '%s\n' \
    'mode=invalid' \
    'path_persistence=sensitive' \
    'hvigor_status=not_checked' \
    'hvigor_source=none' \
    'hvigor_path=none' \
    'hvigor_version=none' \
    'sdk_status=not_checked' \
    'sdk_source=none' \
    'sdk_path=none' \
    'sdk_api=none' \
    'sdk_version=none' \
    'codelinter_status=not_checked' \
    'codelinter_source=none' \
    'codelinter_path=none' \
    'codelinter_version=none' \
    'hdc_status=not_checked' \
    'hdc_source=none' \
    'hdc_path=none' \
    'hdc_version=none' \
    'status=failed' \
    'reason=invalid_argument'
}

[ "$#" -le 1 ] || {
  print_invalid_argument
  exit 2
}

MODE=strict
case "${1:-}" in
  "") ;;
  --strict) MODE=strict ;;
  --build-only) MODE=build-only ;;
  *)
    print_invalid_argument
    exit 2
    ;;
esac

SCRIPT_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd -P)
PROJECT_ROOT=$(CDPATH= cd -P "$SCRIPT_DIR/.." && pwd -P)
PROJECT_PARENT=$(CDPATH= cd -P "$PROJECT_ROOT/.." && pwd -P)
INVOCATION_DIR=$(pwd -P)
ESCAPE_CHARACTER=$(printf '\033')

PROBE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/jetsnack-preflight.XXXXXX")
cleanup_probe_root() {
  if [ -n "${PROBE_ROOT:-}" ] && [ -d "$PROBE_ROOT" ]; then
    rm -rf "$PROBE_ROOT"
  fi
}
trap cleanup_probe_root 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

format_diagnostic_path() {
  format_path=$1
  format_source=$2

  case "$format_source" in
    repository)
      case "$format_path" in
        "$PROJECT_ROOT")
          printf '%s\n' 'repository:.'
          return 0
          ;;
        "$PROJECT_ROOT"/*)
          printf 'repository:%s\n' "${format_path#"$PROJECT_ROOT"/}"
          return 0
          ;;
        "$PROJECT_PARENT"/*)
          printf 'repository:../%s\n' "${format_path#"$PROJECT_PARENT"/}"
          return 0
          ;;
      esac
      ;;
    standard)
      if [ -n "${HOME:-}" ]; then
        case "$format_path" in
          "${HOME:-}")
            printf '%s\n' 'home:.'
            return 0
            ;;
          "${HOME:-}"/*)
            printf 'home:%s\n' "${format_path#"${HOME:-}"/}"
            return 0
            ;;
        esac
      fi
      ;;
  esac

  printf '%s\n' "$format_path"
}

clean_first_line() {
  # Tool wrappers sometimes emit coloured banners. Keep one stable, printable
  # line so the output remains safe for both humans and key=value parsers.
  printf '%s\n' "$1" \
    | LC_ALL=C sed "s/${ESCAPE_CHARACTER}\\[[0-9;]*[[:alpha:]]//g" \
    | LC_ALL=C awk 'NF { sub(/\r$/, ""); print; exit }'
}

is_failure_banner() {
  case "$1" in
    [Ii][Nn][Vv][Aa][Ll][Ii][Dd]* | \
    [Ee][Rr][Rr][Oo][Rr]* | \
    [Ff][Aa][Ii][Ll][Ee][Dd]* | \
    [Ff][Aa][Tt][Aa][Ll]* | \
    [Ff]ile\ not\ found* | \
    [Cc]ommand\ not\ found*) return 0 ;;
    *) return 1 ;;
  esac
}

begin_tool_probe() {
  PROBE_OK=0
  PROBE_SEEN=0
  PROBE_PATH=none
  PROBE_SOURCE=none
  PROBE_VERSION=none
  PROBE_BAD_PATH=none
  PROBE_BAD_SOURCE=none
}

try_tool_candidate() {
  candidate_path=$1
  candidate_source=$2

  [ "$PROBE_OK" -eq 0 ] || return 0
  [ -n "$candidate_path" ] || return 0
  [ -e "$candidate_path" ] || return 0

  case "$candidate_path" in
    /*) ;;
    *) candidate_path=$INVOCATION_DIR/$candidate_path ;;
  esac

  PROBE_SEEN=1
  if [ ! -f "$candidate_path" ] || [ ! -x "$candidate_path" ]; then
    if [ "$PROBE_BAD_PATH" = none ]; then
      PROBE_BAD_PATH=$(format_diagnostic_path "$candidate_path" "$candidate_source")
      PROBE_BAD_SOURCE=$candidate_source
    fi
    return 0
  fi

  candidate_output=
  if raw_output=$(CDPATH= cd -P "$PROBE_ROOT" && "$candidate_path" --version 2>&1); then
    candidate_output=$(clean_first_line "$raw_output")
  fi
  if [ -z "$candidate_output" ] && raw_output=$(CDPATH= cd -P "$PROBE_ROOT" && "$candidate_path" -v 2>&1); then
    candidate_output=$(clean_first_line "$raw_output")
  fi
  if [ -z "$candidate_output" ] && raw_output=$(CDPATH= cd -P "$PROBE_ROOT" && "$candidate_path" --help 2>&1); then
    candidate_output=$(clean_first_line "$raw_output")
  fi
  if [ -n "$candidate_output" ] && is_failure_banner "$candidate_output"; then
    candidate_output=
  fi

  if [ -n "$candidate_output" ]; then
    PROBE_OK=1
    PROBE_PATH=$(format_diagnostic_path "$candidate_path" "$candidate_source")
    PROBE_SOURCE=$candidate_source
    PROBE_VERSION=$candidate_output
  elif [ "$PROBE_BAD_PATH" = none ]; then
    PROBE_BAD_PATH=$(format_diagnostic_path "$candidate_path" "$candidate_source")
    PROBE_BAD_SOURCE=$candidate_source
  fi
}

finish_tool_probe() {
  if [ "$PROBE_OK" -eq 1 ]; then
    PROBE_STATUS=passed
  elif [ "$PROBE_SEEN" -eq 1 ]; then
    PROBE_STATUS=unusable
    PROBE_PATH=$PROBE_BAD_PATH
    PROBE_SOURCE=$PROBE_BAD_SOURCE
  else
    PROBE_STATUS=missing
  fi
}

SDK_OK=0
SDK_REAL_PATH=none
SDK_PATH=none
SDK_SOURCE=none
SDK_API=none
SDK_VERSION=none

try_sdk_candidate() {
  candidate_root=$1
  candidate_source=$2

  [ "$SDK_OK" -eq 0 ] || return 0
  [ -n "$candidate_root" ] || return 0
  [ -d "$candidate_root" ] || return 0

  best_metadata=
  best_api=
  best_version=

  # SDK roots differ between command-line tools, DevEco Studio and public
  # OpenHarmony packages. All accepted layouts must contain real API metadata.
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
    [ -f "$metadata_file" ] || continue
    metadata_api=$(LC_ALL=C sed -n \
      -e 's/^[[:space:]]*"apiVersion"[[:space:]]*:[[:space:]]*"\([0-9][0-9]*\)"[[:space:]]*,\{0,1\}[[:space:]]*$/\1/p' \
      -e 's/^[[:space:]]*"apiVersion"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\)[[:space:]]*,\{0,1\}[[:space:]]*$/\1/p' \
      "$metadata_file" | LC_ALL=C sed -n '1p')
    case "$metadata_api" in
      ""|*[!0-9]*) continue ;;
    esac
    metadata_version=$(LC_ALL=C sed -n \
      's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)"[[:space:]]*,\{0,1\}[[:space:]]*$/\1/p' \
      "$metadata_file" | LC_ALL=C sed -n '1p')
    [ -n "$metadata_version" ] || metadata_version=unknown

    if [ -z "$best_api" ] || [ "$metadata_api" -gt "$best_api" ]; then
      best_metadata=$metadata_file
      best_api=$metadata_api
      best_version=$metadata_version
    fi
  done

  if [ -n "$best_metadata" ]; then
    SDK_OK=1
    SDK_REAL_PATH=$candidate_root
    SDK_PATH=$(format_diagnostic_path "$candidate_root" "$candidate_source")
    SDK_SOURCE=$candidate_source
    SDK_API=$best_api
    SDK_VERSION=$best_version
  fi
}

# Explicit SDK variables have priority, followed by repository-local and then
# normal DevEco/OpenHarmony installation locations.
try_sdk_candidate "${DEVECO_SDK_HOME:-}" environment
try_sdk_candidate "${OHOS_BASE_SDK_HOME:-}" environment
try_sdk_candidate "$PROJECT_ROOT/sdk" repository
try_sdk_candidate "$PROJECT_ROOT/.toolchains/openharmony-api20/sdk" repository
try_sdk_candidate "$PROJECT_ROOT/.toolchains/harmony-cli/sdk" repository
try_sdk_candidate "$PROJECT_ROOT/../.toolchains/openharmony-api20/sdk" repository
try_sdk_candidate "$PROJECT_ROOT/../.toolchains/harmony-cli/sdk" repository
if [ -n "${DEVECO_HOME:-}" ]; then
  try_sdk_candidate "$DEVECO_HOME/sdk" standard
fi
if [ -n "${HOME:-}" ]; then
  try_sdk_candidate "${HOME:-}/Library/Huawei/Sdk" standard
  try_sdk_candidate "${HOME:-}/Library/Huawei/HarmonyOS/Sdk" standard
  try_sdk_candidate "${HOME:-}/Library/OpenHarmony/Sdk" standard
  try_sdk_candidate "${HOME:-}/Huawei/Sdk" standard
  try_sdk_candidate "${HOME:-}/DevEco-Studio/sdk" standard
fi
try_sdk_candidate '/Applications/DevEco-Studio.app/Contents/sdk' standard
try_sdk_candidate '/Applications/DevEco Studio.app/Contents/sdk' standard
try_sdk_candidate '/opt/DevEco-Studio/sdk' standard
try_sdk_candidate '/opt/deveco-studio/sdk' standard

if [ "$SDK_OK" -eq 1 ]; then
  SDK_STATUS=passed
  # Some official wrappers require this variable even when the SDK was found
  # through a standard or repository-local path.
  if [ -z "${DEVECO_SDK_HOME:-}" ]; then
    DEVECO_SDK_HOME=$SDK_REAL_PATH
    export DEVECO_SDK_HOME
  fi
else
  SDK_STATUS=missing
fi

# Hvigor: explicit executable -> repository wrapper -> PATH -> DevEco paths.
begin_tool_probe
try_tool_candidate "${HVIGORW:-}" environment
try_tool_candidate "$PROJECT_ROOT/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/hvigor/bin/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/bin/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/.toolchains/harmony-cli/bin/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/.toolchains/harmony-cli/hvigor/bin/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/../.toolchains/harmony-cli/bin/hvigorw" repository
try_tool_candidate "$PROJECT_ROOT/../.toolchains/harmony-cli/hvigor/bin/hvigorw" repository
if [ "$PROBE_OK" -eq 0 ] && path_candidate=$(command -v hvigorw 2>/dev/null); then
  try_tool_candidate "$path_candidate" path
fi
if [ -n "${DEVECO_HOME:-}" ]; then
  try_tool_candidate "$DEVECO_HOME/tools/hvigor/bin/hvigorw" standard
fi
if [ -n "${HOME:-}" ]; then
  try_tool_candidate "${HOME:-}/Applications/DevEco-Studio.app/Contents/tools/hvigor/bin/hvigorw" standard
  try_tool_candidate "${HOME:-}/Applications/DevEco Studio.app/Contents/tools/hvigor/bin/hvigorw" standard
fi
try_tool_candidate '/Applications/DevEco-Studio.app/Contents/tools/hvigor/bin/hvigorw' standard
try_tool_candidate '/Applications/DevEco Studio.app/Contents/tools/hvigor/bin/hvigorw' standard
if [ -n "${HOME:-}" ]; then
  try_tool_candidate "${HOME:-}/DevEco-Studio/tools/hvigor/bin/hvigorw" standard
fi
try_tool_candidate '/opt/DevEco-Studio/tools/hvigor/bin/hvigorw' standard
try_tool_candidate '/opt/deveco-studio/tools/hvigor/bin/hvigorw' standard
finish_tool_probe
HVIGOR_STATUS=$PROBE_STATUS
HVIGOR_PATH=$PROBE_PATH
HVIGOR_SOURCE=$PROBE_SOURCE
HVIGOR_VERSION=$PROBE_VERSION

# Code Linter follows the same precedence. A wrapper whose backend is absent
# is reported as unusable because its version/help invocation cannot succeed.
begin_tool_probe
try_tool_candidate "${CODELINTER:-}" environment
try_tool_candidate "$PROJECT_ROOT/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/bin/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/codelinter/bin/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/.toolchains/harmony-cli/bin/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/.toolchains/harmony-cli/codelinter/bin/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/../.toolchains/harmony-cli/bin/codelinter" repository
try_tool_candidate "$PROJECT_ROOT/../.toolchains/harmony-cli/codelinter/bin/codelinter" repository
if [ "$PROBE_OK" -eq 0 ] && path_candidate=$(command -v codelinter 2>/dev/null); then
  try_tool_candidate "$path_candidate" path
fi
if [ -n "${DEVECO_HOME:-}" ]; then
  try_tool_candidate "$DEVECO_HOME/tools/codelinter/bin/codelinter" standard
fi
if [ -n "${HOME:-}" ]; then
  try_tool_candidate "${HOME:-}/Applications/DevEco-Studio.app/Contents/tools/codelinter/bin/codelinter" standard
  try_tool_candidate "${HOME:-}/Applications/DevEco Studio.app/Contents/tools/codelinter/bin/codelinter" standard
fi
try_tool_candidate '/Applications/DevEco-Studio.app/Contents/tools/codelinter/bin/codelinter' standard
try_tool_candidate '/Applications/DevEco Studio.app/Contents/tools/codelinter/bin/codelinter' standard
if [ -n "${HOME:-}" ]; then
  try_tool_candidate "${HOME:-}/DevEco-Studio/tools/codelinter/bin/codelinter" standard
fi
try_tool_candidate '/opt/DevEco-Studio/tools/codelinter/bin/codelinter' standard
try_tool_candidate '/opt/deveco-studio/tools/codelinter/bin/codelinter' standard
finish_tool_probe
CODELINTER_STATUS=$PROBE_STATUS
CODELINTER_PATH=$PROBE_PATH
CODELINTER_SOURCE=$PROBE_SOURCE
CODELINTER_VERSION=$PROBE_VERSION

# HDC is useful for device journeys but is not a compile/lint hard gate.
begin_tool_probe
try_tool_candidate "${HDC:-}" environment
try_tool_candidate "$PROJECT_ROOT/hdc" repository
try_tool_candidate "$PROJECT_ROOT/bin/hdc" repository
try_tool_candidate "$PROJECT_ROOT/.toolchains/openharmony-api20/sdk/toolchains/hdc" repository
try_tool_candidate "$PROJECT_ROOT/../.toolchains/openharmony-api20/sdk/toolchains/hdc" repository
if [ "$SDK_OK" -eq 1 ]; then
  try_tool_candidate "$SDK_REAL_PATH/toolchains/hdc" "$SDK_SOURCE"
fi
if [ "$PROBE_OK" -eq 0 ] && path_candidate=$(command -v hdc 2>/dev/null); then
  try_tool_candidate "$path_candidate" path
fi
if [ -n "${DEVECO_HOME:-}" ]; then
  try_tool_candidate "$DEVECO_HOME/sdk/default/openharmony/toolchains/hdc" standard
fi
if [ -n "${HOME:-}" ]; then
  try_tool_candidate "${HOME:-}/Library/Huawei/Sdk/openharmony/toolchains/hdc" standard
  try_tool_candidate "${HOME:-}/Library/Huawei/HarmonyOS/Sdk/openharmony/toolchains/hdc" standard
  try_tool_candidate "${HOME:-}/DevEco-Studio/sdk/default/openharmony/toolchains/hdc" standard
fi
finish_tool_probe
HDC_STATUS=$PROBE_STATUS
HDC_PATH=$PROBE_PATH
HDC_SOURCE=$PROBE_SOURCE
HDC_VERSION=$PROBE_VERSION

if [ "$MODE" = build-only ]; then
  case "$CODELINTER_STATUS" in
    missing) CODELINTER_STATUS=optional_missing ;;
    unusable) CODELINTER_STATUS=optional_unusable ;;
  esac
fi
case "$HDC_STATUS" in
  missing) HDC_STATUS=optional_missing ;;
  unusable) HDC_STATUS=optional_unusable ;;
esac

FINAL_STATUS=passed
FINAL_REASON=ok
if [ "$HVIGOR_STATUS" != passed ]; then
  FINAL_STATUS=failed
  FINAL_REASON=missing_hvigor
elif [ "$SDK_STATUS" != passed ]; then
  FINAL_STATUS=failed
  FINAL_REASON=missing_sdk
elif [ "$MODE" = strict ] && [ "$CODELINTER_STATUS" != passed ]; then
  FINAL_STATUS=failed
  FINAL_REASON=missing_codelinter
fi

printf '%s\n' \
  "mode=$MODE" \
  'path_persistence=sensitive' \
  "hvigor_status=$HVIGOR_STATUS" \
  "hvigor_source=$HVIGOR_SOURCE" \
  "hvigor_path=$HVIGOR_PATH" \
  "hvigor_version=$HVIGOR_VERSION" \
  "sdk_status=$SDK_STATUS" \
  "sdk_source=$SDK_SOURCE" \
  "sdk_path=$SDK_PATH" \
  "sdk_api=$SDK_API" \
  "sdk_version=$SDK_VERSION" \
  "codelinter_status=$CODELINTER_STATUS" \
  "codelinter_source=$CODELINTER_SOURCE" \
  "codelinter_path=$CODELINTER_PATH" \
  "codelinter_version=$CODELINTER_VERSION" \
  "hdc_status=$HDC_STATUS" \
  "hdc_source=$HDC_SOURCE" \
  "hdc_path=$HDC_PATH" \
  "hdc_version=$HDC_VERSION" \
  "status=$FINAL_STATUS" \
  "reason=$FINAL_REASON"

[ "$FINAL_STATUS" = passed ]
