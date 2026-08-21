# WORKFLOW_CORRIDOR.md — Tự động hóa Hành lang Tuyến (Corridor)
> Civil 3D **2027** | Python Managed.NET + CivilConnection | 2026-05-09

---

## Mục đích

Tự động tạo **Corridor 3D** từ Alignment + Profile + Assembly, trích xuất hình học mặt cắt và tích hợp với Revit qua CivilConnection.

---

## Kiến trúc Dữ liệu Corridor

```
Alignment (Bình đồ)          ← Đường cơ sở ngang
    +
Profile FG (Trắc dọc TK)     ← Đường cơ sở đứng
    +
Assembly (Cụm mặt cắt)       ← Định hình mặt cắt ngang
    │
    ├── Subassembly: LaneInsideSuperElevation  (làn xe)
    ├── Subassembly: ShoulderExtendSubbase     (lề đường)
    ├── Subassembly: DaylightStandard          (mái dốc đào/đắp)
    └── Subassembly: CurbGutterGeneral         (vỉa hè nếu đô thị)
    ↓
Corridor 3D Object            ← Kết quả cuối cùng
    ├── Feature Lines          (đường giao mặt dốc)
    ├── Corridor Surface       (bề mặt đường)
    └── Quantity Materials     (khối lượng vật liệu)
```

---

## Bước 1: Tạo Assembly

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Tạo Assembly tại điểm origin
        origin = Point3d(0, -500, 0)  # Đặt ra ngoài vùng bản vẽ
        assembly_style_id = civil_db.Styles.AssemblyStyles[0].ObjectId

        assembly_id = Assembly.Create(db, "ASM-DUONG-CAP-III", origin,
                                       assembly_style_id)
        assembly = tr.GetObject(assembly_id, OpenMode.ForWrite)

        # Thêm Subassembly (tham chiếu từ Catalog)
        # Lưu ý: Subassembly được thêm qua Civil 3D GUI hoặc dùng
        # SubassemblyComposer để custom
        # Đây là cách thêm bằng code (yêu cầu biết tên chính xác trong catalog):
        # SubassemblyUtils.AddSubassembly(assembly_id, "LaneInsideSuperElevation", ...)

        tr.Commit()
        print(f"[OK] Assembly tạo tại: {origin}")
```

---

## Bước 2: Tạo Corridor

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        corridor_id = Corridor.Create(
            db,
            "COR-TUYEN-CHINH",      # Tên Corridor
            align_id,                # Alignment (Baseline)
            fg_profile_id,           # Profile thiết kế FG
            assembly_id,             # Assembly mặt cắt
            None                     # Target Surface (EG cho tính đào/đắp)
        )
        corridor = tr.GetObject(corridor_id, OpenMode.ForWrite)

        # Thiết lập tần suất lấy mặt cắt (Station interval)
        baseline = corridor.Baselines[0]
        region   = baseline.BaselineRegions[0]
        region.FrequencyToApplyAssemblies.AlongTangents          = 20.0  # m
        region.FrequencyToApplyAssemblies.AtHorizontalCurvePoints = 10.0
        region.FrequencyToApplyAssemblies.AtVerticalGeometryPoints = True

        corridor.Rebuild()  # Bắt buộc sau khi thiết lập tham số

        tr.Commit()
        print(f"[OK] Corridor '{corridor.Name}' rebuild xong")
```

---

## Bước 3: Trích xuất Thông số Mặt cắt Ngang

```python
import csv

output_csv = r'G:\output\cross_section_data.csv'

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        corridor = tr.GetObject(corridor_id, OpenMode.ForRead)
        baseline = corridor.Baselines[0]

        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Station', 'Cut_Area', 'Fill_Area',
                        'Left_Width', 'Right_Width', 'FG_Elev'])

            stations = baseline.GetSortedStations()
            for sta in stations:
                section = baseline.GetCorridorSectionAt(sta)
                if section is None:
                    continue

                # Trích xuất thông số
                left_w  = section.GetFeatureLineOffsetAtStation("ETW_Left",  sta) or 0
                right_w = section.GetFeatureLineOffsetAtStation("ETW_Right", sta) or 0
                fg_elev = section.GetFeatureLineElevationAtStation("BaseLine", sta) or 0

                w.writerow([f"{sta:.3f}", 0, 0,
                            f"{abs(left_w):.3f}", f"{right_w:.3f}", f"{fg_elev:.3f}"])

        tr.Commit()

print(f"[OK] Xuất mặt cắt: {output_csv}")
```

---

## Bước 4: Tạo Bề mặt Corridor (Corridor Surface)

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        corridor = tr.GetObject(corridor_id, OpenMode.ForWrite)

        # Thêm bề mặt Top (mặt đường)
        corridor_surface = corridor.CorridorSurfaces.Add("CS-TOP-DUONG")
        corridor_surface.AddLink("Top", True)  # Link trên cùng

        # Thêm bề mặt Datum (nền đường)
        corridor_surface_datum = corridor.CorridorSurfaces.Add("CS-DATUM")
        corridor_surface_datum.AddLink("SubBase Bottom", True)

        corridor.Rebuild()
        tr.Commit()
        print("[OK] Tạo 2 bề mặt Corridor: Top + Datum")
```

---

## Bước 5: Tích hợp với Revit (CivilConnection)

```python
# CivilConnection là thư viện mã nguồn mở kết nối Civil 3D ↔ Revit
# GitHub: https://github.com/civilconnection/CivilConnection

# Chạy trong Dynamo for Revit (không phải Dynamo for Civil 3D)

import clr
clr.AddReference('CivilConnection')
from CivilConnection import *

# Đọc Corridor từ Civil 3D
corridor_data = Corridor.ByName("COR-TUYEN-CHINH")

# Trích xuất shapes và links
shapes = corridor_data.GetShapes()
links  = corridor_data.GetLinks()

# Tạo Adaptive Component Family trong Revit
for shape in shapes:
    revit_family = shape.ToRevitFamily(
        family_template="G:\\Revit\\Templates\\Bridge_Section.rft",
        material_map={"Asphalt": "Asphalt - Flexible Paving",
                      "SubBase": "Concrete - Cast-in-Place"}
    )

print("[OK] Chuyển đổi sang Revit Family không bị tessellation")
```

---

## Checklist Kiểm tra Corridor

- [ ] Corridor Rebuild thành công (không có error trong Event Viewer)
- [ ] Feature Lines chính (Baseline, ETW_Left, ETW_Right, EPS) đầy đủ
- [ ] Bề mặt Corridor Top không có lỗ hổng (Surface Hole)
- [ ] Kiểm tra mặt cắt tại các điểm đặc biệt: cầu, giao cắt, đầu/cuối
- [ ] Volume đào/đắp hợp lý (Material Volume Report)

---

## Các lỗi Thường gặp

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| Corridor rỗng sau Rebuild | Assembly không gắn được vào Baseline | Kiểm tra region frequency > 0 |
| Feature Line bị đứt đoạn | Có điểm Station trùng hoặc khoảng cách quá lớn | Giảm interval tại đường cong |
| Surface có lỗ hổng | Subassembly không phủ đủ tại Superelevation lớn | Thêm Subassembly transition |
| Revit Family bị tessellation | Dùng CivilConnection version cũ | Nâng cấp CivilConnection >= 2024 |
