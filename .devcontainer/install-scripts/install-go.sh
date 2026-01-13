#!/usr/bin/env bash

# Dynamically determine the latest stable Go version by querying the official site
GOLANG_VERSION="$(curl -sSL "https://go.dev/VERSION?m=text" | grep go | sed 's/go//')"
echo "Latest go Version: $GOLANG_VERSION"

# Determine architecture and map it to Go's naming convention
case "$(uname -m)" in
    "x86_64") ARCH="amd64" ;;
    "aarch64") ARCH="arm64" ;;
    *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

echo "Installing go for architecture: ${ARCH}"

# Download the correct Go binary for the detected architecture
curl -fsSL "https://go.dev/dl/go${GOLANG_VERSION}.linux-${ARCH}.tar.gz" -o /tmp/go.tar.gz

# Extract the archive to /usr/local
mkdir -p $HOME/.local/
tar -xzf /tmp/go.tar.gz -C $HOME/.local/

# Clean up downloaded files and apt cache
rm /tmp/go.tar.gz
