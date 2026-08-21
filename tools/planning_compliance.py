"""
Kiem tra 94 Parcel thiet ke co nam trong ranh quy hoach (layer V-PROP-LINE) khong.
Ghi ket qua vao bang compliance_checks trong bim_data.sqlite va xuat bao cao markdown.

Cach dung:
    python planning_compliance.py "G:\\My Drive\\AI-AUTOCAD CIVIL 3D\\Parcel-3A.dwg"
"""

import sys
import os
import sqlite3
import win32com.client
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union, polygonize

BOUNDARY_LAYER = "V-PROP-LINE"
TOLERANCE_PCT = 0.5  # % dien tich nam ngoai ranh duoc coi la "cham nguong", khong tinh vi pham


def get_active_doc(target_path=None):
    acad_app = win32com.client.GetActiveObject("AutoCAD.Application")
    if target_path:
        for d in acad_app.Documents:
            if d.FullName and os.path.normcase(d.FullName) == os.path.normcase(target_path):
                d.Activate()
                break
        else:
            raise RuntimeError(f"File chua duoc mo trong Civil 3D: {target_path}")
    return acad_app.ActiveDocument


def build_boundary_polygon(doc, layer=BOUNDARY_LAYER):
    """Doc tat ca AcDbLine tren layer ranh quy hoach, noi thanh vong khep kin."""
    segments = []
    for ent in doc.ModelSpace:
        try:
            if ent.Layer == layer and ent.ObjectName == "AcDbLine":
                sp, ep = tuple(ent.StartPoint), tuple(ent.EndPoint)
                segments.append(LineString([(sp[0], sp[1]), (ep[0], ep[1])]))
        except Exception:
            pass
    if not segments:
        raise RuntimeError(f"Khong tim thay duong nao tren layer '{layer}'")

    merged = linemerge(unary_union(segments))
    polys = list(polygonize([merged] if merged.geom_type == "LineString" else list(merged.geoms)))
    if not polys:
        raise RuntimeError(f"{len(segments)} doan tren layer '{layer}' khong khep kin thanh vong duoc")
    # Neu co nhieu vong (hiem), lay vong dien tich lon nhat lam ranh chinh
    boundary = max(polys, key=lambda p: p.area)
    return boundary, len(segments)


def ensure_compliance_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compliance_checks (
            check_id        INTEGER PRIMARY KEY,
            element_id      INTEGER REFERENCES elements(element_id),
            boundary_layer  TEXT,
            status          TEXT,           -- 'OK' | 'VI_PHAM' | 'NGOAI_HOAN_TOAN'
            area_total_m2   REAL,
            area_outside_m2 REAL,
            pct_outside     REAL,
            checked_at      TEXT DEFAULT (datetime('now'))
        )
    """)


def run_compliance_check(db_path, boundary):
    conn = sqlite3.connect(db_path)
    ensure_compliance_table(conn)
    conn.execute("DELETE FROM compliance_checks WHERE boundary_layer=?", (BOUNDARY_LAYER,))

    rows = conn.execute("""
        SELECT e.element_id, e.name, g.wkt, g.bbox_min_x, g.bbox_min_y, g.bbox_max_x, g.bbox_max_y
        FROM elements e JOIN element_geometry g ON e.element_id = g.element_id
        WHERE e.object_type='Parcel'
    """).fetchall()

    from shapely import wkt as shapely_wkt
    from shapely.geometry import box
    results = []
    for element_id, name, wkt_str, bx0, by0, bx1, by1 in rows:
        low_confidence = wkt_str is None
        if wkt_str is not None:
            parcel_poly = shapely_wkt.loads(wkt_str)
            if not parcel_poly.is_valid:
                parcel_poly = parcel_poly.buffer(0)
        else:
            # Fallback: khong doc duoc polygon that (xem GeometryWarning) ->
            # dung hinh chu nhat bao (bbox) de kiem tra xap xi, ket qua danh
            # dau LOW-CONFIDENCE can ra hien truong/CAD kiem tra lai thu cong.
            parcel_poly = box(bx0, by0, bx1, by1)
        area_total = parcel_poly.area
        outside = parcel_poly.difference(boundary)
        area_outside = outside.area
        pct_outside = (area_outside / area_total * 100) if area_total else 0

        if pct_outside <= TOLERANCE_PCT:
            status = "OK"
        elif pct_outside >= 99.5:
            status = "NGOAI_HOAN_TOAN"
        else:
            status = "VI_PHAM"
        status_stored = status + ("_APPROX_BBOX" if low_confidence else "")

        conn.execute(
            "INSERT INTO compliance_checks (element_id, boundary_layer, status, area_total_m2, area_outside_m2, pct_outside) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (element_id, BOUNDARY_LAYER, status_stored, area_total, area_outside, round(pct_outside, 3)),
        )
        results.append((name, status, area_total, area_outside, pct_outside, low_confidence))

    conn.commit()
    conn.close()
    return results


def write_report(results, boundary, n_segments, out_path):
    n_total = len(results)
    n_ok = sum(1 for r in results if r[1] == "OK")
    n_vi_pham = sum(1 for r in results if r[1] == "VI_PHAM")
    n_ngoai = sum(1 for r in results if r[1] == "NGOAI_HOAN_TOAN")
    n_low_conf = sum(1 for r in results if r[5])

    lines = []
    lines.append("# Bao cao Tham dinh Quy hoach - Parcel-3A")
    lines.append("")
    lines.append(f"Ranh quy hoach: layer `{BOUNDARY_LAYER}` ({n_segments} doan, dien tich {boundary.area:,.2f} m2)")
    lines.append(f"Nguong bo qua sai so: {TOLERANCE_PCT}% dien tich nam ngoai ranh")
    lines.append("")
    lines.append(f"**Tong so parcel kiem tra: {n_total}**")
    lines.append(f"- OK (nam trong ranh): {n_ok}")
    lines.append(f"- VI PHAM (mot phan nam ngoai ranh): {n_vi_pham}")
    lines.append(f"- NGOAI HOAN TOAN (gan nhu toan bo ngoai ranh): {n_ngoai}")
    if n_low_conf:
        lines.append(f"- ⚠️ {n_low_conf} parcel dung hinh chu nhat bao (bbox) xap xi thay vi bien dang that "
                      f"(khong doc duoc polygon chinh xac) — can kiem tra thu cong lai trong Civil3D")
    lines.append("")

    if n_vi_pham or n_ngoai:
        lines.append("## Danh sach Parcel vi pham")
        lines.append("")
        lines.append("| Parcel | Trang thai | Dien tich (m2) | Dien tich ngoai ranh (m2) | % ngoai ranh |")
        lines.append("|---|---|---|---|---|")
        for name, status, area_total, area_outside, pct, low_conf in sorted(
            [r for r in results if r[1] != "OK"], key=lambda r: -r[4]
        ):
            tag = " (⚠️ xap xi bbox)" if low_conf else ""
            lines.append(f"| {name}{tag} | {status} | {area_total:,.2f} | {area_outside:,.2f} | {pct:.2f}% |")
        lines.append("")

    if n_low_conf:
        lines.append("## Parcel can kiem tra thu cong (khong doc duoc bien dang chinh xac)")
        lines.append("")
        for name, status, area_total, area_outside, pct, low_conf in results:
            if low_conf:
                lines.append(f"- **{name}**: trang thai xap xi = {status} ({pct:.2f}% ngoai ranh theo bbox)")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return n_ok, n_vi_pham, n_ngoai


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    doc = get_active_doc(target)
    dwg_path = doc.FullName
    db_path = os.path.join(os.path.dirname(dwg_path), "bim_data.sqlite")
    report_path = os.path.join(os.path.dirname(dwg_path), "BaoCao_ThamDinh_QuyHoach.md")

    print(f"Dang doc ranh quy hoach tu layer '{BOUNDARY_LAYER}'...")
    boundary, n_segments = build_boundary_polygon(doc)
    print(f"Ranh quy hoach: {n_segments} doan, dien tich {boundary.area:,.2f} m2, valid={boundary.is_valid}")

    print("Dang kiem tra tung parcel...")
    results = run_compliance_check(db_path, boundary)

    n_ok, n_vi_pham, n_ngoai = write_report(results, boundary, n_segments, report_path)
    print(f"OK: {n_ok} | VI PHAM: {n_vi_pham} | NGOAI HOAN TOAN: {n_ngoai}")
    print(f"Bao cao: {report_path}")


if __name__ == "__main__":
    main()
