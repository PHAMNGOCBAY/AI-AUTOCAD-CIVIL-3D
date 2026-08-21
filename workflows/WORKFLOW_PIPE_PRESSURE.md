# WORKFLOW_PIPE_PRESSURE.md — Mạng lưới Ống Áp lực (Cấp nước)
> Civil 3D **2027** (API 2021.2+) | Python Managed.NET | 2026-05-09

---

## Mục đích

Tự động hóa thiết kế **mạng lưới cấp nước áp lực** (Pressure Pipe Network): tạo tuyến ống, phụ kiện, van, và kết nối dữ liệu GIS hai chiều.

---

## Lịch sử API & Giới hạn Kỹ thuật

| Phiên bản | Tính năng mở khóa |
|---|---|
| C3D 2021 | Ra mắt `Pipe Runs` — mô hình theo Alignment + Profile cơ sở |
| C3D 2021.2 | API `AddPipe` chính thức, xóa giới hạn PartSize cũ |
| C3D 2022+ | CPython 3 → dùng được pandas, geopandas với GIS data |
| Hiện tại | Fittings/Appurtenances cần kỹ thuật **Reflection** (API chưa mở hoàn toàn) |

> [!WARNING]
> Thêm phụ kiện (Fittings) và van (Appurtenances) yêu cầu `System.Reflection` vì Autodesk chưa public các lớp nội bộ. Xem Bước 4.

---

## Bước 1: Tạo Pressure Pipe Network

```python
from Autodesk.Civil.DatabaseServices import (
    PressurePipe, PressurePipeNetwork, PressurePartType
)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Tạo mạng lưới áp lực mới
        network_name = "WM-TUYEN-CHINH"
        parts_list_id = civil_db.PressurePartLists[0].ObjectId  # Catalog mặc định

        net_id = PressurePipeNetwork.Create(
            db,
            network_name,
            parts_list_id,
            db.LayerZero
        )
        net = tr.GetObject(net_id, OpenMode.ForWrite)

        # Gắn với Alignment và Profile (Pipe Run)
        run_id = net.PipeRuns.Add("Run-Main", align_id, fg_profile_id)

        tr.Commit()
        print(f"[OK] Tạo Pressure Network '{network_name}'")
```

---

## Bước 2: Thêm Đoạn Ống (AddPipe)

```python
from Autodesk.AutoCAD.Geometry import Point3d

# Dữ liệu ống từ thiết kế
pipe_segments = [
    {'start': (587000, 2345000, 45.0), 'end': (587100, 2345020, 44.5),
     'diameter_mm': 200, 'material': 'HDPE'},
    {'start': (587100, 2345020, 44.5), 'end': (587250, 2345050, 44.0),
     'diameter_mm': 200, 'material': 'HDPE'},
]

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net = tr.GetObject(net_id, OpenMode.ForWrite)
        run = tr.GetObject(run_id, OpenMode.ForWrite)

        for seg in pipe_segments:
            start_pt = Point3d(*seg['start'])
            end_pt   = Point3d(*seg['end'])

            # Lấy PartSize phù hợp từ catalog
            part_size_id = get_part_size_id(
                civil_db, seg['diameter_mm'], seg['material']
            )  # Hàm helper — xem Bước 3

            pipe_id = run.AddPipe(part_size_id, start_pt, end_pt)
            pipe    = tr.GetObject(pipe_id, OpenMode.ForWrite)

            # Ống áp lực tự uốn cong theo bán kính cho phép
            print(f"  Thêm ống D{seg['diameter_mm']}mm: "
                  f"L={pipe.Length:.2f}m | Cover={pipe.CoverDepth:.2f}m")

        tr.Commit()
        print(f"[OK] Thêm {len(pipe_segments)} đoạn ống")
```

---

## Bước 3: Hàm Helper — Lấy PartSize từ Catalog

```python
def get_part_size_id(civil_db, diameter_mm: int, material: str):
    """Tìm PartSize trong catalog theo đường kính và vật liệu."""
    for parts_list in civil_db.PressurePartLists:
        for part_family in parts_list.PartFamilies:
            if material.upper() in part_family.Name.upper():
                for part_size in part_family.PartSizes:
                    if abs(part_size.InnerDiameter * 1000 - diameter_mm) < 5:
                        return part_size.ObjectId
    raise ValueError(f"Không tìm thấy ống D{diameter_mm}mm material={material}")
```

---

## Bước 4: Thêm Van và Phụ kiện (Reflection Technique)

```python
import System.Reflection as Reflection

def add_appurtenance_by_reflection(net, run, location: Point3d,
                                    appurtenance_name: str):
    """
    Thêm van/phụ kiện qua Reflection vì API chưa public.
    appurtenance_name: 'Gate Valve', 'Ball Valve', 'Tee', 'Elbow'
    """
    net_type = type(net)
    methods  = net_type.GetMethods(
        Reflection.BindingFlags.Instance |
        Reflection.BindingFlags.NonPublic |
        Reflection.BindingFlags.Public
    )

    add_method = next((m for m in methods if 'AddAppurtenance' in m.Name), None)
    if add_method is None:
        print(f"[WARN] Không tìm thấy method AddAppurtenance — bỏ qua")
        return None

    # Lấy PartSize ID cho phụ kiện
    app_part_id = get_appurtenance_part_id(civil_db, appurtenance_name)
    result = add_method.Invoke(net, [run.ObjectId, app_part_id, location])
    return result

# Thêm van khóa tại điểm phân nhánh
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net = tr.GetObject(net_id, OpenMode.ForWrite)
        run = tr.GetObject(run_id, OpenMode.ForWrite)

        valve_location = Point3d(587150, 2345035, 44.3)
        add_appurtenance_by_reflection(net, run, valve_location, 'Gate Valve')

        tr.Commit()
        print("[OK] Thêm van khóa")
```

---

## Bước 5: Tích hợp GIS Hai chiều (Esri Geodatabase)

```python
import geopandas as gpd
from shapely.geometry import Point, LineString

# === Đọc dữ liệu từ GIS (Esri Geodatabase / GeoJSON) ===
gdf_pipes = gpd.read_file(r'G:\GIS\WaterNetwork.gdb', layer='Pipes')
gdf_nodes = gpd.read_file(r'G:\GIS\WaterNetwork.gdb', layer='Nodes')

print(f"GIS: {len(gdf_pipes)} ống, {len(gdf_nodes)} nút")

# Cập nhật thuộc tính từ Civil 3D → GIS
pipe_updates = []
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net = tr.GetObject(net_id, OpenMode.ForRead)
        for run_id in net.PipeRuns:
            run = tr.GetObject(run_id, OpenMode.ForRead)
            for pipe_id in run.GetPipeIds():
                p = tr.GetObject(pipe_id, OpenMode.ForRead)
                pipe_updates.append({
                    'PIPE_ID':     p.Name,
                    'COVER_DEPTH': p.CoverDepth,
                    'PRESSURE':    p.AllowableWorkingPressure,
                    'MATERIAL':    p.PartFamilyName,
                    'geometry':    LineString([
                        (p.StartPoint.X, p.StartPoint.Y),
                        (p.EndPoint.X,   p.EndPoint.Y)
                    ])
                })
        tr.Commit()

# Ghi ngược vào GIS
gdf_updated = gpd.GeoDataFrame(pipe_updates, crs="EPSG:4756")  # VN2000
gdf_updated.to_file(r'G:\GIS\output\WaterNetwork_Updated.geojson',
                    driver='GeoJSON')
print(f"[OK] Cập nhật {len(pipe_updates)} ống vào GIS")
```

---

## Bước 6: Tạo Cấu kiện Áp lực Custom từ Solid 3D

```python
# Khi catalog không có phụ kiện cần thiết → tạo từ SQLite catalog

import sqlite3

catalog_db_path = r'C:\ProgramData\Autodesk\C3D 2027\enu\Pipes Catalog\Metric\PressurePipes.sqlite'
conn = sqlite3.connect(catalog_db_path)

# Thêm ký lục vào catalog
conn.execute("""
    INSERT INTO PartSizes (FamilyID, Name, InnerDiameter, OuterDiameter, Material)
    VALUES (?, ?, ?, ?, ?)
""", (family_id, "HDPE-250", 0.250, 0.284, "HDPE"))
conn.commit()
conn.close()

print("[OK] Thêm phụ kiện custom vào catalog SQLite")
```

---

## Checklist Kiểm tra

- [ ] Tất cả ống có độ chôn sâu ≥ 0.8m (tránh tải trọng xe)
- [ ] Áp lực làm việc ≤ 0.8 × áp lực thử nghiệm
- [ ] Không có ống đi ngược lên quá góc ≤ 15° (gây túi khí)
- [ ] Van khóa đặt tại mỗi đoạn ≤ 500m
- [ ] GIS và Civil 3D đồng bộ sau mỗi phiên làm việc
