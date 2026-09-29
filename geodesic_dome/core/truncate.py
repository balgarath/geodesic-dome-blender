"""Truncation, fractions, aliases, dome extraction.

Design.md 4.3.
"""
import math

# Legacy domerama fraction names that do not come from simple reduction.
_LEGACY_ALIASES = {
    (4, 9): "3/8",
    (5, 9): "5/8",
    (7, 15): "3/8",
    (8, 15): "5/8",
}


def dome_edges(mesh, k):
    """Edges of the dome keeping triangle rows 1..k (face row = max vertex row)."""
    es = set()
    for (a, b, c) in mesh.faces:
        if max(mesh.row[a], mesh.row[b], mesh.row[c]) <= k:
            for u, v in ((a, b), (b, c), (c, a)):
                es.add((min(u, v), max(u, v)))
    return sorted(es)


def dome_faces(mesh, k):
    """Faces with max vertex row <= k."""
    out = []
    for (a, b, c) in mesh.faces:
        if max(mesh.row[a], mesh.row[b], mesh.row[c]) <= k:
            out.append((a, b, c))
    return out


def base_ring(mesh, k, edges):
    """Row-k vertices that are used by at least one kept edge."""
    used = set()
    for (u, v) in edges:
        used.add(u)
        used.add(v)
    return sorted(i for i in used if mesh.row[i] == k)


def fraction_alias(k, denom):
    """Return an alias label for k/denom, or None.

    Legacy domerama names win when present; otherwise the reduced fraction
    is returned when it differs from k/denom (gcd > 1). Full sphere
    (k == denom) and fractions with no alias return None.
    """
    if k == denom:
        return None
    legacy = _LEGACY_ALIASES.get((k, denom))
    if legacy is not None:
        return legacy
    g = math.gcd(k, denom)
    if g > 1:
        return "%d/%d" % (k // g, denom // g)
    return None


def base_level_info(mesh_positions, base_verts):
    """(level, z_spread) for the given base vertex positions.

    level = True iff z spread < 1e-9.
    """
    if not base_verts:
        return True, 0.0
    zs = [mesh_positions[i][2] for i in base_verts]
    spread = max(zs) - min(zs)
    return spread < 1e-9, spread
