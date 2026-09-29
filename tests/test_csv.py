import dataclasses

from core.build import build_dome
from core.report_csv import csv_lines


def test_csv_3v_kruschke_5_9():
    geometry = build_dome("KRUSCHKE", 3, 5)
    report_dict = dataclasses.asdict(geometry.report)
    lines = csv_lines(report_dict, radius=3.0, version="0.1.0")

    header = lines[0]
    assert header.startswith("# Geovisual Dome Tools")
    assert any(l.startswith("# method,") for l in lines)
    assert any(l.startswith("# frequency,3V") for l in lines)
    assert any(l.startswith("# fraction,5/9") for l in lines)
    assert any(l.startswith("# radius_m,3") for l in lines)
    assert any(l.startswith("# base_level,") for l in lines)

    strut_header_idx = lines.index(
        "strut,chord_factor,bend_angle_deg,length_m,count,total_length_m,domerama_label,domerama_cf")
    n_types = len(report_dict["strut_types"])
    n_hubs = len(report_dict["hub_valences"])
    strut_rows = lines[strut_header_idx + 1:strut_header_idx + 1 + n_types]
    hub_header = lines[strut_header_idx + 1 + n_types]
    assert hub_header == "hub_valence,count"
    hub_rows = lines[strut_header_idx + 2 + n_types:]
    assert len(strut_rows) == n_types
    assert len(hub_rows) == n_hubs

    assert strut_header_idx == 8  # 8 "#" metadata lines before the strut header

    a_row = strut_rows[0]
    assert a_row.startswith("A,0.32970646,")
    fields = a_row.split(",")
    assert fields[4] == "30"


def test_csv_no_em_dash():
    geometry = build_dome("KRUSCHKE", 3, 5)
    report_dict = dataclasses.asdict(geometry.report)
    lines = csv_lines(report_dict, radius=3.0, version="0.1.0")
    text = "\n".join(lines)
    assert "—" not in text
    assert "--" not in text
