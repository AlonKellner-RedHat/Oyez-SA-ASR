#!/bin/bash

# --- Script to wrap the 'claude' CLI tool with custom exit code logic ---

# Skip if there are no changes to review
if [[ -z "$(git diff HEAD)" ]]; then
  echo "No changes to review, skipping claude-review."
  exit 0
fi

# Execute the command, capturing its combined standard output and standard error.
# The exit code is captured immediately after the command runs.
output=$(claude -p "/pre-commit" 2>&1)
exit_code=$?

# Always print the original output from the command so the user can see it.
echo "$output" | glow -

# --- Main Logic ---

# 1. If exit code is 1 (error) or 127 (claude missing), exit with 0 (success override).
if [[ ($exit_code -eq 1) || ($exit_code -eq 127) ]]; then
  # This is the special case you want to treat as success.
  exit 0

# 2. If the exit code is non-zero (and wasn't the case above), propagate that error code.
elif [[ $exit_code -ne 0 ]]; then
  # For any other error, pass its exit code along.
  exit $exit_code

elif [[ ("$output" == *"[CRITICAL]"*) || ("$output" == *"[SUGGESTION]"*) || ("$output" == *"[FIXED]"*) ]]; then
  exit 1
else
  exit 0
fi
