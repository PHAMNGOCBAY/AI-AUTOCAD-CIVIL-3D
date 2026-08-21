# -*- coding: utf-8 -*-
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# 1. Inputs
L = 7.0
q = 5.0
b = 0.5
h = 0.3
fck = 40.0
Ec = 35e6
rho = 2500

# 2. Calculations
A = b * h
I = b * h**3 / 12.0
m = A * rho
EI = Ec * I
Mmax = q * L**2 / 8.0
Vmax = q * L / 2.0
delta_max = 5 * q * L**4 / (384 * EI)

fn = []
for n in range(1, 4):
    wn = (n * np.pi / L)**2 * np.sqrt((Ec * 1000 * I) / m)
    fn.append(wn / (2 * np.pi))

fcd = fck / 1.5
fyd = 400 / 1.15
d = h - 0.04
M_Ed_Nmm = Mmax * 1e6
K = M_Ed_Nmm / (b * 1000 * (d * 1000)**2 * fcd)
z_c = (d * 1000) * (0.5 + 0.5 * np.sqrt(1 - 3.53 * K))
z_c = min(z_c, 0.95 * d * 1000)
As_req = M_Ed_Nmm / (fyd * z_c)
As_min = 0.0013 * b * 1000 * d * 1000

# 3. Generating PDF using Matplotlib
out_dir = os.path.dirname(os.path.abspath(__file__))
out_pdf = os.path.join(out_dir, 'Report_Baitoan1.pdf')

with PdfPages(out_pdf) as pdf:
    # Page 1: Text report
    fig = plt.figure(figsize=(8.27, 11.69)) # A4 size
    plt.axis('off')
    
    y = 0.95
    plt.text(0.5, y, "Calculation Report / Thuyết minh tính toán (Bài toán 1)", 
             fontsize=16, weight='bold', ha='center', fontname="Arial")
    y -= 0.05
    
    plt.text(0.1, y, "1. Input Parameters / Thông số đầu vào", fontsize=14, weight='bold', fontname="Arial")
    y -= 0.03
    plt.text(0.1, y, f"- Span length / Chiều dài nhịp: L = {L} m", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Uniform load / Tải trọng rải đều: q = {q} kN/m", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Section / Mặt cắt: b = {b} m, h = {h} m", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Concrete / Bê tông: C40 (fck = {fck} MPa, Ec = {Ec/1e6:.1f} GPa)", fontsize=12, fontname="Arial")
    y -= 0.05
    
    plt.text(0.1, y, "2. Section Properties / Đặc trưng mặt cắt", fontsize=14, weight='bold', fontname="Arial")
    y -= 0.03
    plt.text(0.1, y, f"- Area / Diện tích mặt cắt: A = b * h = {A:.4f} m2", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Moment of Inertia / Mô men quán tính: I = b * h^3 / 12 = {I:.6f} m4", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Mass per meter / Khối lượng: m = A * rho = {m:.1f} kg/m", fontsize=12, fontname="Arial")
    y -= 0.05
    
    plt.text(0.1, y, "3. Internal Forces / Nội lực", fontsize=14, weight='bold', fontname="Arial")
    y -= 0.03
    plt.text(0.1, y, f"- Max Bending Moment / Mô men uốn max: M_max = q*L^2/8 = {Mmax:.3f} kN.m", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Max Shear Force / Lực cắt max: V_max = q*L/2 = {Vmax:.3f} kN", fontsize=12, fontname="Arial")
    y -= 0.05
    
    plt.text(0.1, y, "4. Displacement & Vibration / Chuyển vị & Dao động", fontsize=14, weight='bold', fontname="Arial")
    y -= 0.03
    plt.text(0.1, y, f"- Max Displacement / Độ võng max: delta_max = 5qL^4/(384EI) = {delta_max*1000:.2f} mm", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Mode 1 Frequency / Tần số Mode 1: f1 = {fn[0]:.2f} Hz", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Mode 2 Frequency / Tần số Mode 2: f2 = {fn[1]:.2f} Hz", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Mode 3 Frequency / Tần số Mode 3: f3 = {fn[2]:.2f} Hz", fontsize=12, fontname="Arial")
    y -= 0.05
    
    plt.text(0.1, y, "5. Steel Reinforcement Check / Kiểm toán cốt thép", fontsize=14, weight='bold', fontname="Arial")
    y -= 0.03
    plt.text(0.1, y, f"- Steel / Cốt thép: CB400-V (fyd = 400/1.15 = 347.8 MPa)", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Required Steel Area / Diện tích thép yêu cầu: As_req = {As_req:.2f} mm2", fontsize=12, fontname="Arial")
    y -= 0.02
    plt.text(0.1, y, f"- Min Steel Area / Diện tích thép tối thiểu (0.13%): As_min = {As_min:.2f} mm2", fontsize=12, fontname="Arial")
    y -= 0.02
    if As_req < As_min:
        plt.text(0.1, y, f"=> Use As_min / Bố trí theo thép tối thiểu: {As_min:.2f} mm2", fontsize=12, color='red', fontname="Arial")
    
    pdf.savefig(fig)
    plt.close()
    
    # Page 2: Diagrams
    x = np.linspace(0, L, 200)
    V = q * (L/2 - x)
    M = q * x / 2 * (L - x)

    fig = plt.figure(figsize=(8.27, 11.69))
    
    ax1 = fig.add_subplot(311)
    ax1.plot(x, V, 'b-')
    ax1.fill_between(x, V, 0, alpha=0.3, color='b')
    ax1.set_title('Shear Force Diagram / Biểu đồ lực cắt', fontname="Arial", fontsize=14)
    ax1.set_ylabel('V (kN)', fontname="Arial")
    ax1.grid(True)
    
    ax2 = fig.add_subplot(312)
    ax2.plot(x, M, 'r-')
    ax2.fill_between(x, M, 0, alpha=0.3, color='r')
    ax2.set_title('Bending Moment Diagram / Biểu đồ mô men uốn', fontname="Arial", fontsize=14)
    ax2.set_ylabel('M (kN.m)', fontname="Arial")
    ax2.grid(True)
    
    ax3 = fig.add_subplot(313)
    for n in range(1, 4):
        phi = np.sin(n * np.pi * x / L)
        ax3.plot(x, phi, label=f'Mode {n} ({fn[n-1]:.2f} Hz)')
    ax3.set_title('Vibration Mode Shapes / Dạng dao động', fontname="Arial", fontsize=14)
    ax3.set_xlabel('Length / Chiều dài (m)', fontname="Arial")
    ax3.legend()
    ax3.grid(True)
    
    plt.tight_layout(pad=3.0)
    pdf.savefig(fig)
    plt.close()

print(f"Generated PDF successfully at: {out_pdf}")
