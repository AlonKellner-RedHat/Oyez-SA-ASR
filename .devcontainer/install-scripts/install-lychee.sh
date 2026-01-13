#!/usr/bin/env bash
# Determine architecture and map it to lychee's naming convention
case "$(uname -m)" in
    "x86_64") LYCHEE_ARCH="x86_64-unknown-linux-gnu" ;;
    "aarch64") LYCHEE_ARCH="aarch64-unknown-linux-gnu" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac
echo "Detected architecture: $ARCH"

# Construct the download URL and filename
FILENAME="lychee-${LYCHEE_ARCH}.tar.gz"
DOWNLOAD_URL="https://github.com/lycheeverse/lychee/releases/latest/download/${FILENAME}"
echo "Downloading lychee: ${DOWNLOAD_URL}..."

# Download the tarball using curl
curl -L "$DOWNLOAD_URL" -o /tmp/lychee.tar.gz
echo "Extracting binary..."

# Extract the lychee binary from the tarball
mkdir -p $HOME/.local/bin/
tar -xzf /tmp/lychee.tar.gz -C $HOME/.local/bin/
rm /tmp/lychee.tar.gz
