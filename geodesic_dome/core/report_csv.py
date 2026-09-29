"""Pure CSV row assembly for the dome report. Design.md 10.6."""

_METHOD_NAMES = {
    "CLASS_I": "Icosa Class I Method 1",
    "KRUSCHKE": "Kruschke",
    "CUSTOM": "Custom chord table",
}


def _fmt(value, decimals):
    return ("%." + str(decimals) + "f") % value


def csv_lines(report_dict, radius, version):
    """Build CSV lines (no trailing newline) for a DomeReport dict."""
    lines = []
    lines.append("# Geodesic Dome Builder %s" % version)
    method_name = _METHOD_NAMES.get(report_dict["method"], report_dict["method"])
    lines.append("# method,%s" % method_name)
    lines.append("# frequency,%dV" % report_dict["frequency"])
    frac = "%d/%d" % (report_dict["k"], report_dict["denom"])
    alias = report_dict.get("alias")
    if alias:
        lines.append("# fraction,%s,alias,%s" % (frac, alias))
    else:
        lines.append("# fraction,%s" % frac)
    lines.append("# radius_m,%s" % _fmt(radius, 1))
    height_m = report_dict["height_factor"] * radius
    lines.append("# height_m,%s" % _fmt(height_m, 6))
    base_radius_factor = report_dict.get("base_radius_factor")
    if base_radius_factor is not None:
        base_diameter_m = 2.0 * base_radius_factor * radius
        lines.append("# base_diameter_m,%s" % _fmt(base_diameter_m, 6))
    else:
        lines.append("# base_diameter_m,n/a")
    lines.append("# base_level,%s" % ("yes" if report_dict["base_is_level"] else "no"))

    lines.append("strut,chord_factor,bend_angle_deg,length_m,count,total_length_m,domerama_label,domerama_cf")
    for st in report_dict["strut_types"]:
        length_m = st["chord_factor"] * radius
        total_length_m = length_m * st["count"]
        dlabel = st.get("domerama_label") or ""
        dcf = _fmt(st["domerama_cf"], 8) if st.get("domerama_cf") is not None else ""
        lines.append(",".join([
            st["label"],
            _fmt(st["chord_factor"], 8),
            _fmt(st["bend_angle_deg"], 4),
            _fmt(length_m, 6),
            str(st["count"]),
            _fmt(total_length_m, 6),
            dlabel,
            dcf,
        ]))

    lines.append("hub_valence,count")
    for valence in sorted(report_dict["hub_valences"], key=lambda v: -int(v)):
        lines.append("%s,%s" % (valence, report_dict["hub_valences"][valence]))

    return lines
