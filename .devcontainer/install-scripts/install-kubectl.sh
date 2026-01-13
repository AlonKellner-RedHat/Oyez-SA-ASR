#!/usr/bin/env bash

case "$(uname -m)" in
    "x86_64") ARCH="amd64" ;;
    "aarch64") ARCH="arm64" ;;
    *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

echo "Installing kubectl for architecture: ${ARCH}"

# Download the correct kubectl binary for the detected architecture
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl"
install -o vscode -g vscode -m 0755 kubectl $HOME/.local/bin/kubectl
echo 'source <(kubectl completion zsh)' >> ~/.zshrc
