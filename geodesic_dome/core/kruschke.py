"""Kruschke construction (exact 3V/4V) and extended leveling (5V/6V).

Design.md 5.2, 5.4. Ported from reference/verify_geometry.py.
"""
import math
from collections import defaultdict

from .icosa import norm, dist, lerp, icosahedron_vertex_up, hub_neighbors


def interior_orbit_zs(mesh, row):
    """Distinct standard z values (and multiplicities) of the NON-icosa-edge
    points of a vertex row (the 'interior' points)."""
    zs = defaultdict(list)
    for i, p in enumerate(mesh.verts):
        if mesh.row[i] == row and mesh.on_edge[i] is None and not mesh.is_ppt[i]:
            zs[round(p[2], 9)].append(p[2])
    return sorted((sum(v) / len(v), len(v)) for v in zs.values())


def apply_hub_slide(mesh, m):
    """Return new vertex list: hub-adjacent verts -> normalize((1-m)E + m S)."""
    hn = hub_neighbors(mesh)
    out = list(mesh.verts)
    for v, h in hn.items():
        out[v] = norm(lerp(mesh.verts[h], mesh.verts[v], m))
    return out


def solve_kruschke_m(mesh, n, z_target):
    """Closed form: ratio m such that the moved hub-adjacent edge point of
    vertex-row n+1 (first subdivision point of a U-L icosa edge) reaches
    z == z_target after renormalization.

    T(m) = normalize((1-m)E + m S);  T_z = z_target  is a quadratic in m:
      zw(m) = Ez + m(Sz-Ez),  |W(m)|^2 = 1 + 2m(d-1) + 2m^2(1-d),  d = E.S
      zw^2 - z_target^2 |W|^2 = 0.
    """
    hn = hub_neighbors(mesh)
    cand = [v for v in hn
            if mesh.row[v] == n + 1 and mesh.on_edge[v] is not None]
    assert cand, "no hub-adjacent edge point in row n+1"
    v = cand[0]
    h = hn[v]
    E, S = mesh.verts[h], mesh.verts[v]
    d = E[0] * S[0] + E[1] * S[1] + E[2] * S[2]
    dz = S[2] - E[2]
    a = dz * dz - 2.0 * z_target * z_target * (1.0 - d)
    b = 2.0 * E[2] * dz + 2.0 * z_target * z_target * (1.0 - d)
    c = E[2] * E[2] - z_target * z_target
    disc = b * b - 4 * a * c
    assert disc >= 0
    roots = [(-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)]
    good = [m for m in roots
            if 0.0 < m < 2.0
            and abs(norm(lerp(E, S, m))[2] - z_target) < 1e-12]
    assert good, "no valid root: %s" % roots
    return min(good, key=lambda m: abs(m - 1.0))


def slide_on_arc_to_z(E1, E2, near, z_target):
    """Point on the great circle through E1,E2 with z==z_target, nearest to 'near'."""
    c = E1[0] * E2[0] + E1[1] * E2[1] + E1[2] * E2[2]
    s = math.sqrt(1 - c * c)
    W = norm(((E2[0] - E1[0] * c), (E2[1] - E1[1] * c), (E2[2] - E1[2] * c)))
    # z(t) = E1z cos t + Wz sin t = z_target
    A, B = E1[2], W[2]
    R = math.hypot(A, B)
    phi = math.atan2(B, A)
    val = z_target / R
    assert abs(val) <= 1.0 + 1e-12
    val = max(-1.0, min(1.0, val))
    best, bd = None, 1e9
    for t in (phi + math.acos(val), phi - math.acos(val)):
        p = (E1[0] * math.cos(t) + W[0] * math.sin(t),
             E1[1] * math.cos(t) + W[1] * math.sin(t),
             E1[2] * math.cos(t) + W[2] * math.sin(t))
        d = dist(p, near)
        if d < bd:
            best, bd = p, d
    return best


def kruschke_positions(mesh, n, extended=False):
    """Kruschke vertex positions. For n in (3,4): the classic construction.
    extended=True additionally levels every band row (needed for n>=5):
      - row n+1 target z = multiplicity-weighted mean of its interior points
        (equals the single interior z for n=3,4, so it reduces exactly),
      - every other band row n<r<2n: all points move to the row's
        multiplicity-weighted mean z; icosa-edge points slide along their
        edge great circle, interior points along their meridian.
    Returns (positions, m).

    Frequencies: n=3,4 use extended=False; n=5,6 extended=True (the pure
    core exposes the extended construction for internal use and its own
    tests; no Blender UI path may select n=5 or n=6 for Kruschke).
    """
    if n not in (3, 4, 5, 6):
        raise ValueError("Kruschke needs frequency 3 to 6")
    zs = interior_orbit_zs(mesh, n + 1)
    if not extended:
        assert len(zs) == 1, "row n+1 interior points not coplanar; need extended"
        z_target = zs[0][0]
    else:
        z_target = sum(z * c for z, c in zs) / sum(c for _, c in zs)
    m = solve_kruschke_m(mesh, n, z_target)
    pos = apply_hub_slide(mesh, m)
    if extended:
        hn = hub_neighbors(mesh)
        iverts, _, _ = icosahedron_vertex_up()
        for r in range(n + 1, 2 * n):
            members = [i for i in range(len(pos)) if mesh.row[i] == r]
            if r == n + 1:
                zr = z_target
            elif r == 2 * n - 1:
                zr = -z_target  # mirror of row n+1 (hub slide already put edge pts here)
            else:
                zr = sum(mesh.verts[i][2] for i in members) / len(members)
            for i in members:
                if i in hn:
                    continue  # already placed by the hub slide (row n+1 edge pts)
                p = pos[i]
                if abs(p[2] - zr) < 1e-15:
                    continue
                if mesh.on_edge[i] is not None:
                    a, b = mesh.on_edge[i]
                    E1, E2 = iverts[a], iverts[b]
                    pos[i] = slide_on_arc_to_z(E1, E2, p, zr)
                else:
                    r_xy = math.sqrt(max(0.0, 1.0 - zr * zr))
                    lam = math.atan2(p[1], p[0])
                    pos[i] = (r_xy * math.cos(lam), r_xy * math.sin(lam), zr)
    return pos, m
