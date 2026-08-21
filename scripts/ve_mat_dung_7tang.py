#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAT DUNG TOA NHA 7 TANG — Rong 20m, Dai 40m
Luoi: 4 nhip x 5000mm | T1=4200mm | T2-T7=3600mm | Cao +25.800m
Moc: goc toa do (0, 0)
"""
import sys, io, os, time, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT_DIR = r"G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\NhaTang7"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Thong so kien truc ────────────────────────────────────────────
W         = 20000.0     # chieu rong mat dung [mm]
N_BAYS    = 4           # so nhip
BAY_W     = W / N_BAYS  # = 5000mm
COL_X     = [i * BAY_W for i in range(N_BAYS + 1)]

H_GND     = 4200.0      # tang 1 (thuong mai/san xuat)
H_TYP     = 3600.0      # tang dien hinh 2-7
N_FLOOR   = 7
SLAB_H    = 200.0       # do day san [mm]

# Cap do san (y tuyet doi tu 0)
floor_y = [0.0, H_GND]
for _ in range(N_FLOOR - 1):
    floor_y.append(floor_y[-1] + H_TYP)
ROOF_Y = floor_y[-1]    # +25.800m

# Lanh to + ban cua so tang 2-7
WIN_W    = 2800.0; WIN_H    = 1800.0; WIN_SILL = 900.0
# Cua chinh tang 1 (nhip giua)
DOOR_W   = 2200.0; DOOR_H   = 3400.0
# Cua so tang 1 (nhip bien)
WIN1_W   = 2200.0; WIN1_H   = 1800.0; WIN1_SILL = 1000.0
# San thuong (senso / attique)
PARA_H   = 1500.0       # do cao cong trinh tren mai [mm]
PARA_T   = 250.0        # be day mang tuong [mm]

# ── AutoCAD COM ───────────────────────────────────────────────────
try:
    import win32com.client, pythoncom
    from win32com.client import VARIANT

    def pt3d(x, y, z=0.0):
        return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                       (float(x), float(y), float(z)))

    def vtarr(*coords):
        flat = [float(v) for pair in coords for v in pair]
        return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)

    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    try:
        adoc = acad.ActiveDocument; _ = adoc.Name
    except Exception:
        adoc = acad.Documents.Add(); time.sleep(3)
        adoc = acad.ActiveDocument

    msp = adoc.ModelSpace
    for i in range(msp.Count - 1, -1, -1):
        try: msp.Item(i).Delete()
        except: pass
    print(f"[OK] Da lam sach ModelSpace")

    out_dwg = os.path.join(OUT_DIR, "MatDung_7Tang_20x40m.dwg")

    # ── Layers ────────────────────────────────────────────────────
    def mk(name, color):
        try: lyr = adoc.Layers.Item(name)
        except: lyr = adoc.Layers.Add(name)
        lyr.Color = color; return lyr

    mk("WALL",      3)   # xanh la  — tuong ngoai, bao nha
    mk("FLOOR-SLB", 8)   # xam      — san/dam
    mk("COLUMN",    8)   # xam      — cot
    mk("WINDOW",    4)   # xanh lam — o kinh
    mk("DOOR",      4)   # xanh lam — cua chinh
    mk("PARAPET",   3)   # xanh la  — attique / senso
    mk("GROUND",    5)   # tim      — nen dat
    mk("GRID-SYM",  2)   # vang     — ky hieu truc
    mk("ELEV-TAG",  2)   # vang     — ky hieu cao trinh
    mk("DIM",       2)   # vang     — kich thuoc
    mk("TEXT",      7)   # trang    — chu thich

    def sl(n): adoc.ActiveLayer = adoc.Layers.Item(n)

    def pline(pts, lyr, closed=False):
        pl = msp.AddLightWeightPolyline(vtarr(*pts))
        pl.Closed = closed; pl.Layer = lyr; return pl

    def line(x1, y1, x2, y2, lyr):
        ln = msp.AddLine(pt3d(x1, y1), pt3d(x2, y2))
        ln.Layer = lyr; return ln

    def rect(x, y, w, h, lyr):
        return pline([(x,y),(x+w,y),(x+w,y+h),(x,y+h)], lyr, True)

    def txt(s, x, y, ht, lyr="TEXT"):
        t = msp.AddText(str(s), pt3d(x, y), ht)
        t.Layer = lyr; return t

    # ── 1. Nen dat ────────────────────────────────────────────────
    sl("GROUND")
    line(-3000, 0, W + 3000, 0, "GROUND")
    for xi in range(-3000, int(W) + 3001, 600):
        line(xi, 0, xi - 400, -400, "GROUND")

    # ── 2. Tuong ngoai + outline chinh ────────────────────────────
    sl("WALL")
    rect(0, 0, W, ROOF_Y, "WALL")          # bao nha chinh
    # Lop tuong day 250mm (vach ngoai trai/phai)
    rect(0, 0, 250, ROOF_Y, "WALL")
    rect(W - 250, 0, 250, ROOF_Y, "WALL")

    # ── 3. San tung tang (dai + chat filled) ─────────────────────
    sl("FLOOR-SLB")
    for fy in floor_y[1:]:                 # san 2..7 va mai
        rect(0, fy - SLAB_H, W, SLAB_H, "FLOOR-SLB")

    # ── 4. Luoi cot (doc, dung) ───────────────────────────────────
    sl("COLUMN")
    COL_W = 350.0
    for cx in COL_X:
        for fi in range(N_FLOOR):
            y0 = floor_y[fi]
            y1 = floor_y[fi + 1] - SLAB_H
            rect(cx - COL_W/2, y0, COL_W, y1 - y0, "COLUMN")

    # ── 5. Cua so tang 2-7 ────────────────────────────────────────
    sl("WINDOW")
    for fi in range(1, N_FLOOR):
        y_fl = floor_y[fi]
        for bi in range(N_BAYS):
            bcx = (COL_X[bi] + COL_X[bi+1]) / 2
            wx = bcx - WIN_W / 2
            wy = y_fl + WIN_SILL
            rect(wx, wy, WIN_W, WIN_H, "WINDOW")
            # O kinh 2x2
            line(wx + WIN_W/2, wy, wx + WIN_W/2, wy + WIN_H, "WINDOW")
            line(wx, wy + WIN_H/2, wx + WIN_W, wy + WIN_H/2, "WINDOW")
            # Lanh to phia tren
            rect(wx, wy + WIN_H, WIN_W, SLAB_H, "FLOOR-SLB")

    # ── 6. Tang 1: cua chinh (2 nhip giua) + cua so (2 nhip bien)
    sl("DOOR")
    for bi in [1, 2]:
        bcx = (COL_X[bi] + COL_X[bi+1]) / 2
        dx = bcx - DOOR_W / 2
        rect(dx, 0, DOOR_W, DOOR_H, "DOOR")
        line(dx + DOOR_W/2, 0, dx + DOOR_W/2, DOOR_H, "DOOR")  # canh cua
        # Lanh to cua
        rect(dx, DOOR_H, DOOR_W, SLAB_H, "FLOOR-SLB")
    sl("WINDOW")
    for bi in [0, 3]:
        bcx = (COL_X[bi] + COL_X[bi+1]) / 2
        wx = bcx - WIN1_W / 2
        wy = WIN1_SILL
        rect(wx, wy, WIN1_W, WIN1_H, "WINDOW")
        line(wx + WIN1_W/2, wy, wx + WIN1_W/2, wy + WIN1_H, "WINDOW")
        line(wx, wy + WIN1_H/2, wx + WIN1_W, wy + WIN1_H/2, "WINDOW")

    # ── 7. Attique / senso tren mai ──────────────────────────────
    sl("PARAPET")
    # Vach attique ben trai va phai
    rect(-PARA_T, ROOF_Y, PARA_T, PARA_H, "PARAPET")
    rect(W,       ROOF_Y, PARA_T, PARA_H, "PARAPET")
    # Dai ngang tren cung
    rect(-PARA_T, ROOF_Y + PARA_H - 300, W + 2*PARA_T, 300, "PARAPET")
    # Dong phong chu (logo/ten toa nha) — bang chu nhat giua mai
    SIGN_W = 8000.0; SIGN_H = 800.0
    rect(W/2 - SIGN_W/2, ROOF_Y + 200, SIGN_W, SIGN_H, "PARAPET")

    # ── 8. Ky hieu cao trinh (ben phai) ──────────────────────────
    sl("ELEV-TAG")
    for fi, fy in enumerate(floor_y):
        elev_m = fy / 1000.0
        sign   = "+" if elev_m >= 0 else ""
        # Mui ten cao trinh
        line(W + 600, fy, W + 5000, fy, "ELEV-TAG")
        txt(f"{sign}{elev_m:.3f}", W + 5200, fy - 120, 200, "ELEV-TAG")
    # Mai
    line(W + 600, ROOF_Y, W + 5000, ROOF_Y, "ELEV-TAG")
    txt(f"+{ROOF_Y/1000:.3f}", W + 5200, ROOF_Y - 120, 200, "ELEV-TAG")

    # ── 9. Nhan so tang (ben trai) ────────────────────────────────
    sl("TEXT")
    for fi in range(N_FLOOR):
        y_mid = (floor_y[fi] + floor_y[fi+1]) / 2 - 150
        txt(f"TANG {fi+1}", -5500, y_mid, 250, "TEXT")
        line(-3000, (floor_y[fi]+floor_y[fi+1])/2, 0,
             (floor_y[fi]+floor_y[fi+1])/2, "TEXT")
    txt("MAI", -5500, ROOF_Y + PARA_H/2 - 150, 250, "TEXT")

    # ── 10. Ky hieu truc (A-E phia duoi) ─────────────────────────
    sl("GRID-SYM")
    ax_labels = ["A", "B", "C", "D", "E"]
    R_CIR = 450
    for ci, cx in enumerate(COL_X):
        # Duong truc tren (keo len tren mai)
        line(cx, ROOF_Y + PARA_H, cx, ROOF_Y + PARA_H + 800, "GRID-SYM")
        cir_top = msp.AddCircle(pt3d(cx, ROOF_Y + PARA_H + 800 + R_CIR), R_CIR)
        cir_top.Layer = "GRID-SYM"
        txt(ax_labels[ci], cx - 250, ROOF_Y + PARA_H + 800 + R_CIR - 250, 350, "GRID-SYM")
        # Duong truc duoi
        line(cx, 0, cx, -1800, "GRID-SYM")
        cir_bot = msp.AddCircle(pt3d(cx, -1800 - R_CIR), R_CIR)
        cir_bot.Layer = "GRID-SYM"
        txt(ax_labels[ci], cx - 250, -1800 - R_CIR - 250, 350, "GRID-SYM")

    # ── 11. Kich thuoc ────────────────────────────────────────────
    sl("DIM")
    def dim_lin(x1, y1, x2, y2, dx, dy, ang=0.0):
        try:
            o = msp.AddDimLinear(pt3d(x1,y1), pt3d(x2,y2), pt3d(dx,dy), ang)
            o.Layer = "DIM"
        except: pass

    # Chieu cao tung tang (ben phai)
    for fi in range(N_FLOOR):
        dim_lin(W, floor_y[fi], W, floor_y[fi+1],
                W + 2000, (floor_y[fi]+floor_y[fi+1])/2, 90.0)

    # Tong chieu cao (xa hon)
    dim_lin(W, 0, W, ROOF_Y, W + 4000, ROOF_Y/2, 90.0)

    # Buoc cot (phia duoi)
    for bi in range(N_BAYS):
        dim_lin(COL_X[bi], 0, COL_X[bi+1], 0,
                (COL_X[bi]+COL_X[bi+1])/2, -3500)

    # Tong chieu rong (xa hon)
    dim_lin(0, 0, W, 0, W/2, -6000)

    # ── 12. Tieu de ban ve ───────────────────────────────────────
    sl("TEXT")
    TY = ROOF_Y + PARA_H + R_CIR*2 + 1500
    txt("MAT DUNG CHINH (SOUTH ELEVATION)",   W/2 - 4500, TY + 800, 600, "TEXT")
    txt("TOA NHA 7 TANG — MAT BANG 20m x 40m — CAO TRINH +25.800m",
        W/2 - 5500, TY + 100, 320, "TEXT")
    txt("Luoi cot: 4 nhip x 5.0m  |  Tang 1: H=4.2m  |  Tang 2-7: H=3.6m  |  Tyle NTS",
        W/2 - 5500, TY - 350, 260, "TEXT")

    # ── 13. Zoom & Save ──────────────────────────────────────────
    adoc.SendCommand("ZOOM\nE\n")
    adoc.SendCommand("LAYERCLOSE\n")
    adoc.SaveAs(out_dwg)
    print(f"[DWG] Da luu: {out_dwg}")

except Exception as e:
    print(f"[LOI] {e}")
    import traceback; traceback.print_exc()

print(f"\n[HOAN THANH] {out_dwg}")
