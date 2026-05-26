#!/usr/bin/env python3
"""Install/uninstall Linguist hook into Claude Code."""

import argparse
import json
import os
import stat
import subprocess
import sys

LINGUIST_DIR = os.path.dirname(os.path.abspath(__file__))
CLAUDE_DIR = os.path.expanduser("~/.claude")
HOOKS_DIR = os.path.join(CLAUDE_DIR, "hooks")
HOOK_FILE = os.path.join(HOOKS_DIR, "speak-response.sh")
SETTINGS_FILE = os.path.join(CLAUDE_DIR, "settings.json")

HOOK_TEMPLATE = '''#!/bin/bash

LINGUIST_DIR="{linguist_dir}"
LOCKDIR="/tmp/linguist-speak.lock"

if [ "${{LINGUIST_SPEAK:-1}}" = "0" ]; then
  exit 0
fi

INPUT=$(cat /dev/stdin)

STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$STOP_ACTIVE" = "true" ]; then
  exit 0
fi

RESPONSE=$(echo "$INPUT" | jq -r '.response_text // .last_assistant_message // empty')
if [ -z "$RESPONSE" ]; then
  exit 0
fi

EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "Stop"')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')

if [ "$EVENT" = "SubagentStop" ] && [ -n "$AGENT_TYPE" ]; then
  SPEAKER="$AGENT_TYPE agent says:"
else
  SPEAKER="Blitzy says:"
fi

CONDENSED=$(cd "$LINGUIST_DIR" && .venv/bin/python -c '
import sys
sys.path.insert(0, ".")
from src.condense import condense
text = sys.stdin.read()
result = condense(text)
if result:
    print(result)
' <<< "$RESPONSE")

if [ -z "$CONDENSED" ]; then
  exit 0
fi

SPOKEN="$SPEAKER $CONDENSED"
TAG="btw-$(date +%Y%m%d-%H%M%S)-$$"

acquire_lock() {{
  local attempts=0
  while ! mkdir "$LOCKDIR" 2>/dev/null; do
    attempts=$((attempts + 1))
    if [ $attempts -ge 120 ]; then
      rm -rf "$LOCKDIR"
      mkdir "$LOCKDIR" 2>/dev/null
      break
    fi
    sleep 1
  done
}}

release_lock() {{
  rm -rf "$LOCKDIR"
}}

acquire_lock
trap release_lock EXIT

cd "$LINGUIST_DIR" && source .venv/bin/activate && \\
  python main.py speak --text "$SPOKEN" --tag "$TAG" > /dev/null 2>&1 && \\
  afplay "$LINGUIST_DIR/archive/$TAG.wav" 2>/dev/null

exit 0
'''

HOOK_ENTRY = {
    "matcher": "",
    "hooks": [
        {
            "type": "command",
            "command": HOOK_FILE,
            "timeout": 120
        }
    ]
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def has_hook(settings, event):
    hooks = settings.get("hooks", {}).get(event, [])
    return any(
        any(h.get("command", "") == HOOK_FILE for h in entry.get("hooks", []))
        for entry in hooks
    )


def add_hook(settings, event):
    if "hooks" not in settings:
        settings["hooks"] = {}
    if event not in settings["hooks"]:
        settings["hooks"][event] = []
    if not has_hook(settings, event):
        settings["hooks"][event].append(HOOK_ENTRY)


def remove_hook(settings, event):
    hooks = settings.get("hooks", {}).get(event, [])
    settings["hooks"][event] = [
        entry for entry in hooks
        if not any(h.get("command", "") == HOOK_FILE for h in entry.get("hooks", []))
    ]
    if not settings["hooks"][event]:
        del settings["hooks"][event]
    if not settings["hooks"]:
        del settings["hooks"]


def install():
    errors = []
    if not os.path.exists(CLAUDE_DIR):
        errors.append(f"{CLAUDE_DIR} not found. Install Claude Code first.")
    if not os.path.exists(os.path.join(LINGUIST_DIR, ".venv")):
        errors.append(f"No .venv found. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    if subprocess.run(["which", "jq"], capture_output=True).returncode != 0:
        errors.append("jq not found. Run: brew install jq")
    if errors:
        for e in errors:
            print(f"  Error: {e}")
        return False

    os.makedirs(HOOKS_DIR, exist_ok=True)

    hook_content = HOOK_TEMPLATE.format(linguist_dir=LINGUIST_DIR)
    with open(HOOK_FILE, "w") as f:
        f.write(hook_content)
    os.chmod(HOOK_FILE, os.stat(HOOK_FILE).st_mode | stat.S_IEXEC)

    settings = load_settings()
    add_hook(settings, "Stop")
    add_hook(settings, "SubagentStop")
    save_settings(settings)

    print("Linguist hook installed:")
    print(f"  Hook: {HOOK_FILE}")
    print(f"  Linguist: {LINGUIST_DIR}")
    print(f"  Events: Stop, SubagentStop")
    print(f"  Disable: LINGUIST_SPEAK=0")
    return True


def uninstall():
    if os.path.exists(HOOK_FILE):
        os.remove(HOOK_FILE)
        print(f"  Removed {HOOK_FILE}")

    if os.path.exists(SETTINGS_FILE):
        settings = load_settings()
        for event in ["Stop", "SubagentStop"]:
            if has_hook(settings, event):
                remove_hook(settings, event)
                print(f"  Removed {event} hook from settings")
        save_settings(settings)

    print("Linguist hook uninstalled.")


def main():
    parser = argparse.ArgumentParser(description="Install/uninstall Linguist Claude Code hook")
    parser.add_argument("action", choices=["install", "uninstall"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "install":
        install()
    elif args.action == "uninstall":
        uninstall()


if __name__ == "__main__":
    main()
