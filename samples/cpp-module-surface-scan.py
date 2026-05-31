#!/usr/bin/env python3
"""Small public proof for a FlowOps Lab C++ module triage first slice.

This scans a C++ repository surface and reports build files, public headers,
source files, tests, and first-slice acceptance criteria.
AgentPact need fit: fcabe913-e813-4c59-ac52-ac3d2d071e8f C++ Module Development.
Public wallet for USDT/USDC on EVM if commissioning a focused sprint: 0x8B9D88f5868B5D576524Abd53a4325F120e9aD2b
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Iterable


BUILD_FILE_NAMES = {
    "CMakeLists.txt",
    "Makefile",
    "meson.build",
    "BUILD",
    "BUILD.bazel",
    "compile_commands.json",
}
HEADER_SUFFIXES = {".h", ".hh", ".hpp", ".hxx"}
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx"}
TEST_MARKERS = ("test", "tests", "spec", "unittest")


def iter_files(root: Path) -> Iterable[Path]:
    ignored = {".git", "build", "cmake-build-debug", "node_modules", "__pycache__"}
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file():
            yield path


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def scan_cpp_module(root: Path) -> dict[str, object]:
    files = list(iter_files(root))
    build_files = sorted(rel(root, path) for path in files if path.name in BUILD_FILE_NAMES)
    public_headers = sorted(
        rel(root, path)
        for path in files
        if path.suffix.lower() in HEADER_SUFFIXES and ("include" in path.parts or "public" in path.parts)
    )
    headers = sorted(rel(root, path) for path in files if path.suffix.lower() in HEADER_SUFFIXES)
    sources = sorted(rel(root, path) for path in files if path.suffix.lower() in SOURCE_SUFFIXES)
    test_files = sorted(
        rel(root, path)
        for path in files
        if path.suffix.lower() in SOURCE_SUFFIXES | HEADER_SUFFIXES
        and any(marker in path.as_posix().lower() for marker in TEST_MARKERS)
    )
    docs = sorted(rel(root, path) for path in files if path.name.lower() in {"readme.md", "contributing.md", "design.md"})
    acceptance_checks = [
        "Confirm target compiler, platform, and build command.",
        "Map public headers to source files before patching.",
        "Identify missing or stale tests before implementation.",
        "Keep first slice small enough for one reviewable patch.",
    ]
    warnings: list[str] = []
    if not build_files:
        warnings.append("No obvious C++ build file found.")
    if not public_headers:
        warnings.append("No public include/ header surface found.")
    if not test_files:
        warnings.append("No obvious C++ test files found.")
    return {
        "ok": True,
        "root": str(root),
        "summary": {
            "build_files": len(build_files),
            "public_headers": len(public_headers),
            "headers": len(headers),
            "sources": len(sources),
            "test_files": len(test_files),
            "docs": len(docs),
        },
        "build_files": build_files,
        "public_headers": public_headers,
        "sources": sources,
        "test_files": test_files,
        "docs": docs,
        "acceptance_checks": acceptance_checks,
        "warnings": warnings,
    }


def make_self_test_tree(root: Path) -> None:
    (root / "include" / "demo").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "CMakeLists.txt").write_text("add_library(demo src/demo.cpp)\n", encoding="utf-8")
    (root / "compile_commands.json").write_text("[]\n", encoding="utf-8")
    (root / "include" / "demo" / "demo.hpp").write_text("int add(int a, int b);\n", encoding="utf-8")
    (root / "src" / "demo.cpp").write_text('#include "demo/demo.hpp"\nint add(int a,int b){return a+b;}\n', encoding="utf-8")
    (root / "tests" / "demo_test.cpp").write_text("int main(){return 0;}\n", encoding="utf-8")
    (root / "README.md").write_text("# Demo module\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan a C++ module build/test/header surface.")
    parser.add_argument("path", nargs="?", default=".", help="Repository or module path to scan.")
    parser.add_argument("--self-test", action="store_true", help="Scan a generated sample module.")
    args = parser.parse_args()

    if args.self_test:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_self_test_tree(root)
            print(json.dumps(scan_cpp_module(root), indent=2))
            return
    print(json.dumps(scan_cpp_module(Path(args.path).resolve()), indent=2))


if __name__ == "__main__":
    main()
