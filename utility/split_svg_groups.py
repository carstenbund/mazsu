"""Tools for splitting an SVG into multiple files based on ``<g>`` groups."""

from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional
import xml.etree.ElementTree as ET


def _tag_name(element: ET.Element) -> str:
    """Return the local tag name without the XML namespace."""
    if "}" in element.tag:
        return element.tag.split("}", 1)[1]
    return element.tag


def _is_group(element: ET.Element) -> bool:
    """Return ``True`` if *element* is an SVG group element."""
    return _tag_name(element) == "g"


def _deepcopy(element: ET.Element) -> ET.Element:
    """Return a deep copy of an :class:`~xml.etree.ElementTree.Element`."""
    return copy.deepcopy(element)


def _slugify(value: str) -> str:
    """Create a filesystem friendly slug from ``value``."""
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\-_.]", "", value)
    return value or "group"


def split_svg_by_groups(
    svg_path: Path,
    output_dir: Path,
    *,
    include_non_group_children: bool = True,
) -> List[Path]:
    """Split *svg_path* into individual SVG files per top-level ``<g>`` group."""

    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(svg_path)
    root = tree.getroot()

    groups: List[ET.Element] = [child for child in root if _is_group(child)]

    if not groups:
        raise ValueError(f"No <g> groups found in {svg_path}")

    base_name = svg_path.stem
    produced_files: List[Path] = []

    for index, group in enumerate(groups, start=1):
        group_id = group.attrib.get("id")
        suffix = _slugify(group_id) if group_id else f"group-{index}"
        filename = f"{base_name}_{suffix}.svg"
        out_path = output_dir / filename

        new_root = ET.Element(root.tag, root.attrib)

        for child in root:
            if _is_group(child):
                if child is group:
                    new_root.append(_deepcopy(child))
            elif include_non_group_children:
                new_root.append(_deepcopy(child))

        new_tree = ET.ElementTree(new_root)
        new_tree.write(out_path, encoding="utf-8", xml_declaration=True)
        produced_files.append(out_path)

    return produced_files


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split an SVG into one file per top-level <g> group.",
    )
    parser.add_argument("svg", type=Path, help="Path to the source SVG file")
    parser.add_argument(
        "output", type=Path, help="Directory where split SVGs will be written"
    )
    parser.add_argument(
        "--no-common-elements",
        dest="include_non_group_children",
        action="store_false",
        help="Do not include non-group elements (e.g. backgrounds, defs) in outputs",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)

    try:
        produced = split_svg_by_groups(
            args.svg,
            args.output,
            include_non_group_children=args.include_non_group_children,
        )
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for path in produced:
        print(path)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    raise SystemExit(main())
