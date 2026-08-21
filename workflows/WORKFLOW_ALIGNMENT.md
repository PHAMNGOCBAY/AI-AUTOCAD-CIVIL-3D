# WORKFLOW_ALIGNMENT.md — Tự động hóa Bình đồ (Alignment)
> Civil 3D **2027** | Python Managed.NET | 2026-05-09

---

## Mục đích

Hướng dẫn AI Agent tự động hóa toàn bộ quy trình thiết kế **Bình đồ (Alignment)** — từ đọc dữ liệu khảo sát đến tạo đối tượng Alignment hoàn chỉnh trong Civil 3D.

---

## Đầu vào Hỗ trợ

| Loại | Định dạng | Cột bắt buộc |
|---|---|---|
| Tọa độ lý trình | CSV | `Station, Easting, Northing, Type` |
| Điểm khảo sát | CSV | `PointNo, Easting, Northing, Elevation` |
| Tọa độ từ PDF | PDF → pandas extract | `Easting, Northing` |
| Dữ liệu GIS | Shapefile / GeoJSON | geometry LineString |

**Giá trị cột `Type`**: `LINE` (đoạn thẳng) | `CURVE` (đường cong) | `SPIRAL` (xoắn ốc)

---

## Quy trình 5 Bước

### Bước 1: Đọc và Chuẩn bị Dữ liệu

```python
import pandas as pd
import numpy as np

df = pd.read_csv(r'G:\path\survey_data.csv')

# Lọc bỏ các góc sai lệch (>170° → có thể là điểm nhiễu)
def tinh_goc(p1, p2, p3):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos_a, -1, 1)))

# Phân loại đoạn thẳng vs đường cong
points = list(zip(df['Easting'], df['Northing']))
filtered_points = [points[0]]
for i in range(1, len(points) - 1):
    angle = tinh_goc(points[i-1], points[i], points[i+1])
    if angle < 170:  # Giữ lại điểm gãy thực sự
        filtered_points.append(points[i])
filtered_points.append(points[-1])

print(f"Giữ lại {len(filtered_points)}/{len(points)} điểm sau lọc góc")
```

### Bước 2: Khởi tạo Alignment trong Civil 3D

```python
# [Chạy trong Dynamo Python Node hoặc CivilPython]
import clr
clr.AddReference('AcMgd'); clr.AddReference('AcDbMgd'); clr.AddReference('AeccDbMgd')
from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.AutoCAD.Geometry import Point2d
from Autodesk.Civil.DatabaseServices import *

doc      = Application.DocumentManager.MdiActiveDocument
db       = doc.Database
civil_db = CivilDocument.GetCivilDocument(db)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Lấy IDs cần thiết
        site_id        = civil_db.SiteCollection[0].ObjectId
        align_style_id = civil_db.Styles.AlignmentStyles[0].ObjectId
        label_style_id = civil_db.Styles.AlignmentLabelSetStyles[0].ObjectId

        options = AlignmentCreationOptions()
        options.StartingStation = 0.0

        align_id = Alignment.Create(
            db,
            "AL-TU-DONG-01",     # Tên Alignment
            site_id,
            db.LayerZero,
            align_style_id,
            label_style_id,
            options
        )
        align = tr.GetObject(align_id, OpenMode.ForWrite)
        tr.Commit()
print(f"[OK] Tạo Alignment ID: {align_id}")
```

### Bước 3: Thêm Phần tử Hình học

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)

        for i in range(len(filtered_points) - 1):
            pt1 = Point2d(*filtered_points[i])
            pt2 = Point2d(*filtered_points[i+1])

            seg_type = df['Type'].iloc[i] if i < len(df) else 'LINE'

            if seg_type == 'LINE':
                align.Entities.AddFixedLine(pt1, pt2)

            elif seg_type == 'CURVE':
                # Lấy bán kính từ dữ liệu đầu vào
                radius = float(df['Radius'].iloc[i]) if 'Radius' in df.columns else 300.0
                # Curve tiếp xúc với đoạn trước và sau
                ent_before = align.Entities[align.Entities.Count - 1]
                align.Entities.AddFreeCircularCurve(ent_before, pt2, radius,
                                                     CurveType.MoreOrLessParallel)

            elif seg_type == 'SPIRAL':
                clothoid_param = float(df['ClothoidA'].iloc[i]) if 'ClothoidA' in df.columns else 200.0
                align.Entities.AddFixedSpiral(pt1, pt2, clothoid_param,
                                               SpiralType.Clothoid)

        tr.Commit()
        print(f"[OK] Thêm {align.Entities.Count} phần tử hình học")
        print(f"     Chiều dài tổng: {align.Length:.3f}m")
```

### Bước 4: Thiết lập Lý trình (Station Equations)

```python
# Nếu có đoạn lý trình bất thường (cầu, hầm...)
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)
        # Thêm Station Equation tại KM3+000
        # align.StationEquations.Add(raw_station, station_value, increasing=True)
        tr.Commit()
```

### Bước 5: Xuất Kết quả và Log

```python
import csv, datetime

output_csv = r'G:\output\alignment_stations.csv'

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)

        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Station', 'Easting', 'Northing'])
            sta = align.StartingStation
            while sta <= align.EndingStation:
                pt = align.GetPointAtStation(sta)
                w.writerow([f"{sta:.3f}", f"{pt.X:.3f}", f"{pt.Y:.3f}"])
                sta += 20.0  # Cách 20m

        tr.Commit()

print(f"[OK] Xuất {output_csv}")
print(f"[LOG] {datetime.datetime.now()} | Alignment '{align.Name}' | L={align.Length:.2f}m")
```

---

## Checklist Kiểm tra Sau khi Tạo

- [ ] Chiều dài Alignment khớp với tổng khoảng cách điểm đầu-cuối (±0.1%)
- [ ] Bán kính cong tối thiểu ≥ R_min theo tiêu chuẩn dự án
- [ ] Không có đoạn gãy góc đột ngột (kiểm tra góc lệch < 170°)
- [ ] Alignment nằm trong giới hạn bề mặt TIN (Surface extents)
- [ ] Layer hiển thị đúng trong bản vẽ

---

## Thông số Kỹ thuật Tiêu chuẩn Việt Nam

| Loại đường | Vận tốc (km/h) | R_min (m) | Độ dốc ngang max |
|---|---|---|---|
| Cao tốc | 120 | 650 | 6% |
| Quốc lộ cấp I | 100 | 400 | 7% |
| Quốc lộ cấp II | 80 | 250 | 7% |
| Đường đô thị | 60 | 125 | 8% |
| Đường nội bộ | 40 | 60 | 8% |

---

## Các lỗi Thường gặp

| Lỗi | Fix |
|---|---|
| `eInvalidInput` khi AddFixedLine | Hai điểm trùng nhau — kiểm tra khoảng cách > 0.001m |
| Alignment tạo nhưng không có entity | Phải gọi `Entities.Add*` sau khi `Alignment.Create()` |
| Curve không tiếp xúc | Đảm bảo ent_before là entity cuối cùng trước curve |
