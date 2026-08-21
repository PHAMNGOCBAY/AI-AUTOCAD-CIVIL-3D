import os
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF

# 1. Inputs
L = 7.0       # m
q = 5.0       # kN/m
b = 0.5       # m
h = 0.3       # m
fck = 40.0    # MPa
Ec = 35e6     # kPa (35 GPa)
rho = 2500    # kg/m3

# 2. Calculations
A = b * h
I = b * h**3 / 12.0
m = A * rho
EI = Ec * I

# Internal forces
Mmax = q * L**2 / 8.0
Vmax = q * L / 2.0

# Displacement
delta_max = 5 * q * L**4 / (384 * EI)

# Vibration modes
fn = []
for n in range(1, 4):
    wn = (n * np.pi / L)**2 * np.sqrt((Ec * 1000 * I) / m)
    fn.append(wn / (2 * np.pi))

# Steel Reinforcement Check (Eurocode/TCVN based)
fcd = fck / 1.5
fyd = 400 / 1.15
d = h - 0.04  # assuming 40mm cover to center of reinforcement
M_Ed_Nmm = Mmax * 1e6
K = M_Ed_Nmm / (b * 1000 * (d * 1000)**2 * fcd)
# Approximate Eurocode lever arm z
z_c = (d * 1000) * (0.5 + 0.5 * np.sqrt(1 - 3.53 * K))
# Cap z_c at 0.95d
z_c = min(z_c, 0.95 * d * 1000)
As_req = M_Ed_Nmm / (fyd * z_c) # mm2

# 3. Plots
out_dir = os.path.dirname(os.path.abspath(__file__))

# Plot 1: Shear and Moment
x = np.linspace(0, L, 200)
V = q * (L/2 - x)
M = q * x / 2 * (L - x)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
ax1.plot(x, V, 'b-', label='Shear (kN)')
ax1.fill_between(x, V, 0, alpha=0.3, color='b')
ax1.set_title('Shear Force Diagram / Biểu đồ lực cắt', fontname="Arial")
ax1.set_ylabel('V (kN)', fontname="Arial")
ax1.grid(True)

ax2.plot(x, M, 'r-', label='Moment (kN.m)')
ax2.fill_between(x, M, 0, alpha=0.3, color='r')
ax2.set_title('Bending Moment Diagram / Biểu đồ mô men uốn', fontname="Arial")
ax2.set_xlabel('Length / Chiều dài (m)', fontname="Arial")
ax2.set_ylabel('M (kN.m)', fontname="Arial")
ax2.grid(True)
plt.tight_layout()
fig1_path = os.path.join(out_dir, 'forces.png')
plt.savefig(fig1_path, dpi=150)
plt.close()

# Plot 2: Mode shapes
fig, ax = plt.subplots(figsize=(8, 4))
for n in range(1, 4):
    phi = np.sin(n * np.pi * x / L)
    ax.plot(x, phi, label=f'Mode {n} ({fn[n-1]:.2f} Hz)')
ax.set_title('Vibration Mode Shapes / Dạng dao động', fontname="Arial")
ax.set_xlabel('Length / Chiều dài (m)', fontname="Arial")
ax.set_ylabel('Amplitude / Biên độ', fontname="Arial")
ax.legend()
ax.grid(True)
plt.tight_layout()
fig2_path = os.path.join(out_dir, 'modes.png')
plt.savefig(fig2_path, dpi=150)
plt.close()

# 4. PDF Report
pdf = FPDF()
pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")

def add_title_to_page():
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(0, 10, 'Calculation Report / Thuyết minh tính toán (Bài toán 1)', align='C')
    pdf.ln(15)

pdf.add_page()
add_title_to_page()

def add_val(desc_en, desc_vi, formula, val, unit):
    pdf.set_font('Arial', '', 12)
    txt = f"- {desc_en} / {desc_vi}:\n  {formula} = {val:.4f} {unit}"
    pdf.multi_cell(0, 6, txt)
    pdf.ln(2)

pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, '1. Input Parameters / Thông số đầu vào')
pdf.ln(10)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 6, f"- Span length / Chiều dài nhịp: L = {L} m\n- Uniform load / Tải trọng rải đều: q = {q} kN/m\n- Width / Chiều rộng mặt cắt: b = {b} m\n- Height / Chiều cao mặt cắt: h = {h} m\n- Concrete / Bê tông: C40 (fck = {fck} MPa, Ec = {Ec/1e6:.1f} GPa)\n- Density / Khối lượng riêng: rho = {rho} kg/m3")
pdf.ln(5)

pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, '2. Section Properties / Đặc trưng mặt cắt')
pdf.ln(10)
add_val("Area", "Diện tích mặt cắt", "A = b * h", A, "m2")
add_val("Moment of Inertia", "Mô men quán tính", "I = b * h^3 / 12", I, "m4")
add_val("Mass per meter", "Khối lượng trên mét dài", "m = A * rho", m, "kg/m")
pdf.ln(5)

pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, '3. Internal Forces / Nội lực')
pdf.ln(10)
add_val("Max Bending Moment", "Mô men uốn lớn nhất", "M_max = q * L^2 / 8", Mmax, "kN.m")
add_val("Max Shear Force", "Lực cắt lớn nhất", "V_max = q * L / 2", Vmax, "kN")
pdf.image(fig1_path, w=150)
pdf.ln(5)

pdf.add_page()
add_title_to_page()
pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, '4. Displacement & Vibration / Chuyển vị & Dao động')
pdf.ln(10)
add_val("Max Displacement", "Độ võng lớn nhất", "delta_max = 5 * q * L^4 / (384 * Ec * I)", delta_max * 1000, "mm")
add_val("Mode 1 Frequency", "Tần số dao động riêng Mode 1", "f1", fn[0], "Hz")
add_val("Mode 2 Frequency", "Tần số dao động riêng Mode 2", "f2", fn[1], "Hz")
add_val("Mode 3 Frequency", "Tần số dao động riêng Mode 3", "f3", fn[2], "Hz")
pdf.image(fig2_path, w=150)
pdf.ln(5)

pdf.add_page()
pdf.set_font('Arial', 'B', 14)
pdf.cell(0, 10, '5. Steel Reinforcement Check / Kiểm toán cốt thép')
pdf.ln(10)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 6, "Assumptions / Giả thiết:\n- Steel / Cốt thép: CB400-V (fyd = 400/1.15 = 347.8 MPa)\n- Concrete / Bê tông: fcd = 40/1.5 = 26.67 MPa\n- Effective depth / Chiều cao làm việc: d = h - 0.04 m")
add_val("Required Area of Steel", "Diện tích thép yêu cầu (tính toán)", "As_req", As_req, "mm2")

# Check min steel
As_min = 0.0013 * b * 1000 * d * 1000 # 0.13%
add_val("Min Area of Steel", "Diện tích thép cấu tạo tối thiểu", "As_min (0.13%)", As_min, "mm2")

if As_req < As_min:
    pdf.set_text_color(255, 0, 0)
    pdf.multi_cell(0, 6, f"Note: Required As is less than minimum reinforcement. Use As_min = {As_min:.2f} mm2\nLưu ý: As yêu cầu nhỏ hơn thép cấu tạo. Bố trí theo thép tối thiểu As_min.")
    pdf.set_text_color(0, 0, 0)

out_pdf = os.path.join(out_dir, 'Report_Baitoan1.pdf')
pdf.output(out_pdf)
print(f"Generated PDF successfully at: {out_pdf}")
