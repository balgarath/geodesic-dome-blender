"""Geodesic Dome Builder, Blender extension entry point."""
from . import operators
from . import panel


def register():
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
