# Fix MathJax in Cloze - Development

This file keeps the contributor-facing setup, packaging, and versioning notes for this add-on.

## Project Layout

- `addon/__init__.py`: add-on logic, cloze parser, menu hooks, config dialog, and Support tab UI.
- `addon/config.json`: default add-on configuration shipped with the package.
- `addon/manifest.json`: add-on metadata. Version fields are added and synced by `bump.py`.
- `addon/VERSION`: canonical package version written by `bump.py` after the first version sync.
- `addon/Support/`: QR images used in the Support tab.
- `bump.py`: version validation, normalization, syncing, and semantic version bumping.
- `make_ankiaddon.py`: packaging helper for building the distributable `.ankiaddon` archive.

## Versioning

The packaging scripts use semantic versions in `major.minor.patch` form.

- `bump.py` accepts `major`, `minor`, and `patch` bumps.
- A short form like `1.4` is normalized to `1.4.0` when you pass an explicit version.
- `sync_version()` writes the chosen version to:
  - `addon/manifest.json` keys `version` and `human_version`
  - `addon/VERSION`
- If no version metadata exists yet, the first implicit bump starts from `0.0.0`.

## Common Commands

Bump the patch version:

```shell
python bump.py
```

Bump a specific part:

```shell
python bump.py minor
python bump.py major
```

Set an explicit version without incrementing:

```shell
python bump.py 1.2.0
python bump.py 1.2
```

Build the `.ankiaddon` and auto-bump patch first:

```shell
python make_ankiaddon.py
```

Build with an explicit version:

```shell
python make_ankiaddon.py 1.5.0
```

## Packaging Behavior

`make_ankiaddon.py` packages files from `addon/` and creates artifacts named like:

```text
Fix_MathJax_in_Cloze_v<major.minor.patch>_<YYYYMMDDHHMM>.ankiaddon
```

Current packaging rules:

- Includes the contents of `addon/` at the archive root.
- Excludes `__pycache__`, `.git`, `.vscode`, `.github`, and `tests` directories.
- Excludes `.pyc`, `.ankiaddon`, `meta.json`, `.gitignore`, `.gitmodules`, and `mypy.ini`.

## Local Testing

One simple workflow is to symlink `addon/` into your Anki add-ons folder.

Linux:

```shell
ln -s "$(pwd)/addon" ~/.local/share/Anki2/addons21/fix_mathjax_in_cloze_dev
```

Windows (PowerShell as admin):

```powershell
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\Anki2\addons21\fix_mathjax_in_cloze_dev" -Target "$pwd\addon"
```
