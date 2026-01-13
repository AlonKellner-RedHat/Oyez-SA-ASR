#!/bin/sh
# This script is called by pre-commit, which passes the path to the commit message file as the first argument ($1).

# Exit immediately if the first argument (the file path) is not provided.
if [ -z "$1" ]; then
    echo "Error: Commit message file path not provided." >&2
    exit 1
fi

git interpret-trailers --if-exists doNothing --trailer "Signed-off-by: $(git config user.name) <$(git config user.email)>" --in-place "$1"
