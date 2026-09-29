import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORE_DIR = os.path.join(ROOT, "geovisual_dome_tools", "core")


def _iter_py_files(base):
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def test_core_never_imports_bpy():
    offenders = []
    for path in _iter_py_files(CORE_DIR):
        with open(path, "r", encoding="utf8") as f:
            text = f.read()
        if "import bpy" in text:
            offenders.append(path)
    assert not offenders, "core modules importing bpy: %s" % offenders
