# Vendor extensions (sideloaded)

Extensions here are sideloaded because they are not on the OpenVSX registry
(used by Cursor). Automatic install runs on attach/start via
`postAttachCommand` and optionally `postStartCommand`, using
`.devcontainer/install-vendor-extensions.sh`, which finds the Cursor/VS Code
server CLI under `.cursor-server` or `.vscode-server` and runs
`--install-extension` for each VSIX. Download of missing VSIXs is done in
`postCreateCommand`.

## Config file

The list of extensions is in `.devcontainer/vendor-extensions.conf`. Format: one
extension per line:

```text
publisher extension_id version
```

Comment lines (`#`) and empty lines are ignored. Example:

```text
# Sideloaded extensions (not on OpenVSX). Downloaded to .devcontainer/vendor/
# if missing.
sukumo28 wav-preview 2.6.0
```

VSIX files use the name `{publisher}.{extension_id}-{version}.vsix` (e.g.
`sukumo28.wav-preview-2.6.0.vsix`).

## Behavior

- If a VSIX with that name already exists in this directory, it is installed
  from here.
- If it is missing, the script downloads it from the VS Marketplace into this
  directory, then installs it. Later runs reuse the downloaded file.

## Adding or changing extensions

- **Add an extension:** Append a line to `.devcontainer/vendor-extensions.conf`
  with `publisher extension_id version`.
- **Pin or use offline:** Place the VSIX in this directory with the expected
  name; the script will use it and will not download.

## "End of central directory" or truncated VSIX

The marketplace serves vspackage as **gzip**. If the file was downloaded without
decompression (older script or manual wget/curl), it will be invalid. Delete the
`.vsix` in this folder and rebuild the devcontainer so the script re-downloads
with gzip handling (curl `--compressed` or wget + gunzip).

## Known limitation: audio-preview and very large FLAC files

The **sukumo28.wav-preview** (audio-preview) extension uses a WebAssembly FLAC
decoder. Opening very large FLAC files (e.g. hundreds of MB) can cause:

```text
Aborted(). Build with -sASSERTIONS for more info.
Source: audio-preview
```

This comes from the extension’s WASM code hitting a limit or assertion (e.g.
memory or buffer size). It is an extension limitation, not a devcontainer
issue.

**Workarounds:**

- **Preview a segment from the CLI** (inside the container):
  - `ffmpeg -i file.flac -t 60 -acodec copy segment.flac` then open
    `segment.flac` in the editor for waveform/preview.
  - Or use `ffplay file.flac` to play without opening the full file in the
    extension.
- Use the extension for smaller or shortened files; use CLI tools for
  full-length large FLACs.

## If the extension does not install

- **Automatic install:** The script `install-vendor-extensions.sh` runs on
  attach (and on start if called from postStartCommand). It looks for the
  remote CLI in `~/.cursor-server/bin/*/bin/remote-cli/code` or
  `~/.vscode-server/bin/*/bin/remote-cli/code`.
- **Check Extension Host log:** Output panel → "Log (Extension Host)" or
  "Developer: Show Logs" → "Extension Host". Look for install errors.
- **Manual install:** Ctrl+Shift+P → "Extensions: Install from VSIX..." →
  choose the `.vsix` in this folder, then reload the window.
- **References:** [Stack Overflow: VSIX in devcontainer]
  (<https://stackoverflow.com/questions/56055183>), [Cursor forum]
  (<https://forum.cursor.com/t/extensions-in-devcontainer-not-installing-properly/20436>).
