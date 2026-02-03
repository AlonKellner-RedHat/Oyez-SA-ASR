# Vendor extensions (sideloaded)

Extensions here are installed in the devcontainer via `postCreateCommand`
because they are not on the OpenVSX registry (used by Cursor).

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
