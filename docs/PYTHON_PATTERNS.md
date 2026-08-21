# PYTHON_PATTERNS.md — Mẫu Code Python Chuẩn Civil 3D
> Runtime: CPython 3.x | Managed.NET API | Civil 3D **2027** | 2026-05-09
> Copy-paste các mẫu này — KHÔNG tự nghĩ lại cấu trúc Transaction.

---

## Mẫu 0: Khung Import Chuẩn (dùng cho mọi script)

```python
import sys, clr

clr.AddReference('AcMgd')
clr.AddReference('AcCoreMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AeccDbMgd')

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import (
    Transaction, OpenMode, ObjectId
)
from Autodesk.AutoCAD.Geometry import Point3d, Point2d
from Autodesk.Civil.ApplicationServices import CivilApplication
from Autodesk.Civil.DatabaseServices import (
    CivilDocument, Alignment, AlignmentCreationOptions,
    Profile, ProfileCreationOptions,
    Corridor, TinSurface, Network, Structure, Pipe,
    CogoPoint, Catchment
)

doc      = Application.DocumentManager.MdiActiveDocument
db       = doc.Database
ed       = doc.Editor
civil_db = CivilDocument.GetCivilDocument(db)
```

---

## Mẫu 1: Transaction Đọc (Read-Only)

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Lấy tất cả Alignment
        align_ids = civil_db.GetAlignmentIds()
        for aid in align_ids:
            align = tr.GetObject(aid, OpenMode.ForRead)
            print(f"[Alignment] {align.Name} | L={align.Length:.2f}m "
                  f"| Sta: {align.StartingStation:.2f}~{align.EndingStation:.2f}")
        tr.Commit()
```

---

## Mẫu 2: Transaction Ghi (Write / Tạo mới)

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Ví dụ: đổi tên Alignment
        align_id = ...  # lấy từ dict tên→id
        align = tr.GetObject(align_id, OpenMode.ForWrite)
        align.Name = "AL-MOI"

        tr.Commit()  # BẮT BUỘC — thiếu Commit() sẽ Rollback tự động
```

---

## Mẫu 3: Tạo Bình đồ (Alignment) từ CSV

```python
import pandas as pd

# --- Đọc dữ liệu khảo sát ---
df = pd.read_csv(r'G:\path\survey_data.csv')
# Cột: [Station, Easting, Northing, Type]  (Type: LINE / CURVE)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Lấy Site, Layer, Style IDs (lấy từ bản vẽ)
        site_id   = civil_db.SiteCollection[0].ObjectId
        layer_id  = db.LayerZero
        align_style_id = civil_db.Styles.AlignmentStyles[0].ObjectId
        label_style_id = civil_db.Styles.AlignmentLabelSetStyles[0].ObjectId

        options = AlignmentCreationOptions()
        options.StartingStation = float(df['Station'].iloc[0])

        align_id = Alignment.Create(
            db, "AL-TU-DONG", site_id, layer_id,
            align_style_id, label_style_id, options
        )
        align = tr.GetObject(align_id, OpenMode.ForWrite)

        # Thêm từng đoạn
        for i in range(len(df) - 1):
            pt1 = Point2d(df['Easting'].iloc[i],   df['Northing'].iloc[i])
            pt2 = Point2d(df['Easting'].iloc[i+1], df['Northing'].iloc[i+1])
            if df['Type'].iloc[i] == 'LINE':
                align.Entities.AddFixedLine(pt1, pt2)
            # CURVE: align.Entities.AddFreeCurve(...)

        tr.Commit()
        print(f"[OK] Alignment '{align.Name}' L={align.Length:.2f}m")
```

---

## Mẫu 4: Tạo Trắc dọc Thiết kế (FG Profile) — Layout

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)

        # Lấy ProfileView (khung vẽ trắc dọc)
        profile_view_id = align.GetProfileViewIds()[0]

        profile_style_id      = civil_db.Styles.ProfileStyles[0].ObjectId
        profile_label_style_id = civil_db.Styles.ProfileLabelSetStyles[0].ObjectId

        fg_profile_id = Profile.CreateByLayout(
            "FG-DESIGN",
            align_id,
            profile_view_id,
            profile_style_id,
            profile_label_style_id
        )

        fg_profile = tr.GetObject(fg_profile_id, OpenMode.ForWrite)

        # Thêm điểm PVI (Station, Elevation)
        pvi_data = [(0.0, 45.5), (200.0, 44.0), (500.0, 46.2)]
        for sta, elev in pvi_data:
            fg_profile.PVIs.AddPVI(sta, elev)

        tr.Commit()
        print(f"[OK] Profile FG tạo thành công: {fg_profile.Name}")
```

---

## Mẫu 5: Duyệt Mạng lưới Pipe Network

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net_ids = civil_db.GetPipeNetworkIds()
        print(f"Tìm thấy {net_ids.Count} mạng lưới ống")

        for net_id in net_ids:
            network = tr.GetObject(net_id, OpenMode.ForRead)
            print(f"\n[Network] {network.Name}")

            # Duyệt hố ga
            for struct_id in network.GetStructureIds():
                struct = tr.GetObject(struct_id, OpenMode.ForRead)
                pt = struct.InsertionPoint
                print(f"  Hố ga: {struct.Name} @ ({pt.X:.1f}, {pt.Y:.1f}, {pt.Z:.2f})")

            # Duyệt đường ống
            for pipe_id in network.GetPipeIds():
                pipe = tr.GetObject(pipe_id, OpenMode.ForRead)
                print(f"  Ống: {pipe.Name} | D={pipe.InnerDiameterOrWidth:.3f}m "
                      f"| i={pipe.Slope*100:.2f}%")

        tr.Commit()
```

---

## Mẫu 6: Tạo Điểm COGO từ Mảng Tọa độ

```python
import pandas as pd

df = pd.read_csv(r'G:\path\cogo_points.csv')
# Cột: [PointNo, Easting, Northing, Elevation, Description]

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        cogo_collection = civil_db.CogoPoints

        for _, row in df.iterrows():
            pt = Point3d(row['Easting'], row['Northing'], row['Elevation'])
            new_pt = cogo_collection.Add(pt, row['Description'])
            new_pt = tr.GetObject(new_pt, OpenMode.ForWrite)
            new_pt.PointNumber = int(row['PointNo'])

        tr.Commit()
        print(f"[OK] Đã tạo {len(df)} điểm COGO")
```

---

## Mẫu 7: Tính Siêu cao Đường sắt (Cant)

```python
# Công thức: Cant (mm) = 11.8 × V² / R
# V = tốc độ thiết kế (km/h), R = bán kính cong (m)

def tinh_sieu_cao(V_kmh: float, R_m: float) -> float:
    cant_mm = 11.8 * (V_kmh ** 2) / R_m
    return round(cant_mm, 1)

# Ví dụ: V=120 km/h, R=500m
cant = tinh_sieu_cao(120, 500)
print(f"Siêu cao = {cant} mm")  # → 339.8 mm

# Áp dụng vào Civil 3D
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)
        # Truy cập CANTCriticalStationCollection
        cant_stations = align.CANTCriticalStationCollection
        # Thiết lập giá trị siêu cao tại các Station...
        tr.Commit()
```

---

## Mẫu 8: Xuất Dữ liệu Hình học sang CSV

```python
import csv

output_path = r'G:\output\alignment_stations.csv'

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Station', 'Easting', 'Northing', 'Elevation'])

            station = align.StartingStation
            interval = 20.0  # Cách 20m lấy 1 điểm

            while station <= align.EndingStation:
                pt = align.GetPointAtStation(station)
                writer.writerow([f"{station:.3f}", f"{pt.X:.3f}",
                                 f"{pt.Y:.3f}", f"{pt.Z:.3f}"])
                station += interval

        tr.Commit()

print(f"[OK] Xuất ra: {output_path}")
```

---

## Lỗi Phổ biến và Cách Tránh

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| `eNotOpenForWrite` | Quên `UpgradeOpen()` | Dùng `OpenMode.ForWrite` hoặc `.UpgradeOpen()` |
| `eWasErased` | Object đã bị xóa | Kiểm tra `.IsErased` trước khi GetObject |
| `DocumentLockViolation` | Quên `LockDocument()` | Bọc trong `with doc.LockDocument()` |
| `NullReferenceException` | Collection rỗng | Kiểm tra `.Count > 0` trước khi duyệt |
| `UnicodeEncodeError` | Console không hỗ trợ UTF-8 | `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8')` |
