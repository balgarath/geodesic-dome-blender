# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Ledge / Geovisual Creations
"""N-panel report display and CSV export. Design.md 10.5, 10.6."""
import json

import bpy
from bpy.props import StringProperty
from bpy.types import Panel, Operator

from .core.report_csv import csv_lines
from .operators import PLUGIN_VERSION


def _get_report(obj):
    raw = obj.get("geodome_report")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


class VIEW3D_PT_geodome_report(Panel):
    bl_label = "Geodome Report"
    bl_idname = "VIEW3D_PT_geodome_report"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Geodome"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.get("geodome_report") is not None

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        report = _get_report(obj)
        if report is None:
            layout.label(text="No report data on this object.")
            return

        radius = report.get("radius", 1.0)

        box = layout.box()
        box.label(text="Method: %s" % report["method"])
        box.label(text="Frequency: %dV" % report["frequency"])
        frac = "%d/%d" % (report["k"], report["denom"])
        if report.get("alias"):
            frac += " (a.k.a. %s)" % report["alias"]
        box.label(text="Fraction: %s" % frac)
        box.label(text="Radius: %.3f m" % radius)
        box.label(text="Height: %.3f m" % (report["height_factor"] * radius))
        if report.get("base_is_level"):
            box.label(text="Base is level")
            if report.get("base_radius_factor") is not None:
                diameter = 2.0 * report["base_radius_factor"] * radius
                box.label(text="Base diameter: %.3f m" % diameter)
        else:
            mm = report.get("base_z_spread", 0.0) * radius * 1000.0
            box.label(text="Base is not level, max mismatch %.1f mm" % mm)

        table_box = layout.box()
        table_box.label(text="Struts")
        for st in report["strut_types"]:
            row = table_box.row()
            row.label(text=st["label"])
            row.label(text="%.6f" % st["chord_factor"])
            row.label(text="%.1f mm" % (st["chord_factor"] * radius * 1000.0))
            row.label(text=str(st["count"]))
            row.label(text="%.2f" % st["bend_angle_deg"])
            if st.get("domerama_label") or st.get("domerama_cf") is not None:
                row.label(text="Domerama %s: %.6f" % (
                    st.get("domerama_label") or "", st.get("domerama_cf") or 0.0))
            else:
                row.label(text="Domerama:")
            if st.get("sub_spread"):
                mm = st["sub_spread"] * radius * 1000.0
                table_box.label(text="  contains sub-types, spread %.3f mm" % mm)

        hub_box = layout.box()
        hub_box.label(text="Hubs")
        for valence in sorted(report["hub_valences"], key=lambda v: -int(v)):
            hub_box.label(text="%s-way: %s" % (valence, report["hub_valences"][valence]))

        if report.get("notes"):
            notes_box = layout.box()
            for note in report["notes"]:
                notes_box.label(text=note)

        row = layout.row(align=True)
        row.operator("geodome.export_csv", text="Export CSV")
        row.operator("geodome.copy_table", text="Copy Table")


class GEODOME_OT_export_csv(Operator):
    """Write the dome report to a CSV file"""
    bl_idname = "geodome.export_csv"
    bl_label = "Export Dome CSV"

    filepath: StringProperty(subtype='FILE_PATH')

    def invoke(self, context, event):
        obj = context.active_object
        report = _get_report(obj)
        if report is None:
            self.report({'ERROR'}, "Active object has no dome report.")
            return {'CANCELLED'}
        self.filepath = "dome_%s_%dV_%d-%d.csv" % (
            report["method"], report["frequency"], report["k"], report["denom"])
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        obj = context.active_object
        report = _get_report(obj)
        if report is None:
            self.report({'ERROR'}, "Active object has no dome report.")
            return {'CANCELLED'}
        lines = csv_lines(report, report.get("radius", 1.0), report.get("version", PLUGIN_VERSION))
        with open(self.filepath, "w", encoding="utf8", newline="") as f:
            f.write("\n".join(lines) + "\n")
        self.report({'INFO'}, "Wrote %s" % self.filepath)
        return {'FINISHED'}


class GEODOME_OT_copy_table(Operator):
    """Copy the strut table to the clipboard, tab separated"""
    bl_idname = "geodome.copy_table"
    bl_label = "Copy Dome Table"

    def execute(self, context):
        obj = context.active_object
        report = _get_report(obj)
        if report is None:
            self.report({'ERROR'}, "Active object has no dome report.")
            return {'CANCELLED'}
        radius = report.get("radius", 1.0)
        rows = ["label\tchord_factor\tbend_angle_deg\tlength_m\tcount"]
        for st in report["strut_types"]:
            rows.append("\t".join([
                st["label"],
                "%.8f" % st["chord_factor"],
                "%.4f" % st["bend_angle_deg"],
                "%.6f" % (st["chord_factor"] * radius),
                str(st["count"]),
            ]))
        context.window_manager.clipboard = "\n".join(rows)
        self.report({'INFO'}, "Copied strut table to clipboard.")
        return {'FINISHED'}


_CLASSES = (VIEW3D_PT_geodome_report, GEODOME_OT_export_csv, GEODOME_OT_copy_table)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
