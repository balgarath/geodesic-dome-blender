"""Shared test helpers (not collected as tests themselves)."""


def nearest_match_pairs(computed_cfs, reference_cfs):
    """Greedy global nearest-neighbor pairing between two lists of chord
    factors, rather than a sequential first-within-tolerance search (which
    can mis-pair when two values are close together). Returns a list of
    (ref_index, computed_index, distance) tuples, each index used at most
    once, ordered by increasing distance as the pairs were chosen.
    """
    candidates = []
    for ri, rcf in enumerate(reference_cfs):
        for ci, ccf in enumerate(computed_cfs):
            candidates.append((abs(ccf - rcf), ri, ci))
    candidates.sort(key=lambda t: t[0])
    used_r, used_c = set(), set()
    pairs = []
    for d, ri, ci in candidates:
        if ri in used_r or ci in used_c:
            continue
        used_r.add(ri)
        used_c.add(ci)
        pairs.append((ri, ci, d))
    return pairs
