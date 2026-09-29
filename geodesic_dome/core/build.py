"""build_dome() facade: subdivide, position, truncate, classify, assemble.

Design.md 9.
"""
import math
from dataclasses import dataclass

from .icosa import subdivide_class1
from .kruschke import kruschke_positions
from .truncate import dome_edges, dome_faces, base_ring, base_level_info, fraction_alias
from .classify import (
    StrutType, DomeReport, DomeGeometry,
    label, group_edges, hub_valences, face_types, domerama_columns,
)

_KRUSCHKE_DOMERAMA_COMBOS = {(3, 4), (3, 5), (4, 5), (4, 7)}


@dataclass
class FractionInfo:
    k: int
    denom: int
    label: str
    alias: "str | None"
    base_is_level: bool
    note: "str | None" = None


def valid_frequencies(method):
    if method in ("CLASS_I", "CUSTOM"):
        return list(range(1, 9))
    if method == "KRUSCHKE":
        return [3, 4, 5, 6]
    if method == "KRUSCHKE_DOMERAMA":
        return [3, 4]
    raise ValueError("Unknown method: %s" % method)


def _positions_for(method, mesh, frequency):
    if method == "CLASS_I":
        return mesh.verts
    if method in ("KRUSCHKE", "KRUSCHKE_DOMERAMA"):
        extended = frequency in (5, 6)
        pos, _m = kruschke_positions(mesh, frequency, extended=extended)
        return pos
    raise ValueError("No standard positions for method: %s" % method)


def valid_fractions(method, frequency):
    if frequency not in valid_frequencies(method):
        raise ValueError("Frequency %s not valid for method %s" % (frequency, method))
    mesh = subdivide_class1(frequency)
    denom = 3 * frequency
    if method == "KRUSCHKE_DOMERAMA":
        ks = sorted(k for (n, k) in _KRUSCHKE_DOMERAMA_COMBOS if n == frequency)
    else:
        ks = list(range(1, denom + 1))
    positions = _positions_for(method, mesh, frequency)
    out = []
    for k in ks:
        edges = dome_edges(mesh, k)
        base = base_ring(mesh, k, edges)
        level, spread = base_level_info(positions, base)
        alias = fraction_alias(k, denom)
        lbl = "Full sphere" if k == denom else "%d/%d" % (k, denom)
        out.append(FractionInfo(k=k, denom=denom, label=lbl, alias=alias,
                                 base_is_level=level, note=None))
    return out


def expected_custom_count(frequency, k):
    from .custom import expected_class_count
    return expected_class_count(frequency, k)


def class1_defaults(frequency, k, merge_tolerance=1e-4):
    mesh = subdivide_class1(frequency)
    edges = dome_edges(mesh, k)
    _edge_type, groups = group_edges(edges, mesh.verts, merge_tolerance)
    return [g["chord_factor"] for g in groups]


def _remap(mesh, positions, edges, faces):
    used = sorted({v for e in edges for v in e} | {v for f in faces for v in f})
    old_to_new = {old: new for new, old in enumerate(used)}
    new_verts = [positions[old] for old in used]
    new_rows = [mesh.row[old] for old in used]
    new_edges = [(old_to_new[u], old_to_new[v]) for (u, v) in edges]
    new_faces = [(old_to_new[a], old_to_new[b], old_to_new[c]) for (a, b, c) in faces]
    return new_verts, new_rows, new_edges, new_faces, old_to_new


def build_dome(method, frequency, k, merge_tolerance=1e-4, custom_table=None,
               custom_base="CLASS_I"):
    """Build a DomeGeometry for the given method/frequency/truncation.

    method: 'CLASS_I' | 'KRUSCHKE' | 'KRUSCHKE_DOMERAMA' | 'CUSTOM'
    frequency: subdivision frequency n
    k: triangle rows kept, 1..3n (3n = full sphere)
    """
    notes = []
    custom_residual = None

    if method == "CUSTOM":
        from .custom import solve_custom
        if frequency not in valid_frequencies(custom_base if custom_base != "CUSTOM" else "CLASS_I"):
            raise ValueError("Frequency %s not valid for custom base %s" % (frequency, custom_base))
        mesh = subdivide_class1(frequency)
        base_positions = _positions_for(custom_base, mesh, frequency)
        denom = 3 * frequency
        if k < 1 or k > denom:
            raise ValueError("k must be between 1 and %d" % denom)
        targets = custom_table if custom_table is not None else class1_defaults(frequency, k)
        positions, residual = solve_custom(mesh, base_positions, k, targets,
                                            merge_tolerance=1e-7)
        custom_residual = residual
        if residual > 1e-4:
            mm = residual * 1000.0
            notes.append(
                "Chord table is not self-consistent on a sphere. "
                "Worst strut error: %.3f mm at radius %.3f m." % (mm, 1.0))
    else:
        if frequency not in valid_frequencies(method):
            raise ValueError("Frequency %s not valid for method %s" % (frequency, method))
        if method == "KRUSCHKE_DOMERAMA" and (frequency, k) not in _KRUSCHKE_DOMERAMA_COMBOS:
            raise ValueError(
                "Domerama publishes Kruschke tables for 3V 4/9, 3V 5/9, "
                "4V 5/12 and 4V 7/12 only. Use Kruschke (traditional) for other sizes."
            )
        denom = 3 * frequency
        if k < 1 or k > denom:
            raise ValueError("k must be between 1 and %d" % denom)
        mesh = subdivide_class1(frequency)
        positions = _positions_for(method, mesh, frequency)

    edges = dome_edges(mesh, k)
    faces = dome_faces(mesh, k)
    base = base_ring(mesh, k, edges)
    base_level, base_spread = base_level_info(positions, base)

    edge_type, groups = group_edges(edges, positions, merge_tolerance)
    ascending_cfs = [g["chord_factor"] for g in groups]
    dcols = domerama_columns(method, frequency, k, ascending_cfs) if method != "CUSTOM" \
        else [(None, None)] * len(ascending_cfs)

    strut_types = []
    for i, g in enumerate(groups):
        dlabel, dcf = dcols[i]
        bend = math.degrees(math.asin(min(1.0, g["chord_factor"] / 2.0)))
        strut_types.append(StrutType(
            label=label(i),
            chord_factor=g["chord_factor"],
            count=g["count"],
            bend_angle_deg=bend,
            domerama_label=dlabel,
            domerama_cf=dcf,
            sub_spread=g["sub_spread"],
        ))

    hv = hub_valences(edges)

    verts, rows, r_edges, r_faces, old_to_new = _remap(mesh, positions, edges, faces)
    r_edge_type = [edge_type[i] for i in range(len(edges))]
    r_face_type = face_types(faces, edges, edge_type)

    if base:
        height_factor = 1.0 - min(positions[i][2] for i in base)
    else:
        height_factor = 0.0
    base_radius_factor = None
    if base_level and base:
        bz = positions[base[0]][2]
        base_radius_factor = math.sqrt(max(0.0, 1.0 - bz * bz))

    denom = 3 * frequency
    alias = fraction_alias(k, denom)
    fraction_label = "Full sphere" if k == denom else "%d/%d" % (k, denom)

    if not base_level:
        mm = base_spread * 1000.0
        notes.append(
            "Base is not level for this method and fraction. "
            "Max height mismatch: %.3f mm at radius %.3f m." % (mm, 1.0))
        if method == "CLASS_I" and frequency % 2 == 1:
            notes.append("Class I odd frequencies never give a level base. "
                         "The Kruschke method does.")
    if method == "KRUSCHKE" and frequency % 2 == 0 and k == denom // 2:
        notes.append("For 1/2 domes at even frequency, Class I already gives "
                     "a level base with fewer strut types.")
    if method in ("KRUSCHKE", "KRUSCHKE_DOMERAMA") and frequency in (5, 6):
        notes.append("5V and 6V Kruschke are an extension of the 1972 method. "
                     "See the manual.")

    report = DomeReport(
        method=method,
        frequency=frequency,
        k=k,
        denom=denom,
        fraction_label=fraction_label,
        alias=alias,
        strut_types=strut_types,
        hub_valences=hv,
        height_factor=height_factor,
        base_is_level=base_level,
        base_z_spread=0.0 if base_level else base_spread,
        base_radius_factor=base_radius_factor,
        total_struts=len(edges),
        total_faces=len(faces),
        total_verts=len(verts),
        notes=notes,
        custom_residual=custom_residual,
    )

    return DomeGeometry(
        verts=verts,
        edges=r_edges,
        faces=r_faces,
        edge_type=r_edge_type,
        face_type=r_face_type,
        vert_row=rows,
        report=report,
    )
