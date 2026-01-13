#!/usr/bin/env bash
# Extract the tag name using jq (JSON processor)
NVM_VERSION=$(curl --silent "https://api.github.com/repos/nvm-sh/nvm/releases/latest" | jq -r '.tag_name')

# Print the information
echo "Latest nvm Version: $NVM_VERSION"

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh | bash

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

nvm install --lts
npm install -g npm@latest
