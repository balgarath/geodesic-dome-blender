# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Ledge / Geovisual Creations
"""Geodesic Dome Builder, Blender extension entry point."""
from . import operators
from . import panel


def register():
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
