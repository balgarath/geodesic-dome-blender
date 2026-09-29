"""Compare the shipped build_dome(), at its PRODUCTION default merge
tolerance (no override), against the reference JSONs for every documented
Class I variant (1V-8V) and all 4 Kruschke variants. Uses nearest-match
pairing (tests/_helpers.py) rather than a sequential first-within-tolerance
search, and checks strut-type counts explicitly.
"""
import json
import os

from core.build import build_dome
from _helpers import nearest_match_pairs

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "geodesic_dome", "core", "data")

with open(os.path.join(DATA, "domerama_chord_factors.json"), encoding="utf8") as f:
    CLASSI_REF = json.load(f)
with open(os.path.join(DATA, "domerama_kruschke_chord_factors.json"), encoding="utf8") as f:
    KRU_REF = json.load(f)


def _tol_for(cf):
    s = "%r" % cf
    dec = len(s.split(".")[1]) if "." in s else 0
    return 1.0 * 10 ** (-dec) + 5e-6


# (frequency, k) for each documented Class I variant, and the domerama
# (frequency label, fraction label) key to find it in the reference JSON.
CLASS_I_CASES = [
    (1, 2, "1V", "2/3"),
    (2, 3, "2V", "1/2"),
    (3, 4, "3V", "3/8"),
    (3, 5, "3V", "5/8"),
    (4, 6, "4V", "1/2"),
    (5, 7, "5V", "7/15"),
    (5, 8, "5V", "8/15"),
    (6, 9, "6V", "1/2"),
    (7, 10, "7V", "10/21"),
    (8, 12, "8V", None),
]

# domerama displays these as one merged row; the true, physically distinct
# split is documented (design.md 5.1 notes) and verified in test_class1.py.
_KNOWN_SPLITS = {
    (7, 10): {"J": [(0.17585131, 60), (0.17589689, 10)]},
    (8, 12): {"N": [(0.15636158, 60), (0.15638647, 30)]},
}


def _corrected_reference(frequency, k, ref_struts):
    """(cfs, counts) for the reference rows, with known site-merged rows
    replaced by their two true physically distinct values."""
    splits = _KNOWN_SPLITS.get((frequency, k), {})
    cfs, counts = [], []
    for row in ref_struts:
        if row.get("chord_factor") is None:
            continue
        if row["label"] in splits:
            for cf, c in splits[row["label"]]:
                cfs.append(cf)
                counts.append(c)
        else:
            cfs.append(row["chord_factor"])
            counts.append(row.get("count"))
    return cfs, counts


def test_known_splits_sum_to_site_merged_counts():
    # The two true-value pairs in _KNOWN_SPLITS must add up to exactly the
    # count domerama's single merged row shows (J: 70, N: 90), or the
    # "corrected reference" used above would silently misrepresent what
    # domerama actually publishes.
    site_counts = {}
    for dome in CLASSI_REF["domes"]:
        if dome["method"] != "Class I Method 1":
            continue
        for row in dome["struts"]:
            if row["label"] in ("J", "N") and row.get("count"):
                site_counts.setdefault((dome["frequency"], row["label"]), row["count"])

    assert site_counts.get(("7V", "J")) == 70
    assert site_counts.get(("8V", "N")) == 90

    j_split_sum = sum(c for _cf, c in _KNOWN_SPLITS[(7, 10)]["J"])
    n_split_sum = sum(c for _cf, c in _KNOWN_SPLITS[(8, 12)]["N"])
    assert j_split_sum == site_counts[("7V", "J")] == 70
    assert n_split_sum == site_counts[("8V", "N")] == 90


def test_class1_production_defaults_vs_domerama():
    for n, k, freq_label, fraction_label in CLASS_I_CASES:
        ref_struts = None
        for dome in CLASSI_REF["domes"]:
            if dome["method"] != "Class I Method 1":
                continue
            if dome["frequency"] == freq_label and dome["fraction"] == fraction_label:
                if all(s.get("chord_factor") is not None for s in dome["struts"]):
                    ref_struts = dome["struts"]
                    break
        assert ref_struts is not None, "no usable reference for %s %s" % (freq_label, fraction_label)

        ref_cfs, ref_counts = _corrected_reference(n, k, ref_struts)

        geometry = build_dome("CLASS_I", n, k)  # production defaults
        computed = geometry.report.strut_types
        computed_cfs = [st.chord_factor for st in computed]

        assert len(computed) == len(ref_cfs), (
            "%s %s: got %d strut types, expected %d (corrected for known "
            "site-merged rows)" % (freq_label, fraction_label, len(computed), len(ref_cfs)))

        pairs = nearest_match_pairs(computed_cfs, ref_cfs)
        assert len(pairs) == len(ref_cfs), "%s %s: nearest-match pairing left unmatched rows" % (
            freq_label, fraction_label)
        for ri, ci, d in pairs:
            tol = _tol_for(ref_cfs[ri])
            assert d <= tol, "%s %s: nearest match distance %.2e exceeds tolerance %.2e (ref cf %.8f)" % (
                freq_label, fraction_label, d, tol, ref_cfs[ri])
            if ref_counts[ri] is not None:
                assert computed[ci].count == ref_counts[ri], (
                    "%s %s: count %d vs reference %d for cf %.8f"
                    % (freq_label, fraction_label, computed[ci].count, ref_counts[ri], ref_cfs[ri]))


KRU_CASES = [(3, 4), (3, 5), (4, 5), (4, 7)]


def test_kruschke_production_defaults_vs_domerama():
    for n, k in KRU_CASES:
        ref_struts = None
        for dome in KRU_REF["domes"]:
            if dome["frequency"] == n and {(3, 4): "4/9", (3, 5): "5/9", (4, 5): "5/12", (4, 7): "7/12"}[(n, k)] == dome["fraction"]:
                ref_struts = dome["struts"]
                break
        assert ref_struts is not None

        ref_cfs = [s["chord_factor"] for s in ref_struts]
        ref_counts = [s["count"] for s in ref_struts]

        geometry = build_dome("KRUSCHKE", n, k)  # production defaults
        computed = geometry.report.strut_types
        computed_cfs = [st.chord_factor for st in computed]

        assert len(computed) == len(ref_cfs), "%dV k=%d: got %d types, expected %d" % (
            n, k, len(computed), len(ref_cfs))

        pairs = nearest_match_pairs(computed_cfs, ref_cfs)
        assert len(pairs) == len(ref_cfs)
        for ri, ci, d in pairs:
            assert d <= 6e-6, "%dV k=%d: nearest match distance %.2e too large" % (n, k, d)
            assert computed[ci].count == ref_counts[ri], "%dV k=%d: count %d vs reference %d" % (
                n, k, computed[ci].count, ref_counts[ri])
