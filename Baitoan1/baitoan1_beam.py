#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAI TOAN 1 — DAM GIAN DON / SIMPLY SUPPORTED BEAM
Noi luc, chuyen vi, dao dong (3 mo hinh), kiem toan thep
Internal forces, deflection, vibration (3 models), steel check
Tieu chuan / Standard: TCVN 5574:2018, TCVN 1651-2:2018
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import scipy.linalg as la
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# 0. OUTPUT
# ═══════════════════════════════════════════════════════════════
OUT = r"G:\My Drive\AI-AUTOCAD CIVIL 3D\Baitoan1"
os.makedirs(OUT, exist_ok=True)
PDF = os.path.join(OUT, "Baitoan1_DamGianDon_Report.pdf")

# ═══════════════════════════════════════════════════════════════
# 1. THONG SO DAU VAO / INPUT PARAMETERS
# ═══════════════════════════════════════════════════════════════
L    = 7.0      # Nhip [m] / Span [m]
q    = 5.0      # Tai phan bo deu [kN/m] / UDL [kN/m]
b    = 0.50     # Be rong [m] / Width [m]
h    = 0.30     # Chieu cao [m] / Height [m]

# Be tong C40 — TCVN 5574:2018 Bang 6
Rb   = 22.0     # Cuong do chiu nen tinh toan [MPa]
Rbt  = 1.4      # Cuong do chiu keo tinh toan [MPa]
Eb   = 32500.0  # Modul dan hoi [MPa]
rho  = 2500.0   # Khoi luong rieng [kg/m3]
nu   = 0.2      # He so Poisson

# Thep CB400-V — TCVN 1651-2:2018
Rs   = 350.0    # Cuong do chiu keo tinh toan [MPa]
Rsc  = 350.0    # Cuong do chiu nen tinh toan [MPa]
Es   = 200000.0 # Modul dan hoi thep [MPa]
xi_R = 0.531    # Gia tri gioi han xi_R (CB400-V, C40, TCVN 5574:2018 Bang 9)

# Thep dai CB240-T
Rsw  = 175.0    # [MPa]

# Lop bao ve
a_s  = 0.035    # [m] = 35mm (bao ve 25mm + ban kinh cot 10mm)

# ═══════════════════════════════════════════════════════════════
# 2. DAC TRUNG MAT CAT / SECTION PROPERTIES
# ═══════════════════════════════════════════════════════════════
A    = b * h                    # Dien tich [m2]
I    = b * h**3 / 12            # Moment quan tinh [m4]
Wg   = I / (h / 2)             # Moment chong uon [m3]
EI   = Eb * 1e6 * I            # Do cung uon [N.m2]
m    = rho * A                  # Khoi luong don vi chieu dai [kg/m]
h0   = h - a_s                  # Chieu cao lam viec [m]
S0   = b * (h/2) * (h/4)       # Moment tinh [m3] tai truc trung hoa
alpha_E = Es / Eb               # Ti so modul

# ═══════════════════════════════════════════════════════════════
# 3. NOI LUC / INTERNAL FORCES
# ═══════════════════════════════════════════════════════════════
RA   = RB = q * L / 2          # Phan luc [kN]

NX   = 1000
x    = np.linspace(0, L, NX)
V    = RA - q * x               # Luc cat [kN]
M    = RA * x - q * x**2 / 2   # Moment uon [kN.m]

M_max = q * L**2 / 8           # [kN.m]
V_max = q * L / 2              # [kN]

# Ung suat / Stresses
sigma_top = -(M_max * 1e3) * (h/2) / I / 1e6   # [MPa] nen / compression
sigma_bot =  (M_max * 1e3) * (h/2) / I / 1e6   # [MPa] keo / tension
tau_max   = (V_max  * 1e3) * S0  / (I * b) / 1e6  # [MPa]

# ═══════════════════════════════════════════════════════════════
# 4. CHUYEN VI / DEFLECTION
# ═══════════════════════════════════════════════════════════════
# y(x) = q*x*(L^3 - 2L*x^2 + x^3) / (24EI)
y       = (q * 1e3) * x * (L**3 - 2*L*x**2 + x**3) / (24 * EI)   # [m]
y_max   = 5 * (q * 1e3) * L**4 / (384 * EI)                        # [m]
y_mm    = y_max * 1000                                              # [mm]
y_allow = L / 400                                                   # [m] cho phep
y_allow_mm = y_allow * 1000
ratio_defl = y_max / y_allow

# Goc xoay tai goi / Slope at supports
theta_A = (q * 1e3) * L**3 / (24 * EI)   # [rad]
theta_A_deg = np.degrees(theta_A)

# ═══════════════════════════════════════════════════════════════
# 5. DAO DONG MO HINH 1 — GIAI TICH (Euler-Bernoulli)
# VIBRATION MODEL 1 — ANALYTICAL
# ═══════════════════════════════════════════════════════════════
# omega_n = (n*pi/L)^2 * sqrt(EI/m)
x_phi = np.linspace(0, L, 300)
modes1 = []
for n_m in range(1, 4):
    w = (n_m * np.pi / L)**2 * np.sqrt(EI / m)
    f = w / (2 * np.pi)
    T = 1.0 / f
    phi = np.sin(n_m * np.pi * x_phi / L)
    modes1.append(dict(n=n_m, omega=w, f=f, T=T, phi=phi))

# ═══════════════════════════════════════════════════════════════
# 6. DAO DONG MO HINH 2 — PHUONG PHAP RAYLEIGH
# VIBRATION MODEL 2 — RAYLEIGH METHOD
# ═══════════════════════════════════════════════════════════════
# Ham dang: y(x) = x(L^3 - 2Lx^2 + x^3) (dang vong tinh)
# omega^2 = [EI * integral(phi''^2 dx)] / [m * integral(phi^2 dx)]
x_r  = np.linspace(0, L, 2000)
dx_r = x_r[1] - x_r[0]
phi_r  = x_r * (L**3 - 2*L*x_r**2 + x_r**3)
phi_r  = phi_r / np.max(phi_r)                    # chuan hoa / normalize
phi_pp = np.gradient(np.gradient(phi_r, dx_r), dx_r)   # vi phan so 2 / 2nd deriv

num_r = EI * np.trapezoid(phi_pp**2, x_r)
den_r = m  * np.trapezoid(phi_r**2,  x_r)
omega_r = np.sqrt(num_r / den_r)
f_r = omega_r / (2 * np.pi)
T_r = 1.0 / f_r
modes2 = dict(omega=omega_r, f=f_r, T=T_r, phi=phi_r, x=x_r)

# ═══════════════════════════════════════════════════════════════
# 7. DAO DONG MO HINH 3 — PHAN TU HUU HAN (FEM)
# VIBRATION MODEL 3 — FINITE ELEMENT METHOD
# ═══════════════════════════════════════════════════════════════
nE  = 20
nN  = nE + 1
Le  = L / nE

def ke_mat(EI_val, le):
    """Ma tran do cung phan tu dam Hermitian 4x4"""
    k = EI_val / le**3 * np.array([
        [ 12,    6*le,  -12,    6*le],
        [  6*le, 4*le**2,-6*le, 2*le**2],
        [-12,   -6*le,   12,   -6*le],
        [  6*le, 2*le**2,-6*le, 4*le**2]
    ])
    return k

def me_mat(m_lin, le):
    """Ma tran khoi luong nhat quan 4x4"""
    f = m_lin * le / 420
    M = f * np.array([
        [ 156,    22*le,   54,  -13*le],
        [  22*le,  4*le**2, 13*le, -3*le**2],
        [  54,    13*le,  156,  -22*le],
        [-13*le,  -3*le**2,-22*le,  4*le**2]
    ])
    return M

nDOF = 2 * nN
KG = np.zeros((nDOF, nDOF))
MG_fem = np.zeros((nDOF, nDOF))

for e in range(nE):
    ke = ke_mat(EI, Le)
    me = me_mat(m, Le)
    d  = [2*e, 2*e+1, 2*e+2, 2*e+3]
    for i in range(4):
        for j in range(4):
            KG[d[i], d[j]]     += ke[i, j]
            MG_fem[d[i], d[j]] += me[i, j]

# Dieu kien bien: w=0 tai goi trai (DOF 0) va goi phai (DOF 2*nE)
cons  = [0, 2*nE]
free  = [i for i in range(nDOF) if i not in cons]

Kf = KG[np.ix_(free, free)]
Mf = MG_fem[np.ix_(free, free)]

evals, evecs = la.eigh(Kf, Mf)
omegas_fem = np.sqrt(np.abs(evals))
freqs_fem  = omegas_fem / (2 * np.pi)

x_node = np.linspace(0, L, nN)
modes3 = []
for nm in range(3):
    phi_f = np.zeros(nDOF)
    phi_f[free] = evecs[:, nm]
    w_n = np.array([phi_f[2*i] for i in range(nN)])
    if np.max(np.abs(w_n)) > 0:
        w_n = w_n / np.max(np.abs(w_n))
    modes3.append(dict(n=nm+1, omega=omegas_fem[nm],
                       f=freqs_fem[nm], T=1/freqs_fem[nm], phi=w_n))

# ═══════════════════════════════════════════════════════════════
# 8. KIEM TOAN COT THEP — TCVN 5574:2018
# STEEL REINFORCEMENT CHECK
# ═══════════════════════════════════════════════════════════════
M_Nm  = M_max * 1e3             # [N.m]
Rb_Pa = Rb * 1e6                # [Pa]
Rs_Pa = Rs * 1e6                # [Pa]
Rbt_Pa= Rbt* 1e6                # [Pa]
Rsw_Pa= Rsw* 1e6                # [Pa]

alpha_m = M_Nm / (Rb_Pa * b * h0**2)
xi_calc = 1.0 - np.sqrt(max(1.0 - 2.0 * alpha_m, 0))
eta_s   = 1.0 - xi_calc / 2.0
z_arm   = eta_s * h0

As_req    = M_Nm / (Rs_Pa * z_arm)
As_req_mm2= As_req * 1e6
As_req_cm2= As_req * 1e4

# Chon thanh thep / Bar selection
bar_options = [(2,14),(2,16),(3,12),(3,14),(2,18),(3,16),(2,20),(3,18),(4,16)]
chosen = None
for nb, db in bar_options:
    a_prov = nb * np.pi/4 * (db/1000)**2 * 1e6  # mm2
    if a_prov >= As_req_mm2:
        chosen = (nb, db, a_prov)
        break
if chosen is None:
    chosen = (4, 20, 4 * np.pi/4 * (20/1000)**2 * 1e6)

n_bars, d_bar_mm, As_prov_mm2 = chosen
As_prov_m2   = As_prov_mm2 / 1e6
As_prov_cm2  = As_prov_mm2 / 100

# Truc trung hoa thuc te / Actual neutral axis
x_na    = As_prov_m2 * Rs_Pa / (Rb_Pa * b)
xi_act  = x_na / h0
ok_xi   = xi_act < xi_R

# Kha nang chiu uon thuc te / Actual moment capacity
M_Rd_Nm = Rs_Pa * As_prov_m2 * (h0 - x_na/2)
M_Rd    = M_Rd_Nm / 1e3      # [kN.m]
ok_M    = M_Rd >= M_max

# Ham luong cot thep / Rein. ratio
rho_s   = As_prov_m2 / (b * h0)
rho_min = 0.001              # 0.1%
ok_rho  = rho_s >= rho_min

# Kiem toan luc cat / Shear check
V_Nm    = V_max * 1e3
Qb0     = 0.5 * Rbt_Pa * b * h0   # Kha nang cat toi thieu
need_st = V_Nm > Qb0

# Thiet ke cot dai / Stirrup design
d_stir_mm= 8
Asw      = 2 * np.pi/4 * (d_stir_mm/1000)**2   # 2 nut [m2]
qsw_need = V_Nm / z_arm                         # [N/m]
s_th     = Asw * Rsw_Pa / qsw_need              # [m]
s_max1   = 0.75 * h0
s_max2   = 0.30                                 # max 300mm
s_lim    = min(s_th, s_max1, s_max2)
s_mm_raw = int(np.floor(s_lim * 1000 / 25) * 25)
s_prov_mm= max(s_mm_raw, 100)                   # toi thieu 100mm
s_prov   = s_prov_mm / 1000

qsw_prov = Asw * Rsw_Pa / s_prov
Q_sw     = qsw_prov * z_arm
Q_total  = Qb0 + Q_sw
ok_V     = Q_total >= V_Nm

# ═══════════════════════════════════════════════════════════════
# 9. VE BIEU DO & XUAT PDF
# ═══════════════════════════════════════════════════════════════

A4   = (8.27, 11.69)
C_BL = '#1565C0'   # Blue
C_RD = '#C62828'   # Red
C_GN = '#1B5E20'   # Green
C_OR = '#E65100'   # Orange
C_GR = '#37474F'   # Gray
C_LB = '#E3F2FD'   # Light blue bg
C_LG = '#F1F8E9'   # Light green bg
C_LR = '#FFEBEE'   # Light red bg

plt.rcParams.update({
    'font.family':    'DejaVu Sans',
    'font.size':       9,
    'axes.titlesize': 10,
    'axes.titleweight':'bold',
    'axes.grid':      True,
    'grid.alpha':     0.25,
    'axes.spines.top':   False,
    'axes.spines.right': False,
})

def hdr(fig, vi_title, en_title, pg, total=10):
    fig.text(0.5, 0.975, vi_title, ha='center', va='top',
             fontsize=13, fontweight='bold', color=C_BL)
    fig.text(0.5, 0.952, en_title, ha='center', va='top',
             fontsize=10, color=C_GR, fontstyle='italic')
    fig.add_artist(plt.Line2D([0.05,0.95],[0.943,0.943],
                              transform=fig.transFigure,
                              color=C_BL, lw=1.5))
    fig.text(0.5, 0.008,
             f'Trang/Page {pg}/{total}  |  Dam gian don be tong C40  |  '
             f'L={L}m, b={b}m, h={h}m, q={q}kN/m  |  '
             f'TCVN 5574:2018  |  {datetime.now().strftime("%d/%m/%Y")}',
             ha='center', va='bottom', fontsize=7, color='gray')
    fig.add_artist(plt.Line2D([0.05,0.95],[0.022,0.022],
                              transform=fig.transFigure,
                              color=C_BL, lw=0.8, linestyle='--'))

def draw_beam_scheme(ax):
    ax.set_xlim(-0.8, L+0.8)
    ax.set_ylim(-1.0, 1.4)
    ax.set_aspect('equal')
    ax.axis('off')
    # Beam body
    beam = Rectangle((0, 0), L, h, lw=1.5, ec='black', fc='#CFD8DC', alpha=0.8)
    ax.add_patch(beam)
    ax.text(L/2, h/2, f'b={b*100:.0f}cm × h={h*100:.0f}cm',
            ha='center', va='center', fontsize=8, color=C_BL, fontweight='bold')
    # UDL arrows
    for xi in np.linspace(0.2, L-0.2, 13):
        ax.annotate('', xy=(xi, h), xytext=(xi, h+0.6),
                    arrowprops=dict(arrowstyle='->', color=C_RD, lw=1.2))
    ax.plot([0, L], [h+0.6, h+0.6], color=C_RD, lw=2.5)
    ax.text(L/2, h+0.85, f'q = {q} kN/m', ha='center',
            fontsize=9, color=C_RD, fontweight='bold')
    # Left pin support
    pts_l = np.array([[0,0],[-0.25,-0.45],[0.25,-0.45],[0,0]])
    ax.plot(pts_l[:,0], pts_l[:,1], 'k-', lw=1.5)
    ax.plot([-0.32, 0.32], [-0.52, -0.52], 'k-', lw=2)
    # Right roller support
    pts_r = np.array([[L,0],[L-0.25,-0.45],[L+0.25,-0.45],[L,0]])
    ax.plot(pts_r[:,0], pts_r[:,1], 'k-', lw=1.5)
    for xi in np.linspace(L-0.32, L+0.32, 5):
        c = plt.Circle((xi, -0.52), 0.07, ec='k', fc='gray', lw=1)
        ax.add_patch(c)
    ax.plot([L-0.4, L+0.4], [-0.65, -0.65], 'k-', lw=2)
    # Span annotation
    ax.annotate('', xy=(L,-0.80), xytext=(0,-0.80),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.2))
    ax.text(L/2, -0.92, f'L = {L} m', ha='center', fontsize=9, fontweight='bold')
    # Reactions
    ax.annotate('', xy=(0, -0.08), xytext=(0, -0.5),
                arrowprops=dict(arrowstyle='->', color=C_GN, lw=2))
    ax.text(-0.5, -0.28, f'RA={RA:.1f}kN', ha='right', fontsize=8, color=C_GN, fontweight='bold')
    ax.annotate('', xy=(L, -0.08), xytext=(L, -0.5),
                arrowprops=dict(arrowstyle='->', color=C_GN, lw=2))
    ax.text(L+0.5, -0.28, f'RB={RB:.1f}kN', ha='left', fontsize=8, color=C_GN, fontweight='bold')

# ──────────────────────────────────────────────────────────────
with PdfPages(PDF) as pdf:

    # ─────────────────────────────────────────────────────────
    # TRANG 1: BIA / COVER
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')

    # Header band
    band = Rectangle((0, 0.87), 1, 0.13, transform=fig.transFigure,
                      fc=C_BL, ec='none', clip_on=False)
    fig.patches.append(band)
    fig.text(0.5, 0.965, 'BÀI TOÁN 1 / PROBLEM 1', ha='center', va='center',
             fontsize=22, fontweight='bold', color='white', transform=fig.transFigure)
    fig.text(0.5, 0.920, 'TÍNH TOÁN DẦM GIẢN ĐƠN — SIMPLY SUPPORTED BEAM ANALYSIS',
             ha='center', va='center', fontsize=11, color='#BBDEFB',
             transform=fig.transFigure)

    # Beam diagram
    ax0 = fig.add_axes([0.08, 0.64, 0.84, 0.22])
    draw_beam_scheme(ax0)
    ax0.set_title('Sơ đồ tính / Structural Diagram', fontsize=10,
                  color=C_BL, fontweight='bold', pad=4)

    # Parameter boxes
    params = [
        ('Nhịp / Span',          f'L = {L} m'),
        ('Tải phân bố / UDL',    f'q = {q} kN/m'),
        ('Bề rộng / Width',      f'b = {b*100:.0f} cm'),
        ('Chiều cao / Height',   f'h = {h*100:.0f} cm'),
        ('Vật liệu / Material',  'Bê tông C40 / Concrete C40'),
        ('Cường độ nen / fck',   f'fck = {Rb:.0f} MPa  |  Eb = {Eb:.0f} MPa'),
        ('Cốt thép / Steel',     f'CB400-V  |  Rs = {Rs:.0f} MPa'),
        ('Tiêu chuẩn / Standard','TCVN 5574:2018 | TCVN 1651-2:2018'),
    ]
    cols = 2
    rows = 4
    for i, (lbl, val) in enumerate(params):
        row = i // cols
        col = i  % cols
        x0 = 0.08 + col * 0.46
        y0 = 0.57 - row * 0.065
        fc = C_LB if col == 0 else C_LG
        fb = FancyBboxPatch((x0, y0), 0.43, 0.055,
                            boxstyle='round,pad=0.008',
                            transform=fig.transFigure,
                            fc=fc, ec=C_BL, lw=0.8, clip_on=False)
        fig.patches.append(fb)
        fig.text(x0+0.01, y0+0.038, lbl, transform=fig.transFigure,
                 fontsize=7.5, color=C_GR, fontweight='bold')
        fig.text(x0+0.01, y0+0.012, val, transform=fig.transFigure,
                 fontsize=9, color=C_BL, fontweight='bold')

    # Contents
    fig.text(0.08, 0.30, 'NỘI DUNG BÁO CÁO / REPORT CONTENTS', fontsize=10,
             fontweight='bold', color=C_BL, transform=fig.transFigure)
    contents = [
        ('Trang 2', 'Thông số & Đặc trưng mặt cắt  /  Parameters & Section Properties'),
        ('Trang 3', 'Biểu đồ nội lực BMD + SFD  /  Bending Moment & Shear Force Diagrams'),
        ('Trang 4', 'Phân tích độ võng  /  Deflection Analysis'),
        ('Trang 5', 'Dao động Mô hình 1 — Giải tích  /  Vibration Model 1 — Analytical'),
        ('Trang 6', 'Dao động Mô hình 2 — Phương pháp Rayleigh  /  Vibration Model 2 — Rayleigh'),
        ('Trang 7', 'Dao động Mô hình 3 — Phần tử hữu hạn  /  Vibration Model 3 — FEM'),
        ('Trang 8', 'So sánh 3 mô hình dao động  /  Vibration Models Comparison'),
        ('Trang 9', 'Kiểm toán cốt thép TCVN 5574:2018  /  Steel Check'),
        ('Trang 10','Tóm tắt kết quả  /  Summary of Results'),
    ]
    for i, (pg, txt) in enumerate(contents):
        y_pos = 0.267 - i * 0.027
        clr = C_BL if i % 2 == 0 else C_GN
        fig.text(0.09, y_pos, f'▶ {pg}:', fontsize=8, color=clr,
                 fontweight='bold', transform=fig.transFigure)
        fig.text(0.17, y_pos, txt, fontsize=8.5, color=C_GR,
                 transform=fig.transFigure)

    fig.text(0.5, 0.022,
             f'Tao ngay / Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}  |  '
             f'Python {matplotlib.__version__} (matplotlib)',
             ha='center', fontsize=7.5, color='gray', transform=fig.transFigure)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 2: THONG SO & MAT CAT / PARAMETERS & SECTION
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'THÔNG SỐ ĐẦU VÀO & ĐẶC TRƯNG MẶT CẮT',
        'Input Parameters & Cross-Section Properties', 2)

    gs = GridSpec(2, 2, figure=fig,
                  left=0.07, right=0.96, top=0.92, bottom=0.06,
                  hspace=0.35, wspace=0.3)

    # ── Material table
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    ax1.set_title('Vật liệu — TCVN 5574:2018\nMaterial Properties', color=C_BL, pad=6)
    mat_data = [
        ['Thông số / Parameter', 'Ký hiệu', 'Giá trị / Value', 'Đơn vị'],
        ['CĐ nen thiết kế / Design compr.',  'Rb',    f'{Rb:.1f}',    'MPa'],
        ['CĐ kéo thiết kế / Design tens.',   'Rbt',   f'{Rbt:.1f}',   'MPa'],
        ['Môđun đàn hồi / Elastic mod.',     'Eb',    f'{Eb:.0f}',    'MPa'],
        ['Khối lượng riêng / Density',       'ρ',     f'{rho:.0f}',   'kg/m³'],
        ['Hệ số Poisson / Poisson ratio',    'ν',     f'{nu:.2f}',    '—'],
        ['Thép dọc / Long. steel CB400-V',   'Rs',    f'{Rs:.0f}',    'MPa'],
        ['Thép đai / Stirrup CB240-T',       'Rsw',   f'{Rsw:.0f}',   'MPa'],
        ['Môđun thép / Steel mod.',          'Es',    f'{Es:.0f}',    'MPa'],
        ['Tỉ số môđun / Modular ratio',      'αE',    f'{alpha_E:.1f}','—'],
    ]
    tbl1 = ax1.table(cellText=mat_data[1:], colLabels=mat_data[0],
                     cellLoc='center', loc='center')
    tbl1.auto_set_font_size(False)
    tbl1.set_fontsize(7.5)
    tbl1.scale(1, 1.35)
    for (r,c), cell in tbl1.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        elif r % 2 == 0:
            cell.set_facecolor(C_LB)
        cell.set_edgecolor('#B0BEC5')

    # ── Section properties table
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    ax2.set_title('Đặc trưng mặt cắt\nCross-Section Properties', color=C_BL, pad=6)
    sec_data = [
        ['Đặc trưng', 'Công thức', 'Giá trị', 'Đơn vị'],
        ['Diện tích / Area',        'A = b×h',       f'{A:.4f}',    'm²'],
        ['Moment quán tính / I',    'I = bh³/12',    f'{I:.4e}',    'm⁴'],
        ['Moment chống uốn / W',    'W = I/(h/2)',   f'{Wg:.4e}',   'm³'],
        ['Độ cứng uốn / EI',        'EI = Eb×I',     f'{EI:.4e}',   'N·m²'],
        ['Khối lượng dài / m',      'm = ρ×A',       f'{m:.2f}',    'kg/m'],
        ['Chiều cao làm việc / h0', 'h0 = h - as',   f'{h0:.3f}',   'm'],
        ['Moment tĩnh / S0',        'S0 = bh²/8',    f'{S0:.6f}',   'm³'],
    ]
    tbl2 = ax2.table(cellText=sec_data[1:], colLabels=sec_data[0],
                     cellLoc='center', loc='center')
    tbl2.auto_set_font_size(False)
    tbl2.set_fontsize(7.5)
    tbl2.scale(1, 1.35)
    for (r,c), cell in tbl2.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_GN); cell.set_text_props(color='white', fontweight='bold')
        elif r % 2 == 0:
            cell.set_facecolor(C_LG)
        cell.set_edgecolor('#B0BEC5')

    # ── Section drawing
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_xlim(-0.4, 1.2)
    ax3.set_ylim(-0.1, 1.1)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('Mặt cắt ngang / Cross Section  (đơn vị: cm)', color=C_BL, pad=4)

    bsc = b * 100; hsc = h * 100  # cm
    rect = Rectangle((0.2, 0.1), 0.6, 0.8, lw=2, ec=C_BL, fc='#CFD8DC', alpha=0.7,
                      transform=ax3.transAxes)
    ax3.add_patch(rect)

    # Hatch (concrete)
    for yi in np.linspace(0.1, 0.9, 8):
        ax3.plot([0.2, 0.8], [yi, yi], 'gray', lw=0.3, alpha=0.4, transform=ax3.transAxes)

    # Dimensions
    ax3.annotate('', xy=(0.18, 0.1), xytext=(0.18, 0.9),
                 arrowprops=dict(arrowstyle='<->', color='black', lw=1),
                 xycoords='axes fraction', textcoords='axes fraction')
    ax3.text(0.12, 0.50, f'h={hsc:.0f}cm', ha='center', va='center',
             rotation=90, fontsize=9, fontweight='bold', transform=ax3.transAxes)

    ax3.annotate('', xy=(0.2, 0.05), xytext=(0.8, 0.05),
                 arrowprops=dict(arrowstyle='<->', color='black', lw=1),
                 xycoords='axes fraction', textcoords='axes fraction')
    ax3.text(0.50, 0.00, f'b={bsc:.0f}cm', ha='center', va='bottom',
             fontsize=9, fontweight='bold', transform=ax3.transAxes)

    # Centroid
    ax3.plot(0.50, 0.50, 'r+', ms=12, mew=2, transform=ax3.transAxes)
    ax3.text(0.82, 0.50, 'G (centroid)', fontsize=8, color=C_RD,
             transform=ax3.transAxes)

    # Steel bars (schematic)
    for xi in [0.28, 0.40, 0.52, 0.64]:
        circ = plt.Circle((xi, 0.14), 0.025, fc=C_OR, ec='black', lw=0.8,
                          transform=ax3.transAxes)
        ax3.add_patch(circ)
    ax3.text(0.50, 0.07, f'Cốt thép: {n_bars}φ{d_bar_mm}',
             ha='center', fontsize=8, color=C_OR, fontweight='bold',
             transform=ax3.transAxes)

    # ── Formula block
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    ax4.set_title('Công thức cơ bản / Key Formulas', color=C_BL, pad=4)
    formulas = [
        r'$A = b \times h = 0.50 \times 0.30 = 0.150\ m^2$',
        r'$I = \frac{bh^3}{12} = \frac{0.50 \times 0.30^3}{12} = 1.125 \times 10^{-3}\ m^4$',
        r'$EI = E_b \times I = 32500 \times 1.125 \times 10^{-3}$',
        r'$\quad\quad = 36.56\ MN{\cdot}m^2$',
        r'$m = \rho \times A = 2500 \times 0.150 = 375\ kg/m$',
        r'$h_0 = h - a_s = 0.30 - 0.035 = 0.265\ m$',
        r'$W = \frac{I}{h/2} = \frac{1.125\times10^{-3}}{0.15} = 7.5\times10^{-3}\ m^3$',
    ]
    for i, f in enumerate(formulas):
        bg = C_LB if i % 2 == 0 else 'white'
        ax4.text(0.02, 0.93 - i*0.125, f, fontsize=9, va='top',
                 transform=ax4.transAxes,
                 bbox=dict(boxstyle='round,pad=0.3', fc=bg, ec='none'))

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 3: BIEU DO NOI LUC / INTERNAL FORCES
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'BIỂU ĐỒ NỘI LỰC — DẦM GIẢN ĐƠN',
        'Internal Force Diagrams — Simply Supported Beam', 3)

    gs = GridSpec(4, 2, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.55, wspace=0.35)

    # ── Beam schematic (top)
    ax_s = fig.add_subplot(gs[0, :])
    draw_beam_scheme(ax_s)
    ax_s.set_title('Sơ đồ dầm / Beam Diagram', fontsize=10, color=C_BL, pad=4)

    # ── BMD
    ax_M = fig.add_subplot(gs[1, :])
    ax_M.fill_between(x, 0, M, alpha=0.35, color=C_BL, label='M(x)')
    ax_M.plot(x, M, color=C_BL, lw=2)
    ax_M.axhline(0, color='black', lw=0.8)
    ax_M.plot(L/2, M_max, 'ro', ms=8, zorder=5)
    ax_M.annotate(f'Mmax = {M_max:.3f} kN·m\n@ x = {L/2:.2f} m',
                  xy=(L/2, M_max), xytext=(L*0.6, M_max*0.75),
                  fontsize=9, color=C_RD, fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C_RD, lw=1.2))
    ax_M.set_xlabel('x (m)', fontsize=9)
    ax_M.set_ylabel('M (kN·m)', fontsize=9)
    ax_M.set_title('Biểu đồ Moment Uốn / Bending Moment Diagram (BMD)', color=C_BL)
    ax_M.set_xlim(0, L)
    ax_M.invert_yaxis()   # convention: sagging positive, plotted downward

    # ── SFD
    ax_V = fig.add_subplot(gs[2, :])
    ax_V.fill_between(x, 0, V, where=(V >= 0), alpha=0.35, color=C_GN, label='V≥0')
    ax_V.fill_between(x, 0, V, where=(V <  0), alpha=0.35, color=C_RD, label='V<0')
    ax_V.plot(x, V, color=C_GN, lw=2)
    ax_V.axhline(0, color='black', lw=0.8)
    ax_V.plot(0, V_max,  'g^', ms=8, zorder=5)
    ax_V.plot(L, -V_max, 'rv', ms=8, zorder=5)
    ax_V.annotate(f'+{V_max:.2f} kN', xy=(0.1, V_max),
                  fontsize=9, color=C_GN, fontweight='bold')
    ax_V.annotate(f'-{V_max:.2f} kN', xy=(L-0.8, -V_max-0.8),
                  fontsize=9, color=C_RD, fontweight='bold')
    ax_V.set_xlabel('x (m)', fontsize=9)
    ax_V.set_ylabel('V (kN)', fontsize=9)
    ax_V.set_title('Biểu đồ Lực Cắt / Shear Force Diagram (SFD)', color=C_BL)
    ax_V.set_xlim(0, L)

    # ── Formula + results table
    ax_t = fig.add_subplot(gs[3, :])
    ax_t.axis('off')
    rows_t = [
        ['Đại lượng / Quantity', 'Công thức / Formula', 'Giá trị / Value', 'Đơn vị'],
        ['Phản lực gối / Reaction',  r'R = qL/2',
         f'RA = RB = {RA:.3f}', 'kN'],
        ['M lớn nhất / Max moment',  r'Mmax = qL²/8',
         f'{M_max:.4f}', 'kN·m'],
        ['V lớn nhất / Max shear',   r'Vmax = qL/2',
         f'{V_max:.4f}', 'kN'],
        ['Ứng suất trên / Top stress',r'σtop = M·(h/2)/I',
         f'{sigma_top:.3f}', 'MPa (nen/compr.)'],
        ['Ứng suất dưới / Bot stress',r'σbot = M·(h/2)/I',
         f'{sigma_bot:.3f}', 'MPa (keo/tension)'],
        ['Ứng suất cắt / Shear stress',r'τmax = V·S₀/(I·b)',
         f'{tau_max:.4f}', 'MPa'],
    ]
    tbl = ax_t.table(cellText=rows_t[1:], colLabels=rows_t[0],
                     cellLoc='center', loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.3)
    for (r,c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        elif r % 2 == 0:
            cell.set_facecolor(C_LB)
        cell.set_edgecolor('#B0BEC5')
    ax_t.set_title('Bảng tóm tắt nội lực / Internal Force Summary', color=C_BL, pad=4)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 4: DO VONG / DEFLECTION
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'PHÂN TÍCH ĐỘ VÕNG', 'Deflection Analysis', 4)

    gs = GridSpec(3, 2, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.50, wspace=0.3)

    # ── Deflection curve
    ax_d = fig.add_subplot(gs[0, :])
    ax_d.fill_between(x, 0, -y*1000, alpha=0.3, color=C_BL)
    ax_d.plot(x, -y*1000, color=C_BL, lw=2.5, label='δ(x) [mm]')
    ax_d.axhline(-y_allow_mm, color=C_OR, lw=1.5, ls='--',
                 label=f'Giới hạn cho phép L/400 = {y_allow_mm:.2f} mm')
    ax_d.plot(L/2, -y_mm, 'ro', ms=9, zorder=5)
    ax_d.annotate(f'δmax = {y_mm:.3f} mm\n@ x = {L/2:.2f} m',
                  xy=(L/2, -y_mm), xytext=(L*0.62, -y_mm*0.55),
                  fontsize=9.5, color=C_RD, fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C_RD, lw=1.2))
    ax_d.set_xlabel('x (m)', fontsize=9)
    ax_d.set_ylabel('δ (mm)', fontsize=9)
    ax_d.set_title('Đường đàn hồi / Elastic Curve', color=C_BL)
    ax_d.legend(fontsize=8, loc='lower center')
    ax_d.set_xlim(0, L)
    ax_d.invert_yaxis()

    # ── Formula block
    ax_f = fig.add_subplot(gs[1, 0])
    ax_f.axis('off')
    ax_f.set_title('Công thức độ võng / Deflection Formulas', color=C_BL, pad=4)
    lines_f = [
        r'$\delta(x) = \frac{qx(L^3 - 2Lx^2 + x^3)}{24EI}$',
        '',
        r'$\delta_{max} = \frac{5qL^4}{384EI}$ (tại x = L/2)',
        '',
        r'$\delta_{max} = \frac{5 \times 5000 \times 7^4}{384 \times 36{,}562{,}500}$',
        '',
        r'$\delta_{max} = \frac{60{,}025{,}000}{14{,}040{,}000{,}000}$',
        '',
        r'$\delta_{max} = 4.276 \times 10^{-3}\ m = \mathbf{4.28\ mm}$',
        '',
        r'$\theta_A = \frac{qL^3}{24EI} = $' + f'{theta_A_deg:.4f}°',
    ]
    for i, line in enumerate(lines_f):
        ax_f.text(0.05, 0.98 - i*0.088, line,
                  transform=ax_f.transAxes, fontsize=9, va='top',
                  bbox=dict(boxstyle='round,pad=0.2',
                            fc=C_LB if i % 4 == 0 else 'white', ec='none')
                        if line else None)

    # ── Check table
    ax_c = fig.add_subplot(gs[1, 1])
    ax_c.axis('off')
    ax_c.set_title('Kiểm tra độ võng / Deflection Check', color=C_BL, pad=4)
    chk = [
        ['Kiểm tra', 'Yêu cầu', 'Thực tế', 'Kết quả'],
        ['δmax / L', f'≤ 1/400 = {1/400:.5f}',
         f'{y_max/L:.5f}', '✓ ĐẠT' if ratio_defl < 1 else '✗ KHÔNG ĐẠT'],
        ['δmax (mm)', f'≤ {y_allow_mm:.2f} mm',
         f'{y_mm:.3f} mm', '✓ ĐẠT' if ratio_defl < 1 else '✗ KHÔNG ĐẠT'],
        ['Tỉ lệ / Ratio', '< 1.00',
         f'{ratio_defl:.3f}', '✓' if ratio_defl < 1 else '✗'],
    ]
    tbl_c = ax_c.table(cellText=chk[1:], colLabels=chk[0],
                       cellLoc='center', loc='center')
    tbl_c.auto_set_font_size(False); tbl_c.set_fontsize(8.5); tbl_c.scale(1, 1.6)
    for (r,c_), cell in tbl_c.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        elif c_ == 3 and r > 0:
            fc_ = C_LG if '✓' in cell.get_text().get_text() else C_LR
            cell.set_facecolor(fc_)
        elif r % 2 == 0:
            cell.set_facecolor(C_LB)
        cell.set_edgecolor('#B0BEC5')

    # ── Slope diagram
    ax_sl = fig.add_subplot(gs[2, :])
    theta = np.gradient(-y*1000, x)
    ax_sl.plot(x, theta, color=C_GN, lw=2, label='dδ/dx = Góc xoay (mm/m)')
    ax_sl.axhline(0, color='black', lw=0.7)
    ax_sl.fill_between(x, 0, theta, alpha=0.2, color=C_GN)
    ax_sl.set_xlabel('x (m)', fontsize=9)
    ax_sl.set_ylabel('Góc xoay / Slope (mm/m)', fontsize=9)
    ax_sl.set_title('Biểu đồ góc xoay / Slope Diagram θ(x)', color=C_BL)
    ax_sl.set_xlim(0, L)
    ax_sl.legend(fontsize=8)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 5: DAO DONG MO HINH 1 — GIAI TICH
    # VIBRATION MODEL 1 — ANALYTICAL
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'DAO ĐỘNG — MÔ HÌNH 1: GIẢI TÍCH (Euler-Bernoulli)',
        'Vibration — Model 1: Analytical Solution', 5)

    gs = GridSpec(3, 3, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.55, wspace=0.3)

    # Theory box
    ax_th = fig.add_subplot(gs[0, :])
    ax_th.axis('off')
    ax_th.set_facecolor(C_LB)
    theory_lines = [
        r'$\mathbf{LÝ\ THUYẾT\ /\ THEORY:}$  Phương trình vi phân / Differential equation:',
        r'$EI\frac{\partial^4 w}{\partial x^4} + m\frac{\partial^2 w}{\partial t^2} = 0$',
        r'Nghiệm / Solution:  $w_n(x,t) = \sin\!\left(\frac{n\pi x}{L}\right)\cdot e^{i\omega_n t}$',
        r'Tần số góc / Angular frequency:  '
        r'$\omega_n = \left(\frac{n\pi}{L}\right)^2\!\sqrt{\frac{EI}{m}}$',
        r'$\omega_1 = \left(\frac{\pi}{7}\right)^2\sqrt{\frac{36{,}563{,}000}{375}}'
        r'= \mathbf{' + f'{modes1[0]["omega"]:.2f}' + r'\ rad/s}$',
    ]
    for i, line in enumerate(theory_lines):
        ax_th.text(0.02, 0.97 - i*0.195, line, transform=ax_th.transAxes,
                   fontsize=9.5, va='top',
                   color=C_BL if i == 0 else 'black')

    # Mode shape plots
    titles = ['Mode 1 (n=1)', 'Mode 2 (n=2)', 'Mode 3 (n=3)']
    for nm, mode in enumerate(modes1):
        ax_m = fig.add_subplot(gs[1, nm])
        phi_plot = mode['phi']
        ax_m.plot(x_phi, phi_plot, color=C_BL, lw=2.5)
        ax_m.fill_between(x_phi, 0, phi_plot, alpha=0.25, color=C_BL)
        ax_m.axhline(0, color='black', lw=0.8)
        ax_m.set_xlim(0, L)
        ax_m.set_ylim(-1.3, 1.3)
        ax_m.set_xlabel('x (m)', fontsize=8)
        ax_m.set_ylabel('φ(x)', fontsize=8)
        ax_m.set_title(f'{titles[nm]}\nf{mode["n"]} = {mode["f"]:.3f} Hz',
                       color=C_BL, fontsize=9)
        n_nodes = nm + 2
        nodes = np.linspace(0, L, n_nodes)
        ax_m.plot(nodes, np.zeros(n_nodes), 'ro', ms=6, zorder=5,
                  label='Điểm nút / Nodes')
        ax_m.legend(fontsize=7)

    # Results table
    ax_res = fig.add_subplot(gs[2, :])
    ax_res.axis('off')
    tbl_data = [
        ['Mode n', 'ωn (rad/s)', 'Công thức ωn', 'fn (Hz)', 'Tn (s)',
         'Dạng dao động / Mode Shape'],
    ]
    shapes = ['sin(πx/L) — 1 bụng / 1 antinode',
              'sin(2πx/L) — 2 bụng / 2 antinodes',
              'sin(3πx/L) — 3 bụng / 3 antinodes']
    for i, mode in enumerate(modes1):
        tbl_data.append([
            f'n = {mode["n"]}',
            f'{mode["omega"]:.4f}',
            f'({mode["n"]}π/L)² √(EI/m)',
            f'{mode["f"]:.4f}',
            f'{mode["T"]:.4f}',
            shapes[i],
        ])
    tbl_r = ax_res.table(cellText=tbl_data[1:], colLabels=tbl_data[0],
                         cellLoc='center', loc='center')
    tbl_r.auto_set_font_size(False); tbl_r.set_fontsize(8.5); tbl_r.scale(1, 1.8)
    for (r,c), cell in tbl_r.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        elif r % 2 == 0:
            cell.set_facecolor(C_LB)
        cell.set_edgecolor('#B0BEC5')
    ax_res.set_title('Kết quả dao động — Giải tích / Analytical Vibration Results', color=C_BL, pad=4)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 6: DAO DONG MO HINH 2 — RAYLEIGH
    # VIBRATION MODEL 2 — RAYLEIGH METHOD
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'DAO ĐỘNG — MÔ HÌNH 2: PHƯƠNG PHÁP RAYLEIGH',
        'Vibration — Model 2: Rayleigh Energy Method', 6)

    gs = GridSpec(3, 2, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.50, wspace=0.30)

    # Theory
    ax_th2 = fig.add_subplot(gs[0, :])
    ax_th2.axis('off')
    th_lines = [
        r'$\mathbf{NGUYÊN\ LÝ\ RAYLEIGH\ /\ RAYLEIGH\ QUOTIENT:}$',
        r'Chọn hàm dạng / Shape function: $\varphi(x) = x(L^3 - 2Lx^2 + x^3)$  '
        r'(dạng vồng tĩnh / static deflection shape)',
        r"$\omega^2 = \frac{EI\int_0^L [\varphi''(x)]^2\,dx}{m\int_0^L [\varphi(x)]^2\,dx}$",
        r"$\varphi''(x) = 12x(x - L)$   (vi ph\^an b\^ac 2 / 2nd derivative)",
        r'Tích phân số / Numerical integration:  $\omega_1^{Rayleigh} = '
        f'{omega_r:.4f}$ rad/s  →  $f_1 = {f_r:.4f}$ Hz',
    ]
    for i, line in enumerate(th_lines):
        ax_th2.text(0.02, 0.97 - i*0.19, line, transform=ax_th2.transAxes,
                    fontsize=9, va='top',
                    color=C_GN if i == 0 else 'black')

    # Shape function plot
    ax_p1 = fig.add_subplot(gs[1, 0])
    ax_p1.plot(x_r, modes2['phi'], color=C_GN, lw=2.5)
    ax_p1.fill_between(x_r, 0, modes2['phi'], alpha=0.25, color=C_GN)
    ax_p1.set_xlabel('x (m)', fontsize=9); ax_p1.set_ylabel('φ(x) / max', fontsize=9)
    ax_p1.set_title('Hàm dạng / Shape Function φ(x)\n(chuẩn hóa / normalized)', color=C_GN)
    ax_p1.set_xlim(0, L)

    # Second derivative
    ax_p2 = fig.add_subplot(gs[1, 1])
    phi_pp_plot = np.gradient(np.gradient(modes2['phi'], x_r[1]-x_r[0]), x_r[1]-x_r[0])
    ax_p2.plot(x_r, phi_pp_plot, color=C_OR, lw=2.5)
    ax_p2.fill_between(x_r, 0, phi_pp_plot, alpha=0.2, color=C_OR)
    ax_p2.axhline(0, color='black', lw=0.7)
    ax_p2.set_xlabel('x (m)', fontsize=9); ax_p2.set_ylabel("φ''(x)", fontsize=9)
    ax_p2.set_title("Đạo hàm bậc 2 / 2nd Derivative φ''(x)\n(tỉ lệ với moment / prop. to moment)",
                    color=C_OR)
    ax_p2.set_xlim(0, L)

    # Results + comparison
    ax_cmp = fig.add_subplot(gs[2, :])
    ax_cmp.axis('off')
    diff_pct = abs(omega_r - modes1[0]['omega']) / modes1[0]['omega'] * 100
    rows_c = [
        ['Phương pháp / Method', 'ω₁ (rad/s)', 'f₁ (Hz)', 'T₁ (s)', 'Sai lệch so GT / Error vs Analytical'],
        ['Giải tích / Analytical', f'{modes1[0]["omega"]:.4f}', f'{modes1[0]["f"]:.4f}', f'{modes1[0]["T"]:.4f}', '— (Chuẩn)'],
        ['Rayleigh',              f'{omega_r:.4f}',            f'{f_r:.4f}',            f'{T_r:.4f}',            f'{diff_pct:.3f} %'],
    ]
    tbl_cmp = ax_cmp.table(cellText=rows_c[1:], colLabels=rows_c[0],
                            cellLoc='center', loc='center')
    tbl_cmp.auto_set_font_size(False); tbl_cmp.set_fontsize(9); tbl_cmp.scale(1, 2.0)
    for (r,c), cell in tbl_cmp.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_GN); cell.set_text_props(color='white', fontweight='bold')
        elif r == 1:
            cell.set_facecolor(C_LB)
        elif r == 2:
            cell.set_facecolor(C_LG)
        cell.set_edgecolor('#B0BEC5')
    ax_cmp.set_title('So sánh kết quả / Comparison of Results', color=C_BL, pad=4)

    ax_cmp.text(0.5, 0.05,
                f'Nhận xét / Remark: Phương pháp Rayleigh cho kết quả xấp xỉ rất tốt '
                f'(sai lệch {diff_pct:.3f}%). / '
                f'Rayleigh method gives excellent approximation (error {diff_pct:.3f}%).',
                ha='center', fontsize=9, color=C_GN, fontstyle='italic',
                transform=ax_cmp.transAxes,
                bbox=dict(boxstyle='round', fc=C_LG, ec=C_GN, lw=0.8))

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 7: DAO DONG MO HINH 3 — PHAN TU HUU HAN (FEM)
    # VIBRATION MODEL 3 — FEM
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'DAO ĐỘNG — MÔ HÌNH 3: PHẦN TỬ HỮU HẠN (FEM)',
        'Vibration — Model 3: Finite Element Method', 7)

    gs = GridSpec(3, 3, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.55, wspace=0.3)

    # Theory
    ax_th3 = fig.add_subplot(gs[0, :])
    ax_th3.axis('off')
    fem_lines = [
        r'$\mathbf{PHẦN\ TỬ\ HỮU\ HẠN\ /\ FINITE\ ELEMENT:}$  '
        f'Chia thành {nE} phần tử dầm / Divided into {nE} beam elements',
        r'Ma trận độ cứng phần tử / Element stiffness matrix $[k_e]_{4\times4}$  (Hermitian)',
        r'$[k_e] = \frac{EI}{l^3} \cdot \mathbf{K_{4\times4}}$:  '
        r'$\{12,\ 6l,\ -12,\ 6l\ |\ 6l,\ 4l^2,\ -6l,\ 2l^2\ |\ \ldots\}$ (đối xứng / symmetric)',
        r'Bài toán trị riêng / Eigenvalue problem:  '
        r'$([K] - \omega^2[M])\{\phi\} = \{0\}$',
        f'Số bậc tự do / Total DOF: {nDOF}   →   Sau BC / After BC: {len(free)}',
    ]
    for i, line in enumerate(fem_lines):
        ax_th3.text(0.02, 0.98 - i*0.19, line, transform=ax_th3.transAxes,
                    fontsize=8.5, va='top',
                    color=C_OR if i == 0 else 'black')

    # FEM mesh
    ax_mesh = fig.add_subplot(gs[0, 2])  # reuse last column for mesh schematic
    ax_mesh.axis('off')  # handled above; skip to avoid double use

    # Mode shapes from FEM
    clrs = [C_BL, C_GN, C_OR]
    for nm, mode in enumerate(modes3):
        ax_m = fig.add_subplot(gs[1, nm])
        phi_plot = mode['phi']
        ax_m.plot(x_node, phi_plot, 'o-', color=clrs[nm], lw=2, ms=4)
        ax_m.fill_between(x_node, 0, phi_plot, alpha=0.2, color=clrs[nm])
        ax_m.axhline(0, color='black', lw=0.8)
        ax_m.set_xlim(0, L); ax_m.set_ylim(-1.3, 1.3)
        ax_m.set_xlabel('x (m)', fontsize=8); ax_m.set_ylabel('φ(x)', fontsize=8)
        ax_m.set_title(f'FEM Mode {nm+1}\nf = {mode["f"]:.4f} Hz',
                       color=clrs[nm], fontsize=9)

    # Results table
    ax_r3 = fig.add_subplot(gs[2, :])
    ax_r3.axis('off')
    rows_f = [['Mode n', 'ωn FEM (rad/s)', 'ωn GT (rad/s)', 'fn FEM (Hz)',
               'fn GT (Hz)', 'Tn (s)', 'Sai lệch / Error']]
    for i in range(3):
        m3 = modes3[i]; m1 = modes1[i]
        err = abs(m3['omega'] - m1['omega']) / m1['omega'] * 100
        rows_f.append([
            f'Mode {i+1}',
            f'{m3["omega"]:.4f}',
            f'{m1["omega"]:.4f}',
            f'{m3["f"]:.4f}',
            f'{m1["f"]:.4f}',
            f'{m3["T"]:.4f}',
            f'{err:.3f} %',
        ])
    tbl_f = ax_r3.table(cellText=rows_f[1:], colLabels=rows_f[0],
                        cellLoc='center', loc='center')
    tbl_f.auto_set_font_size(False); tbl_f.set_fontsize(8.5); tbl_f.scale(1, 1.7)
    for (r,c), cell in tbl_f.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_OR); cell.set_text_props(color='white', fontweight='bold')
        elif r % 2 == 0:
            cell.set_facecolor('#FFF3E0')
        cell.set_edgecolor('#B0BEC5')
    ax_r3.set_title(f'Kết quả FEM ({nE} phần tử / elements) / FEM Results', color=C_BL, pad=4)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 8: SO SANH 3 MO HINH DAO DONG
    # VIBRATION MODELS COMPARISON
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'SO SÁNH 3 MÔ HÌNH DAO ĐỘNG',
        'Comparison of 3 Vibration Models', 8)

    gs = GridSpec(3, 2, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.50, wspace=0.3)

    methods = ['Giải tích\n(Analytical)', 'Rayleigh', 'FEM\n(20 elements)']
    mode_ns = [1, 2, 3]
    omega_data = [
        [m['omega'] for m in modes1],
        [omega_r,    None,         None],
        [m['omega']  for m in modes3],
    ]
    f_data = [
        [m['f']  for m in modes1],
        [f_r,    None,         None],
        [m['f']  for m in modes3],
    ]

    # Bar chart - frequency comparison
    ax_bar = fig.add_subplot(gs[0, :])
    x_bar = np.arange(3)
    w_bar = 0.25
    colors_b = [C_BL, C_GN, C_OR]
    for im, (meth, f_list, clr) in enumerate(zip(methods, f_data, colors_b)):
        vals = [v for v in f_list if v is not None]
        xpos = x_bar[:len(vals)] + (im - 1) * w_bar
        bars = ax_bar.bar(xpos, vals, w_bar, label=meth, color=clr, alpha=0.8, ec='white')
        for bar, v in zip(bars, vals):
            ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{v:.2f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    ax_bar.set_xticks(x_bar)
    ax_bar.set_xticklabels([f'Mode {n}' for n in mode_ns])
    ax_bar.set_ylabel('Tần số / Frequency fn (Hz)', fontsize=9)
    ax_bar.set_title('So sánh tần số dao động riêng / Natural Frequency Comparison', color=C_BL)
    ax_bar.legend(fontsize=8)

    # Mode shape overlay for Mode 1
    ax_ov = fig.add_subplot(gs[1, 0])
    ax_ov.plot(x_phi, modes1[0]['phi'], color=C_BL, lw=2.5,
               label=f'Giải tích: {modes1[0]["f"]:.3f} Hz', ls='-')
    ax_ov.plot(modes2['x'], modes2['phi'], color=C_GN, lw=2, ls='--',
               label=f'Rayleigh: {f_r:.3f} Hz')
    ax_ov.plot(x_node, modes3[0]['phi'], 'o-', color=C_OR, lw=1.5, ms=4,
               label=f'FEM: {modes3[0]["f"]:.3f} Hz')
    ax_ov.legend(fontsize=7.5, loc='lower center')
    ax_ov.set_xlim(0, L); ax_ov.set_ylim(-1.3, 1.3)
    ax_ov.set_xlabel('x (m)', fontsize=9); ax_ov.set_ylabel('φ(x)', fontsize=9)
    ax_ov.axhline(0, color='black', lw=0.7)
    ax_ov.set_title('Dạng dao động Mode 1 / Mode 1 Shape\n(cả 3 mô hình / all 3 models)',
                    color=C_BL, fontsize=9)

    # Error bar
    ax_err = fig.add_subplot(gs[1, 1])
    err_ray = [abs(omega_r - modes1[0]['omega']) / modes1[0]['omega'] * 100]
    err_fem = [abs(modes3[i]['omega'] - modes1[i]['omega']) / modes1[i]['omega'] * 100
               for i in range(3)]
    ax_err.bar(['Rayleigh\n(Mode 1)'], err_ray, color=C_GN, alpha=0.8, width=0.4)
    ax_err.bar([f'FEM\nMode {i+1}' for i in range(3)], err_fem, color=C_OR, alpha=0.8, width=0.4)
    ax_err.axhline(1.0, color=C_RD, ls='--', lw=1.5, label='1% ngưỡng')
    ax_err.set_ylabel('Sai lệch / Error (%)', fontsize=9)
    ax_err.set_title('Sai lệch so với giải tích\nError vs Analytical', color=C_BL, fontsize=9)
    ax_err.legend(fontsize=8)

    # Full comparison table
    ax_tbl = fig.add_subplot(gs[2, :])
    ax_tbl.axis('off')
    full_rows = [
        ['Mô hình\nModel', 'Mode', 'ωn (rad/s)', 'fn (Hz)', 'Tn (s)',
         'Sai lệch ω\nError in ω', 'Nhận xét\nRemark'],
    ]
    refs = modes1
    for nm_idx in range(3):
        # Analytical
        full_rows.append([
            'Giải tích\nAnalytical' if nm_idx == 0 else '',
            f'{nm_idx+1}',
            f'{modes1[nm_idx]["omega"]:.4f}',
            f'{modes1[nm_idx]["f"]:.4f}',
            f'{modes1[nm_idx]["T"]:.5f}',
            '0.000 %',
            'Chuẩn / Reference' if nm_idx == 0 else '',
        ])
    # Rayleigh only mode 1
    full_rows.append([
        'Rayleigh', '1',
        f'{omega_r:.4f}', f'{f_r:.4f}', f'{T_r:.5f}',
        f'{abs(omega_r-modes1[0]["omega"])/modes1[0]["omega"]*100:.3f} %',
        'Tốt / Good'
    ])
    for nm_idx in range(3):
        m3 = modes3[nm_idx]; m1 = modes1[nm_idx]
        err = abs(m3['omega']-m1['omega'])/m1['omega']*100
        full_rows.append([
            'FEM' if nm_idx == 0 else '', f'{nm_idx+1}',
            f'{m3["omega"]:.4f}', f'{m3["f"]:.4f}', f'{m3["T"]:.5f}',
            f'{err:.3f} %',
            'Rất tốt / Excellent' if err < 0.5 else 'Tốt / Good'
        ])
    tbl_full = ax_tbl.table(cellText=full_rows[1:], colLabels=full_rows[0],
                            cellLoc='center', loc='center')
    tbl_full.auto_set_font_size(False); tbl_full.set_fontsize(7.5); tbl_full.scale(1, 1.25)
    for (r,c), cell in tbl_full.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        cell.set_edgecolor('#B0BEC5')
    ax_tbl.set_title('Bảng so sánh đầy đủ / Full Comparison Table', color=C_BL, pad=4)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 9: KIEM TOAN COT THEP / STEEL CHECK
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')
    hdr(fig, 'KIỂM TOÁN CỐT THÉP — TCVN 5574:2018',
        'Steel Reinforcement Check — TCVN 5574:2018', 9)

    gs = GridSpec(3, 2, figure=fig,
                  left=0.10, right=0.96, top=0.91, bottom=0.06,
                  hspace=0.50, wspace=0.30)

    # ── Bending check formulas
    ax_bf = fig.add_subplot(gs[0, 0])
    ax_bf.axis('off')
    ax_bf.set_title('Tính cốt thép chịu uốn / Bending Steel Design\n(TCVN 5574:2018 Đ.8.1)',
                    color=C_BL, pad=4)
    bend_lines = [
        r'$M_{sd} = M_{max} = $' + f'{M_max:.3f} kN·m',
        r'$h_0 = h - a_s = $' + f'{h0*100:.1f} cm',
        r'$\alpha_m = \frac{M_{sd}}{R_b \cdot b \cdot h_0^2} = $'
        + f'{alpha_m:.5f}',
        r'$\xi = 1 - \sqrt{1-2\alpha_m} = $' + f'{xi_calc:.5f}',
        r'$\eta = 1 - \xi/2 = $' + f'{eta_s:.5f}',
        r'$z = \eta \cdot h_0 = $' + f'{z_arm*100:.3f} cm',
        r'$A_s^{req} = \frac{M_{sd}}{R_s \cdot z} = $' + f'{As_req_cm2:.3f} cm²',
        f'Chọn / Select: {n_bars}φ{d_bar_mm}',
        r'$A_s^{prov} = $' + f'{As_prov_cm2:.2f} cm²  ' + ('✓' if As_prov_cm2 >= As_req_cm2 else '✗'),
    ]
    for i, line in enumerate(bend_lines):
        bg = C_LB if i % 2 == 0 else 'white'
        if 'prov' in line or 'Select' in line:
            bg = C_LG
        ax_bf.text(0.03, 0.97 - i*0.104, line, transform=ax_bf.transAxes,
                   fontsize=8.8, va='top',
                   bbox=dict(boxstyle='round,pad=0.25', fc=bg, ec='none'))

    # ── Shear check formulas
    ax_sf = fig.add_subplot(gs[0, 1])
    ax_sf.axis('off')
    ax_sf.set_title('Kiểm tra lực cắt / Shear Check\n(TCVN 5574:2018 Đ.8.3)', color=C_BL, pad=4)
    shear_lines = [
        r'$V_{sd} = V_{max} = $' + f'{V_max:.3f} kN',
        r'$Q_{b0} = 0.5 R_{bt} b h_0 = $' + f'{Qb0/1e3:.3f} kN',
        f'Cần cốt đai? / Need stirrups? {"CÓ / YES" if need_st else "KHÔNG / NO"}',
        f'Chọn cốt đai / Stirrup: 2φ{d_stir_mm}@{s_prov_mm}mm',
        r'$A_{sw} = $' + f'{Asw*1e6:.2f} mm²  (2 nhánh / legs)',
        r'$s_{prov} = $' + f'{s_prov_mm} mm',
        r'$q_{sw} = A_{sw}R_{sw}/s = $' + f'{qsw_prov/1e3:.2f} kN/m',
        r'$Q_{total} = Q_{b0} + q_{sw} \cdot z = $' + f'{Q_total/1e3:.3f} kN',
        r'$Q_{total} \geq V_{sd}$: ' + ('✓ ĐẠT' if ok_V else '✗ KHÔNG ĐẠT'),
    ]
    for i, line in enumerate(shear_lines):
        bg = '#FFF3E0' if i % 2 == 0 else 'white'
        if 'total' in line.lower() or 'ĐẠT' in line:
            bg = C_LG if ok_V else C_LR
        ax_sf.text(0.03, 0.97 - i*0.104, line, transform=ax_sf.transAxes,
                   fontsize=8.8, va='top',
                   bbox=dict(boxstyle='round,pad=0.25', fc=bg, ec='none'))

    # ── Cross-section drawing with steel
    ax_cs = fig.add_subplot(gs[1, 0])
    ax_cs.set_xlim(-0.1, 1.1); ax_cs.set_ylim(-0.1, 1.1)
    ax_cs.set_aspect('equal'); ax_cs.axis('off')
    ax_cs.set_title(f'Mặt cắt bố trí thép / Reinforced Section\n'
                    f'{n_bars}φ{d_bar_mm} + đai 2φ{d_stir_mm}@{s_prov_mm}mm', color=C_BL, pad=4)

    # Concrete section
    sec_rect = Rectangle((0.1, 0.1), 0.8, 0.8, lw=2, ec=C_BL, fc='#CFD8DC', alpha=0.6)
    ax_cs.add_patch(sec_rect)

    # Cover lines
    cov_frac = a_s / h * 0.8
    cover_rect = Rectangle((0.1+0.05, 0.1+0.05), 0.8-0.10, 0.8-0.10,
                            lw=1, ec='gray', fc='none', ls='--', alpha=0.5)
    ax_cs.add_patch(cover_rect)

    # Tension bars (bottom)
    bar_y = 0.1 + cov_frac
    bar_r = 0.04
    x_positions = np.linspace(0.1 + 0.1, 0.9 - 0.1, n_bars)
    for xb in x_positions:
        circ = plt.Circle((xb, bar_y), bar_r, fc=C_OR, ec='black', lw=1.5, zorder=5)
        ax_cs.add_patch(circ)
    ax_cs.text(0.5, bar_y - 0.09, f'{n_bars}φ{d_bar_mm}  As={As_prov_cm2:.2f}cm²',
               ha='center', fontsize=9, color=C_OR, fontweight='bold')

    # Stirrups (schematic)
    for side_x in [0.1+0.04, 0.9-0.04]:
        ax_cs.plot([side_x, side_x], [0.16, 0.84], color='purple', lw=2)
    ax_cs.plot([0.14, 0.86], [0.84, 0.84], color='purple', lw=2)
    ax_cs.plot([0.14, 0.86], [0.16, 0.16], color='purple', lw=2)
    ax_cs.text(0.5, 0.92, f'Đai 2φ{d_stir_mm}@{s_prov_mm}mm', ha='center',
               fontsize=8.5, color='purple', fontweight='bold')

    # Dimension
    ax_cs.annotate('', xy=(0.02, 0.10), xytext=(0.02, 0.90),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1))
    ax_cs.text(-0.04, 0.50, f'h=30cm', va='center', ha='center', rotation=90, fontsize=8)
    ax_cs.annotate('', xy=(0.10, 0.02), xytext=(0.90, 0.02),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1))
    ax_cs.text(0.50, -0.06, f'b=50cm', va='center', ha='center', fontsize=8)

    # ── Summary check table
    ax_st = fig.add_subplot(gs[1, 1])
    ax_st.axis('off')
    ax_st.set_title('Bảng kiểm tra / Check Summary', color=C_BL, pad=4)
    sts_rows = [
        ['Mục / Item', 'Yêu cầu / Required', 'Thực tế / Actual', 'Kết quả'],
        ['αm < αR(0.408)', '< 0.408', f'{alpha_m:.5f}', '✓' if alpha_m < 0.408 else '✗'],
        ['ξ < ξR (0.531)',  '< 0.531', f'{xi_act:.5f}',  '✓' if ok_xi else '✗'],
        ['As ≥ As,req', f'≥ {As_req_cm2:.3f} cm²', f'{As_prov_cm2:.2f} cm²', '✓' if ok_M else '✗'],
        ['MRd ≥ Msd', f'≥ {M_max:.3f} kN·m', f'{M_Rd:.3f} kN·m', '✓' if ok_M else '✗'],
        ['Qtotal ≥ Vsd', f'≥ {V_max:.3f} kN', f'{Q_total/1e3:.3f} kN', '✓' if ok_V else '✗'],
        ['ρs ≥ ρmin', f'≥ {rho_min*100:.2f}%', f'{rho_s*100:.3f}%', '✓' if ok_rho else '✗'],
    ]
    tbl_st = ax_st.table(cellText=sts_rows[1:], colLabels=sts_rows[0],
                         cellLoc='center', loc='center')
    tbl_st.auto_set_font_size(False); tbl_st.set_fontsize(8.5); tbl_st.scale(1, 1.55)
    for (r,c), cell in tbl_st.get_celld().items():
        if r == 0:
            cell.set_facecolor(C_BL); cell.set_text_props(color='white', fontweight='bold')
        elif c == 3 and r > 0:
            txt = cell.get_text().get_text()
            cell.set_facecolor(C_LG if '✓' in txt else C_LR)
        elif r % 2 == 0:
            cell.set_facecolor(C_LB)
        cell.set_edgecolor('#B0BEC5')

    # ── Moment capacity diagram
    ax_Mdiag = fig.add_subplot(gs[2, :])
    ax_Mdiag.fill_between(x, 0, M, alpha=0.35, color=C_BL, label=f'M(x) phát sinh / Applied')
    ax_Mdiag.plot(x, M, color=C_BL, lw=2)
    ax_Mdiag.axhline(M_Rd, color=C_GN, lw=2.5, ls='--',
                     label=f'MRd = {M_Rd:.3f} kN·m (khả năng / capacity)')
    ax_Mdiag.plot(L/2, M_max, 'ro', ms=8)
    ax_Mdiag.set_xlabel('x (m)', fontsize=9)
    ax_Mdiag.set_ylabel('M (kN·m)', fontsize=9)
    ax_Mdiag.set_title('Biểu đồ moment và khả năng chịu lực / Moment & Capacity Diagram',
                       color=C_BL)
    ax_Mdiag.legend(fontsize=9)
    ax_Mdiag.set_xlim(0, L)
    ax_Mdiag.invert_yaxis()
    dM = M_Rd - M_max
    ax_Mdiag.text(L*0.75, M_max*0.5,
                  f'Dư / Reserve: {dM:.3f} kN·m ({dM/M_max*100:.1f}%)',
                  fontsize=9, color=C_GN, fontweight='bold',
                  bbox=dict(boxstyle='round', fc=C_LG, ec=C_GN))

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ─────────────────────────────────────────────────────────
    # TRANG 10: TOM TAT KET QUA / SUMMARY
    # ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=A4, facecolor='#FAFAFA')

    # Full-page header
    band_top = Rectangle((0, 0.88), 1, 0.12, transform=fig.transFigure,
                         fc=C_BL, ec='none', clip_on=False)
    fig.patches.append(band_top)
    fig.text(0.5, 0.955, 'TÓM TẮT KẾT QUẢ / SUMMARY OF RESULTS',
             ha='center', va='center', fontsize=16, fontweight='bold',
             color='white', transform=fig.transFigure)
    fig.text(0.5, 0.908, 'Dầm giản đơn C40  |  L=7m, b=0.5m, h=0.3m, q=5kN/m  |  TCVN 5574:2018',
             ha='center', va='center', fontsize=9.5, color='#BBDEFB',
             transform=fig.transFigure)

    # Summary data in grouped boxes
    groups = [
        ('NOI LUC / INTERNAL FORCES', C_BL, [
            ('Phản lực gối / Reaction',      'RA = RB = qL/2',         f'{RA:.3f} kN'),
            ('Moment max / Max moment',      'Mmax = qL²/8',           f'{M_max:.4f} kN·m'),
            ('Lực cắt max / Max shear',      'Vmax = qL/2',            f'{V_max:.4f} kN'),
            ('Ứng suất max / Max stress',    'σmax = M·(h/2)/I',       f'{sigma_bot:.4f} MPa'),
            ('Ứng suất cắt / Shear stress',  'τmax = V·S₀/(I·b)',      f'{tau_max:.4f} MPa'),
        ]),
        ('DO VONG / DEFLECTION', C_GN, [
            ('Độ võng max / Max deflection', 'δ = 5qL⁴/(384EI)',        f'{y_mm:.4f} mm'),
            ('Giới hạn / Allowable',         'L/400',                   f'{y_allow_mm:.2f} mm'),
            ('Tỉ lệ / Ratio',                'δmax/δallow',             f'{ratio_defl:.4f}'),
            ('Kết quả / Result',             'δmax ≤ δallow ?',         '✓ ĐẠT / PASS' if ratio_defl < 1 else '✗ KHÔNG ĐẠT'),
            ('Góc xoay gối / End slope',     'θ = qL³/(24EI)',          f'{theta_A_deg:.5f}°'),
        ]),
        ('DAO DONG / VIBRATION', C_OR, [
            ('f₁ Giải tích / Analytical',   '(π/L)²√(EI/m)/(2π)',     f'{modes1[0]["f"]:.4f} Hz'),
            ('T₁ Giải tích',                'T = 1/f',                 f'{modes1[0]["T"]:.4f} s'),
            ('f₁ Rayleigh',                 'Rayleigh quotient',        f'{f_r:.4f} Hz'),
            ('f₁ FEM (20 elem.)',            'Eigenvalue K,M',          f'{modes3[0]["f"]:.4f} Hz'),
            ('f₂ FEM / f₃ FEM',            'Mode 2 / Mode 3',         f'{modes3[1]["f"]:.3f} / {modes3[2]["f"]:.3f} Hz'),
        ]),
        ('COT THEP / REINFORCEMENT', C_RD, [
            ('Diện tích yêu cầu / Req.',    'As,req = M/(Rs·z)',       f'{As_req_cm2:.3f} cm²'),
            ('Cốt thép chọn / Provided',     f'{n_bars}φ{d_bar_mm} mm', f'{As_prov_cm2:.2f} cm²'),
            ('Khả năng / Capacity',          'MRd = Rs·As·(h₀-x/2)',   f'{M_Rd:.3f} kN·m'),
            ('Cốt đai / Stirrups',           f'2φ{d_stir_mm}@{s_prov_mm}mm', f'Qtotal={Q_total/1e3:.2f} kN'),
            ('Kết quả / Result',             'MRd ≥ Msd & Qtotal ≥ Vsd','✓ ĐẠT / PASS' if ok_M and ok_V else '✗ KHÔNG ĐẠT'),
        ]),
    ]

    colors_box = [C_LB, C_LG, '#FFF3E0', C_LR]
    header_clrs = [C_BL, C_GN, C_OR, C_RD]

    for gi, (title, hclr, items) in enumerate(groups):
        row = gi // 2
        col = gi  % 2
        y0 = 0.82 - row * 0.39
        x0 = 0.05 + col * 0.495

        # Group box
        grp_box = FancyBboxPatch((x0, y0 - 0.35), 0.46, 0.36,
                                 boxstyle='round,pad=0.01',
                                 transform=fig.transFigure,
                                 fc=colors_box[gi], ec=hclr, lw=1.5, clip_on=False)
        fig.patches.append(grp_box)

        # Title bar
        hdr_box = Rectangle((x0, y0 - 0.05), 0.46, 0.045,
                             transform=fig.transFigure,
                             fc=hclr, ec='none', clip_on=False)
        fig.patches.append(hdr_box)
        fig.text(x0 + 0.23, y0 - 0.028, title, ha='center', va='center',
                 fontsize=9, fontweight='bold', color='white',
                 transform=fig.transFigure)

        # Items
        for ii, (param, formula, value) in enumerate(items):
            iy = y0 - 0.098 - ii * 0.056
            fig.text(x0 + 0.01, iy, param, fontsize=7.8, color=C_GR,
                     transform=fig.transFigure)
            fig.text(x0 + 0.24, iy, formula, fontsize=7.5, color='gray',
                     transform=fig.transFigure, fontstyle='italic')
            fclr = C_GN if '✓' in value else (C_RD if '✗' in value else hclr)
            fig.text(x0 + 0.37, iy, value, fontsize=8.5, color=fclr,
                     fontweight='bold', transform=fig.transFigure)

    # Footer verdict
    all_ok = ratio_defl < 1 and ok_M and ok_V and ok_xi and ok_rho
    verdict = '✓  KẾT LUẬN: DẦM ĐẠT YÊU CẦU  /  CONCLUSION: BEAM PASSES ALL CHECKS  ✓'
    verdict_fc = '#E8F5E9' if all_ok else '#FFEBEE'
    verdict_ec = C_GN if all_ok else C_RD
    verdict_tc = C_GN if all_ok else C_RD
    fig.text(0.5, 0.055, verdict, ha='center', va='center', fontsize=11.5,
             fontweight='bold', color=verdict_tc, transform=fig.transFigure,
             bbox=dict(boxstyle='round,pad=0.5', fc=verdict_fc,
                       ec=verdict_ec, lw=2))
    fig.text(0.5, 0.022,
             f'File: {PDF}  |  Tao ngay / Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
             ha='center', fontsize=7, color='gray', transform=fig.transFigure)

    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close(fig)

print(f"\n{'='*60}")
print(f"HOAN THANH / COMPLETED!")
print(f"PDF da luu tai / PDF saved at:")
print(f"  {PDF}")
print(f"{'='*60}")
print(f"\nTOM TAT KET QUA CHINH / KEY RESULTS:")
print(f"  Mmax = {M_max:.4f} kN.m")
print(f"  Vmax = {V_max:.4f} kN")
print(f"  delta_max = {y_mm:.4f} mm  (L/400 = {y_allow_mm:.2f} mm) -> {'PASS' if ratio_defl < 1 else 'FAIL'}")
print(f"  f1 = {modes1[0]['f']:.4f} Hz  (T1 = {modes1[0]['T']:.4f} s)")
print(f"  As,req = {As_req_cm2:.3f} cm2  ->  {n_bars}phi{d_bar_mm} = {As_prov_cm2:.2f} cm2")
print(f"  MRd = {M_Rd:.3f} kN.m  {'PASS' if ok_M else 'FAIL'}")
print(f"  Qtotal = {Q_total/1e3:.3f} kN  {'PASS' if ok_V else 'FAIL'}")
