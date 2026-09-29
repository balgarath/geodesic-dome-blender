# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Edge / Geovisual Creations
"""mesh.geodesic_dome_add operator and strut visualization helper.

Design.md 10.2, 10.3, 10.4.
"""
import colorsys
import dataclasses
import json
import math

import bpy
from bpy.props import (
    EnumProperty, FloatProperty, BoolProperty, StringProperty,
)
from bpy.types import Operator
from mathutils import Vector

from .core.build import build_dome, valid_frequencies, valid_fractions
from .core.custom import parse_table, expected_class_count

PLUGIN_VERSION = "0.1.3"

METHOD_ITEMS = [
    ("KRUSCHKE", "Kruschke", "The 1972 Kruschke flat base construction, 3V and 4V. The report shows domerama's published chord factor next to ours for the fractions domerama documents"),
    ("CLASS_I", "Icosa Class I Method 1", "Standard equal chord subdivision projected to the sphere, 1V to 8V"),
    ("CUSTOM", "Custom chord table", "Build from a user supplied chord factor table"),
]

# Traditional Kruschke is restricted to 3V and 4V in the UI. The extended
# 5V/6V construction stays in the pure core (and its tests) but no operator
# path may reach it; see docs/design.md 14 and Ralph's decision log.
_UI_KRUSCHKE_FREQUENCIES = (3, 4)

# Cache for dynamic EnumProperty item tuples: Blender only keeps a weak
# reference to the strings returned by an items callback, so the tuples
# must be kept alive by something outside the callback's local scope.
_FREQUENCY_ITEMS_CACHE = {}
_FRACTION_ITEMS_CACHE = {}


def _method_frequencies(method):
    if method == "KRUSCHKE":
        return list(_UI_KRUSCHKE_FREQUENCIES)
    return valid_frequencies(method)


def _frequency_items(self, context):
    method = getattr(self, "method", "KRUSCHKE")
    freqs = _method_frequencies(method)
    items = [(str(n), "%dV" % n, "Frequency %d" % n) for n in freqs]
    _FREQUENCY_ITEMS_CACHE[method] = items
    return _FREQUENCY_ITEMS_CACHE[method]


def _fraction_items(self, context):
    method = getattr(self, "method", "KRUSCHKE")
    try:
        frequency = int(self.frequency)
    except (ValueError, TypeError):
        frequency = _method_frequencies(method)[0]
    try:
        infos = valid_fractions(method, frequency)
    except ValueError:
        infos = []
    if method == "KRUSCHKE":
        # Kruschke is a flat-base construction: only level-base fractions
        # are offered (this includes domerama's 4/9, 5/9, 5/12, 7/12).
        infos = [info for info in infos if info.base_is_level]
    items = []
    for info in infos:
        text = info.label
        if info.alias:
            text += " (a.k.a. %s)" % info.alias
        text += ", level base" if info.base_is_level else ", base not level"
        key = "%d_%d" % (info.k, info.denom)
        items.append((key, text, text))
    if not items:
        items = [("NONE", "No fractions available", "No fractions available")]
    cache_key = (method, frequency)
    _FRACTION_ITEMS_CACHE[cache_key] = items
    return _FRACTION_ITEMS_CACHE[cache_key]


# Ralph's usual Kruschke builds: the larger of the two domerama-documented
# level fractions at each frequency (3V 5/9, 4V 7/12), not just "the first
# level item" (which would be a tiny, impractical dome like 3V 1/9).
_KRUSCHKE_PREFERRED_FRACTION = {3: (5, 9), 4: (7, 12)}


def _default_fraction_key(method, frequency):
    """Ralph-typical build for Kruschke; else the first level-base item."""
    try:
        infos = valid_fractions(method, frequency)
    except ValueError:
        return "NONE"
    if not infos:
        return "NONE"
    if method == "KRUSCHKE":
        infos = [info for info in infos if info.base_is_level]
        if not infos:
            return "NONE"
        preferred = _KRUSCHKE_PREFERRED_FRACTION.get(frequency)
        if preferred:
            for info in infos:
                if (info.k, info.denom) == preferred:
                    return "%d_%d" % (info.k, info.denom)
        chosen = max(infos, key=lambda info: info.k)
        return "%d_%d" % (chosen.k, chosen.denom)
    level = [info for info in infos if info.base_is_level]
    chosen = level[0] if level else infos[0]
    return "%d_%d" % (chosen.k, chosen.denom)


# Shop strut colors, shortest to longest (A, B, C, ...). Matches the paint
# code on Ralph's 4V Kruschke build.
STRUT_PALETTE = (
    (1.0, 0.0, 0.0, 1.0),     # red
    (0.0, 0.2, 1.0, 1.0),     # blue
    (0.0, 0.8, 0.1, 1.0),     # green
    (1.0, 0.85, 0.0, 1.0),    # yellow
    (0.55, 0.1, 0.9, 1.0),    # purple
    (0.02, 0.02, 0.02, 1.0),  # black
)


def _hsv_color(i):
    """Strut type color: shop palette first, generated hues past it."""
    if i < len(STRUT_PALETTE):
        return STRUT_PALETTE[i]
    hue = (0.48 + 0.618033988749895 * i) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.9)
    return (r, g, b, 1.0)


class MESH_OT_geodesic_dome_add(Operator):
    """Add a geodesic dome frame mesh"""
    bl_idname = "mesh.geodesic_dome_add"
    bl_label = "Geodesic Dome"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(
        name="Method",
        items=METHOD_ITEMS,
        default="KRUSCHKE",
        description="Chord factor method",
    )
    frequency: EnumProperty(
        name="Frequency",
        items=_frequency_items,
        description="Subdivision frequency",
    )
    fraction: EnumProperty(
        name="Fraction",
        items=_fraction_items,
        description="Triangle rows kept, as a fraction of the full sphere",
    )
    radius: FloatProperty(
        name="Radius",
        default=3.0,
        min=0.01,
        unit='LENGTH',
        description="Sphere radius",
    )
    orientation: EnumProperty(
        name="Orientation",
        items=[
            ("BASE_ORIGIN", "Base at Origin", "Base plane sits at Z = 0"),
            ("CENTER_ORIGIN", "Center at Origin", "Sphere center sits at Z = 0"),
        ],
        default="BASE_ORIGIN",
        description="Where the dome sits relative to the object origin",
    )
    merge_tolerance: FloatProperty(
        name="Merge Tolerance",
        default=1e-6,
        min=0.0,
        max=1e-3,
        precision=7,
        description="Strut lengths this close are reported as one cut length. "
                     "Raising this merges near-identical struts into one cut "
                     "length, which is convenient to build but less exact",
    )
    add_base_face: BoolProperty(
        name="Add Base Face",
        default=False,
        description="Add a face across the base ring, when the base is level",
    )
    create_strut_object: BoolProperty(
        name="Create Strut Object",
        default=True,
        description="Build a colored strut prism object alongside the frame",
    )
    strut_thickness: FloatProperty(
        name="Strut Thickness",
        default=0.025,
        min=0.001,
        unit='LENGTH',
        description="Strut prism inscribed radius",
    )
    custom_table: StringProperty(
        name="Chord Factors",
        default="",
        description="Chord factors for the Custom method, comma or space separated",
    )
    custom_base: EnumProperty(
        name="Custom Base",
        items=[
            ("CLASS_I", "Class I", "Class I topology, 1V to 8V"),
            ("KRUSCHKE", "Kruschke", "Kruschke topology, 3V to 6V"),
        ],
        default="CLASS_I",
        description="Topology the custom chord table is applied to",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "method")
        layout.prop(self, "frequency")
        layout.prop(self, "fraction")
        layout.prop(self, "radius")
        layout.prop(self, "orientation")
        layout.prop(self, "merge_tolerance")
        layout.prop(self, "add_base_face")
        layout.prop(self, "create_strut_object")
        if self.create_strut_object:
            layout.prop(self, "strut_thickness")
        if self.method == "CUSTOM":
            layout.prop(self, "custom_base")
            layout.prop(self, "custom_table")

    def execute(self, context):
        # Dynamic EnumProperty items pick their first item as an implicit
        # default, which is not Ralph's usual build (see
        # _default_fraction_key). Apply the real default whenever the
        # caller did not explicitly set frequency/fraction, regardless of
        # whether Blender routed this call through invoke() or straight to
        # execute() (both happen depending on how the operator is run).
        if not self.properties.is_property_set("frequency"):
            self.frequency = str(_method_frequencies(self.method)[0])
        if not self.properties.is_property_set("fraction") or not self.fraction:
            self.fraction = _default_fraction_key(self.method, int(self.frequency))

        try:
            frequency = int(self.frequency)
        except (ValueError, TypeError):
            self.report({'ERROR'}, "Choose a frequency.")
            return {'CANCELLED'}

        if self.fraction == "NONE" or not self.fraction:
            self.report({'ERROR'}, "No valid fraction for this method and frequency.")
            return {'CANCELLED'}
        k, denom = (int(x) for x in self.fraction.split("_"))

        custom_table = None
        if self.method == "CUSTOM":
            try:
                custom_table = parse_table(self.custom_table)
            except ValueError as exc:
                self.report({'ERROR'}, str(exc))
                return {'CANCELLED'}
            expected = expected_class_count(frequency, k, self.custom_base)
            if len(custom_table) != expected:
                self.report(
                    {'ERROR'},
                    "Expected %d chord factor values, got %d." % (expected, len(custom_table)),
                )
                return {'CANCELLED'}

        try:
            if self.method == "CUSTOM":
                geometry = build_dome(
                    self.method, frequency, k,
                    merge_tolerance=self.merge_tolerance,
                    custom_table=custom_table,
                    custom_base=self.custom_base,
                    radius=self.radius,
                )
            else:
                geometry = build_dome(
                    self.method, frequency, k,
                    merge_tolerance=self.merge_tolerance,
                    radius=self.radius,
                )
        except ValueError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        radius = self.radius
        verts = [(p[0] * radius, p[1] * radius, p[2] * radius) for p in geometry.verts]

        z_offset = 0.0
        if self.orientation == "BASE_ORIGIN":
            base_zs = [v[2] for i, v in enumerate(verts) if geometry.vert_row[i] == k]
            if base_zs:
                z_offset = -min(base_zs)
        if z_offset:
            verts = [(v[0], v[1], v[2] + z_offset) for v in verts]

        faces = geometry.faces
        if self.add_base_face and geometry.report.base_is_level and k != denom:
            base_idx = [i for i in range(len(verts)) if geometry.vert_row[i] == k]
            if base_idx:
                cx = sum(verts[i][0] for i in base_idx) / len(base_idx)
                cy = sum(verts[i][1] for i in base_idx) / len(base_idx)
                base_idx.sort(key=lambda i: math.atan2(verts[i][1] - cy, verts[i][0] - cx))
                faces = list(faces) + [tuple(base_idx)]
        elif self.add_base_face and not geometry.report.base_is_level:
            self.report({'WARNING'}, "Base is not level; skipped Add Base Face.")

        mesh = bpy.data.meshes.new("Geodesic Dome")
        mesh.from_pydata(verts, geometry.edges, faces)
        mesh.validate()
        mesh.update()

        # Blender can reorder edges and faces inside from_pydata (observed:
        # only 1/310 edges kept their input index for Kruschke 4V 7/12 in
        # Blender 4.0.1), so attributes must be looked up by vertex-index
        # pair / vertex-index set, never by the original list position.
        edge_type_by_pair = {
            (min(u, v), max(u, v)): t
            for (u, v), t in zip(geometry.edges, geometry.edge_type)
        }
        face_type_by_verts = {
            tuple(sorted(f)): t
            for f, t in zip(geometry.faces, geometry.face_type)
        }

        n_types = len(geometry.report.strut_types)
        colors = [_hsv_color(i) for i in range(n_types)]

        mesh_edge_type = []
        for e in mesh.edges:
            u, v = e.vertices[0], e.vertices[1]
            mesh_edge_type.append(edge_type_by_pair.get((min(u, v), max(u, v)), -1))

        strut_type_attr = mesh.attributes.new("strut_type", 'INT', 'EDGE')
        strut_type_attr.data.foreach_set("value", mesh_edge_type)

        color_attr = mesh.attributes.new("strut_color", 'FLOAT_COLOR', 'EDGE')
        flat_colors = []
        for t in mesh_edge_type:
            flat_colors.extend(colors[t] if 0 <= t < len(colors) else (1.0, 1.0, 1.0, 1.0))
        color_attr.data.foreach_set("color", flat_colors)

        mesh_face_type = []
        for poly in mesh.polygons:
            key = tuple(sorted(poly.vertices))
            mesh_face_type.append(face_type_by_verts.get(key, -1))

        panel_attr = mesh.attributes.new("panel_type", 'INT', 'FACE')
        panel_attr.data.foreach_set("value", mesh_face_type)

        # Vertex order is not reindexed by from_pydata (only edges/faces
        # are), but look it up defensively too: geometry.verts is already
        # aligned 1:1 with the vertex list passed in, and Blender preserves
        # that order, so a direct index assignment is safe here.
        row_attr = mesh.attributes.new("row", 'INT', 'POINT')
        row_attr.data.foreach_set("value", geometry.vert_row)

        obj = bpy.data.objects.new("Geodesic Dome", mesh)
        context.collection.objects.link(obj)

        report_dict = dataclasses.asdict(geometry.report)
        report_dict["radius"] = radius
        report_dict["version"] = PLUGIN_VERSION
        obj["geodome_report"] = json.dumps(report_dict)

        if self.create_strut_object:
            create_strut_object(context, obj, geometry, radius, self.strut_thickness, colors)

        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}


def create_strut_object(context, frame_obj, geometry, radius, thickness, colors):
    """Triangular-prism strut visualization, one material slot per type."""
    verts = frame_obj.data.vertices
    positions = [v.co.copy() for v in verts]

    prism_verts = []
    prism_faces = []
    face_material = []
    for edge_i, (a, b) in enumerate(geometry.edges):
        pa, pb = positions[a], positions[b]
        axis = (pb - pa)
        length = axis.length
        if length < 1e-9:
            continue
        axis.normalize()
        # build an arbitrary perpendicular basis
        ref = Vector((1.0, 0.0, 0.0)) if abs(axis.x) < 0.9 else Vector((0.0, 1.0, 0.0))
        side1 = axis.cross(ref).normalized()
        side2 = axis.cross(side1).normalized()
        r = thickness
        offsets = [
            side1 * r,
            (-side1 * 0.5 + side2 * 0.866025) * r,
            (-side1 * 0.5 - side2 * 0.866025) * r,
        ]
        base = len(prism_verts)
        for off in offsets:
            prism_verts.append(pa + off)
        for off in offsets:
            prism_verts.append(pb + off)
        t = geometry.edge_type[edge_i]
        for i in range(3):
            j = (i + 1) % 3
            prism_faces.append((base + i, base + j, base + 3 + j, base + 3 + i))
            face_material.append(t)

    strut_mesh = bpy.data.meshes.new("%s Struts" % frame_obj.name)
    strut_mesh.from_pydata(prism_verts, [], prism_faces)
    strut_mesh.validate()
    strut_mesh.update()

    n_types = len(geometry.report.strut_types)
    for i, st in enumerate(geometry.report.strut_types):
        mat_name = "Strut %s" % st.label
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
        color = colors[i] if i < len(colors) else (1.0, 1.0, 1.0, 1.0)
        mat.diffuse_color = color
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            if "Base Color" in bsdf.inputs:
                bsdf.inputs["Base Color"].default_value = color
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = 0.05
        strut_mesh.materials.append(mat)

    if strut_mesh.polygons:
        for poly, mat_index in zip(strut_mesh.polygons, face_material):
            poly.material_index = mat_index

    strut_obj = bpy.data.objects.new("%s Struts" % frame_obj.name, strut_mesh)
    context.collection.objects.link(strut_obj)
    strut_obj.parent = frame_obj
    return strut_obj


def menu_func(self, context):
    self.layout.operator(MESH_OT_geodesic_dome_add.bl_idname, text="Geodesic Dome", icon='MESH_ICOSPHERE')


_CLASSES = (MESH_OT_geodesic_dome_add,)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
