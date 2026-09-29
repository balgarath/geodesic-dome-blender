"""Icosahedron geometry and Class I Method 1 subdivision.

Ported from reference/verify_geometry.py (the verified math oracle).
Do not change the math; port only.
"""
import math
from collections import defaultdict


def norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / l, v[1] / l, v[2] / l)


def dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def icosahedron_vertex_up():
    """Icosahedron, unit circumradius, apex at +Z (vertex-zenith).

    Returns (verts, faces, corner_tier) where corner_tier[i] in {0,1,2,3}:
    0 for apex, 1 for upper ring, 2 for lower ring, 3 for nadir.
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
        faces.append((U(k), L(k), U(k + 1)))       # band
        faces.append((L(k), L(k + 1), U(k + 1)))   # band inverted
        faces.append((11, L(k + 1), L(k)))         # lower cap
    tier = {0: 0, 11: 3}
    for k in range(5):
        tier[U(k)] = 1
        tier[L(k)] = 2
    return verts, faces, tier


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
