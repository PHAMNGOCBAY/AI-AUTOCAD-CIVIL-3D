# CLAUDE.md — AI Agent Context: AutoCAD Civil 3D
> Đọc file này TRƯỚC TIÊN mỗi phiên làm việc với Civil 3D.
> Phiên bản: v1.1 | Cập nhật: 2026-05-09

---

## 1. Môi trường Phần mềm

| Thông số | Giá trị |
|---|---|
| Phần mềm | AutoCAD Civil 3D **2027** |
| Đường dẫn EXE | `C:\Program Files\Autodesk\AutoCAD 2027\acad.exe` |
| Launch Profile | `/ld "...\AecBase.dbx" /p "<<C3D_Metric>>" /product C3D /language en-US` |
| Python Runtime | CPython 3.x (CivilPython / Dynamo 2.x+) |
| API Mode | **Managed.NET** (ưu tiên) / COM (fallback) |
| MCP Server | `civil3d-mcp` — localhost:3000 |

---

## 2. Namespace .NET Quan trọng

```
Autodesk.AutoCAD.ApplicationServices   → Application, Document
Autodesk.AutoCAD.DatabaseServices      → Database, Transaction, ObjectId, OpenMode
Autodesk.AutoCAD.Geometry              → Point3d, Vector3d
Autodesk.Civil.ApplicationServices     → CivilApplication
Autodesk.Civil.DatabaseServices        → CivilDocument, Alignment, Profile,
                                          Corridor, Pipe, Structure, CogoPoint,
                                          Surface, Catchment, PressurePipe
DLLs: AcMgd.dll, AcCoreMgd.dll, AcDbMgd.dll, AeccDbMgd.dll
```

---

## 3. Transaction Pattern — BẮT BUỘC

```python
import sys, clr
clr.AddReference('AcMgd'); clr.AddReference('AcCoreMgd')
clr.AddReference('AcDbMgd'); clr.AddReference('AeccDbMgd')

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.Civil.DatabaseServices import *

doc = Application.DocumentManager.MdiActiveDocument
db  = doc.Database
civil_db = CivilDocument.GetCivilDocument(db)

with doc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        obj = tr.GetObject(some_id, OpenMode.ForRead)
        # Sửa đổi: obj.UpgradeOpen() → obj.Property = value
        tr.Commit()  # BẮT BUỘC
```

---

## 4. MCP Server (civil3d-mcp)

```json
{
  "mcpServers": {
    "civil3d": {
      "command": "node",
      "args": ["C:\\path\\to\\civil3d-mcp\\dist\\index.js"],
      "env": {
        "ACAD_EXE": "C:\\Program Files\\Autodesk\\AutoCAD 2027\\acad.exe",
        "ACAD_ARGS": "/ld \"C:\\Program Files\\Autodesk\\AutoCAD 2027\\AecBase.dbx\" /p \"<<C3D_Metric>>\" /product C3D /language en-US"
      }
    }
  }
}
```

Khi icon 🔨 xuất hiện trong AI client → MCP đã kết nối.

Luồng: **AI → MCP Server → Socket → C3D Plugin → Managed.NET API → Model**

---

## 5. Tài liệu Tham chiếu

| File | Mục đích |
|---|---|
| `docs/API_REFERENCE.md` | Bảng tra lớp .NET + phương thức Civil 3D |
| `docs/MCP_TOOLS.md` | Danh sách tool gọi qua MCP |
| `docs/PYTHON_PATTERNS.md` | Mẫu code chuẩn (copy-paste) |
| `docs/TROUBLESHOOTING.md` | Lỗi thường gặp & cách xử lý |
| `docs/PYTHON_LIBS_FEM.md` | Thư viện FEM: OpenSeesPy, PyNite, PyCBA |
| `docs/PYTHON_LIBS_DESIGN_CHECK.md` | Kiểm toán TCVN 5574:2018 & Eurocode |
| `docs/PYTHON_LIBS_GEOTECH.md` | Địa kỹ thuật: OpenPile, geofound, PySlope |
| `docs/PYTHON_LIBS_BIM_CAD.md` | BIM/CAD: pyRevit, ezdxf, pyautocad |
| `docs/PYTHON_LIBS_REPORTING.md` | Báo cáo: PyLaTeX, docxtpl, ERP |
| `workflows/WORKFLOW_ALIGNMENT.md` | Tự động hóa Bình đồ |
| `workflows/WORKFLOW_PROFILE.md` | Trắc dọc EG & FG |
| `workflows/WORKFLOW_CORRIDOR.md` | Hành lang tuyến + Assembly |
| `workflows/WORKFLOW_PIPE_GRAVITY.md` | Mạng ống trọng lực (thoát nước) |
| `workflows/WORKFLOW_PIPE_PRESSURE.md` | Mạng ống áp lực (cấp nước) |
| `workflows/WORKFLOW_RAILWAY.md` | Đường sắt: Cant, Turnout |
| `workflows/WORKFLOW_QTO.md` | Bóc tách khối lượng + Drawing Production |
| `workflows/WORKFLOW_AI_MULTIAGENT.md` | Kiến trúc AI đa tác tử (Multi-Agent) |

---

## 6. Nguyên tắc Làm việc

1. **Đọc trước khi viết**: Gọi `get_drawing_info` + `list_civil_object_types` trước khi thao tác
2. **Không xóa dữ liệu gốc**: Tạo mới, không overwrite dữ liệu khảo sát
3. **Test trên layer `AI_DRAFT`**: Xác nhận đúng mới promote lên layer chính
4. **Log thay đổi**: Ghi vào `projects/[TEN_DU_AN]/DESIGN_LOG.md`
5. **Rollback khi lỗi**: Transaction thất bại → rollback + báo exception đầy đủ
6. **Dọn dẹp sau lệnh**: Sau mỗi lệnh vẽ/sửa, BẮT BUỘC thực hiện 2 bước:
   - `doc.SendCommand('LAYERCLOSE\n')` — đóng cửa sổ Layer Properties nếu đang mở
   - `doc.SendCommand('ZOOM\nE\n')` — Zoom Extents vừa khít toàn bộ đối tượng


---

## 7. Quy tắc Quản lý File *.md

> [!IMPORTANT]
> **Giới hạn 350 dòng / file** — Mỗi file `*.md` trong hệ thống này KHÔNG được vượt quá **350 dòng**.

### Lý do
- Giữ file súc tích, dễ đọc và dễ tìm kiếm
- Đảm bảo AI đọc được toàn bộ nội dung trong một lần (tránh cắt ngữ cảnh)
- Dễ bảo trì và cập nhật

### Quy tắc xử lý khi file gần đạt giới hạn
| Tình huống | Hành động |
|---|---|
| File đạt 300+ dòng | ⚠️ Cảnh báo — cần xem xét cắt bớt |
| File đạt 350 dòng | 🔴 Bắt buộc tách thành 2 file con |
| Thêm nội dung mới | Phải tính trước: tổng dòng sau khi thêm < 350 |

### Cách tách file (khi vượt 350 dòng)
```
WORKFLOW_QTO.md (>350 dòng)
    → WORKFLOW_QTO_PART1_VOLUME.md    (Bóc tách khối lượng)
    → WORKFLOW_QTO_PART2_DRAWING.md   (Sản xuất bản vẽ)
```

### Kiểm tra số dòng hiện tại
```powershell
# Chạy lệnh này để kiểm tra tất cả file *.md
Get-ChildItem -Path "G:\My Drive\AI-AUTOCAD CIVIL 3D" -Recurse -Filter "*.md" |
ForEach-Object {
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    [PSCustomObject]@{
        File   = $_.Name
        Lines  = $lines
        Status = if($lines -gt 350){"🔴 VƯỢT GIỚI HẠN"} elseif($lines -gt 300){"⚠️ Gần giới hạn"} else {"✅ OK"}
    }
} | Sort-Object Lines -Descending | Format-Table -AutoSize
```

### Trạng thái hiện tại (2026-05-09)
| File | Dòng | Trạng thái |
|---|---|---|
| WORKFLOW_AI_MULTIAGENT.md | ~280 | ✅ OK |
| WORKFLOW_QTO.md | 252 | ✅ OK |
| PYTHON_LIBS_FEM.md | ~230 | ✅ OK |
| PYTHON_LIBS_REPORTING.md | ~220 | ✅ OK |
| WORKFLOW_RAILWAY.md | 284 | ⚠️ Gần giới hạn |
| PYTHON_LIBS_GEOTECH.md | ~215 | ✅ OK |
| PYTHON_LIBS_BIM_CAD.md | ~210 | ✅ OK |
| PYTHON_PATTERNS.md | 197 | ✅ OK |
| PYTHON_LIBS_DESIGN_CHECK.md | ~195 | ✅ OK |
| WORKFLOW_PIPE_GRAVITY.md | 235 | ✅ OK |
| MCP_TOOLS.md | 179 | ✅ OK |
| WORKFLOW_PIPE_PRESSURE.md | 173 | ✅ OK |
| WORKFLOW_PROFILE.md | 211 | ✅ OK |
| WORKFLOW_CORRIDOR.md | 148 | ✅ OK |
| WORKFLOW_ALIGNMENT.md | 148 | ✅ OK |
| API_REFERENCE.md | 118 | ✅ OK |
| TROUBLESHOOTING.md | 117 | ✅ OK |
| CLAUDE.md | ~200 | ✅ OK |

---

## 8. Nhật ký Phiên làm việc

> Xem chi tiết tại: `SESSION_LOG.md`
> AI Agent ghi tóm tắt vào đây sau mỗi phiên làm việc.

| Phiên | Ngày | Nội dung chính | Kết quả |
|---|---|---|---|
| #001 | 2026-05-09 | Khởi tạo toàn bộ hệ thống 12 file *.md | ✅ Hoàn thành |
| #002 | 2026-05-09 | Cập nhật Civil 3D 2024 → 2027, launch args | ✅ Hoàn thành |
| #003 | 2026-05-09 | Thêm quy tắc 350 dòng, tạo SESSION_LOG.md | ✅ Hoàn thành |
| #004 | 2026-05-09 | Tạo 5 file mới từ PNAY-PYTHON FOR CIVIL.docx: FEM, Design Check, Geotech, BIM/CAD, Reporting (PyLaTeX) + Workflow AI MultiAgent | ✅ Hoàn thành |

