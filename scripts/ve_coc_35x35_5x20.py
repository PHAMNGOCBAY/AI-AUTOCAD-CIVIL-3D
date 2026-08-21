#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VE MAT BANG BO TRI COC — Nha 5x20m, 6 coc 35x35cm
Luoi 2x3: truc A(x=0) & truc B(x=5000), hang 1/2/3 (y=0/10000/20000)
Moc: goc toa do (0, 0)
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT_DIR = r"G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\CocNha5x20"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Thong so ──────────────────────────────────────────────────────
B_PILE   = 350.0    # chieu rong coc [mm]
H_PILE   = 350.0    # chieu cao coc [mm]
B_HOUSE  = 4000.0   # nha rong [mm]
L_HOUSE  = 20000.0  # nha dai [mm]
SPA_Y    = 10000.0  # buoc coc theo chieu dai [mm]

HALF_B   = B_PILE / 2
HALF_H   = H_PILE / 2

# Vi tri trung tam 6 coc (x, y, nhan)
PILES = [
    (0,       0,       "C1"),
    (B_HOUSE, 0,       "C2"),
    (0,       SPA_Y,   "C3"),
    (B_HOUSE, SPA_Y,   "C4"),
    (0,       L_HOUSE, "C5"),
    (B_HOUSE, L_HOUSE, "C6"),
]

# ── AutoCAD COM ───────────────────────────────────────────────────
try:
    import win32com.client, pythoncom, time
    from win32com.client import VARIANT

    def pt3d(x, y, z=0.0):
        return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                       (float(x), float(y), float(z)))

    def vtarr(*coords):
        flat = [float(v) for pair in coords for v in pair]
        return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)

    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    try:
        adoc = acad.ActiveDocument
        _    = adoc.Name
    except Exception:
        adoc = acad.Documents.Add()
        time.sleep(3)
        adoc = acad.ActiveDocument

    msp     = adoc.ModelSpace
    out_dwg = os.path.join(OUT_DIR, "MatBang_Coc_6coc35x35_4x20.dwg")

    # Xoa tat ca doi tuong cu trong ModelSpace
    for i in range(msp.Count - 1, -1, -1):
        try:
            msp.Item(i).Delete()
        except Exception:
            pass
    print(f"[OK] Da xoa {msp.Count} doi tuong cu")

    # ── Layers ────────────────────────────────────────────────────
    def mk_layer(name, color_idx):
        try:
            lyr = adoc.Layers.Item(name)
        except Exception:
            lyr = adoc.Layers.Add(name)
        lyr.Color = color_idx
        return lyr

    mk_layer("COC-OUTLINE",  1)   # do  — duong bien coc
    mk_layer("COC-CROSS",    1)   # do  — dau cheo trong coc
    mk_layer("HOUSE-WALL",   8)   # xam — vach nha
    mk_layer("GRID-LINE",    9)   # xam nhat — luoi truc
    mk_layer("DIM",          2)   # vang — kich thuoc
    mk_layer("TEXT",         7)   # trang — chu

    def set_lyr(name):
        adoc.ActiveLayer = adoc.Layers.Item(name)

    # ── 1. Duong bao nha (5000 x 20000) ──────────────────────────
    set_lyr("HOUSE-WALL")
    pl_h = msp.AddLightWeightPolyline(vtarr(
        (0, 0), (B_HOUSE, 0), (B_HOUSE, L_HOUSE), (0, L_HOUSE)
    ))
    pl_h.Closed = True
    pl_h.Layer  = "HOUSE-WALL"

    # ── 2. Luoi truc (centerlines vuot ra ngoai 2000mm moi phia) ─
    set_lyr("GRID-LINE")
    OVER = 2000.0
    for gx in [0.0, B_HOUSE]:
        ln = msp.AddLine(pt3d(gx, -OVER), pt3d(gx, L_HOUSE + OVER))
        ln.Layer = "GRID-LINE"
    for gy in [0.0, SPA_Y, L_HOUSE]:
        ln = msp.AddLine(pt3d(-OVER, gy), pt3d(B_HOUSE + OVER, gy))
        ln.Layer = "GRID-LINE"

    # ── 3. Coc: hinh vuong + dau cheo (X) ────────────────────────
    for (cx, cy, label) in PILES:
        set_lyr("COC-OUTLINE")
        pl_p = msp.AddLightWeightPolyline(vtarr(
            (cx - HALF_B, cy - HALF_H),
            (cx + HALF_B, cy - HALF_H),
            (cx + HALF_B, cy + HALF_H),
            (cx - HALF_B, cy + HALF_H),
        ))
        pl_p.Closed = True
        pl_p.Layer  = "COC-OUTLINE"

        set_lyr("COC-CROSS")
        d1 = msp.AddLine(pt3d(cx - HALF_B, cy - HALF_H),
                         pt3d(cx + HALF_B, cy + HALF_H))
        d1.Layer = "COC-CROSS"
        d2 = msp.AddLine(pt3d(cx + HALF_B, cy - HALF_H),
                         pt3d(cx - HALF_B, cy + HALF_H))
        d2.Layer = "COC-CROSS"

        # Nhan coc
        set_lyr("TEXT")
        t = msp.AddText(label, pt3d(cx - 120, cy + HALF_H + 150), 220)
        t.Layer = "TEXT"

    # ── 4. Nhan truc (A, B va 1, 2, 3) ──────────────────────────
    set_lyr("TEXT")
    TH_AX = 350   # chieu cao chu truc

    # Truc doc (A tai x=0, B tai x=5000)
    for gx, name in [(0.0, "A"), (B_HOUSE, "B")]:
        # Ky hieu tron o duoi (y = -OVER - 500)
        cir = msp.AddCircle(pt3d(gx, -OVER - 500), 400)
        cir.Layer = "TEXT"
        t = msp.AddText(name, pt3d(gx - 180, -OVER - 700), TH_AX)
        t.Layer = "TEXT"
        # Phia tren
        cir2 = msp.AddCircle(pt3d(gx, L_HOUSE + OVER + 500), 400)
        cir2.Layer = "TEXT"
        t2 = msp.AddText(name, pt3d(gx - 180, L_HOUSE + OVER + 300), TH_AX)
        t2.Layer = "TEXT"

    # Truc ngang (1 tai y=0, 2 tai y=10000, 3 tai y=20000)
    for gy, num in [(0.0, "1"), (SPA_Y, "2"), (L_HOUSE, "3")]:
        cir = msp.AddCircle(pt3d(-OVER - 500, gy), 400)
        cir.Layer = "TEXT"
        t = msp.AddText(num, pt3d(-OVER - 650, gy - 180), TH_AX)
        t.Layer = "TEXT"

    # ── 5. Kich thuoc ─────────────────────────────────────────────
    set_lyr("DIM")

    def dim_lin(x1, y1, x2, y2, dx, dy, ang=0.0):
        try:
            obj = msp.AddDimLinear(
                pt3d(x1, y1), pt3d(x2, y2), pt3d(dx, dy), ang)
            obj.Layer = "DIM"
        except Exception:
            pass

    # Chieu rong nha (duoi)
    dim_lin(0, 0, B_HOUSE, 0, B_HOUSE/2, -2500)

    # Buoc coc theo chieu dai (phai)
    dim_lin(B_HOUSE, 0,     B_HOUSE, SPA_Y,   B_HOUSE + 2500, SPA_Y/2,     90.0)
    dim_lin(B_HOUSE, SPA_Y, B_HOUSE, L_HOUSE, B_HOUSE + 2500, SPA_Y*1.5,   90.0)

    # Tong chieu dai nha (phai, xa hon)
    dim_lin(B_HOUSE, 0, B_HOUSE, L_HOUSE, B_HOUSE + 4500, L_HOUSE/2, 90.0)

    # Kich thuoc coc (annotation rieng tai C1)
    cx0, cy0 = PILES[0][0], PILES[0][1]
    dim_lin(cx0 - HALF_B, cy0 - HALF_H, cx0 + HALF_B, cy0 - HALF_H,
            cx0, cy0 - HALF_H - 1500)           # B_coc = 350
    dim_lin(cx0 - HALF_B, cy0 - HALF_H, cx0 - HALF_B, cy0 + HALF_H,
            cx0 - HALF_B - 1500, cy0, 90.0)     # H_coc = 350

    # ── 6. Tieu de va chu thich ──────────────────────────────────
    set_lyr("TEXT")
    TY = L_HOUSE + OVER + 1500
    msp.AddText("MAT BANG BO TRI COC",
                pt3d(B_HOUSE/2 - 2000, TY + 500), 450).Layer = "TEXT"
    msp.AddText("Nha 4x20m — 6 coc BTCT 350x350mm — Moc: goc toa do (0,0)",
                pt3d(B_HOUSE/2 - 3000, TY),       300).Layer = "TEXT"
    msp.AddText("Buoc luoi coc: 5000mm x 10000mm",
                pt3d(B_HOUSE/2 - 2000, TY - 400), 280).Layer = "TEXT"

    # ── 7. Zoom & Save ───────────────────────────────────────────
    adoc.SendCommand("ZOOM\nE\n")
    adoc.SendCommand("LAYERCLOSE\n")
    adoc.SaveAs(out_dwg)
    print(f"[DWG] Da luu: {out_dwg}")

except Exception as e:
    print(f"[LOI] {e}")
    import traceback; traceback.print_exc()

print(f"\n[HOAN THANH] {out_dwg}")
