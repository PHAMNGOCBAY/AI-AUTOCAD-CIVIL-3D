# PYTHON_LIBS_BIM_CAD.md — Thư viện Python: BIM & CAD Automation
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Tổng quan

| Công cụ | Phạm vi | Môi trường |
|---|---|---|
| `pyRevit` / `RevitPythonShell` | Tự động hóa Revit BIM | Trong Revit (IronPython) |
| `ezdxf` | Tạo/sửa file DXF/DWG độc lập | Không cần AutoCAD |
| `pyautocad` | Điều khiển AutoCAD đang mở | ActiveX/COM Automation |

---

## 1. pyRevit — Tự động hóa Revit

### Ứng dụng: Mô hình hóa Cốt thép 3D (3D Rebar Detailing)

```python
# Chạy trong môi trường pyRevit / RevitPythonShell
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

def dat_cot_thep_dam(element_id, As_req_mm2, bar_dia_mm=20):
    """
    Tự động bố trí cốt thép dọc cho dầm từ kết quả kiểm toán.
    As_req_mm2: Diện tích thép yêu cầu (mm²)
    bar_dia_mm: Đường kính thanh thép (mm)
    """
    import math

    A_1bar = math.pi * (bar_dia_mm/2)**2  # mm²
    n_bars = math.ceil(As_req_mm2 / A_1bar)

    with Transaction(doc, f"Đặt {n_bars}Ø{bar_dia_mm} vào dầm") as tx:
        tx.Start()

        element = doc.GetElement(ElementId(element_id))
        host_face = element.GetGeneratingElementIds()[0]

        # Lấy RebarBarType (Ø20)
        rebar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()
        bar_type = next(
            (t for t in rebar_types if
             abs(t.BarDiameter * 304.8 - bar_dia_mm) < 1),
            None
        )

        if bar_type is None:
            print(f"[WARN] Không tìm thấy RebarBarType Ø{bar_dia_mm}mm")
            tx.RollBack()
            return

        # Khai báo tọa độ thanh thép (vị trí cover=40mm)
        cover = 40 / 304.8  # Convert mm → feet (Revit units)
        bb = element.get_BoundingBox(None)
        z_bot = bb.Min.Z + cover

        for i in range(n_bars):
            spacing = (bb.Max.X - bb.Min.X - 2*cover) / max(n_bars-1, 1)
            x = bb.Min.X + cover + i * spacing

            pt_start = XYZ(x, bb.Min.Y + cover, z_bot)
            pt_end   = XYZ(x, bb.Max.Y - cover, z_bot)
            curve    = Line.CreateBound(pt_start, pt_end)

            rebar = Rebar.CreateFromCurves(
                doc,
                RebarStyle.Standard,
                bar_type,
                None, None,
                element,
                XYZ(0, 0, 1),  # Normal
                [curve],
                RebarHookOrientation.Left,
                RebarHookOrientation.Right,
                True, True
            )

        tx.Commit()
        print(f"[OK] Đặt {n_bars}Ø{bar_dia_mm} — As={n_bars*A_1bar:.0f}mm² ≥ {As_req_mm2:.0f}mm²")

# Gọi hàm
dat_cot_thep_dam(element_id=12345, As_req_mm2=1500)
```

### Ứng dụng: Quản trị BIM hàng loạt
```python
# Đồng nhất hóa TextNoteTypes trong toàn bộ dự án
with Transaction(doc, "Dọn dẹp Text Styles") as tx:
    tx.Start()

    all_text_types = FilteredElementCollector(doc)\
        .OfClass(TextNoteType)\
        .ToElements()

    # Giữ lại chỉ style chuẩn "Arial 2.5mm"
    standard_type = next(
        (t for t in all_text_types if "Arial 2.5mm" in t.Name), None
    )

    text_notes = FilteredElementCollector(doc)\
        .OfClass(TextNote)\
        .ToElements()

    for note in text_notes:
        if note.TextNoteType.Id != standard_type.Id:
            note.TextNoteType = standard_type

    tx.Commit()
    print(f"[OK] Đồng nhất hóa {len(text_notes)} TextNote")
```

---

## 2. ezdxf — Tạo Bản vẽ DXF Độc lập

> **Không cần cài AutoCAD** — chạy trực tiếp từ Python

### Tạo chi tiết cốt thép dầm từ kết quả tính toán
```python
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math

def tao_ban_ve_cot_thep_dam(
    ten_dam: str,
    B_mm: float, H_mm: float,
    As_bot_mm2: float,
    As_top_mm2: float,
    bar_dia: int = 20,
    output_path: str = None
):
    """Tự động sinh bản vẽ chi tiết cốt thép dầm (file .dxf)"""

    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # ---- Thiết lập Layer ----
    layers = {
        'BT': ('CONCRETE', ezdxf.colors.YELLOW),
        'THEP': ('REBAR', ezdxf.colors.RED),
        'DIM': ('DIMENSION', ezdxf.colors.CYAN),
        'TEXT': ('TEXT', ezdxf.colors.WHITE),
    }
    for code, (name, color) in layers.items():
        doc.layers.new(name=name, dxfattribs={'color': color})

    # ---- Vẽ tiết diện dầm ----
    cover = 40  # mm
    pts = [(0,0), (B_mm,0), (B_mm,H_mm), (0,H_mm), (0,0)]
    msp.add_lwpolyline(pts, dxfattribs={'layer': 'CONCRETE'})

    # ---- Vẽ cốt thép dọc (dưới) ----
    A_1bar = math.pi * (bar_dia/2)**2
    n_bot = math.ceil(As_bot_mm2 / A_1bar)
    spacing_bot = (B_mm - 2*cover) / max(n_bot-1, 1)
    for i in range(n_bot):
        cx = cover + i * spacing_bot
        cy = cover
        msp.add_circle(
            center=(cx, cy), radius=bar_dia/2,
            dxfattribs={'layer': 'REBAR'}
        )
        msp.add_hatch(
            color=1,  # Đỏ
            dxfattribs={'layer': 'REBAR'}
        ).paths.add_ellipse_path(
            center=(cx, cy), major_axis=(bar_dia/2, 0), ratio=1.0
        )

    # ---- Vẽ cốt thép dọc (trên) ----
    n_top = math.ceil(As_top_mm2 / A_1bar)
    spacing_top = (B_mm - 2*cover) / max(n_top-1, 1)
    for i in range(n_top):
        cx = cover + i * spacing_top
        cy = H_mm - cover
        msp.add_circle(
            center=(cx, cy), radius=bar_dia/2,
            dxfattribs={'layer': 'REBAR'}
        )

    # ---- Ghi chú ----
    msp.add_text(
        f"{ten_dam}: {B_mm}x{H_mm}mm",
        dxfattribs={'layer': 'TEXT', 'height': 15}
    ).set_placement((B_mm/2, H_mm + 30), align=TextEntityAlignment.CENTER)

    msp.add_text(
        f"Bot: {n_bot}Ø{bar_dia} (As={n_bot*A_1bar:.0f}mm²)",
        dxfattribs={'layer': 'TEXT', 'height': 10}
    ).set_placement((B_mm/2, -20), align=TextEntityAlignment.CENTER)

    # ---- Xuất file ----
    if output_path is None:
        output_path = f"output/{ten_dam}_detail.dxf"
    doc.saveas(output_path)
    print(f"[OK] Xuất bản vẽ: {output_path}")

# Gọi hàm
tao_ban_ve_cot_thep_dam(
    ten_dam="D1-B1",
    B_mm=300, H_mm=600,
    As_bot_mm2=1520,   # Từ kết quả kiểm toán EurocodePy
    As_top_mm2=760,
    bar_dia=20,
    output_path="output/D1-B1_detail.dxf"
)
```

---

## 3. pyautocad — Điều khiển AutoCAD Đang mở

```python
from pyautocad import Autocad, APoint

acad = Autocad(create_if_not_exists=True)
acad.prompt("Kết nối AutoCAD thành công!\n")

# Vẽ lưới trục (Grid Lines)
cols = ['A', 'B', 'C', 'D']
rows = [1, 2, 3, 4, 5]
span_x = 6000   # mm
span_y = 8000   # mm

for i, col in enumerate(cols):
    x = i * span_x
    # Vẽ đường trục cột
    acad.model.AddLine(
        APoint(x, 0, 0),
        APoint(x, len(rows)*span_y, 0)
    )
    # Ký hiệu trục
    txt = acad.model.AddText(col, APoint(x, -500, 0), 300)
    txt.Layer = "AXIS"

for j, row in enumerate(rows):
    y = j * span_y
    acad.model.AddLine(
        APoint(0, y, 0),
        APoint(len(cols)*span_x, y, 0)
    )
    acad.model.AddText(str(row), APoint(-500, y, 0), 300)

print(f"[OK] Vẽ lưới trục {len(cols)}x{len(rows)} vào AutoCAD")

# Xuất khối lượng thép sang Excel
import xlwings as xw
wb = xw.Book()
ws = wb.sheets[0]
ws["A1"].value = "Tên cấu kiện"
ws["B1"].value = "Đường kính (mm)"
ws["C1"].value = "Diện tích (mm²)"
# ... (điền dữ liệu từ model)
wb.save("output/khoi_luong_thep.xlsx")
```

---

## Checklist BIM & CAD

- [ ] ezdxf: Phân Layer rõ ràng (CONCRETE / REBAR / DIMENSION / TEXT)
- [ ] ezdxf: Lưu file `.dxf` vào thư mục `output/` trước khi mở AutoCAD
- [ ] pyRevit: Dùng `Transaction` — không quên `tx.Commit()`
- [ ] pyRevit: Kiểm tra đơn vị (Revit dùng **feet**, phải convert mm÷304.8)
- [ ] pyautocad: Đặt Layer trước khi vẽ (`obj.Layer = "AXIS"`)
- [ ] Kết hợp ezdxf + XREF cho bản vẽ phức hợp nhiều tầng
