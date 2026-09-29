"""Geodesic Dome Builder, Blender extension entry point."""
from . import operators


def register():
    operators.register()


def unregister():
    operators.unregister()
