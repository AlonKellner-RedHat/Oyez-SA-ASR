#!/usr/bin/env bash
# Install sideloaded VSIX extensions from .devcontainer/vendor using the
# Cursor/VS Code server remote CLI, or by extracting into the server extensions
# dir when the CLI refuses to run (e.g. "Command is only available in WSL or
# inside a Visual Studio Code terminal"). Idempotent. Run from postAttachCommand
# and/or postStartCommand.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="${SCRIPT_DIR}/vendor-extensions.conf"
VENDOR_DIR="${SCRIPT_DIR}/vendor"

# Resolve server extensions directory (Cursor or VS Code).
EXT_DIR=""
for d in /home/vscode/.cursor-server/extensions /home/vscode/.vscode-server/extensions; do
	if [ -d "$d" ]; then
		EXT_DIR="$d"
		break
	fi
done

CODE_CLI=""
for dir in /home/vscode/.cursor-server/bin/*/bin/remote-cli/code /home/vscode/.vscode-server/bin/*/bin/remote-cli/code; do
	[ -x "$dir" ] && CODE_CLI="$dir" && break
done

if [ ! -f "$CONF" ]; then
	exit 0
fi

install_via_cli() {
	local vsix="$1"
	local out
	out="$("$CODE_CLI" --install-extension "$vsix" 2>&1)" || true
	if [[ "$out" == *"Command is only available in WSL or inside a Visual Studio Code terminal"* ]]; then
		return 1
	fi
	return 0
}

# Install by extracting VSIX into server extensions dir (VSIX has extension/ + extension.vsixmanifest).
install_via_extract() {
	local vsix="$1"
	local ext_name="$2"
	local ext_path="${EXT_DIR:?}/${ext_name}"
	[ -z "$EXT_DIR" ] && return 1
	[ -d "$ext_path" ] && return 0
	local tmp
	tmp="$(mktemp -d)"
	if ! (unzip -q -o "$vsix" -d "$tmp" && [ -d "$tmp/extension" ]); then
		rm -rf "$tmp"
		return 1
	fi
	mkdir -p "$ext_path"
	cp -R "$tmp/extension/." "$ext_path/"
	[ -f "$tmp/extension.vsixmanifest" ] && cp "$tmp/extension.vsixmanifest" "$ext_path/"
	rm -rf "$tmp"
	return 0
}

while IFS= read -r line; do
	[[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]] && continue
	read -r publisher extension_id version <<< "$line"
	VSIX="${VENDOR_DIR}/${publisher}.${extension_id}-${version}.vsix"
	EXT_NAME="${publisher}.${extension_id}-${version}"
	if [ ! -f "$VSIX" ]; then
		continue
	fi
	echo "   Installing ${publisher}.${extension_id} from vendor..."
	installed=0
	if [ -n "$CODE_CLI" ]; then
		if install_via_cli "$VSIX"; then
			installed=1
		fi
	fi
	if [ "$installed" -eq 0 ] && [ -n "$EXT_DIR" ]; then
		if install_via_extract "$VSIX" "$EXT_NAME"; then
			installed=1
		fi
	fi
	[ "$installed" -eq 0 ] && echo "   Warning: could not install ${publisher}.${extension_id} (CLI not available in this context; manual install may be required)." >&2
done < "$CONF"
exit 0
