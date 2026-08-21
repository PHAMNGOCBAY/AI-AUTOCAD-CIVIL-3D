#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NOI LUC DAM LIEN TUC 3 NHIP — b=0.35m x h=0.40m
Phuong phap: Phuong trinh 3 momen (Clapeyron)
Xuat: PDF bieu do SFD + BMD
"""
import sys, io, os
import numpy as np
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT_DIR = r"G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\DamLienTuc3Nhip"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 1. THONG SO ───────────────────────────────────────────────────
b   = 0.35                          # [m]
h   = 0.40                          # [m]
L   = np.array([5.0, 5.0, 5.0])    # chieu dai nhip [m]
q   = np.array([20.0, 20.0, 20.0]) # tai phan bo [kN/m]
N   = 3                             # so nhip
NP  = 300                           # so diem noi suy

x_sup = np.concatenate([[0], np.cumsum(L)])  # toa do goi: [0,5,10,15]
LT    = L.sum()                              # chieu dai toan dam

# ── 2. GIAI PHUONG TRINH 3 MOMEN ─────────────────────────────────
# L[i-1]*M[i-1] + 2*(L[i-1]+L[i])*M[i] + L[i]*M[i+1]
#   = -q[i-1]*L[i-1]^3/4 - q[i]*L[i]^3/4
# 2 an: M_B (i=1), M_C (i=2), bien bieu M_A=M_D=0
A_mat = np.array([
    [2*(L[0]+L[1]), L[1]          ],
    [L[1],          2*(L[1]+L[2]) ],
])
rhs = np.array([
    -q[0]*L[0]**3/4 - q[1]*L[1]**3/4,
    -q[1]*L[1]**3/4 - q[2]*L[2]**3/4,
])
M_int = np.linalg.solve(A_mat, rhs)
M_sup = np.array([0.0, M_int[0], M_int[1], 0.0])   # [M_A, M_B, M_C, M_D]

# ── 3. PHAN LUC ───────────────────────────────────────────────────
# R_left  = (q*L/2) + (M_right - M_left)/L  (tu can bang momen quanh nut phai)
R_left  = np.array([q[i]*L[i]/2 + (M_sup[i+1]-M_sup[i])/L[i] for i in range(N)])
R_right = np.array([q[i]*L[i]/2 - (M_sup[i+1]-M_sup[i])/L[i] for i in range(N)])

R = np.zeros(N+1)
R[0] = R_left[0]
for i in range(1, N):
    R[i] = R_right[i-1] + R_left[i]
R[N] = R_right[N-1]

# ── 4. SFD VA BMD TAI TUNG DIEM ──────────────────────────────────
segs_x, segs_V, segs_M = [], [], []
for i in range(N):
    xs = x_sup[i]
    x_loc = np.linspace(0, L[i], NP)
    V = R_left[i] - q[i]*x_loc
    M = M_sup[i] + R_left[i]*x_loc - 0.5*q[i]*x_loc**2
    segs_x.append(xs + x_loc)
    segs_V.append(V)
    segs_M.append(M)

# ── 5. CUC TRI ───────────────────────────────────────────────────
peaks = []
for i in range(N):
    x0_V = R_left[i] / q[i]          # diem V=0 trong nhip
    if 0 < x0_V < L[i]:
        M_peak = M_sup[i] + R_left[i]*x0_V - 0.5*q[i]*x0_V**2
        peaks.append((i, x_sup[i]+x0_V, M_peak))

V_maxabs = max(max(abs(sv[0]), abs(sv[-1])) for sv in segs_V)

# ── 6. IN KET QUA ────────────────────────────────────────────────
print("=" * 60)
print("  DAM LIEN TUC 3 NHIP  b=0.35m x h=0.40m")
print("=" * 60)
print(f"  L = {L[0]:.1f} + {L[1]:.1f} + {L[2]:.1f} = {LT:.1f} m")
print(f"  q = {q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} kN/m")
print()
print("MO MEN TAI GOI:")
lbl = ['A','B','C','D']
for i,m in enumerate(M_sup):
    print(f"  M_{lbl[i]} = {m:+.3f} kN.m")
print()
print("PHAN LUC:")
for i,r in enumerate(R):
    print(f"  R_{lbl[i]} = {r:+.3f} kN")
print(f"  Kiem tra: sum R = {R.sum():.2f}  (tai = {(q*L).sum():.2f}) kN")
print()
print("CUC TRI MO MEN DUONG:")
for (sp, xp, mp) in peaks:
    print(f"  Nhip {sp+1}: M_max+ = {mp:+.3f} kN.m  tai x = {xp:.3f} m")
print(f"LUC CAT MAX: |Q|_max = {V_maxabs:.3f} kN")
print("=" * 60)

# ── 7. VE PDF ────────────────────────────────────────────────────
out_pdf = os.path.join(OUT_DIR, "NoiLuc_DamLienTuc_3Nhip.pdf")
CV = '#1a6fad'; CP = '#c0392b'; CN = '#27ae60'

with PdfPages(out_pdf) as pdf:

    # ════ TRANG 1: So do + SFD + BMD ════════════════════════════
    fig = plt.figure(figsize=(14, 20))
    gs  = fig.add_gridspec(4, 1, height_ratios=[1.4, 0.2, 1.8, 2.0],
                           hspace=0.45)

    # ── Subplot A: So do dam ─────────────────────────────────────
    ax0 = fig.add_subplot(gs[0])
    ax0.set_title("Sơ đồ dầm liên tục 3 nhịp", fontsize=13, fontweight='bold')
    ax0.set_xlim(-1.5, LT + 1.5)
    ax0.set_ylim(-3.2, 3.5)
    ax0.axis('off')

    # Duong dam
    ax0.plot([0, LT], [0, 0], 'k-', lw=5, solid_capstyle='round')

    # Tai phan bo (mui ten + duong ngang)
    for i in range(N):
        x0 = x_sup[i]; x1 = x_sup[i+1]
        ax0.plot([x0, x1], [2.0, 2.0], color='gray', lw=2)
        for xq in np.linspace(x0+0.2, x1-0.2, 10):
            ax0.annotate('', xy=(xq, 0.05),
                         xytext=(xq, 1.95),
                         arrowprops=dict(arrowstyle='->', color='gray', lw=1.2))
        ax0.text((x0+x1)/2, 2.3, f'q={q[i]:.0f} kN/m',
                 ha='center', fontsize=10, color='gray')

    # Goi + phan luc
    for j, (sx, rv) in enumerate(zip(x_sup, R)):
        # Tam giac goi
        tri = plt.Polygon([[sx,-0.05],[sx-0.35,-0.7],[sx+0.35,-0.7]], color='k')
        ax0.add_patch(tri)
        ax0.plot([sx-0.5, sx+0.5], [-0.75, -0.75], 'k-', lw=1.5)
        # Mui ten phan luc
        ax0.annotate('', xy=(sx, -0.8), xytext=(sx, -2.2),
                     arrowprops=dict(arrowstyle='<-', color=CV, lw=2))
        ax0.text(sx, -2.5, f'{rv:.1f}kN', ha='center', fontsize=9,
                 color=CV, fontweight='bold')
        ax0.text(sx, 0.25, lbl[j], ha='center', fontsize=11, fontweight='bold')

    # Nhan nhip va momen goi
    for i in range(N):
        xm = (x_sup[i]+x_sup[i+1])/2
        ax0.text(xm, -0.4, f'L{i+1}={L[i]:.1f}m', ha='center', fontsize=10)
    for j in [1,2]:
        ax0.text(x_sup[j], 0.6, f'M={M_sup[j]:.1f}kN.m',
                 ha='center', fontsize=9, color=CN,
                 bbox=dict(boxstyle='round,pad=0.2', fc='#e8f8e8', ec=CN, lw=0.8))

    # ── Spacer ───────────────────────────────────────────────────
    ax_sp = fig.add_subplot(gs[1]); ax_sp.axis('off')

    # ── Subplot B: Bieu do luc cat SFD ───────────────────────────
    ax1 = fig.add_subplot(gs[2])
    ax1.set_title("Biểu đồ Lực Cắt  Q (kN)", fontsize=12, fontweight='bold')

    # Xay dung duong SFD co jump tai goi
    x_sfd, V_sfd = [], []
    for i in range(N):
        xs  = x_sup[i]
        V_l = R_left[i]
        V_r = R_left[i] - q[i]*L[i]
        if i == 0:
            x_sfd += [xs, xs + L[i]]
            V_sfd += [V_l, V_r]
        else:
            x_sfd += [xs, xs, xs + L[i]]
            V_sfd += [V_sfd[-1], V_l, V_r]

    xsfd = np.array(x_sfd); vsfd = np.array(V_sfd)
    ax1.plot(xsfd, vsfd, color=CV, lw=2.5)
    ax1.fill_between(xsfd, vsfd, 0, where=vsfd>=0, alpha=0.25, color=CV)
    ax1.fill_between(xsfd, vsfd, 0, where=vsfd< 0, alpha=0.25, color='orange')
    ax1.axhline(0, color='k', lw=1.2)

    # Nhan gia tri tai goi
    for i in range(N):
        xs = x_sup[i]; xe = x_sup[i+1]
        vl = segs_V[i][0];  vr = segs_V[i][-1]
        off_y = 4 if vl >= 0 else -9
        ax1.text(xs+0.15, vl+off_y, f'{vl:.1f}', fontsize=9, color=CV, fontweight='bold')
        off_yr = -9 if vr < 0 else 4
        ax1.text(xe-0.5, vr+off_yr, f'{vr:.1f}', fontsize=9, color='darkorange', fontweight='bold')
        # Diem V=0
        x0V = R_left[i]/q[i]
        if 0 < x0V < L[i]:
            ax1.axvline(xs+x0V, color='gray', lw=0.8, ls='--')
            ax1.text(xs+x0V+0.1, 2, f'V=0\nx={xs+x0V:.2f}m', fontsize=8, color='gray')

    ax1.set_xlabel('x (m)', fontsize=11)
    ax1.set_ylabel('Q (kN)', fontsize=11)
    ax1.set_xlim(-0.5, LT+0.5)
    ax1.grid(True, alpha=0.35)
    # Nhan truc x tai goi
    ax1.set_xticks(x_sup)
    ax1.set_xticklabels([f'{lbl[j]}\n{x_sup[j]:.0f}m' for j in range(N+1)], fontsize=9)

    # ── Subplot C: Bieu do mo men BMD ────────────────────────────
    ax2 = fig.add_subplot(gs[3])
    ax2.set_title("Biểu đồ Mô Men  M (kN.m)  [dương = căng thớ dưới]",
                  fontsize=12, fontweight='bold')

    xf = np.concatenate(segs_x)
    Mf = np.concatenate(segs_M)
    ax2.plot(xf, Mf, 'k-', lw=2.5)
    ax2.fill_between(xf, Mf, 0, where=Mf>=0, alpha=0.3, color=CP, label='M > 0')
    ax2.fill_between(xf, Mf, 0, where=Mf< 0, alpha=0.3, color=CN, label='M < 0')
    ax2.axhline(0, color='k', lw=1.2)

    # Nhan mo men cuc dai duong
    for (sp, xp, mp) in peaks:
        ax2.annotate(f'+{mp:.2f}', xy=(xp, mp), xytext=(xp, mp+4),
                     ha='center', fontsize=10, color=CP, fontweight='bold',
                     arrowprops=dict(arrowstyle='->', color=CP, lw=1))

    # Nhan mo men tai goi (am)
    for j in [1, 2]:
        mv = M_sup[j]
        ax2.annotate(f'{mv:.2f}', xy=(x_sup[j], mv),
                     xytext=(x_sup[j]+0.3, mv-6),
                     ha='center', fontsize=10, color=CN, fontweight='bold',
                     arrowprops=dict(arrowstyle='->', color=CN, lw=1))

    ax2.legend(fontsize=10, loc='lower center', ncol=2)
    ax2.set_xlabel('x (m)', fontsize=11)
    ax2.set_ylabel('M (kN.m)', fontsize=11)
    ax2.set_xlim(-0.5, LT+0.5)
    ax2.set_xticks(x_sup)
    ax2.set_xticklabels([f'{lbl[j]}\n{x_sup[j]:.0f}m' for j in range(N+1)], fontsize=9)
    ax2.grid(True, alpha=0.35)

    fig.suptitle(
        "NỘI LỰC DẦM LIÊN TỤC 3 NHỊP   b×h = 0.35×0.40 m\n"
        f"L₁={L[0]:.1f}m  L₂={L[1]:.1f}m  L₃={L[2]:.1f}m  |  "
        f"q={q[0]:.0f} kN/m (đều)",
        fontsize=14, fontweight='bold', y=0.995)

    pdf.savefig(fig, bbox_inches='tight', dpi=150)
    plt.close()

    # ════ TRANG 2: Mat cat va bang tong hop ══════════════════════
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 8),
                               gridspec_kw={'width_ratios': [1, 2]})

    # ── Mat cat ngang dam ────────────────────────────────────────
    ax_cs = axes2[0]
    ax_cs.set_title("Mặt cắt ngang dầm\n b×h = 0.35×0.40 m",
                    fontsize=12, fontweight='bold')
    bm = b*1000; hm = h*1000
    rect = mpatches.FancyBboxPatch((0, 0), bm, hm,
                                    boxstyle='square,pad=0',
                                    linewidth=2, edgecolor='k',
                                    facecolor='#d9e8f5')
    ax_cs.add_patch(rect)
    # Ky hieu kich thuoc
    ax_cs.annotate('', xy=(bm, -40), xytext=(0, -40),
                   arrowprops=dict(arrowstyle='<->', color='k', lw=1.5))
    ax_cs.text(bm/2, -70, f'b = {b*100:.0f} cm', ha='center', fontsize=11)
    ax_cs.annotate('', xy=(bm+40, hm), xytext=(bm+40, 0),
                   arrowprops=dict(arrowstyle='<->', color='k', lw=1.5))
    ax_cs.text(bm+80, hm/2, f'h = {h*100:.0f} cm', va='center', fontsize=11)
    ax_cs.set_xlim(-50, bm+200); ax_cs.set_ylim(-120, hm+80)
    ax_cs.set_aspect('equal'); ax_cs.axis('off')

    # ── Bang tong hop ────────────────────────────────────────────
    ax_tb = axes2[1]
    ax_tb.axis('off')
    ax_tb.set_title("Bảng Tổng hợp Nội lực", fontsize=12, fontweight='bold')

    rows = [
        ["Vị trí", "Q (kN)", "M (kN.m)", "Ghi chú"],
    ]
    for i in range(N):
        vl = segs_V[i][0]; vr = segs_V[i][-1]
        xm = (x_sup[i]+x_sup[i+1])/2
        idx = np.argmin(np.abs(segs_x[i] - (R_left[i]/q[i])))
        mm  = segs_M[i][idx]
        rows.append([f"Nhịp {i+1} đầu   ({lbl[i]})", f"{vl:+.2f}", f"{M_sup[i]:+.2f}", "gối"])
        rows.append([f"Nhịp {i+1} giữa  (x={x_sup[i]+R_left[i]/q[i]:.2f}m)",
                     f"0.00", f"{mm:+.2f}", "M_max+"])
        rows.append([f"Nhịp {i+1} cuối  ({lbl[i+1]})", f"{vr:+.2f}", f"{M_sup[i+1]:+.2f}", "gối"])
        rows.append(["", "", "", ""])

    tbl = ax_tb.table(cellText=rows[1:], colLabels=rows[0],
                       cellLoc='center', loc='center',
                       bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False); tbl.set_fontsize(10)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor('#2c3e7a'); cell.set_text_props(color='white', fontweight='bold')
        elif r % 4 == 0:
            cell.set_facecolor('#dce8f7')
        cell.set_linewidth(0.5)

    fig2.suptitle("BẢNG TỔNG HỢP NỘI LỰC — DẦM LIÊN TỤC 3 NHỊP",
                  fontsize=13, fontweight='bold')
    pdf.savefig(fig2, bbox_inches='tight', dpi=150)
    plt.close()

print(f"\n[PDF] Da luu: {out_pdf}")
