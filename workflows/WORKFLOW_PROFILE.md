# WORKFLOW_PROFILE.md — Tự động hóa Trắc dọc (Profile)
> Civil 3D **2027** | Python Managed.NET | 2026-05-09

---

## Mục đích

Tự động hóa tạo **Trắc dọc Tự nhiên (EG)** và **Trắc dọc Thiết kế (FG)**, tích hợp thuật toán tối ưu hóa cân bằng khối lượng đào-đắp.

---

## Phân biệt Hai Loại Profile

| Loại | Tên gọi | Nguồn dữ liệu | Phương thức API |
|---|---|---|---|
| Trắc dọc Tự nhiên | EG (Existing Ground) | Bề mặt TIN khảo sát | `Profile.CreateFromFeatureLine()` hoặc cắt từ Surface |
| Trắc dọc Thiết kế | FG (Finished Ground) | Tính toán kỹ thuật | `Profile.CreateByLayout()` |

---

## Bước 1: Tạo Trắc dọc Tự nhiên (EG) — Cắt từ Surface

```python
# Cắt EG tự động từ bề mặt TIN theo Alignment
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Lấy Alignment
        align = tr.GetObject(align_id, OpenMode.ForRead)

        # Lấy Surface TIN
        surface_ids = civil_db.GetSurfaceIds()
        eg_surface = None
        for sid in surface_ids:
            s = tr.GetObject(sid, OpenMode.ForRead)
            if "EG" in s.Name or "KSDT" in s.Name:
                eg_surface = s
                break

        if eg_surface is None:
            raise ValueError("Không tìm thấy bề mặt EG!")

        # Lấy ProfileView (tạo nếu chưa có)
        profile_view_ids = align.GetProfileViewIds()
        if profile_view_ids.Count == 0:
            # Tạo ProfileView
            pv_style_id = civil_db.Styles.ProfileViewStyles[0].ObjectId
            pv_band_style_id = civil_db.Styles.ProfileViewBandSetStyles[0].ObjectId
            pv_id = ProfileView.Create(
                align_id, Point2d(0, 0), "PV-AL-01",
                pv_style_id, pv_band_style_id
            )
        else:
            pv_id = profile_view_ids[0]

        # Tạo EG Profile từ Surface
        eg_style_id   = civil_db.Styles.ProfileStyles[0].ObjectId
        eg_label_id   = civil_db.Styles.ProfileLabelSetStyles[0].ObjectId

        eg_profile_id = Profile.CreateFromSurface(
            "EG - " + align.Name,
            align_id,
            eg_surface.ObjectId,
            pv_id,
            eg_style_id,
            eg_label_id
        )

        tr.Commit()
        print(f"[OK] Tạo EG Profile: {eg_profile_id}")
```

---

## Bước 2: Tạo Trắc dọc Thiết kế (FG) — Layout

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        fg_style_id = civil_db.Styles.ProfileStyles[1].ObjectId  # Style FG
        fg_label_id = civil_db.Styles.ProfileLabelSetStyles[1].ObjectId

        fg_profile_id = Profile.CreateByLayout(
            "FG-DESIGN - " + align.Name,
            align_id,
            pv_id,
            fg_style_id,
            fg_label_id
        )

        fg_profile = tr.GetObject(fg_profile_id, OpenMode.ForWrite)

        # Thêm PVI từ tính toán kỹ thuật
        # Định dạng: [(station, elevation, curve_length), ...]
        pvi_data = [
            (0.0,    45.50, 0.0),    # Điểm đầu
            (200.0,  44.20, 80.0),   # PVI với đường cong đứng L=80m
            (600.0,  47.80, 120.0),  # PVI với đường cong đứng L=120m
            (1000.0, 45.00, 0.0),    # Điểm cuối
        ]

        for sta, elev, curve_len in pvi_data:
            pvi = fg_profile.PVIs.AddPVI(sta, elev)
            if curve_len > 0:
                pvi.CurveLength = curve_len  # Đường cong đứng

        tr.Commit()
        print(f"[OK] Tạo FG Profile với {len(pvi_data)} PVI")
```

---

## Bước 3: Tối ưu hóa Trắc dọc (Cân bằng Đào-Đắp)

```python
import numpy as np
from scipy.optimize import minimize

def tinh_khoi_luong_dao_dap(pvi_elevations, eg_elevations, stations):
    """
    Tính khối lượng đào/đắp dựa trên hiệu cao độ FG - EG.
    Trả về: (V_dao, V_dap, hieu)
    """
    diff = np.array(pvi_elevations) - np.array(eg_elevations)
    cut  = np.trapz(np.maximum(diff, 0),  stations)
    fill = np.trapz(np.maximum(-diff, 0), stations)
    return cut, fill, abs(cut - fill)

def objective(fg_elevs, eg_elevs, stations, slope_max=0.05):
    """Hàm mục tiêu: tối thiểu hóa hiệu đào-đắp + phạt độ dốc vượt ngưỡng"""
    cut, fill, imbalance = tinh_khoi_luong_dao_dap(fg_elevs, eg_elevs, stations)

    # Phạt độ dốc vượt slope_max
    slopes = np.abs(np.diff(fg_elevs) / np.diff(stations))
    slope_penalty = np.sum(np.maximum(slopes - slope_max, 0)) * 1e6

    return imbalance + slope_penalty

# Lấy dữ liệu EG từ Civil 3D
stations = np.arange(0, 1001, 20)  # 0 → 1000m, cách 20m
eg_elevs = []

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        eg_profile = tr.GetObject(eg_profile_id, OpenMode.ForRead)
        for sta in stations:
            eg_elevs.append(eg_profile.ElevationAt(sta))
        tr.Commit()

eg_elevs = np.array(eg_elevs)

# Tối ưu hóa
initial_fg = eg_elevs.copy()  # Khởi điểm bằng EG
result = minimize(
    objective, initial_fg,
    args=(eg_elevs, stations, 0.05),
    method='L-BFGS-B',
    options={'maxiter': 500}
)

if result.success:
    optimal_fg = result.x
    cut, fill, imbalance = tinh_khoi_luong_dao_dap(optimal_fg, eg_elevs, stations)
    print(f"[OK] Tối ưu thành công!")
    print(f"     V_đào = {cut:,.1f} m³")
    print(f"     V_đắp = {fill:,.1f} m³")
    print(f"     Mất cân = {imbalance:,.1f} m³")
```

---

## Bước 4: Áp dụng FG tối ưu vào Civil 3D

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        fg_profile = tr.GetObject(fg_profile_id, OpenMode.ForWrite)

        # Xóa PVI cũ
        while fg_profile.PVIs.Count > 0:
            fg_profile.PVIs.Remove(fg_profile.PVIs[0])

        # Thêm PVI mới từ kết quả tối ưu (lấy 1 điểm mỗi 100m)
        sample_idx = range(0, len(stations), 5)  # 1 PVI / 100m
        for i in sample_idx:
            fg_profile.PVIs.AddPVI(float(stations[i]), float(optimal_fg[i]))

        tr.Commit()
        print(f"[OK] Cập nhật FG Profile với {len(list(sample_idx))} PVI")
```

---

## Checklist Kiểm tra

- [ ] EG Profile liên tục, không có khoảng trống
- [ ] Độ dốc FG không vượt quá giới hạn tiêu chuẩn
- [ ] Bán kính đường cong đứng ≥ R_min_vertical
- [ ] Tỷ lệ V_đào / V_đắp trong khoảng 0.8 ~ 1.2 (cân bằng chấp nhận được)
- [ ] Cao độ FG tại điểm giao nhau > EG + 0.5m (tránh ngập)

---

## Thông số Đường cong Đứng (Tiêu chuẩn Việt Nam)

| Loại đường cong | Vận tốc (km/h) | R_min (m) |
|---|---|---|
| Lồi (Convex) | 120 | 12000 |
| Lồi (Convex) | 80  | 4000  |
| Lõm (Concave) | 120 | 4000 |
| Lõm (Concave) | 80  | 2000 |
