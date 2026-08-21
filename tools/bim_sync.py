"""
Dong bo du lieu BIM tu Civil 3D (COM automation) vao SQLite theo tung project.
Chay thu cong khi can (khong chay nen/tu dong).

Cach dung:
    python bim_sync.py "G:\\My Drive\\AI-AUTOCAD CIVIL 3D\\Parcel-3A.dwg"

Neu khong truyen duong dan, dung ActiveDocument dang mo trong Civil 3D.
File SQLite duoc tao cung thu muc voi file .dwg, ten "bim_data.sqlite".
"""

import sys
import os
import math
import sqlite3
import win32com.client
from shapely.geometry import Polygon

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "bim_schema.sql")


def _circle_from_3pts(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    return (ux, uy), r


def _norm_angle(a):
    while a < 0:
        a += 2 * math.pi
    while a >= 2 * math.pi:
        a -= 2 * math.pi
    return a


def bulge_to_arc_points(sx, sy, ex, ey, bulge, n_segments=32):
    """Noi suy cung tron tu bulge factor (chuan AutoCAD) thanh cac diem thang.
    Dung cach dung duong tron qua 3 diem (dau - giua cung - cuoi) thay vi
    suy tam bang cong thuc dau (de sai dau khi bulge am/duong).
    bulge = 2*sagitta/chord (dinh nghia DXF). Tra ve danh sach diem
    TRUNG GIAN (khong bao gom diem dau/cuoi)."""
    if bulge == 0:
        return []
    length = math.hypot(ex - sx, ey - sy)
    if length == 0:
        return []
    sagitta = bulge * length / 2
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    perp_x, perp_y = -dy / length, dx / length
    amx, amy = mx + perp_x * sagitta, my + perp_y * sagitta  # diem giua cung that

    (cx, cy), r = _circle_from_3pts((sx, sy), (amx, amy), (ex, ey))
    a_start = _norm_angle(math.atan2(sy - cy, sx - cx))
    a_mid = _norm_angle(math.atan2(amy - cy, amx - cx))
    a_end = _norm_angle(math.atan2(ey - cy, ex - cx))

    ccw_total = (a_end - a_start) if a_end >= a_start else (a_end - a_start + 2 * math.pi)
    ccw_to_mid = (a_mid - a_start) if a_mid >= a_start else (a_mid - a_start + 2 * math.pi)
    if ccw_to_mid <= ccw_total + 1e-9:
        sweep, direction = ccw_total, 1
    else:
        sweep, direction = 2 * math.pi - ccw_total, -1

    points = []
    for i in range(1, n_segments):
        t = a_start + direction * sweep * (i / n_segments)
        points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return points


def get_parcel_polygon(parcel_bound):
    """Doc toa do dinh THAT cua parcel qua ParcelLoops -> Segments,
    tra ve shapely Polygon (co tessellate cung tron qua bulge)."""
    loops = win32com.client.gencache.EnsureDispatch(parcel_bound.ParcelLoops)
    rings = []
    for li in range(loops.Count):
        loop = win32com.client.gencache.EnsureDispatch(loops.Item(li))
        ring = []
        for si in range(loop.Count):
            seg = win32com.client.gencache.EnsureDispatch(loop.Item(si))
            ring.append((seg.StartX, seg.StartY))
            # Segment thang (IAeccParcelSegmentLine) khong co thuoc tinh Bulge -
            # chi segment cung (IAeccParcelSegmentArc) moi co.
            bulge = getattr(seg, "Bulge", 0)
            ring.extend(bulge_to_arc_points(seg.StartX, seg.StartY, seg.EndX, seg.EndY, bulge))
        if ring:
            ring.append(ring[0])
            rings.append(ring)
    if not rings:
        return None
    return Polygon(rings[0], rings[1:] if len(rings) > 1 else None)


def get_active_doc(target_path=None):
    acad_app = win32com.client.GetActiveObject("AutoCAD.Application")
    aec_app = acad_app.GetInterfaceObject("AeccXUiLand.AeccApplication.13.9")

    if target_path:
        for d in acad_app.Documents:
            if d.FullName and os.path.normcase(d.FullName) == os.path.normcase(target_path):
                d.Activate()
                break
        else:
            raise RuntimeError(f"File chua duoc mo trong Civil 3D: {target_path}")

    return acad_app.ActiveDocument, aec_app.ActiveDocument


def open_db(dwg_path):
    db_path = os.path.join(os.path.dirname(dwg_path), "bim_data.sqlite")
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    # Migration: them cot moi vao bang da ton tai tu truoc (IF NOT EXISTS
    # khong tu them cot cho table cu).
    cols = [r[1] for r in conn.execute("PRAGMA table_info(element_geometry)")]
    if "wkt" not in cols:
        conn.execute("ALTER TABLE element_geometry ADD COLUMN wkt TEXT")
    return conn, db_path


def upsert_model(conn, dwg_path):
    cur = conn.execute(
        "INSERT INTO models (file_path, civil3d_version, last_synced_at) "
        "VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(file_path) DO UPDATE SET last_synced_at = datetime('now') "
        "RETURNING model_id",
        (dwg_path, "2027"),
    )
    return cur.fetchone()[0]


def upsert_element(conn, model_id, handle, object_type, category, layer, name, site_name=None):
    cur = conn.execute(
        "INSERT INTO elements (model_id, handle, object_type, category, layer, name, site_name) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(model_id, handle) DO UPDATE SET "
        "  category=excluded.category, layer=excluded.layer, name=excluded.name, site_name=excluded.site_name "
        "RETURNING element_id",
        (model_id, handle, object_type, category, layer, name, site_name),
    )
    return cur.fetchone()[0]


def set_property(conn, element_id, prop_name, prop_value, prop_unit=None):
    if prop_value is None:
        return
    conn.execute(
        "INSERT INTO element_properties (element_id, prop_name, prop_value, prop_unit) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(element_id, prop_name) DO UPDATE SET prop_value=excluded.prop_value, prop_unit=excluded.prop_unit",
        (element_id, prop_name, str(prop_value), prop_unit),
    )


def set_geometry_from_bbox(conn, element_id, geom_type, min_pt, max_pt):
    cx = (min_pt[0] + max_pt[0]) / 2
    cy = (min_pt[1] + max_pt[1]) / 2
    cz = (min_pt[2] + max_pt[2]) / 2
    conn.execute(
        "INSERT INTO element_geometry "
        "(element_id, geom_type, centroid_x, centroid_y, centroid_z, bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(element_id) DO UPDATE SET "
        "  geom_type=excluded.geom_type, centroid_x=excluded.centroid_x, centroid_y=excluded.centroid_y, "
        "  centroid_z=excluded.centroid_z, bbox_min_x=excluded.bbox_min_x, bbox_min_y=excluded.bbox_min_y, "
        "  bbox_max_x=excluded.bbox_max_x, bbox_max_y=excluded.bbox_max_y",
        (element_id, geom_type, cx, cy, cz, min_pt[0], min_pt[1], max_pt[0], max_pt[1]),
    )


def set_geometry_polygon(conn, element_id, polygon, elevation=0.0):
    """Ghi geometry CHINH XAC (khong xap xi bbox) - dung cho parcel can
    doi chieu voi ranh quy hoach."""
    cx, cy = polygon.centroid.x, polygon.centroid.y
    minx, miny, maxx, maxy = polygon.bounds
    conn.execute(
        "INSERT INTO element_geometry "
        "(element_id, geom_type, centroid_x, centroid_y, centroid_z, bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y, wkt) "
        "VALUES (?, 'Polygon', ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(element_id) DO UPDATE SET "
        "  centroid_x=excluded.centroid_x, centroid_y=excluded.centroid_y, centroid_z=excluded.centroid_z, "
        "  bbox_min_x=excluded.bbox_min_x, bbox_min_y=excluded.bbox_min_y, "
        "  bbox_max_x=excluded.bbox_max_x, bbox_max_y=excluded.bbox_max_y, wkt=excluded.wkt",
        (element_id, cx, cy, elevation, minx, miny, maxx, maxy, polygon.wkt),
    )


def set_geometry_point(conn, element_id, x, y, z):
    conn.execute(
        "INSERT INTO element_geometry "
        "(element_id, geom_type, centroid_x, centroid_y, centroid_z, bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y) "
        "VALUES (?, 'Point', ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(element_id) DO UPDATE SET "
        "  centroid_x=excluded.centroid_x, centroid_y=excluded.centroid_y, centroid_z=excluded.centroid_z, "
        "  bbox_min_x=excluded.bbox_min_x, bbox_min_y=excluded.bbox_min_y, bbox_max_x=excluded.bbox_max_x, bbox_max_y=excluded.bbox_max_y",
        (element_id, x, y, z, x, y, x, y),
    )


def sync_parcels(conn, model_id, aecdoc):
    count = 0
    for site in aecdoc.Sites:
        for p in site.Parcels:
            eid = upsert_element(
                conn, model_id,
                handle=p.Handle, object_type="Parcel",
                category=p.StyleName, layer=p.Layer,
                name=p.Name, site_name=site.Name,
            )
            set_property(conn, eid, "Number", p.Number)
            # Area/Perimeter khong nam truc tiep tren Parcel ma trong sub-object
            # Statistics - can EnsureDispatch (early-bound) moi truy cap duoc.
            p_bound = win32com.client.gencache.EnsureDispatch(p)
            stats = win32com.client.gencache.EnsureDispatch(p_bound.Statistics)
            set_property(conn, eid, "Area", stats.Area, "m2")
            set_property(conn, eid, "Perimeter", stats.Perimeter, "m")

            # Xoa property cu (neu co tu lan sync truoc) de tranh du lieu
            # ton du khi ket qua lan nay khac nhanh (VD: valid -> invalid).
            conn.execute(
                "DELETE FROM element_properties WHERE element_id=? AND prop_name IN "
                "('Area_Shapely_CheckDiffPct','GeometryWarning')", (eid,)
            )

            polygon = get_parcel_polygon(p_bound)
            if polygon is not None and not polygon.is_valid:
                # Tu sua loi hinh hoc nho (self-intersection do sai so lam tron
                # khi tessellate cung) - ky thuat buffer(0) chuan cua shapely.
                polygon = polygon.buffer(0)
                if polygon.geom_type != "Polygon":
                    polygon = None

            if polygon is not None and polygon.is_valid and not polygon.is_empty:
                set_geometry_polygon(conn, eid, polygon)
                # Doi chieu Area tinh tu polygon that voi Area cua Civil3D -
                # canh bao neu lech nhieu (dau hieu doc sai loop/segment).
                shapely_area = polygon.area
                set_property(conn, eid, "Area_Shapely_CheckDiffPct",
                             round(abs(shapely_area - stats.Area) / stats.Area * 100, 3) if stats.Area else None)
            else:
                min_pt, max_pt = p_bound.GetBoundingBox()
                set_geometry_from_bbox(conn, eid, "Polygon", min_pt, max_pt)
                set_property(conn, eid, "GeometryWarning", "Khong doc duoc polygon that, dung bbox xap xi")
            count += 1
    return count


def sync_alignments(conn, model_id, aecdoc):
    count = 0
    for a in aecdoc.AlignmentsSiteless:
        eid = upsert_element(
            conn, model_id,
            handle=a.Handle, object_type="Alignment",
            category=a.StyleName, layer=None, name=a.Name,
        )
        set_property(conn, eid, "Length", a.Length, "m")
        a_bound = win32com.client.gencache.EnsureDispatch(a)
        min_pt, max_pt = a_bound.GetBoundingBox()
        set_geometry_from_bbox(conn, eid, "LineString", min_pt, max_pt)
        count += 1
    return count


def sync_surfaces(conn, model_id, aecdoc):
    count = 0
    for s in aecdoc.Surfaces:
        eid = upsert_element(
            conn, model_id,
            handle=s.Handle, object_type="Surface",
            category=s.StyleName, layer=None, name=s.Name,
        )
        s_bound = win32com.client.gencache.EnsureDispatch(s)
        min_pt, max_pt = s_bound.GetBoundingBox()
        set_geometry_from_bbox(conn, eid, "Surface", min_pt, max_pt)
        count += 1
    return count


def sync_points(conn, model_id, aecdoc):
    count = 0
    for pt in aecdoc.Points:
        eid = upsert_element(
            conn, model_id,
            handle=pt.Handle, object_type="CogoPoint",
            category=pt.RawDescription, layer=None, name=pt.Name,
        )
        set_property(conn, eid, "Easting", pt.Easting, "m")
        set_property(conn, eid, "Northing", pt.Northing, "m")
        set_property(conn, eid, "Elevation", pt.Elevation, "m")
        set_geometry_point(conn, eid, pt.Easting, pt.Northing, pt.Elevation)
        count += 1
    return count


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    doc, aecdoc = get_active_doc(target)
    dwg_path = doc.FullName
    print(f"Dang dong bo: {dwg_path}")

    conn, db_path = open_db(dwg_path)
    model_id = upsert_model(conn, dwg_path)

    n_parcel = sync_parcels(conn, model_id, aecdoc)
    n_align = sync_alignments(conn, model_id, aecdoc)
    n_surf = sync_surfaces(conn, model_id, aecdoc)
    n_pts = sync_points(conn, model_id, aecdoc)

    conn.execute(
        "INSERT INTO change_log (element_id, action, detail) VALUES (NULL, 'SYNC', ?)",
        (f"Parcel={n_parcel} Alignment={n_align} Surface={n_surf} CogoPoint={n_pts}",),
    )
    conn.commit()
    conn.close()

    print(f"DB: {db_path}")
    print(f"Parcel: {n_parcel} | Alignment: {n_align} | Surface: {n_surf} | CogoPoint: {n_pts}")


if __name__ == "__main__":
    main()
