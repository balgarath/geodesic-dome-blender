#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Ledge / Geovisual Creations
"""Numerical verification of the geodesic math for the Blender extension.

Verifies, against reference/domerama_chord_factors.json and
reference/domerama_kruschke_chord_factors.json:

  1. Class I Method 1 (equal planar chords projected to sphere), 1V-8V:
     chord factors, per-truncation strut counts, hub valences.
     Also derives the authoritative 4V table (domerama's own pages disagree).
  2. Kruschke construction (3V, 4V): standard Method 1 + slide every
     vertex adjacent to an icosahedron vertex ("hub") along the chord
     hub->vertex (renormalized to the sphere), with ONE ratio m per
     frequency solved from the leveling condition:
         z(moved edge point of row n+1) == z(fixed interior point of row n+1)
     This reproduces domerama's Kruschke chord factors / counts / heights,
     and acidome.ru's implementation (their 3V magic 0.9442890204731844).
  3. Extended Kruschke for 5V/6V (our documented generalization):
     hub slide (m from weighted-mean leveling of row n+1) + meridian
     slides of remaining band-row points to per-row weighted-mean z,
     with icosa-edge points sliding along their edge great circles.
     Verifies band rows are exactly level and prints the strut tables
     (these become the plugin's reference constants).

Run:  python verify_geometry.py
Pure stdlib. Exit code 0 = all checks pass.
"""
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EPS_WELD = 1e-9
EPS_GROUP = 1e-7          # lengths closer than this are the same strut type
PASS = "PASS"
FAIL = "FAIL"

failures = []


def check(ok, msg):
    print(("  [%s] " % (PASS if ok else FAIL)) + msg)
    if not ok:
        failures.append(msg)
    return ok


# ---------------------------------------------------------------- vectors
def norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / l, v[1] / l, v[2] / l)


def dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


# ---------------------------------------------------------------- icosahedron
def icosahedron_vertex_up():
    """Icosahedron, unit circumradius, apex at +Z (vertex-zenith).

    Returns (verts, faces, corner_row) where corner_row[i] in {0,n... } is
    expressed in units of the frequency later: 0 for apex, 1 for upper ring,
    2 for lower ring, 3 for nadir (multiply by n for vertex-row index).
    """
    zu = 1.0 / math.sqrt(5.0)
    ru = 2.0 / math.sqrt(5.0)
    verts = [(0.0, 0.0, 1.0)]
    for k in range(5):  # upper ring, longitudes 0,72,...
        a = math.radians(72.0 * k)
        verts.append((ru * math.cos(a), ru * math.sin(a), zu))
    for k in range(5):  # lower ring, longitudes 36,108,...
        a = math.radians(72.0 * k + 36.0)
        verts.append((ru * math.cos(a), ru * math.sin(a), -zu))
    verts.append((0.0, 0.0, -1.0))
    U = lambda k: 1 + (k % 5)
    L = lambda k: 6 + (k % 5)
    faces = []
    for k in range(5):
        faces.append((0, U(k), U(k + 1)))          # cap
        faces.append((U(k), L(k), U(k + 1)))       # band, apex-ish down edge U-U top? (U,L,U)
        faces.append((L(k), L(k + 1), U(k + 1)))   # band inverted
        faces.append((11, L(k + 1), L(k)))         # lower cap
    tier = {0: 0, 11: 3}
    for k in range(5):
        tier[U(k)] = 1
        tier[L(k)] = 2
    return verts, faces, tier


# ---------------------------------------------------------------- subdivision
class Mesh:
    def __init__(self):
        self.verts = []          # positions (unit sphere)
        self.row = []            # vertex-row index 0..3n
        self.on_edge = []        # None or (icosa vertex id pair) if on an icosa edge chord
        self.is_ppt = []         # True if an original icosahedron vertex
        self.ppt_id = []         # icosa vertex index or -1
        self.faces = []          # triangles (i,j,k)
        self._weld = {}

    def add_vertex(self, p, row, on_edge, is_ppt, ppt_id):
        key = (round(p[0], 9), round(p[1], 9), round(p[2], 9))
        if key in self._weld:
            i = self._weld[key]
            assert self.row[i] == row, "row mismatch at weld"
            return i
        i = len(self.verts)
        self._weld[key] = i
        self.verts.append(p)
        self.row.append(row)
        self.on_edge.append(on_edge)
        self.is_ppt.append(is_ppt)
        self.ppt_id.append(ppt_id)
        return i

    def edges(self):
        es = set()
        for (a, b, c) in self.faces:
            for u, v in ((a, b), (b, c), (c, a)):
                es.add((min(u, v), max(u, v)))
        return sorted(es)


def subdivide_class1(n):
    """Class I Method 1: equal chords on the planar face, projected to sphere."""
    iverts, ifaces, tier = icosahedron_vertex_up()
    mesh = Mesh()
    for (ia, ib, ic) in ifaces:
        A, B, C = iverts[ia], iverts[ib], iverts[ic]
        ra, rb, rc = tier[ia] * n, tier[ib] * n, tier[ic] * n
        ids = {}
        for i in range(n + 1):          # weight of A
            for j in range(n + 1 - i):  # weight of B
                k = n - i - j
                p = norm((A[0] * i + B[0] * j + C[0] * k,
                          A[1] * i + B[1] * j + C[1] * k,
                          A[2] * i + B[2] * j + C[2] * k))
                row = (ra * i + rb * j + rc * k) // n
                assert (ra * i + rb * j + rc * k) % n == 0
                corners = [w for w, iv in ((i, ia), (j, ib), (k, ic)) if w > 0]
                names = [iv for w, iv in ((i, ia), (j, ib), (k, ic)) if w > 0]
                is_ppt = len(corners) == 1
                on_edge = tuple(sorted(names)) if len(corners) == 2 else None
                ppt = names[0] if is_ppt else -1
                ids[(i, j)] = mesh.add_vertex(p, row, on_edge, is_ppt, ppt)
        for i in range(n):
            for j in range(n - i):
                v0 = ids[(i, j)]
                v1 = ids[(i + 1, j)]
                v2 = ids[(i, j + 1)]
                mesh.faces.append((v0, v1, v2))
                if j + i + 1 < n:
                    v3 = ids[(i + 1, j + 1)]
                    mesh.faces.append((v1, v3, v2))
    return mesh


# ---------------------------------------------------------------- kruschke
def hub_neighbors(mesh):
    """vertex id -> icosa hub vertex id it is adjacent to (must be unique)."""
    nb = defaultdict(set)
    for (u, v) in mesh.edges():
        if mesh.is_ppt[u] and not mesh.is_ppt[v]:
            nb[v].add(u)
        if mesh.is_ppt[v] and not mesh.is_ppt[u]:
            nb[u].add(v)
    out = {}
    for v, hubs in nb.items():
        assert len(hubs) == 1, "vertex adjacent to several hubs (n too small)"
        out[v] = next(iter(hubs))
    return out


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


def kruschke_positions(mesh, n, extended=False):
    """Kruschke vertex positions. For n in (3,4): the classic construction.
    extended=True additionally levels every band row (needed for n>=5):
      - row n+1 target z = multiplicity-weighted mean of its interior points
        (equals the single interior z for n=3,4, so it reduces exactly),
      - every other band row n<r<2n: all points move to the row's
        multiplicity-weighted mean z; icosa-edge points slide along their
        edge great circle, interior points along their meridian.
    Returns (positions, m).
    """
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
        # per-row target z (band rows), from *standard* positions
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


def slide_on_arc_to_z(E1, E2, near, z_target):
    """Point on the great circle through E1,E2 with z==z_target, nearest to 'near'."""
    c = E1[0] * E2[0] + E1[1] * E2[1] + E1[2] * E2[2]
    s = math.sqrt(1 - c * c)
    W = norm(((E2[0] - E1[0] * c), (E2[1] - E1[1] * c), (E2[2] - E1[2] * c)))
    # z(t) = E1z cos t + Wz sin t = z_target
    A, B = E1[2], W[2]
    R = math.hypot(A, B)
    phi = math.atan2(B, A)   # z(t) = R cos(t - phi')? use: A cos t + B sin t = R cos(t - phi)
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


# ---------------------------------------------------------------- truncation / stats
def dome_edges(mesh, k):
    """Edges of the dome keeping triangle rows 1..k (face row = max vertex row)."""
    es = set()
    for (a, b, c) in mesh.faces:
        if max(mesh.row[a], mesh.row[b], mesh.row[c]) <= k:
            for u, v in ((a, b), (b, c), (c, a)):
                es.add((min(u, v), max(u, v)))
    return sorted(es)


def group_lengths(edges, pos):
    groups = []  # list of [length_sum, count, min, max]
    lens = sorted(dist(pos[u], pos[v]) for (u, v) in edges)
    for l in lens:
        if groups and l - groups[-1][3] < EPS_GROUP:
            g = groups[-1]
            g[0] += l
            g[1] += 1
            g[3] = l
        else:
            groups.append([l, 1, l, l])
    return [(g[0] / g[1], g[1]) for g in groups]  # (mean length, count) ascending


def hub_valences(edges):
    val = defaultdict(int)
    for (u, v) in edges:
        val[u] += 1
        val[v] += 1
    out = defaultdict(int)
    for _, d in val.items():
        out[d] += 1
    return dict(out)


def min_gap(groups):
    gs = [groups[i + 1][0] - groups[i][0] for i in range(len(groups) - 1)]
    return min(gs) if gs else float("inf")


# ---------------------------------------------------------------- comparisons
def tol_for(cf):
    # full ulp of the digits domerama displays (they truncate sometimes),
    # plus slack: site values are independently computed/rounded
    s = ("%r" % cf)
    dec = len(s.split(".")[1]) if "." in s else 0
    return 1.0 * 10 ** (-dec) + 5e-6


def compare_table(name, groups, ref_struts, check_counts=True):
    """Match generated (length,count) groups against domerama strut rows."""
    ok_all = True
    used = set()
    for srow in ref_struts:
        cf = srow["chord_factor"]
        if cf is None:
            continue
        tol = tol_for(cf)
        hit = None
        for gi, (l, c) in enumerate(groups):
            if gi not in used and abs(l - cf) <= tol:
                hit = gi
                break
        if hit is None:
            # allow near-miss report
            best = min(range(len(groups)), key=lambda gi: abs(groups[gi][0] - cf))
            ok_all &= check(False, "%s %s: CF %.8f not matched (nearest %.8f, diff %.2e)"
                            % (name, srow["label"], cf, groups[best][0], groups[best][0] - cf))
            continue
        used.add(hit)
        l, c = groups[hit]
        if check_counts and srow.get("count") is not None:
            note = ""
            if c != srow["count"]:
                # domerama's 5-decimal tables sometimes merge two true strut
                # types (7V J, 8V N); absorb neighbours within 2e-4
                for gj, (l2, c2) in enumerate(groups):
                    if gj not in used and abs(l2 - cf) < 2e-4 and c + c2 == srow["count"]:
                        used.add(gj)
                        c += c2
                        note = " (site merged types %.8f + %.8f)" % (l, l2)
                        break
            ok = c == srow["count"]
            ok_all &= check(ok, "%s %s: CF %.8f ~ %.8f (diff %.1e), count %d vs ref %d%s"
                            % (name, srow["label"], l, cf, l - cf, c, srow["count"], note))
        else:
            ok_all &= check(True, "%s %s: CF %.8f ~ %.8f (diff %.1e)"
                            % (name, srow["label"], l, cf, l - cf))
    if not any(s["chord_factor"] is not None for s in ref_struts):
        return ok_all  # counts-only reference entry: nothing to match against
    extra = [g for gi, g in enumerate(groups) if gi not in used]
    if extra:
        ok_all &= check(False, "%s: %d unmatched generated strut types: %s"
                        % (name, len(extra), ", ".join("%.6f x%d" % (l, c) for l, c in extra)))
    return ok_all


def compare_hubs(name, edges, ref_hubs):
    if not ref_hubs:
        return True
    got = hub_valences(edges)
    want = {}
    for kk, vv in ref_hubs.items():
        want[int(kk.split("-")[0])] = vv
    ok = got == want
    return check(ok, "%s hubs: got %s vs ref %s" % (name, dict(sorted(got.items())), dict(sorted(want.items()))))


# ---------------------------------------------------------------- main
def main():
    with open(os.path.join(HERE, "domerama_chord_factors.json"), encoding="utf8") as f:
        classi_ref = json.load(f)
    with open(os.path.join(HERE, "domerama_kruschke_chord_factors.json"), encoding="utf8") as f:
        kru_ref = json.load(f)

    # -------------------------------------------------- Class I
    print("=" * 72)
    print("CLASS I METHOD 1 vs domerama")
    print("=" * 72)
    # (frequency, fraction) -> triangle rows kept k of 3n
    trunc = {("1V", "2/3"): 2, ("2V", "1/2"): 3,
             ("3V", "3/8"): 4, ("3V", "5/8"): 5,
             ("4V", "1/2"): 6,
             ("5V", "7/15"): 7, ("5V", "8/15"): 8,
             ("6V", "1/2"): 9, ("7V", "10/21"): 10, ("8V", None): 12}
    meshes = {}
    for dome in classi_ref["domes"]:
        if dome["method"] != "Class I Method 1":
            continue
        n = int(dome["frequency"][0])
        key = (dome["frequency"], dome["fraction"])
        if key not in trunc:
            continue
        k = trunc[key]
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        mesh = meshes[n]
        edges = dome_edges(mesh, k)
        groups = group_lengths(edges, mesh.verts)
        nm = "%s %s" % (dome["frequency"], dome["fraction"])
        print("-- %s: %d struts, %d types, min type gap %.2e" %
              (nm, len(edges), len(groups), min_gap(groups)))
        # 4V chord-chart entry has no counts (ambiguous on site) -> CF only
        counts_ok = all(s.get("count") for s in dome["struts"] if s["chord_factor"])
        compare_table(nm, groups, dome["struts"], check_counts=counts_ok)
        compare_hubs(nm, edges, dome.get("hubs"))

    # authoritative 4V table
    print("-- derived authoritative 4V 1/2 table (resolves domerama inconsistency):")
    mesh4 = meshes.get(4) or subdivide_class1(4)
    meshes[4] = mesh4
    g4 = group_lengths(dome_edges(mesh4, 6), mesh4.verts)
    for i, (l, c) in enumerate(g4):
        print("     %s: CF %.8f  count %3d  bend %.2f deg"
              % (chr(65 + i), l, c, math.degrees(math.asin(l / 2))))

    # -------------------------------------------------- Kruschke 3V / 4V
    print()
    print("=" * 72)
    print("KRUSCHKE (classic construction, m solved from leveling) vs domerama")
    print("=" * 72)
    kru_trunc = {("3V", "4/9"): 4, ("3V", "5/9"): 5, ("4V", "5/12"): 5, ("4V", "7/12"): 7}
    kru_pos = {}
    for dome in kru_ref["domes"]:
        n = dome["frequency"]
        k = kru_trunc[("%dV" % n, dome["fraction"])]
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        mesh = meshes[n]
        if n not in kru_pos:
            kru_pos[n], m = kruschke_positions(mesh, n)
            print("-- %dV: solved m = %.16f" % (n, m))
            if n == 3:
                check(abs(m - 0.9442890204731844) < 2e-7,
                      "3V m matches acidome magic 0.9442890204731844 (diff %.2e)"
                      % (m - 0.9442890204731844))
        pos = kru_pos[n]
        edges = dome_edges(mesh, k)
        groups = group_lengths(edges, pos)
        nm = "%dV %s Kruschke" % (n, dome["fraction"])
        print("-- %s: %d struts, %d types, min type gap %.2e"
              % (nm, len(edges), len(groups), min_gap(groups)))
        compare_table(nm, groups, dome["struts"])
        # base level + height factor
        base = [i for i in range(len(pos)) if mesh.row[i] == k]
        base_in = set()
        for (u, v) in edges:
            base_in.add(u)
            base_in.add(v)
        base = [i for i in base if i in base_in]
        zs = [pos[i][2] for i in base]
        check(max(zs) - min(zs) < 1e-12, "%s base ring level (spread %.2e)" % (nm, max(zs) - min(zs)))
        h = 1.0 - zs[0]
        check(abs(h - dome["height_factor"]) <= tol_for(dome["height_factor"]),
              "%s height factor %.6f vs ref %s" % (nm, h, dome["height_factor"]))
        hubs = classi_hub_ref(kru_ref, classi_ref, n, dome["fraction"])
        if (n, dome["fraction"]) == (4, "5/12"):
            # domerama lists 85x6-way for BOTH 4V Kruschke pages; correct
            # value for 5/12 (rows 0-5) is 45. Known site copy-paste bug
            # (same pages also duplicate bolt counts). Assert our own value.
            got = hub_valences(edges)
            check(got == {4: 20, 5: 6, 6: 45},
                  "%s hubs: got %s (site claims 85x6-way: known site bug, "
                  "correct is 45)" % (nm, dict(sorted(got.items()))))
        elif hubs:
            compare_hubs(nm, edges, hubs)

    # difference table: exact construction vs domerama published values
    print("-- Domerama-published vs exact-construction chord factors:")
    for dome in kru_ref["domes"]:
        n = dome["frequency"]
        k = kru_trunc[("%dV" % n, dome["fraction"])]
        groups = group_lengths(dome_edges(meshes[n], k), kru_pos[n])
        print("   %dV %s:" % (n, dome["fraction"]))
        for srow, (l, c) in zip(dome["struts"], groups):
            print("     %s: site %.6f  exact %.8f  diff %+.1e  count %d"
                  % (srow["label"], srow["chord_factor"], l, l - srow["chord_factor"], c))

    # -------------------------------------------------- extended 5V / 6V
    print()
    print("=" * 72)
    print("EXTENDED KRUSCHKE 5V/6V (our generalization; no external reference)")
    print("=" * 72)
    ext_out = {"source": "verify_geometry.py (extended Kruschke construction)",
               "notes": "Our documented 5V/6V generalization; no external reference exists. "
                        "m = hub slide ratio; tables are golden regression values.",
               "domes": []}
    for n, ks in ((5, (6, 7, 8, 9)), (6, (7, 8, 9, 10, 11))):
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        mesh = meshes[n]
        pos, m = kruschke_positions(mesh, n, extended=True)
        print("-- %dV extended: m = %.12f" % (n, m))
        # sanity: all verts on sphere
        rmax = max(abs(math.sqrt(p[0] ** 2 + p[1] ** 2 + p[2] ** 2) - 1) for p in pos)
        check(rmax < 1e-12, "%dV extended: all vertices on unit sphere (max dev %.1e)" % (n, rmax))
        # spokes all equal
        hn = hub_neighbors(mesh)
        sp = sorted(dist(pos[v], pos[h]) for v, h in hn.items())
        check(sp[-1] - sp[0] < 1e-12, "%dV extended: all %d hub spokes equal (%.8f)" % (n, len(sp), sp[0]))
        for r in range(n + 1, 2 * n):
            zs = [pos[i][2] for i in range(len(pos)) if mesh.row[i] == r]
            check(max(zs) - min(zs) < 1e-12,
                  "%dV extended: row %d level at z=%.6f (spread %.1e)" % (n, r, zs[0], max(zs) - min(zs)))
        for k in ks:
            edges = dome_edges(mesh, k)
            groups = group_lengths(edges, pos)
            print("   %dV %d/%d: %d struts, %d types (min gap %.2e), height %.6f, hubs %s"
                  % (n, k, 3 * n, len(edges), len(groups), min_gap(groups),
                     1.0 - min(pos[i][2] for i in set(sum(map(list, edges), []))),
                     dict(sorted(hub_valences(edges).items()))))
            for i, (l, c) in enumerate(groups):
                print("      %s: CF %.8f  count %3d  bend %.2f deg"
                      % (label(i), l, c, math.degrees(math.asin(min(1, l / 2)))))
            ext_out["domes"].append({
                "frequency": n, "fraction": "%d/%d" % (k, 3 * n),
                "m": m,
                "height_factor": 1.0 - min(pos[i][2] for i in set(sum(map(list, edges), []))),
                "hubs": {str(kk): vv for kk, vv in sorted(hub_valences(edges).items())},
                "struts": [{"label": label(i), "chord_factor": round(l, 10), "count": c}
                           for i, (l, c) in enumerate(groups)]})
    with open(os.path.join(HERE, "kruschke_extended_reference.json"), "w", encoding="utf8") as f:
        json.dump(ext_out, f, indent=1)
    print("-- wrote kruschke_extended_reference.json")

    # -------------------------------------------------- summary
    print()
    print("=" * 72)
    if failures:
        print("RESULT: %d FAILURES" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


def label(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def classi_hub_ref(kru_ref, classi_ref, n, fraction):
    for d in classi_ref["domes"]:
        if d.get("method") == "Kruschke" and d["frequency"] == "%dV" % n:
            if d["fraction"] == fraction and d.get("hubs") and len(d["hubs"]) == 3:
                return d["hubs"]
    return None


if __name__ == "__main__":
    sys.exit(main())
