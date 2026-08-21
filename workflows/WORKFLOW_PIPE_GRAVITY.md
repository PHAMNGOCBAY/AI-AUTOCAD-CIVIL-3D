# WORKFLOW_PIPE_GRAVITY.md — Mạng lưới Ống Trọng lực (Thoát nước)
> Civil 3D **2027** | Python Managed.NET | 2026-05-09

---

## Mục đích

Tự động hóa thiết kế **mạng lưới thoát nước mưa và nước thải** (Gravity Pipe Network): khoanh vùng lưu vực, định tuyến, tính thủy văn, thiết kế hố ga và đường ống.

---

## Kiến trúc Dữ liệu

```
Catchment (Lưu vực)          → BoundaryPolyline3d → Diện tích, hệ số chảy tràn
    ↓ Thủy văn (Q = C×i×A)
Structure (Hố ga)            → InsertionPoint, InnerDiameter, WallThickness
    ↓ Kết nối
Pipe (Đường ống trọng lực)   → StartInvert, EndInvert, Slope, Diameter
    ↓ Tập hợp thành
Gravity Pipe Network         → Mô hình hoàn chỉnh
```

---

## Bước 1: Trích xuất Lưu vực (Catchment)

```python
from Autodesk.AutoCAD.Geometry import Point3dCollection

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Lấy tất cả Catchment trong bản vẽ
        catchment_ids = civil_db.GetCatchmentIds()
        print(f"Tìm thấy {catchment_ids.Count} lưu vực")

        catchment_data = []
        for cat_id in catchment_ids:
            cat = tr.GetObject(cat_id, OpenMode.ForRead)

            # Lấy đường biên lưu vực (Point3dCollection)
            boundary = cat.BoundaryPolyline3d

            # Chuyển sang list Python để tính toán
            pts = [(p.X, p.Y) for p in boundary]

            # Tính diện tích (Shoelace formula)
            n = len(pts)
            area = abs(sum(pts[i][0]*pts[(i+1)%n][1] -
                          pts[(i+1)%n][0]*pts[i][1]
                          for i in range(n))) / 2

            catchment_data.append({
                'name': cat.Name,
                'area_m2': area,
                'runoff_coeff': 0.85,   # Mặc định đô thị
                'tc_min': 10.0,          # Thời gian tập trung nước (phút)
                'points': pts
            })

            print(f"  {cat.Name}: A={area:.1f}m² ({area/10000:.4f}ha)")

        tr.Commit()
```

---

## Bước 2: Tính Lưu lượng Thủy văn (Q = C × i × A)

```python
import math

def cuong_do_mua(T_phut: float, chu_ky_nam: int = 5) -> float:
    """
    Tính cường độ mưa theo phương pháp HCM (áp dụng vùng đô thị VN).
    i (mm/h) = A_hcm / (t + b)^n
    Thông số cho TP.HCM: A=6949, b=9.78, n=0.79 (chu kỳ 5 năm)
    """
    A, b, n = 6949, 9.78, 0.79
    return A / (T_phut + b) ** n

def tinh_luu_luong(catchment: dict) -> float:
    """Q (m³/s) = C × i (m/s) × A (m²)"""
    C = catchment['runoff_coeff']
    i_mm_h = cuong_do_mua(catchment['tc_min'])
    i_m_s  = i_mm_h / 1000 / 3600
    A_m2   = catchment['area_m2']
    Q = C * i_m_s * A_m2
    return Q

for cat in catchment_data:
    Q = tinh_luu_luong(cat)
    cat['Q_m3s'] = Q
    print(f"  {cat['name']}: Q = {Q*1000:.2f} L/s = {Q:.5f} m³/s")
```

---

## Bước 3: Chọn Đường kính Ống tối ưu

```python
def chon_duong_kinh_ong(Q_m3s: float, i_min: float = 0.003) -> dict:
    """
    Chọn đường kính ống nhỏ nhất thỏa mãn Q tại độ dốc tối thiểu.
    Dùng công thức Manning: Q = (1/n) × A × R^(2/3) × i^(1/2)
    n_Manning = 0.013 (bê tông)
    """
    n_manning = 0.013
    diameters = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5]  # m

    for D in diameters:
        A = math.pi * D**2 / 4         # Tiết diện đầy ống
        R = D / 4                       # Bán kính thủy lực
        Q_full = (1/n_manning) * A * R**(2/3) * i_min**0.5

        if Q_full >= Q_m3s * 1.2:  # Hệ số an toàn 1.2
            return {'D_mm': int(D*1000), 'Q_full_m3s': Q_full,
                    'fill_ratio': Q_m3s / Q_full}
    return {'D_mm': 1500, 'Q_full_m3s': 0, 'fill_ratio': 1.0}  # Lấy max

for cat in catchment_data:
    ong = chon_duong_kinh_ong(cat['Q_m3s'])
    cat['pipe_D_mm'] = ong['D_mm']
    print(f"  {cat['name']}: D={ong['D_mm']}mm | fill={ong['fill_ratio']:.0%}")
```

---

## Bước 4: Duyệt Mạng lưới Ống — Tự động lập Connected Order Map

```python
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net_ids = civil_db.GetPipeNetworkIds()

        for net_id in net_ids:
            network = tr.GetObject(net_id, OpenMode.ForRead)
            print(f"\n[Network] {network.Name}")

            # Xây dựng đồ thị kết nối
            graph = {}  # {struct_id: [connected_pipe_ids]}

            for pipe_id in network.GetPipeIds():
                pipe = tr.GetObject(pipe_id, OpenMode.ForRead)
                start_struct = pipe.StartStructureId
                end_struct   = pipe.EndStructureId

                if start_struct not in graph:
                    graph[start_struct] = []
                graph[start_struct].append(pipe_id)

                print(f"  Ống: {pipe.Name} | D={pipe.InnerDiameterOrWidth*1000:.0f}mm "
                      f"| i={pipe.Slope*100:.2f}% "
                      f"| Inv_đầu={pipe.StartInvert:.3f}m "
                      f"| Inv_cuối={pipe.EndInvert:.3f}m")

            for struct_id in network.GetStructureIds():
                struct = tr.GetObject(struct_id, OpenMode.ForRead)
                pt = struct.InsertionPoint
                print(f"  Hố ga: {struct.Name} @ Z={pt.Z:.3f}m "
                      f"| WT={struct.WallThickness:.3f}m")  # Chỉ qua Managed.NET

        tr.Commit()
```

---

## Bước 5: Gộp nhiều Pipe Network riêng lẻ

```python
# Vấn đề: Civil 3D không tự gộp các Network → dùng Python duyệt database

def gop_network(source_net_id, target_net_id, tr):
    """Gộp source_net vào target_net bằng cách tạo lại kết nối"""
    source_net = tr.GetObject(source_net_id, OpenMode.ForRead)
    target_net = tr.GetObject(target_net_id, OpenMode.ForWrite)

    # Lấy tất cả pipe từ source
    for pipe_id in source_net.GetPipeIds():
        pipe = tr.GetObject(pipe_id, OpenMode.ForWrite)
        # Di chuyển ống sang target network
        target_net.ImportPipe(pipe_id)

    print(f"[OK] Gộp '{source_net.Name}' → '{target_net.Name}'")

# Sử dụng:
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        net_ids = list(civil_db.GetPipeNetworkIds())
        if len(net_ids) > 1:
            for i in range(1, len(net_ids)):
                gop_network(net_ids[i], net_ids[0], tr)
        tr.Commit()
```

---

## Bước 6: Xuất Bảng Thống kê Mạng lưới

```python
import pandas as pd

data = []
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        for net_id in civil_db.GetPipeNetworkIds():
            net = tr.GetObject(net_id, OpenMode.ForRead)
            for pipe_id in net.GetPipeIds():
                p = tr.GetObject(pipe_id, OpenMode.ForRead)
                data.append({
                    'Ten_ong': p.Name,
                    'D_mm': p.InnerDiameterOrWidth * 1000,
                    'Chieu_dai_m': p.Length3DToInsideEdge,
                    'Do_doc_pct': p.Slope * 100,
                    'Inv_dau_m': p.StartInvert,
                    'Inv_cuoi_m': p.EndInvert,
                    'Chat_lieu': p.PartFamilyName
                })
        tr.Commit()

df = pd.DataFrame(data)
df.to_excel(r'G:\output\pipe_network_summary.xlsx', index=False)
print(f"[OK] Xuất {len(df)} đường ống → Excel")
```

---

## Checklist Kiểm tra

- [ ] Tất cả ống có độ dốc ≥ 0.003 (0.3%) — tránh lắng đọng
- [ ] Tất cả hố ga có nắp đậy ≥ cao độ mặt đường
- [ ] Không có ống ngược chiều dòng chảy
- [ ] Kiểm tra va chạm không gian với mạng ống khác (MEP clash detection)
- [ ] Diện tích lưu vực × hệ số chảy tràn khớp với lưu lượng tính toán
