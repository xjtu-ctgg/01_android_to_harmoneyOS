#!/usr/bin/env python3
"""Run one command with a deterministic timeout and process-group cleanup."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys


TIMEOUT_EXIT_CODE = 124


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", required=True, type=float)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = arguments.command
    if command and command[0] == "--":
        command = command[1:]
    if arguments.timeout <= 0 or not command:
        parser.error("timeout must be positive and command must be non-empty")

    process = subprocess.Popen(command, start_new_session=True)
    try:
        return process.wait(timeout=arguments.timeout)
    except subprocess.TimeoutExpired:
        terminate_process_group(process)
        return TIMEOUT_EXIT_CODE
    except KeyboardInterrupt:
        terminate_process_group(process)
        return 130


if __name__ == "__main__":
    sys.exit(main())
