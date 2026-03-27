import argparse
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
SHORT_VERSION_RE = re.compile(r"^\d+\.\d+$")
BUMP_PART_ALIASES = {
    "major": "major",
    "minor": "minor",
    "patch": "patch",
    "path": "patch",
}
DEFAULT_BASE_VERSION = "0.0.0"


def normalize_version(version_string: str) -> str:
    version = (version_string or "").strip()
    if SHORT_VERSION_RE.fullmatch(version):
        return f"{version}.0"
    return version


def validate_version(version_string: str) -> str:
    normalized = normalize_version(version_string)
    if not VERSION_RE.fullmatch(normalized):
        raise ValueError(
            f"Invalid version '{version_string}'. Expected format: major.minor.patch"
        )
    return normalized


def sync_version(version_string: str, addon_root: Path) -> None:
    version = validate_version(version_string)
    if not addon_root.is_dir():
        raise FileNotFoundError(f"Addon directory not found: {addon_root}")

    manifest_path = addon_root / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    manifest["version"] = version
    manifest["human_version"] = version
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    version_path = addon_root / "VERSION"
    version_path.write_text(f"{version}\n", encoding="utf-8")


def normalize_bump_part(part: str) -> str:
    normalized = (part or "").strip().lower()
    mapped = BUMP_PART_ALIASES.get(normalized)
    if not mapped:
        valid = ", ".join(sorted(key for key in BUMP_PART_ALIASES if key != "path"))
        raise ValueError(f"Invalid bump part '{part}'. Expected one of: {valid}")
    return mapped


def increment_version(version_string: str, bump_part: str = "patch") -> str:
    try:
        major, minor, patch = map(int, version_string.split("."))
    except ValueError as exc:
        raise ValueError(
            f"Invalid version '{version_string}'. Expected major.minor.patch"
        ) from exc

    part = normalize_bump_part(bump_part)
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


def read_current_version(addon_dir: Path) -> str:
    version_file = addon_dir / "VERSION"
    if version_file.exists():
        return validate_version(version_file.read_text(encoding="utf-8").strip())

    manifest_file = addon_dir / "manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for key in ("human_version", "version"):
            value = str(manifest.get(key, "")).strip()
            if not value:
                continue
            try:
                return validate_version(value)
            except ValueError:
                continue

    return DEFAULT_BASE_VERSION


def bump_version(addon_dir: Path = Path("addon"), bump_part: str = "patch") -> int:
    try:
        current_version = read_current_version(addon_dir)
        part = normalize_bump_part(bump_part)
        new_version = increment_version(current_version, part)
        print(f"Bumping {part} version: {current_version} -> {new_version}")
        sync_version(new_version, addon_dir)
        print(f"Successfully updated manifest.json and VERSION to {new_version}")
        return 0
    except Exception as exc:
        print(f"Failed to bump version: {exc}")
        return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Set an explicit add-on version or bump major, minor, or patch. "
            "Default action is a patch bump."
        )
    )
    parser.add_argument(
        "value",
        nargs="?",
        default="patch",
        help="Explicit version (major.minor.patch or major.minor) or bump part: major, minor, patch.",
    )
    parser.add_argument(
        "--addon-dir",
        default="addon",
        help="Path to the addon directory (default: addon).",
    )
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    addon_dir = Path(args.addon_dir)

    try:
        normalized = normalize_bump_part(args.value)
    except ValueError:
        version = validate_version(args.value)
        sync_version(version, addon_dir)
        print(f"Set version to {version}")
        return 0

    return bump_version(addon_dir, normalized)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
