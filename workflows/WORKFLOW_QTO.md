# WORKFLOW_QTO.md — Bóc tách Khối lượng & Sản xuất Bản vẽ Hàng loạt
> Civil 3D **2027** | Python Managed.NET + Sheet Set Manager | 2026-05-09

---

## Mục đích

Tự động hóa hai quy trình cuối cùng trong vòng đời thiết kế:
1. **Bóc tách Khối lượng (QTO)** — từ mô hình 3D sang hồ sơ dự toán 5D
2. **Sản xuất Bản vẽ hàng loạt** — Plan-Profile Sheets tự động không lỗi format

---

## PHẦN A: Bóc tách Khối lượng (Quantity Takeoff)

### Kiến trúc QTO trong Civil 3D

```
Đối tượng hình học (Corridor, Pipe, Surface, Solid3D)
    ↓ Gán Pay Item Code (mã định mức)
QTO Manager (ATT + CSV + XML catalog)
    ↓ AeccTakeoff (lệnh nội bộ)
Bảng khối lượng (Material Volume Report)
    ↓ Handle ID + giá trị
Excel / OpenBIM Dashboard
```

---

### A1: Trích xuất Khối lượng Đào-Đắp từ Corridor

```python
import pandas as pd

volumes = []

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        corridor = tr.GetObject(corridor_id, OpenMode.ForRead)
        baseline = corridor.Baselines[0]

        # Tạo Material Volumes Report
        material_volume_ids = corridor.MaterialVolumeIds
        for mv_id in material_volume_ids:
            mv = tr.GetObject(mv_id, OpenMode.ForRead)
            print(f"Vật liệu: {mv.Name}")
            print(f"  V_đào (Cut)  = {mv.CutVolume:,.2f} m³")
            print(f"  V_đắp (Fill) = {mv.FillVolume:,.2f} m³")
            print(f"  Net          = {mv.NetVolume:,.2f} m³")
            volumes.append({
                'Material':      mv.Name,
                'Cut_m3':        mv.CutVolume,
                'Fill_m3':       mv.FillVolume,
                'Net_m3':        mv.NetVolume
            })

        tr.Commit()

df_vol = pd.DataFrame(volumes)
df_vol.to_excel(r'G:\output\khoi_luong_dao_dap.xlsx', index=False)
print(f"[OK] Xuất bảng đào đắp: {len(volumes)} loại vật liệu")
```

---

### A2: Gán Pay Item Code tự động

```python
# Pay Item = mã định mức chi phí (VD: "01.01.01 - Đào đất cấp I")

# Đọc file định mức từ CSV
import csv

pay_items_csv = r'G:\templates\pay_items_catalog.csv'
# Cột: [PayItemCode, Description, Unit, ObjectType, KeyProperty, KeyValue]

pay_item_map = {}
with open(pay_items_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['ObjectType'], row['KeyProperty'], row['KeyValue'])
        pay_item_map[key] = row['PayItemCode']

# Gán vào đối tượng Civil 3D
with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Gán cho Pipe Network
        for net_id in civil_db.GetPipeNetworkIds():
            net = tr.GetObject(net_id, OpenMode.ForRead)
            for pipe_id in net.GetPipeIds():
                p = tr.GetObject(pipe_id, OpenMode.ForWrite)
                D_mm = int(p.InnerDiameterOrWidth * 1000)
                key  = ('Pipe', 'Diameter', str(D_mm))
                if key in pay_item_map:
                    p.PayItemCodes.Add(pay_item_map[key])

        # Gán cho Corridor Materials
        corridor = tr.GetObject(corridor_id, OpenMode.ForWrite)
        for mat in corridor.CorridorSurfaces:
            key = ('CorridorSurface', 'Name', mat.Name)
            if key in pay_item_map:
                mat.PayItemCode = pay_item_map[key]

        tr.Commit()
        print("[OK] Gán Pay Item Code hoàn tất")
```

---

### A3: Kích hoạt AeccTakeoff và Xuất Hàng loạt

```python
# AeccTakeoff là lệnh nội bộ Civil 3D để tổng hợp khối lượng

import subprocess, os

def run_aecctakeoff_export(dwg_folder: str, output_folder: str):
    """
    Duyệt tất cả file DWG trong thư mục, xuất QTO mà không cần mở GUI.
    Sử dụng AutoCAD Scripts (.scr).
    """
    script_lines = [
        '_QNEW',                    # Bản vẽ mới
        f'_OPEN "{dwg_folder}"',    # Mở folder
        '_AECCTAKEOFF',             # Kích hoạt QTO
        '_EXPORT CSV',              # Xuất CSV
        f'"{output_folder}\\qto_export.csv"',
        '_CLOSE',
    ]

    script_path = r'G:\scripts\run_qto.scr'
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))

    # Chạy AutoCAD 2027 với script (batch mode)
    acad_exe = r'C:\Program Files\Autodesk\AutoCAD 2027\acad.exe'
    acad_args = [
        acad_exe,
        '/ld', r'C:\Program Files\Autodesk\AutoCAD 2027\AecBase.dbx',
        '/p', '<<C3D_Metric>>',
        '/product', 'C3D',
        '/language', 'en-US',
        '/b', script_path
    ]
    subprocess.run(acad_args, timeout=300)
    print(f"[OK] QTO xuất ra: {output_folder}")

# Xuất đồng loạt nhiều file DWG
dwg_folder    = r'G:\DuAnA\BanVe'
output_folder = r'G:\DuAnA\KhoiLuong'
run_aecctakeoff_export(dwg_folder, output_folder)
```

---

### A4: Tạo Dashboard Khối lượng (Plotly Web)

```python
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

df = pd.read_excel(r'G:\output\khoi_luong_dao_dap.xlsx')

fig = go.Figure()

fig.add_trace(go.Bar(
    name='Khối lượng Đào (m³)',
    x=df['Material'],
    y=df['Cut_m3'],
    marker_color='#EF4444'
))
fig.add_trace(go.Bar(
    name='Khối lượng Đắp (m³)',
    x=df['Material'],
    y=df['Fill_m3'],
    marker_color='#3B82F6'
))

fig.update_layout(
    title='Bảng Khối lượng Đào - Đắp theo Vật liệu',
    barmode='group',
    xaxis_title='Loại Vật liệu',
    yaxis_title='Khối lượng (m³)',
    template='plotly_dark'
)

fig.write_html(r'G:\output\dashboard_khoi_luong.html')
print("[OK] Tạo dashboard web: dashboard_khoi_luong.html")
```

---

## PHẦN B: Sản xuất Bản vẽ Hàng loạt (Drawing Production)

### B1: Tạo Plan-Profile Sheets tự động qua Sheet Set Manager

```python
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.Civil.DatabaseServices import *

# Mỗi Sheet = 1 khung bình đồ + 1 khung trắc dọc
SHEET_LENGTH_M = 200.0   # Mỗi tờ chứa 200m tuyến đường
SCALE_PLAN     = 1000    # Tỉ lệ 1:1000
SCALE_PROFILE  = 100     # Tỉ lệ 1:100 (dọc) × 1:1000 (ngang)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        align = tr.GetObject(align_id, OpenMode.ForRead)

        total_length = align.Length
        n_sheets     = int(total_length / SHEET_LENGTH_M) + 1

        for i in range(n_sheets):
            sta_start = align.StartingStation + i * SHEET_LENGTH_M
            sta_end   = min(sta_start + SHEET_LENGTH_M, align.EndingStation)

            sheet_name = f"PL-PD-{i+1:03d}"
            print(f"  Tạo sheet {sheet_name}: KM{sta_start/1000:.3f}~KM{sta_end/1000:.3f}")

            # Tạo View Frame
            # (Trong thực tế dùng ViewFrameGroup.Create() của Civil 3D API)
            # Tạm dùng script để gọi lệnh CreateSheetsCmd
            # view_frame_id = ViewFrameGroup.Create(align_id, sta_start, sta_end, ...)

        tr.Commit()
        print(f"[OK] Sẽ tạo {n_sheets} tờ bản vẽ Plan-Profile")
```

---

### B2: Sửa lỗi Format Hàng loạt (tỉ lệ, màu sắc, data fragments)

```python
# Các lỗi thường gặp khi CreateViewFrames thủ công:
# 1. Zoom Extended sai → sửa bằng script
# 2. Màu sắc không đồng nhất giữa Layout
# 3. Phân mảnh dữ liệu tại điểm gãy Sheet

def fix_layout_viewports(doc):
    """Chuẩn hóa tỉ lệ và màu sắc toàn bộ Layout trong bản vẽ."""
    db = doc.Database
    with doc.LockDocument():
        with db.TransactionManager.StartTransaction() as tr:
            layout_dict = db.LayoutDictionaryId
            layout_table = tr.GetObject(layout_dict, OpenMode.ForRead)

            for layout_id in layout_table:
                layout = tr.GetObject(layout_id, OpenMode.ForWrite)
                if layout.LayoutName == "Model":
                    continue

                # Duyệt tất cả Viewport trong Layout
                for vp_id in layout.GetViewports():
                    vp = tr.GetObject(vp_id, OpenMode.ForWrite)
                    if vp is None:
                        continue

                    # Fix tỉ lệ theo loại viewport (Plan / Profile)
                    if "PLAN" in layout.LayoutName.upper():
                        vp.CustomScale = 1.0 / SCALE_PLAN
                    else:
                        vp.CustomScale = 1.0 / SCALE_PROFILE

                    # Fix màu nền
                    vp.ColorIndex = 7  # Màu trắng (chuẩn in)

            tr.Commit()
    print("[OK] Chuẩn hóa Viewport toàn bộ Layout")

fix_layout_viewports(doc)
```

---

### B3: Xuất PDF hàng loạt

```python
import subprocess

def xuat_pdf_hang_loat(dwg_path: str, output_folder: str):
    """Xuất tất cả Layout sang PDF dùng AutoCAD 2027 Publish."""
    script = f"""
_PUBLISH
"""
    script_path = r'G:\scripts\publish_pdf.scr'
    with open(script_path, 'w') as f:
        f.write(script)

    acad_exe  = r'C:\Program Files\Autodesk\AutoCAD 2027\acad.exe'
    acad_args = [
        acad_exe, dwg_path,
        '/ld', r'C:\Program Files\Autodesk\AutoCAD 2027\AecBase.dbx',
        '/p', '<<C3D_Metric>>',
        '/product', 'C3D',
        '/language', 'en-US',
        '/b', script_path
    ]
    subprocess.run(acad_args, timeout=600)
    print(f"[OK] Xuất PDF hàng loạt → {output_folder}")

xuat_pdf_hang_loat(
    r'G:\DuAnA\BanVe\main_drawing.dwg',
    r'G:\DuAnA\PDF_Output'
)
```

---

## Checklist QTO & Bản vẽ

**Khối lượng**
- [ ] Tổng V_đào / V_đắp trong phạm vi ±20% (cân bằng hợp lý)
- [ ] Pay Item Code gán đủ cho 100% đối tượng
- [ ] So sánh kết quả với bảng tính thủ công (±5%)

**Bản vẽ**
- [ ] Số lượng tờ bản vẽ khớp với chiều dài tuyến
- [ ] Tỉ lệ đúng: Plan 1:1000, Profile 1:100/1:1000
- [ ] Không có khoảng trống dữ liệu tại ranh giới tờ bản vẽ
- [ ] Bảng thống kê đặt đúng vị trí, font đúng chuẩn
- [ ] File PDF không bị vỡ font tiếng Việt
