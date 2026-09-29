import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFERENCE_DIR = os.path.join(ROOT, "reference")
DATA_DIR = os.path.join(ROOT, "geodesic_dome", "core", "data")

FILENAMES = [
    "domerama_chord_factors.json",
    "domerama_kruschke_chord_factors.json",
    "kruschke_extended_reference.json",
]


def test_bundled_data_matches_reference():
    for name in FILENAMES:
        with open(os.path.join(REFERENCE_DIR, name), "rb") as f:
            ref_bytes = f.read()
        with open(os.path.join(DATA_DIR, name), "rb") as f:
            bundled_bytes = f.read()
        assert ref_bytes == bundled_bytes, "%s differs from reference copy" % name
