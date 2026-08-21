# PYTHON_LIBS_DESIGN_CHECK.md — Kiểm toán Kết cấu theo Tiêu chuẩn
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Tổng quan

| Phạm vi | Thư viện | Tiêu chuẩn |
|---|---|---|
| Đặc trưng mặt cắt thép | `SectionProperties` | AISC, BS |
| Bê tông cốt thép (biểu đồ P-M) | `ConcreteProperties`, `PyCivil` | TCVN 5574:2018 |
| Eurocode tổng hợp | `EurocodePy`, `StructuralCodes` | EN 1990 – EN 1997 |
| Móng đơn / móng băng | `FoundationDesign` | Eurocode 2 + UK NA |

---

## 1. SectionProperties — Đặc trưng Mặt cắt Thép

```python
import sectionproperties.pre.library.steel_sections as steel
from sectionproperties.analysis.section import Section

# Tạo mặt cắt HEA 200
geom = steel.i_section(
    d=190,  # Chiều cao (mm)
    b=200,  # Bề rộng cánh
    t_f=10, # Bề dày cánh
    t_w=6.5,# Bề dày bụng
    r=18,   # Bán kính góc lượn
    n_r=16  # Số điểm nội suy cung tròn
)

geom.create_mesh(mesh_sizes=[5.0])
section = Section(geom)
section.calculate_geometric_properties()
section.calculate_warping_properties()

# Trích xuất đặc trưng
props = section.get_section_properties()
print(f"A  = {props.area:.2f} mm²")
print(f"Ix = {props.ixx_c:.2e} mm⁴")
print(f"Iy = {props.iyy_c:.2e} mm⁴")
print(f"Zx = {props.zxx:.2e} mm³  (mô đun chống uốn)")
print(f"J  = {props.j:.2e} mm⁴   (chống xoắn)")
print(f"Iw = {props.iw:.2e} mm⁶  (warping constant)")
```

---

## 2. ConcreteProperties — Biểu đồ P-M Theo TCVN 5574:2018

### Nguyên tắc TCVN 5574:2018 (khác bản 2012)
- **Tăng bề dày lớp bảo vệ** thêm 5–10mm so với phiên bản cũ
- **Bắt buộc dùng mô hình phi tuyến (NLDM)**:
  - Cốt thép CB-400V, CB-500V: mô hình **song tuyến tính (bi-linear)**
  - Bê tông chịu nén: mô hình **tam tuyến tính (tri-linear)**

```python
from concreteproperties import (
    ConcreteSection, Concrete, SteelBar,
    RectangularSection, CircularSection
)
import numpy as np

# ---- Khai báo vật liệu (TCVN 5574:2018) ----
# Bê tông B25: f'c = 18.5 MPa
concrete = Concrete(
    name="B25",
    density=2400,
    stress_strain_profile='tri_linear',  # Tam tuyến tính
    compressive_strength=18.5e6,         # Pa
    ultimate_strain=0.0035
)

# Cốt thép CB-400V: fy = 350 MPa (tính toán)
steel = SteelBar(
    name="CB400V",
    stress_strain_profile='bilinear',    # Song tuyến tính
    yield_strength=350e6,                # Pa
    elastic_modulus=200e9
)

# ---- Khai báo mặt cắt cột 400x500mm ----
# Lớp bảo vệ = 40mm (TCVN 2018: tăng thêm 5mm)
cover = 40e-3  # m

geom = RectangularSection(
    b=0.4, d=0.5,
    concrete=concrete,
    cover=cover
)

# Thêm 8Ø20 (4 góc + 2 giữa mỗi cạnh dài)
bar_positions = [
    (-0.15, -0.20), (-0.15, 0.0), (-0.15, 0.20),
    ( 0.15, -0.20), ( 0.15, 0.0), ( 0.15, 0.20),
    (0.0, -0.20),   (0.0,  0.20),
]
for x, y in bar_positions:
    geom.add_bar(x, y, diameter=20e-3, steel=steel)

section = ConcreteSection(geom)

# ---- Biểu đồ tương tác P-M (Axial-Moment Interaction) ----
pm_results = section.moment_interaction_diagram(
    phi_0=0.65,    # Hệ số giảm khả năng chịu lực (nén thuần)
    phi_flexure=0.9
)

# Xuất biểu đồ
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
pm_results.plot_diagram(ax=ax)
ax.set_title("Biểu đồ P-M — Cột 400x500 / B25 / 8Ø20 CB400V")
plt.savefig("assets/diagrams/pm_col_C1.png", dpi=150)
print("[OK] Xuất biểu đồ P-M")

# ---- Kiểm tra điểm tải trọng thiết kế ----
N_design = -800e3   # N (nén)
M_design =  120e6   # N.mm

status = section.check_section(N_design, M_design)
ratio  = status.utilization_ratio
print(f"Utilization ratio = {ratio:.3f} → {'PASS ✅' if ratio<=1.0 else 'FAIL ❌'}")
```

---

## 3. EurocodePy — Kiểm toán Theo Eurocode 2

```python
from eurocodepy import MaterialConcrete, MaterialSteel
from eurocodepy.ec2 import BeamBending, ShearCheck, PunchingShear

# Vật liệu từ database chuẩn EC2
concrete = MaterialConcrete("C30/37")
steel    = MaterialSteel("B500B")

print(f"fck = {concrete.fck} MPa")
print(f"fcd = {concrete.fcd:.1f} MPa (tính toán)")
print(f"fyd = {steel.fyd:.1f} MPa")

# Kiểm toán uốn dầm chữ T
beam = BeamBending(
    b_eff=1200,   # mm — bề rộng cánh hiệu quả
    h_f=150,      # mm — bề dày cánh
    b_w=300,      # mm — bề rộng bụng
    h=600,        # mm — chiều cao dầm
    d=540,        # mm — chiều cao làm việc
    concrete=concrete,
    steel=steel
)

# ULS — Tính diện tích thép yêu cầu
M_Ed = 450e6  # N.mm
As_req = beam.required_reinforcement(M_Ed)
print(f"As yêu cầu = {As_req:.0f} mm² → chọn 4Ø20 = {4*314:.0f} mm²")

# Kiểm tra cắt (EC2 §6.2)
shear = ShearCheck(
    V_Ed=280e3,    # N
    b_w=300,
    d=540,
    fck=concrete.fck,
    rho_l=As_req / (300*540)
)
print(f"V_Rd,c = {shear.V_Rd_c/1e3:.1f} kN | V_Ed = {280:.1f} kN")
if shear.requires_stirrups:
    print(f"Cần cốt đai: Asw/s ≥ {shear.asw_s_required:.2f} mm²/mm")

# Kiểm tra chống chọc thủng bản sàn (EC2 §6.4)
punch = PunchingShear(
    V_Ed=1200e3,   # N — Phản lực cột
    d=200,         # mm
    fck=30,
    u0=1200,       # mm — chu vi cột
    u1=4000        # mm — chu vi kiểm tra 2d
)
print(f"v_Rd,c = {punch.v_Rd_c:.3f} MPa | v_Ed = {punch.v_Ed:.3f} MPa")
```

---

## 4. Tự động Xuất JSON Kết quả (Pydantic Schema)

```python
from pydantic import BaseModel
from typing import Literal

class DesignCheckResult(BaseModel):
    element_id:       str
    status:           Literal['PASS', 'FAIL']
    min_reinforcement_cm2: float
    utilization_ratio:     float
    governing_load_case:   str
    diagram_path:          str

# Tạo kết quả
result = DesignCheckResult(
    element_id="Column_C1",
    status="PASS" if ratio <= 1.0 else "FAIL",
    min_reinforcement_cm2=As_req / 100,
    utilization_ratio=ratio,
    governing_load_case="LC_05_WindX",
    diagram_path="assets/diagrams/pm_col_C1.png"
)

import json
with open("output/col_C1_result.json", "w", encoding="utf-8") as f:
    json.dump(result.dict(), f, ensure_ascii=False, indent=2)

print(json.dumps(result.dict(), ensure_ascii=False, indent=2))
```

---

## Checklist Kiểm toán

- [ ] Bê tông dùng mô hình **tam tuyến tính** (không dùng parabolic đơn giản)
- [ ] Cốt thép CB-400V/CB-500V dùng mô hình **song tuyến tính**
- [ ] Lớp bảo vệ bê tông tăng 5–10mm so với TCVN 2012
- [ ] Biểu đồ P-M lưu vào `assets/diagrams/` trước khi báo cáo
- [ ] Mọi kết quả lưu JSON theo Pydantic Schema để Agent đọc được
