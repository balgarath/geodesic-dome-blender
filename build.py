#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Edge / Geovisual Creations
"""Build the installable extension zip.

Reads the version from geodesic_dome/blender_manifest.toml and zips the
CONTENTS of geodesic_dome/ (manifest at the zip root) plus the repo-root
LICENSE file to dist/geodesic_dome_builder-<version>.zip. Excludes
__pycache__.
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "geodesic_dome")
DIST = os.path.join(HERE, "dist")
MANIFEST = os.path.join(SRC, "blender_manifest.toml")
LICENSE = os.path.join(HERE, "LICENSE")


def read_version():
    with open(MANIFEST, encoding="utf8") as f:
        text = f.read()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise SystemExit("Could not find version in %s" % MANIFEST)
    return m.group(1)


def build():
    version = read_version()
    os.makedirs(DIST, exist_ok=True)
    out_path = os.path.join(DIST, "geodesic_dome_builder-%s.zip" % version)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(SRC):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, SRC)
                zf.write(full, rel.replace(os.sep, "/"))
        if os.path.exists(LICENSE):
            zf.write(LICENSE, "LICENSE")

    print(out_path)
    return out_path


if __name__ == "__main__":
    build()
