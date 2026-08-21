"""
Ve lai hinh hoc tu bim_data.sqlite bang matplotlib, xuat ra PNG.
To mau Parcel theo trang thai tuan thu quy hoach (neu co bang compliance_checks).

Cach dung:
    python plot_bim.py "G:\\My Drive\\AI-AUTOCAD CIVIL 3D\\bim_data.sqlite"
"""

import sys
import sqlite3
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely import wkt as shapely_wkt

COLOR_OK = "#8fd694"
COLOR_VI_PHAM = "#f4a261"
COLOR_NGOAI = "#e63946"
COLOR_APPROX_EDGE = "#6c757d"
COLOR_BOUNDARY = "#264653"
COLOR_POINT = "#1d3557"
COLOR_ALIGNMENT = "#e76f51"


def load_data(db_path):
    conn = sqlite3.connect(db_path)

    parcels = conn.execute("""
        SELECT e.name, g.wkt, c.status, g.bbox_min_x, g.bbox_min_y, g.bbox_max_x, g.bbox_max_y
        FROM elements e
        JOIN element_geometry g ON e.element_id = g.element_id
        LEFT JOIN compliance_checks c ON c.element_id = e.element_id
        WHERE e.object_type = 'Parcel'
    """).fetchall()

    points = conn.execute("""
        SELECT g.centroid_x, g.centroid_y
        FROM elements e JOIN element_geometry g ON e.element_id = g.element_id
        WHERE e.object_type = 'CogoPoint'
    """).fetchall()

    alignments = conn.execute("""
        SELECT e.name, g.bbox_min_x, g.bbox_min_y, g.bbox_max_x, g.bbox_max_y
        FROM elements e JOIN element_geometry g ON e.element_id = g.element_id
        WHERE e.object_type = 'Alignment'
    """).fetchall()

    conn.close()
    return parcels, points, alignments


def status_color(status):
    if status is None:
        return "#cccccc"
    base = status.replace("_APPROX_BBOX", "")
    return {"OK": COLOR_OK, "VI_PHAM": COLOR_VI_PHAM, "NGOAI_HOAN_TOAN": COLOR_NGOAI}.get(base, "#cccccc")


def plot(db_path, out_path):
    parcels, points, alignments = load_data(db_path)

    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)

    for name, wkt_str, status, bx0, by0, bx1, by1 in parcels:
        approx = wkt_str is None or (status is not None and "_APPROX_BBOX" in status)
        if wkt_str is not None:
            poly = shapely_wkt.loads(wkt_str)
        else:
            # Khong doc duoc polygon that -> ve hinh chu nhat bao (bbox) net
            # dut de khong bo sot du lieu tren hinh, nhung van de phan biet
            # ro day la gia tri xap xi.
            from shapely.geometry import box
            poly = box(bx0, by0, bx1, by1)
        color = status_color(status)
        xs, ys = poly.exterior.xy
        patch = MplPolygon(
            list(zip(xs, ys)),
            closed=True,
            facecolor=color,
            edgecolor=COLOR_APPROX_EDGE if approx else "#333333",
            linewidth=1.2 if approx else 0.6,
            linestyle="--" if approx else "-",
            alpha=0.85,
        )
        ax.add_patch(patch)
        cx, cy = poly.centroid.x, poly.centroid.y
        ax.text(cx, cy, name.replace("STANDARD: ", "").replace("SINGLE-FAMILY: ", "SF"),
                ha="center", va="center", fontsize=4.5, color="#111111")

    if points:
        px = [p[0] for p in points]
        py = [p[1] for p in points]
        ax.scatter(px, py, s=1.5, color=COLOR_POINT, alpha=0.4, label=f"CogoPoint ({len(points)})", zorder=5)

    for name, minx, miny, maxx, maxy in alignments:
        ax.plot([minx, maxx], [miny, maxy], color=COLOR_ALIGNMENT, linewidth=1.5, linestyle=":",
                label="Alignment (bbox xap xi)", zorder=4)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_OK, edgecolor="#333333", label="Parcel OK"),
        plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_VI_PHAM, edgecolor="#333333", label="Parcel VI PHAM"),
        plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_NGOAI, edgecolor="#333333", label="Parcel NGOAI RANH"),
        plt.Line2D([0], [0], color=COLOR_APPROX_EDGE, linestyle="--", label="Vien net dut = xap xi bbox"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.9)

    ax.set_aspect("equal")
    ax.set_title(f"BIM Data — {os.path.basename(db_path)}", fontsize=13)
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.grid(True, linewidth=0.3, alpha=0.4)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Da luu: {out_path}")
    print(f"Parcel ve: {len(parcels)} | CogoPoint: {len(points)} | Alignment: {len(alignments)}")


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "bim_data.sqlite"
    out_path = os.path.splitext(db_path)[0] + "_plot.png"
    plot(db_path, out_path)


if __name__ == "__main__":
    main()
