# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Edge / Geovisual Creations
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
    raise ValueError("Unknown method: %s" % method)


def _positions_for(method, mesh, frequency):
    if method in ("CLASS_I", "CUSTOM"):
        # CUSTOM has no standard positions of its own; for level-base /
        # fraction-listing purposes before a table is solved, use the Class
        # I topology it defaults to (see class1_defaults and design.md 7).
        return mesh.verts
    if method == "KRUSCHKE":
        extended = frequency in (5, 6)
        pos, _m = kruschke_positions(mesh, frequency, extended=extended)
        return pos
    raise ValueError("No standard positions for method: %s" % method)


def valid_fractions(method, frequency):
    if frequency not in valid_frequencies(method):
        raise ValueError("Frequency %s not valid for method %s" % (frequency, method))
    mesh = subdivide_class1(frequency)
    denom = 3 * frequency
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


def class1_defaults(frequency, k, merge_tolerance=1e-6):
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


def build_dome(method, frequency, k, merge_tolerance=1e-6, custom_table=None,
               custom_base="CLASS_I", radius=1.0):
    """Build a DomeGeometry for the given method/frequency/truncation.

    method: 'CLASS_I' | 'KRUSCHKE' | 'CUSTOM'
    frequency: subdivision frequency n
    k: triangle rows kept, 1..3n (3n = full sphere)
    """
    notes = []
    custom_residual = None

    if method == "CUSTOM":
        from .custom import solve_custom, base_defaults
        if frequency not in valid_frequencies(custom_base if custom_base != "CUSTOM" else "CLASS_I"):
            raise ValueError("Frequency %s not valid for custom base %s" % (frequency, custom_base))
        mesh = subdivide_class1(frequency)
        base_positions = _positions_for(custom_base, mesh, frequency)
        denom = 3 * frequency
        if k < 1 or k > denom:
            raise ValueError("k must be between 1 and %d" % denom)
        # Defaults must be classified at the same tolerance and the same
        # base topology solve_custom itself uses internally, or the count
        # solve_custom expects can mismatch the count these defaults
        # produce (e.g. 7V/8V with custom_base='KRUSCHKE') and raise
        # ValueError even though no table was supplied.
        targets = custom_table if custom_table is not None else \
            base_defaults(frequency, k, custom_base, merge_tolerance=1e-7)
        targets_count = len(targets)
        positions, residual = solve_custom(mesh, base_positions, k, targets,
                                            merge_tolerance=1e-7)
        custom_residual = residual
        if residual > 1e-4:
            mm = residual * 1000.0 * radius
            notes.append(
                "Chord table is not self-consistent on a sphere. "
                "Worst strut error: %.3f mm at radius %.3f m." % (mm, radius))
    else:
        if frequency not in valid_frequencies(method):
            raise ValueError("Frequency %s not valid for method %s" % (frequency, method))
        denom = 3 * frequency
        if k < 1 or k > denom:
            raise ValueError("k must be between 1 and %d" % denom)
        mesh = subdivide_class1(frequency)
        positions = _positions_for(method, mesh, frequency)

    edges = dome_edges(mesh, k)
    faces = dome_faces(mesh, k)
    base = base_ring(mesh, k, edges)
    # Level check in real length at the chosen radius: a base is level
    # enough to build when its spread is under a small tolerance at that
    # radius, not only when it is exactly 0 on the unit sphere. This
    # matters for e.g. a Custom dome fed domerama's own rounded Kruschke
    # factors, whose spread is about 1e-6 on the unit sphere (a few
    # thousandths of a millimeter at any sane radius) but would fail a
    # strict 1e-9 check.
    #
    # The physical tolerance itself must shrink with radius, not stay a
    # fixed 0.1 mm: a fixed absolute tolerance is a huge relative slack at
    # small radii (0.1 mm out of a 14.5 mm radius dome is not "level", it's
    # most of the model), which let tiny Class I odd-frequency domes
    # falsely report level. Use the smaller of a 0.1 mm cap and a relative
    # 1e-5 x radius tolerance, with a tiny absolute floor so radius -> 0
    # doesn't divide by zero.
    if radius > 0:
        threshold_m = max(1e-9 * radius, min(0.0001, 1e-5 * radius))
        level_tol = threshold_m / radius
    else:
        level_tol = 1e-9
    base_level, base_spread = base_level_info(positions, base, tol=level_tol)

    edge_type, groups = group_edges(edges, positions, merge_tolerance)
    ascending_cfs = [g["chord_factor"] for g in groups]
    dcols = domerama_columns(method, frequency, k, ascending_cfs) if method != "CUSTOM" \
        else [(None, None)] * len(ascending_cfs)

    if method == "CUSTOM":
        # Count distinct lengths for this warning at a tolerance loose
        # enough to absorb the solver's own noise, not the (possibly much
        # tighter) reporting merge_tolerance: otherwise a table that is
        # genuinely self-consistent (tiny residual) but merges under a
        # coarse merge_tolerance looks "inconsistent" for the wrong reason,
        # and a table fed back with sub-1e-4 rounding (e.g. domerama's own
        # published Kruschke CFs) falsely reports many extra types created
        # purely by relaxation jitter rather than a bad table.
        consistency_tol = max(merge_tolerance, 3.0 * residual)
        _ct_edge_type, consistency_groups = group_edges(edges, positions, consistency_tol)
        if len(consistency_groups) > targets_count and residual > 1e-4:
            notes.append(
                "Your table is not geometrically consistent for this dome, so "
                "the mesh has %d strut lengths instead of %d." % (len(consistency_groups), targets_count))

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
        mm = base_spread * 1000.0 * radius
        notes.append(
            "Base is not level for this method and fraction. "
            "Max height mismatch: %.3f mm at radius %.3f m." % (mm, radius))
        if method == "CLASS_I" and frequency % 2 == 1:
            notes.append("Class I odd frequencies never give a level base. "
                         "The Kruschke method does.")
    elif base_spread > 0.0 and len(base) > 1:
        mm = base_spread * 1000.0 * radius
        if round(mm, 4) > 0.0:
            notes.append("Base spread: %.4f mm at radius %.3f m, within tolerance." % (mm, radius))
    if method == "KRUSCHKE" and frequency % 2 == 0 and k == denom // 2:
        notes.append("For 1/2 domes at even frequency, Class I already gives "
                     "a level base with fewer strut types.")
    if method == "KRUSCHKE" and frequency in (5, 6):
        notes.append("5V and 6V Kruschke are an extension of the 1972 method. "
                     "See the manual.")

    for st in strut_types:
        if st.sub_spread > 0:
            mm = st.sub_spread * 1000.0 * radius
            if mm > 0.5:
                notes.append(
                    "Strut %s merges sub-types with spread %.3f mm at radius %.3f m. "
                    "Lower the merge tolerance for a precise cut list." % (st.label, mm, radius))

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
