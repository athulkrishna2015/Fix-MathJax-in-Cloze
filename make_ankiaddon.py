import argparse
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from bump import bump_version as bump_semver
from bump import read_current_version, sync_version, validate_version

ADDON_NAME = "Fix_MathJax_in_Cloze"
ADDON_DIR = "addon"
EXCLUDE_DIRS = {"__pycache__", ".git", ".vscode", ".github", "tests"}
EXCLUDE_EXTS = {".ankiaddon", ".pyc"}
EXCLUDE_FILES = {"meta.json", ".gitignore", ".gitmodules", "mypy.ini"}


def artifact_names(
    addon_name: str,
    version: str,
    when: datetime | None = None,
) -> tuple[str, str]:
    dt = when or datetime.today()
    timestamp = dt.strftime("%Y%m%d%H%M")
    base = f"{addon_name}_v{version}_{timestamp}"
    return f"{base}.zip", f"{base}.ankiaddon"


def bump_version(addon_path: Path | None = None) -> int:
    target = addon_path or Path(ADDON_DIR)
    return bump_semver(target)


def resolve_build_version(
    addon_path: Path,
    explicit_version: str | None = None,
) -> str:
    if explicit_version is None:
        code = bump_version(addon_path)
        if code != 0:
            raise RuntimeError("failed to bump version")
        return read_current_version(addon_path)

    version = validate_version(explicit_version)
    sync_version(version, addon_path)
    print(f"Using explicit version: {version}")
    return version


def create_ankiaddon(explicit_version: str | None = None) -> int:
    root_dir = Path(__file__).resolve().parent
    addon_path = root_dir / ADDON_DIR

    if not addon_path.exists():
        print(f"Error: {ADDON_DIR} directory not found.")
        return 1

    try:
        build_version = resolve_build_version(addon_path, explicit_version)
    except Exception as exc:
        print(f"Error: Could not prepare build version: {exc}")
        return 1

    zip_name, final_name = artifact_names(ADDON_NAME, build_version)
    zip_path = root_dir / zip_name
    final_path = root_dir / final_name

    print(f"Creating {final_name} from {ADDON_DIR}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(addon_path):
            dirs[:] = [directory for directory in dirs if directory not in EXCLUDE_DIRS]

            for file_name in files:
                file_path = Path(root) / file_name
                if file_name in EXCLUDE_FILES or file_path.suffix in EXCLUDE_EXTS:
                    continue

                archive_name = file_path.relative_to(addon_path)
                zipf.write(file_path, archive_name)

    if final_path.exists():
        final_path.unlink()
    zip_path.rename(final_path)
    print(f"Successfully created: {final_name}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a .ankiaddon package. "
            "If no version is provided, the patch version is auto-bumped first."
        )
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Optional explicit version (major.minor.patch or major.minor) to set before packaging.",
    )
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return create_ankiaddon(args.version)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
