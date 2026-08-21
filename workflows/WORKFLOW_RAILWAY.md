# WORKFLOW_RAILWAY.md — Thiết kế Đường sắt (Railway Design)
> Civil 3D **2027** | Python Managed.NET | Tiêu chuẩn UIC + TCVN | 2026-05-09

---

## Mục đích

Tự động hóa các yếu tố kỹ thuật đặc thù của đường sắt: **Siêu cao (Cant)**, **Đoạn chuyển tiếp**, **Ghi đường (Turnout)**, **Catenary**, và kết nối sang Revit.

---

## Đặc thù Kỹ thuật Đường sắt vs Đường bộ

| Yếu tố | Đường bộ | Đường sắt |
|---|---|---|
| Bán kính tối thiểu | R = 60m (đô thị) | R = 300m (metro) / R = 1500m (HSR) |
| Siêu cao | Độ dốc ngang 6-8% | Cant (mm) = 11.8 × V² / R |
| Đoạn chuyển tiếp | Clothoid tiêu chuẩn | Bắt buộc kiểm soát Cant gradient |
| Ghi đường | Không có | Turnout Catalog (JSON file) |
| Tải trọng | Xe bánh hơi | Bánh thép trên ray thép → động lực học chặt chẽ |

---

## Bước 1: Tính và Thiết lập Siêu cao (Cant)

### Công thức tính Cant

```python
def tinh_sieu_cao(V_kmh: float, R_m: float,
                  cant_max_mm: float = 150.0) -> dict:
    """
    Tính siêu cao theo UIC 703.
    V: tốc độ thiết kế (km/h)
    R: bán kính cong (m)
    Cant_max: 150mm (đường sắt thường) / 180mm (đường cao tốc)
    """
    cant_ly_thuyet = 11.8 * (V_kmh ** 2) / R_m

    # Siêu cao thực tế = min(lý thuyết, max cho phép)
    cant_thuc_te = min(cant_ly_thuyet, cant_max_mm)

    # Siêu cao thiếu (Cant Deficiency)
    cant_thieu = cant_ly_thuyet - cant_thuc_te

    # Chiều dài đoạn chuyển tiếp tối thiểu
    cant_gradient_max = 1.0  # mm/m (UIC)
    L_min = cant_thuc_te / cant_gradient_max

    return {
        'cant_ly_thuyet_mm': round(cant_ly_thuyet, 1),
        'cant_thuc_te_mm':   round(cant_thuc_te, 1),
        'cant_thieu_mm':     round(cant_thieu, 1),
        'L_chuyen_tiep_min': round(L_min, 1)
    }

# Ví dụ: Metro Hà Nội - V=80km/h, R=500m
result = tinh_sieu_cao(V_kmh=80, R_m=500)
print(f"Cant lý thuyết : {result['cant_ly_thuyet_mm']} mm")
print(f"Cant thực tế   : {result['cant_thuc_te_mm']} mm")
print(f"Cant thiếu     : {result['cant_thieu_mm']} mm")
print(f"L chuyển tiếp  ≥ {result['L_chuyen_tiep_min']} m")
```

---

## Bước 2: Áp dụng Siêu cao vào Civil 3D

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)

        # Truy cập tập hợp siêu cao đặc biệt của Railway
        cant_stations = align.CANTCriticalStationCollection

        # Lấy danh sách đường cong trong Alignment
        for entity in align.Entities:
            if hasattr(entity, 'Radius'):  # Là đường cong
                R = entity.Radius
                sta_start = entity.StartStation
                sta_end   = entity.EndStation
                sta_mid   = (sta_start + sta_end) / 2

                cant_data = tinh_sieu_cao(V_kmh=80, R_m=R)
                cant_mm   = cant_data['cant_thuc_te_mm']
                L_trans   = cant_data['L_chuyen_tiep_min']

                print(f"Station {sta_start:.1f}~{sta_end:.1f}: "
                      f"R={R:.0f}m → Cant={cant_mm:.1f}mm | L_trans≥{L_trans:.1f}m")

                # Thêm Station siêu cao
                cant_stations.Add(sta_mid, cant_mm)

        # Duyệt SuperElevationCurves (đường cong siêu cao)
        for se_curve in align.SuperElevationCurves:
            se_curve.CantValue = cant_mm  # mm
            se_curve.TransitionLength = L_trans

        tr.Commit()
        print(f"[OK] Thiết lập siêu cao cho {align.SuperElevationCurves.Count} đoạn")
```

---

## Bước 3: Phương pháp Xoay Siêu cao (Cant Pivot Method)

```python
# Ba phương pháp xoay siêu cao:
# 1. OUTER_RAIL  : Xoay quanh ray lưng (high side)
# 2. INNER_RAIL  : Xoay quanh ray bụng (low side)
# 3. CENTERLINE  : Xoay quanh đường tâm tuyến

CANT_PIVOT_METHODS = {
    'ray_lung':    'HighRail',   # Phổ biến nhất ở Việt Nam
    'ray_bung':    'LowRail',
    'duong_tam':   'CenterLine'
}

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)

        for se_curve in align.SuperElevationCurves:
            # Thiết lập phương pháp xoay
            se_curve.PivotMethod = CantPivotMethod.HighRail

            # Kiểm tra: không xảy ra giật cục động lực học
            # Điều kiện: Cant gradient ≤ 1 mm/m (UIC 703)
            actual_gradient = se_curve.CantValue / se_curve.TransitionLength
            if actual_gradient > 1.0:
                print(f"[WARN] Cant gradient = {actual_gradient:.2f} mm/m > 1.0 mm/m!")
                # Tăng chiều dài đoạn chuyển tiếp
                se_curve.TransitionLength = se_curve.CantValue / 1.0

        tr.Commit()
```

---

## Bước 4: Quản lý Ghi đường (Turnout Catalog)

### Đường dẫn file Catalog
```
C:\ProgramData\Autodesk\C3D 2027\enu\Data\Railway Design Standards\Turnout\
├── Turnout_1_9.json       (Ghi 1/9 — đường sắt thường)
├── Turnout_1_12.json      (Ghi 1/12 — đường cao tốc)
├── Crossover_1_9.json     (Giao cắt)
└── [CustomName].json      (Catalog tùy chỉnh)
```

### Tạo Turnout Catalog tùy chỉnh (Tiêu chuẩn VN)
```python
import json

turnout_vn = {
    "name": "Ghi-1_9-VietNam-1435mm",
    "description": "Ghi 1/9 theo tiêu chuẩn đường sắt Việt Nam, khổ 1435mm",
    "parameters": {
        "gauge_mm":           1435,
        "turnout_angle":      "1:9",
        "frog_angle_deg":     6.34,
        "switch_rail_length": 6.0,     # m
        "stock_rail_length":  12.5,    # m
        "sleeper_spacing_mm": 600,
        "turnout_radius_m":   190,
        "heel_spread_mm":     160
    },
    "point_of_switch": {"x": 0.0, "y": 0.0},
    "point_of_frog":   {"x": 54.2, "y": 6.02}
}

catalog_path = (r'C:\ProgramData\Autodesk\C3D 2027\enu\Data'
                r'\Railway Design Standards\Turnout\Ghi_1_9_VN.json')
with open(catalog_path, 'w', encoding='utf-8') as f:
    json.dump(turnout_vn, f, ensure_ascii=False, indent=2)

print(f"[OK] Tạo catalog ghi: {catalog_path}")
```

### Đặt Ghi vào mô hình
```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForWrite)

        # Thêm Turnout tại Station 450m (điểm rẽ sang đường tránh)
        turnout_station = 450.0
        pt = align.GetPointAtStation(turnout_station)

        # Civil 3D tự động tính hướng từ Alignment tại điểm đó
        turnout = RailwayTurnout.Create(
            db,
            "GT-01",                 # Tên ghi
            align_id,                # Alignment tuyến chính
            turnout_station,
            "Ghi_1_9_VN",           # Tên catalog
            TurnoutDirection.Right   # Hướng rẽ
        )

        tr.Commit()
        print(f"[OK] Đặt ghi GT-01 tại KM{turnout_station/1000:.3f}")
```

---

## Bước 5: Mô hình hóa Dây điện Trên cao (Catenary)

```python
# Catenary = hệ thống dây điện cấp điện cho đầu máy điện
# Kết hợp Civil 3D + Revit + Dynamo

# Trong Dynamo for Revit:
# 1. Đọc Alignment station từ Civil 3D
# 2. Tạo điểm đỡ cột catenary cách nhau 60m
# 3. Tạo Adaptive Component "Cột Catenary" tại mỗi điểm

catenary_spacing_m = 60.0  # Khoảng cách cột catenary tiêu chuẩn

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)
        cogo_coll = civil_db.CogoPoints

        sta = align.StartingStation
        while sta <= align.EndingStation:
            pt = align.GetPointAtStation(sta)
            # Tạo điểm đỡ cột
            cog_id = cogo_coll.Add(
                Point3d(pt.X, pt.Y, pt.Z + 5.5),  # Chiều cao 5.5m
                f"CAT-{sta:.0f}"
            )
            sta += catenary_spacing_m

        tr.Commit()
        n_cols = int((align.Length / catenary_spacing_m) + 1)
        print(f"[OK] Tạo {n_cols} điểm cột catenary")
```

---

## Bước 6: Xuất Cant Views để Thẩm tra

```python
# Cant View = biểu đồ siêu cao theo lý trình (tương tự Profile View)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)

        cant_view_style = civil_db.Styles.CantViewStyles[0].ObjectId

        # Tạo Cant View
        cant_view_id = CantView.Create(
            align_id,
            Point2d(0, -200),    # Vị trí đặt trong bản vẽ (Paper Space)
            "CV-SIEU-CAO-01",
            cant_view_style
        )

        tr.Commit()
        print(f"[OK] Tạo Cant View để thẩm tra siêu cao")
```

---

## Thông số Kỹ thuật Đường sắt Việt Nam

| Loại | Khổ đường (mm) | V_TK (km/h) | R_min (m) | Cant_max (mm) |
|---|---|---|---|---|
| Đường sắt hiện hữu 1000mm | 1000 | 90 | 300 | 110 |
| Đường sắt đô thị metro | 1435 | 80 | 300 | 150 |
| Đường sắt tốc độ cao | 1435 | 200 | 2500 | 150 |
| Đường sắt cao tốc | 1435 | 350 | 6000 | 180 |

---

## Checklist Kiểm tra

- [ ] Cant gradient ≤ 1 mm/m tại mọi đoạn chuyển tiếp
- [ ] Không có đoạn chuyển tiếp ngắn hơn L_min
- [ ] Ghi đường ≥ R_min_switch theo tiêu chuẩn dự án
- [ ] Khoảng thông xe đứng (vertical clearance) ≥ 6.1m tại mọi điểm
- [ ] Không có siêu cao liền tiếp không qua đoạn bình (gây nguy hiểm)
