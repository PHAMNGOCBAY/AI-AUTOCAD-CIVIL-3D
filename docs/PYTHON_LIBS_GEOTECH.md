# PYTHON_LIBS_GEOTECH.md — Thư viện Python: Địa kỹ thuật & Nền móng
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Tổng quan Thư viện Địa kỹ thuật

| Phạm vi | Thư viện | Thay thế phần mềm |
|---|---|---|
| Xử lý số liệu CPT/SPT | `groundhog`, `geolysis` | Plaxis Input, Geo5 |
| Tương tác cọc-đất (Winkler) | `OpenPile` | Plaxis 3D Foundation |
| Sức chịu tải cọc (TCVN 10304:2014) | `geofound` + Python tùy chỉnh | Geo5 Pile |
| Ổn định mái dốc | `PySlope` | Slide (Rocscience), Geo5 |

---

## 1. groundhog & geolysis — Xử lý Số liệu Khảo sát

### groundhog — Xử lý dữ liệu CPT
```python
import groundhog as gh

# Đọc file CPT (định dạng AGS/GEF/CSV)
cpt = gh.CPTProcessing.from_csv("BH-01_CPT.csv",
    depth_col="Depth_m",
    qc_col="qc_MPa",
    fs_col="fs_kPa"
)

# Phân loại đất tự động (Robertson 1990)
cpt.classify_soil(method='robertson')

# Vẽ hồ sơ địa chất
cpt.plot_profile(title="Hố khoan BH-01 — Phân loại đất Robertson")

# Ngoại suy tính chất cố kết
cpt.estimate_consolidation_properties()
print(cpt.layers_summary)
```

### geolysis — Phân loại & Sức chịu tải Móng nông
```python
from geolysis.soil_classifier import USCSClassifier
from geolysis.bearing_capacity import BearingCapacityFactory

# Phân loại đất USCS từ chỉ số Atterberg
classifier = USCSClassifier(
    liquid_limit=45,
    plastic_limit=22,
    fines_content=78.0
)
print(f"Phân loại USCS: {classifier.soil_class}")  # VD: CL (Sét gầy)

# Hiệu chỉnh SPT (áp lực buồng, hiệu suất búa)
N_raw = 18   # Số búa đo tại hiện trường
depth = 6.0  # m
gamma = 18.5 # kN/m³

N60 = geolysis.spt.correct_n60(N_raw, hammer_efficiency=0.60)
N1_60 = geolysis.spt.correct_overburden(N60, sigma_v=gamma*depth)
print(f"N_raw={N_raw} → N60={N60:.1f} → (N1)60={N1_60:.1f}")

# Sức chịu tải móng nông (Terzaghi)
bc = BearingCapacityFactory.create(
    method='terzaghi',
    phi=28.0,    # Góc ma sát trong (độ)
    c=15.0,      # Sức kháng cắt không thoát nước (kPa)
    gamma=18.5,  # kN/m³
    Df=1.5,      # Chiều sâu chôn móng (m)
    B=1.8        # Bề rộng móng (m)
)
print(f"q_ult = {bc.ultimate:.1f} kPa | q_allow = {bc.allowable(FS=3):.1f} kPa")
```

---

## 2. OpenPile — Tương tác Cọc-Đất (Mô hình Winkler)

### Phương trình vi phân chi phối

```
EI × d⁴w(z)/dz⁴ + k × w(z) = q(z)
```
Trong đó:
- `EI` — Độ cứng chống uốn của cọc
- `k`  — Mô đun nền Winkler (N/m/m)
- `q(z)` — Tải trọng tác dụng theo chiều sâu

### Ví dụ: Cọc nhồi Ø800, L=25m
```python
from openpile import Pile, SoilProfile, Layer
from openpile.soil_springs import API_Sand

# Khai báo cọc (bê tông C30, Ø800mm)
pile = Pile(
    name="P-01",
    type='circular_hollow',
    diameter=0.80,          # m
    wall_thickness=0.0,     # 0 = cọc đặc
    E=30e9,                 # Pa (C30)
    L=25.0,                 # m
    top_elevation=0.0
)

# Khai báo hồ sơ đất
profile = SoilProfile(
    layers=[
        Layer(name="Bùn sét",     top=-1.5, bottom=-8.0,
              unit_weight=16.0, su=25.0),   # kN/m³, kPa
        Layer(name="Sét dẻo cứng", top=-8.0, bottom=-18.0,
              unit_weight=18.5, su=80.0),
        Layer(name="Cát chặt",    top=-18.0, bottom=-30.0,
              unit_weight=20.0, phi=32.0),  # phi: góc ma sát (độ)
    ]
)

# Tải trọng đầu cọc
pile.apply_head_loads(
    H=200e3,   # N — Lực ngang
    M=500e3,   # N.m — Mô men
    V=2000e3   # N — Lực dọc (nén)
)

# Phân tích (Euler-Bernoulli FEM 1D)
results = pile.analyze(profile, n_elements=50)

# Kết quả
print(f"Chuyển vị đầu cọc: {results.head_displacement*1000:.2f} mm")
print(f"Góc xoay đầu cọc : {results.head_rotation*1000:.4f} mrad")
print(f"M_max tại z={results.depth_max_moment:.1f}m: {results.max_moment/1e6:.1f} kN.m")

# Vẽ đường chuyển vị và nội lực dọc cọc
results.plot(components=['displacement', 'moment', 'shear'])
```

---

## 3. Sức chịu tải Cọc — TCVN 10304:2014

```python
import json
import numpy as np
import matplotlib.pyplot as plt

def tinh_suc_chiu_tai_coc_tcvn(soil_layers: list,
                                D_coc: float, L_coc: float) -> dict:
    """
    Tính sức chịu tải cực hạn cọc nhồi theo TCVN 10304:2014
    Phương pháp: Số liệu địa chất (fi, R)

    soil_layers: [{'name', 'thickness_m', 'fi_kPa', 'R_kPa', 'layer_type'}]
    D_coc: Đường kính cọc (m)
    L_coc: Chiều dài cọc (m)
    """
    u = np.pi * D_coc          # Chu vi cọc (m)
    A_mui = np.pi * D_coc**2 / 4  # Diện tích mũi cọc (m²)

    # Sức kháng ma sát hông
    Qs = 0.0
    z_current = 0.0
    for layer in soil_layers:
        if z_current >= L_coc:
            break
        dz = min(layer['thickness_m'], L_coc - z_current)
        Qs += u * layer['fi_kPa'] * dz
        z_current += dz

    # Sức kháng mũi cọc (lấy giá trị lớp cuối tiếp xúc mũi)
    R_mui = soil_layers[-1].get('R_kPa', 0)
    Qp = A_mui * R_mui

    Qu = Qs + Qp           # Sức chịu tải cực hạn (kN)
    Qa = Qu / 2.0          # Sức chịu tải cho phép (FS = 2.0)

    return {
        'Qu_kN': round(Qu, 1),
        'Qa_kN': round(Qa, 1),
        'Qs_kN': round(Qs, 1),
        'Qp_kN': round(Qp, 1),
        'D_mm': int(D_coc * 1000),
        'L_m': L_coc
    }

# Ví dụ sử dụng
layers = [
    {'name': 'Bùn sét',      'thickness_m': 6.5,  'fi_kPa': 12, 'R_kPa': 0},
    {'name': 'Sét dẻo cứng', 'thickness_m': 10.0, 'fi_kPa': 45, 'R_kPa': 0},
    {'name': 'Cát chặt',     'thickness_m': 8.5,  'fi_kPa': 80, 'R_kPa': 4500},
]

result = tinh_suc_chiu_tai_coc_tcvn(layers, D_coc=0.8, L_coc=25.0)
print(f"Qu = {result['Qu_kN']} kN | Qa = {result['Qa_kN']} kN")
print(f"  Qs (ma sát) = {result['Qs_kN']} kN")
print(f"  Qp (mũi)   = {result['Qp_kN']} kN")

# Phân tích độ nhạy: quét chiều dài cọc 15m → 30m
L_range = np.arange(15, 31, 0.5)
Qu_list = []
for L in L_range:
    r = tinh_suc_chiu_tai_coc_tcvn(layers, D_coc=0.8, L_coc=L)
    Qu_list.append(r['Qu_kN'])

plt.figure(figsize=(8, 5))
plt.plot(L_range, Qu_list, 'b-o', markersize=4)
plt.axhline(y=2000, color='r', linestyle='--', label='Tải trọng thiết kế 2000 kN')
plt.xlabel("Chiều dài cọc (m)")
plt.ylabel("Sức chịu tải cực hạn Qu (kN)")
plt.title("Phân tích độ nhạy — Sức chịu tải theo chiều dài cọc Ø800")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("assets/diagrams/pile_capacity_curve.png", dpi=150)
```

---

## 4. PySlope — Ổn định Mái Dốc

```python
from pyslope import Slope, Material, SlopeResults

# Khai báo mái dốc và lớp địa chất
slope = Slope(
    height=8.0,    # m
    angle=35.0,    # độ
    length=20.0    # m (chiều ngang chân mái)
)

# Khai báo vật liệu (Bishop Simplified Method)
slope.set_material(
    Material(
        unit_weight=18.5,   # kN/m³
        friction_angle=22,  # độ
        cohesion=15.0,      # kPa
        depth_below=0.0,    # m (từ mặt đất)
        layer_height=8.0    # m
    )
)

# Mực nước ngầm (tính áp lực nước lỗ rỗng)
slope.set_water_table(height=3.0)

# Chạy phân tích (phương pháp Bishop đơn giản)
results: SlopeResults = slope.analyze(method='bishop')

print(f"Hệ số ổn định Fs = {results.min_fs:.3f}")
print(f"Tâm mặt trượt: ({results.critical_circle.cx:.1f}, "
      f"{results.critical_circle.cy:.1f})")

if results.min_fs < 1.3:
    print("⚠️ CẢNH BÁO: Fs < 1.3 — Cần biện pháp gia cố!")
elif results.min_fs < 1.5:
    print("⚠️ Fs < 1.5 — Kiểm tra kỹ (công trình tạm có thể chấp nhận)")
else:
    print("✅ Mái dốc ổn định (Fs ≥ 1.5)")

results.plot()
```

---

## Checklist Địa kỹ thuật

- [ ] Hiệu chỉnh N60 và (N1)60 từ số liệu SPT thực đo
- [ ] Phân loại đất theo USCS trước khi tính sức chịu tải
- [ ] Sức chịu tải cọc dùng **FS = 2** (sức chịu tải cho phép)
- [ ] Phân tích độ nhạy: quét L_coc để tìm chiều dài kinh tế
- [ ] Fs mái dốc ≥ 1.5 (ổn định lâu dài) / ≥ 1.3 (xây dựng tạm)
- [ ] Xuất đường cong sức chịu tải → `assets/diagrams/`
