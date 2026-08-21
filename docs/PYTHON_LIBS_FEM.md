# PYTHON_LIBS_FEM.md — Thư viện Python: Phân tích Kết cấu (FEM)
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Tổng quan Thư viện FEM Mã nguồn Mở

| Phạm vi | Thư viện | Thay thế phần mềm | Ưu điểm cốt lõi |
|---|---|---|---|
| Động lực học & Phi tuyến | `OpenSeesPy` | SAP2000, ETABS, Perform3D | Phần tử sợi, phi tuyến vật liệu, time-history |
| Tĩnh lực học 3D | `PyNite`, `StructPy` | STAAD.Pro, Robot Structural | Nhẹ, triển khai nhanh, ma trận độ cứng chính xác |
| Kết cấu 2D & Dầm | `AnaStruct`, `PyCBA` | SAP2000 2D, MIDAS Civil | Đường ảnh hưởng, tổ hợp tải di chuyển cho cầu |
| Động lực học rung động | `pydvma`, `SDyPy` | ANSYS Mechanical (Modal) | FFT, hàm truyền, ma trận thưa |

---

## 1. OpenSeesPy — Phân tích Phi tuyến & Động lực học

### Điểm mạnh
- Mô phỏng hành vi dẻo phi tuyến (plastic behavior) qua **phần tử sợi (fiber sections)**
- Phân tích **lịch sử thời gian (time-history)** và **phổ phản ứng (spectral modal)**
- Tương đồng cao với SAP2000/ETABS về kết quả vĩ mô

### Lưu ý so với SAP2000
```
SAP2000: Tự động tính trọng lượng bản thân cột trong phân tích trọng trường
OpenSees: Phải định nghĩa tường minh khối lượng này
```

### Ví dụ cơ bản
```python
import openseespy.opensees as ops

ops.wipe()
ops.model('basic', '-ndm', 2, '-ndf', 3)

# Khai báo vật liệu phi tuyến bê tông (Concrete02)
ops.uniaxialMaterial('Concrete02', 1,
    -30e6,   # fpc  - cường độ nén đỉnh (Pa)
    -0.002,  # epsc0 - biến dạng tại đỉnh
    -6e6,    # fpcu  - cường độ nén cuối
    -0.006,  # epsU  - biến dạng cực hạn
    0.1,     # lambda - tham số đường xuống
    3.6e6,   # ft    - cường độ kéo
    0.0001   # Ets  - modul giảm sau khi nứt
)

# Phần tử sợi (Fiber Section)
ops.section('Fiber', 1)
ops.patch('rect', 1, 10, 10,
    -0.15, -0.15, 0.15, 0.15)  # Lưới bê tông 10x10 sợi

ops.analyze(100, 0.01)         # 100 bước, dt=0.01s
print(f"Chuyển vị đỉnh: {ops.nodeDisp(2, 1)*1000:.2f} mm")
```

---

## 2. PyNite — Phân tích Tĩnh lực học 3D

### Đặc điểm
- FEM 3D cho dầm, khung, giàn — kết quả **trùng khớp tuyệt đối với SAP2000**
- Tự động hóa hoàn toàn: sinh mô hình → giải → trích xuất nội lực

### Lưu ý thiết lập điều kiện biên tương đương với SAP2000
```python
# Bỏ qua biến dạng cắt (Shear Deformation = OFF)
member.Iy = 0    # Diện tích chịu cắt = 0 → bỏ biến dạng cắt
```

### Ví dụ phân tích khung 3D
```python
from PyNite import FEModel3D

frame = FEModel3D()

# Vật liệu thép
E = 200e9     # Pa
G = 77e9      # Pa
nu = 0.3
rho = 7850    # kg/m³

# Thêm nút
frame.add_node('N1', 0, 0, 0)
frame.add_node('N2', 0, 5, 0)   # Đỉnh cột h=5m
frame.add_node('N3', 6, 5, 0)   # Đầu dầm L=6m
frame.add_node('N4', 6, 0, 0)

# Thêm cấu kiện (HEA 200)
Iy = 3.69e-5  # m⁴
Iz = 1.34e-5  # m⁴
J  = 2.28e-7  # m⁴ (xoắn)
A  = 53.8e-4  # m²

frame.add_member('C1', 'N1', 'N2', E, G, Iy, Iz, J, A)
frame.add_member('D1', 'N2', 'N3', E, G, Iy, Iz, J, A)
frame.add_member('C2', 'N3', 'N4', E, G, Iy, Iz, J, A)

# Điều kiện biên: ngàm tại N1, N4
for node in ['N1', 'N4']:
    frame.def_support(node, True, True, True, True, True, True)

# Tải trọng: lực ngang đỉnh cột
frame.add_node_load('N2', 'FX', 10e3)   # 10 kN ngang
frame.add_member_dist_load('D1', 'FY', -20e3, -20e3)  # 20 kN/m đứng

frame.analyze()

# Trích xuất nội lực tại đầu dầm
M_max = frame.members['D1'].max_moment('Mz')
V_max = frame.members['D1'].max_shear('Fy')
print(f"M_max = {M_max/1e3:.2f} kN.m | V_max = {V_max/1e3:.2f} kN")
```

---

## 3. StructPy — Phân tích Khung & Giàn 3D (Tĩnh lực học)

### Điểm khác biệt so với PyNite
- API **hướng đối tượng** rõ ràng hơn, phù hợp với quy trình học thuật
- Tích hợp sẵn **mô hình vật liệu** và **mặt cắt thư viện** (HEA, IPE, CHS...)
- Sinh biểu đồ nội lực trực tiếp từ đối tượng Member

```python
import structpy as sp

# Khai báo kết cấu
structure = sp.Structure()

# Vật liệu thép S355
material = sp.Material(
    name='Steel_S355',
    E=210e9,      # Pa
    G=81e9,       # Pa
    density=7850  # kg/m³
)

# Mặt cắt HEA 240
section = sp.Section.from_library('HEA240')  # Lấy từ database thư viện
print(f"A={section.A:.2e}m² | Iy={section.Iy:.2e}m⁴ | Iz={section.Iz:.2e}m⁴")

# Thêm nút
n1 = structure.add_node(x=0, y=0, z=0)
n2 = structure.add_node(x=0, y=0, z=4.0)  # Đỉnh cột
n3 = structure.add_node(x=6.0, y=0, z=4.0)  # Đầu dầm
n4 = structure.add_node(x=6.0, y=0, z=0)

# Thêm cấu kiện
c1 = structure.add_member(n1, n2, section, material, name='Col-1')
d1 = structure.add_member(n2, n3, section, material, name='Beam-1')
c2 = structure.add_member(n3, n4, section, material, name='Col-2')

# Điều kiện biên: ngàm 6 bậc tự do
for node in [n1, n4]:
    structure.add_support(node, Tx=True, Ty=True, Tz=True,
                                Rx=True, Ry=True, Rz=True)

# Tải trọng
structure.add_nodal_load(n2, Fx=15e3, Fz=-5e3)  # 15kN ngang, 5kN đứng
structure.add_distributed_load(d1, qz=-25e3)     # 25 kN/m đứng trên dầm

# Giải và trích xuất
structure.analyze()

# Biểu đồ nội lực
for member in [c1, d1, c2]:
    print(f"{member.name}: N={member.axial_force(0)/1e3:.1f}kN "
          f"| M_max={member.max_moment()/1e3:.2f}kN.m "
          f"| V_max={member.max_shear()/1e3:.2f}kN")

# Xuất biểu đồ M, V, N
structure.plot_bending_moment(scale=1/1e6, title="Biểu đồ Mô men (kN.m)")
```

---

## 4. AnaStruct — Phân tích Khung & Giàn 2D

### Điểm mạnh
- Chuyên biệt cho **bài toán phẳng (2D)** — nhanh, API trực quan
- Hỗ trợ **nút phi tuyến** và **phi tuyến hình học**
- Vẽ biểu đồ chất lượng xuất bản (publication-quality)

```python
from anastruct import SystemElements

ss = SystemElements()

# Khai báo cấu kiện (mm → đổi sang m nếu cần)
# Cột trái: (0,0) → (0,4)
ss.add_element(location=[[0, 0], [0, 4]],
               EI=210e9 * 3.69e-5,  # E*I (N.m²)
               EA=210e9 * 53.8e-4)  # E*A (N)

# Dầm: (0,4) → (6,4)
ss.add_element(location=[[0, 4], [6, 4]],
               EI=210e9 * 3.69e-5,
               EA=210e9 * 53.8e-4)

# Cột phải: (6,4) → (6,0)
ss.add_element(location=[[6, 4], [6, 0]],
               EI=210e9 * 3.69e-5,
               EA=210e9 * 53.8e-4)

# Điều kiện biên: ngàm tại chân cột (node_id=1 và 4)
ss.add_support_fixed(node_id=1)
ss.add_support_fixed(node_id=4)

# Tải trọng
ss.add_load_nodal(node_id=2, Fx=20e3)          # Lực ngang 20kN
ss.add_load_element(element_id=2, q=-15e3)      # Phân bố 15kN/m trên dầm

# Giải
ss.solve()

# Trích xuất kết quả
for el_id in [1, 2, 3]:
    el = ss.element_map[el_id]
    print(f"Phần tử {el_id}: "
          f"M_i={el.bending_moment[0]/1e3:.2f}kN.m | "
          f"M_j={el.bending_moment[-1]/1e3:.2f}kN.m | "
          f"V={el.shear_force[0]/1e3:.2f}kN")

# Vẽ biểu đồ nội lực
ss.show_bending_moment(factor=1e-6)
ss.show_shear_force()
ss.show_displacement(factor=200)  # phóng đại 200 lần để rõ

# Xuất phản lực
for node_id, reaction in ss.get_node_results_system().items():
    if abs(reaction['Fx']) > 1 or abs(reaction['Fy']) > 1:
        print(f"Nút {node_id}: Rx={reaction['Fx']/1e3:.2f}kN "
              f"| Ry={reaction['Fy']/1e3:.2f}kN "
              f"| Mz={reaction.get('Tz',0)/1e3:.2f}kN.m")
```

---

## 5. PyCBA — Dầm Liên tục & Đường ảnh hưởng (Cầu)

### Điểm mạnh
- Phân tích **đường ảnh hưởng (influence lines)**
- **Tải trọng di chuyển (moving load)** theo tiêu chuẩn AS/TCVN
- Tổ hợp **đường bao (envelope)** để tìm nội lực bất lợi nhất

```python
from pycba import BeamAnalysis

# Khai báo dầm liên tục 3 nhịp (m)
#   Gối: P=Pin, F=Fixed, R=Roller
ba = BeamAnalysis(
    L=[20.0, 25.0, 20.0],
    EI=2.5e10,              # N.m²
    R=['P', 'R', 'R', 'P'], # Gối tựa 4 vị trí
)

# Tải trọng xe tải HL-93 (kN)
vehicle = {'axle_loads': [35, 145, 145],
           'axle_spacing': [4.3, 9.0]}

ba.add_vehicle_load(vehicle, step=0.5)
results = ba.analyze()

# Đường bao mô men (kN.m)
M_env_max = results.envelope_moment_max
M_env_min = results.envelope_moment_min
print(f"M+ max = {max(M_env_max)/1e3:.1f} kN.m")
print(f"M- max = {min(M_env_min)/1e3:.1f} kN.m")
```

---

## 6. Phân tích Rung động — pydvma & SDyPy

### pydvma — Xử lý Tín hiệu Đo đạc Thực tế

```python
import pydvma as dvma
import numpy as np

# Đọc dữ liệu gia tốc đo đạc (từ cảm biến thực tế)
data = dvma.load_measurement('acceleration_data.csv')

# Biến đổi Fourier nhanh (FFT)
fft_result = dvma.compute_fft(data, window='hanning')
dvma.plot_fft(fft_result, title='Phổ Tần số Kết cấu')

# Hàm truyền (FRF - Frequency Response Function)
frf = dvma.compute_frf(input_data=data['force'],
                       output_data=data['accel'])

# Ước lượng tần số tự nhiên và hệ số cản
modal = dvma.modal_analysis(frf)
for i, mode in enumerate(modal.modes):
    print(f"Mode {i+1}: f={mode.freq:.2f}Hz | ζ={mode.damping:.3f}")
```

### SDyPy — Phân tích Modal từ Ma trận Khối lượng/Độ cứng

> Phù hợp khi đã có ma trận M, K từ mô hình FEM (OpenSeesPy / PyNite)

```python
import sdypy as sd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh

# ---- Ví dụ: Hệ 3 bậc tự do (khung 3 tầng) ----
# Khối lượng mỗi tầng (kg)
m = 50000.0
M = np.diag([m, m, m])

# Ma trận độ cứng (N/m) — khung cắt (shear frame)
k = 5e7   # N/m
K = np.array([
    [ 2*k, -k,   0  ],
    [-k,   2*k, -k  ],
    [ 0,  -k,    k  ]
])

# Giải bài toán trị riêng tổng quát: K*φ = ω²*M*φ
# Phương pháp QR với phản xạ Householder (scipy.linalg.eigh)
from scipy.linalg import eigh
omega2, phi = eigh(K, M)   # Trả về trị riêng tăng dần

omega = np.sqrt(omega2)    # rad/s
freq  = omega / (2 * np.pi)  # Hz

print("Tần số tự nhiên:")
for i, f in enumerate(freq):
    T = 1 / f
    print(f"  Mode {i+1}: f={f:.3f} Hz | T={T:.3f}s | ω={omega[i]:.3f} rad/s")

# ---- Phân tích phổ phản ứng (Response Spectrum) ----
# Dùng SDyPy tính gia tốc đỉnh theo TCVN 9386:2012
xi  = 0.05  # Hệ số cản 5%
PGA = 0.1   # g (gia tốc nền thiết kế, vùng 2a VN)

Sa_list = []
for i in range(len(freq)):
    T_i = 1 / freq[i]
    # Spectrum shape theo TCVN 9386 (Loại 1, đất nền C)
    TB, TC, TD = 0.15, 0.50, 2.0
    S, eta = 1.15, max(0.55, 1/np.sqrt(2*xi/0.05))

    if T_i <= TB:
        Sa = PGA * S * (1 + T_i/TB * (eta*2.5 - 1))
    elif T_i <= TC:
        Sa = PGA * S * eta * 2.5
    elif T_i <= TD:
        Sa = PGA * S * eta * 2.5 * (TC/T_i)
    else:
        Sa = PGA * S * eta * 2.5 * (TC*TD/T_i**2)

    Sa_list.append(Sa * 9.81)  # m/s²
    print(f"  Mode {i+1}: Sa={Sa:.3f}g = {Sa*9.81:.3f} m/s²")

# Tổ hợp CQC (Complete Quadratic Combination)
xi_arr = np.full(len(freq), xi)
Sd_arr = np.array([Sa / w**2 for Sa, w in zip(Sa_list, omega)])
U_cqc  = sd.response_spectrum.cqc_combination(
    phi=phi, Sd=Sd_arr, M=M, xi=xi_arr
)
print(f"\nChuyển vị đỉnh CQC: {U_cqc[-1]*1000:.2f} mm")
```

---

## Checklist Lựa chọn Thư viện

| Bài toán | Thư viện ưu tiên |
|---|---|
| Động lực học phi tuyến / kháng chấn | **OpenSeesPy** |
| Khung 3D tĩnh — API học thuật | **StructPy** |
| Khung 3D tĩnh — so sánh SAP2000 | **PyNite** |
| Khung phẳng 2D / giàn | **AnaStruct** |
| Dầm liên tục / tải trọng di chuyển | **PyCBA** |
| Xử lý tín hiệu đo đạc hiện trường | **pydvma** |
| Phân tích modal từ ma trận M, K | **SDyPy** + `scipy.linalg.eigh` |
| Tổ hợp phổ phản ứng (CQC/SRSS) | **SDyPy** |

- [ ] Hệ thưa (> 1000 bậc tự do) → dùng `scipy.sparse.linalg.eigsh` thay vì `eigh`
- [ ] Cần so sánh với SAP2000 → bỏ biến dạng cắt (`Iy=0` trong PyNite)
- [ ] Phổ phản ứng TCVN 9386:2012 → đất nền A/B/C/D cho hệ số S, TB, TC, TD khác nhau
