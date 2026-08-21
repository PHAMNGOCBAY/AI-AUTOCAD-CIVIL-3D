# AI-AutoCAD Civil 3D

Bộ công cụ tự động hóa AutoCAD Civil 3D 2027 bằng AI (Claude) thông qua MCP
(Model Context Protocol), kết hợp Managed .NET API / CivilPython, cùng các
script phân tích kết cấu, địa kỹ thuật và GIS.

> Xem [CLAUDE.md](CLAUDE.md) để biết ngữ cảnh đầy đủ dành cho AI agent khi
> làm việc với dự án này.

## Cấu trúc thư mục

```
.
├── civil3d_mcp_server/   # MCP server kết nối AI ↔ Civil 3D (localhost:3000)
├── docs/                 # Tài liệu tham chiếu API, mẫu code, xử lý lỗi
├── workflows/            # Quy trình tự động hóa (Alignment, Profile, Corridor, Pipe, QTO...)
├── scripts/              # Script kết cấu (dầm, cọc, mặt đứng...)
├── tools/                # Công cụ đồng bộ dữ liệu BIM, kiểm tra quy hoạch
├── projects/             # Dữ liệu từng dự án (bản vẽ, log thiết kế - phần lớn bị .gitignore)
└── requirements.txt      # Thư viện Python cần thiết
```

## Yêu cầu môi trường

| Thành phần | Giá trị |
|---|---|
| Phần mềm | AutoCAD Civil 3D 2027 |
| Python | CPython 3.x |
| API | Managed .NET (ưu tiên) / COM (fallback) |

## Cài đặt

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## MCP Server

Cấu hình MCP server trỏ tới `civil3d_mcp_server/server.py` (xem mẫu trong
`CLAUDE.md` mục 4). File cấu hình cục bộ `.agents/mcp_config.json` chứa
đường dẫn máy cục bộ nên không được commit lên repo.

## Ghi chú

- File bản vẽ (`.dwg`, `.dxf`), dữ liệu sinh ra (`.sqlite`, shapefile,
  `.geojson`, hình ảnh) và tài liệu Office (`.xlsx`, `.docx`, `.pdf`) được
  loại trừ khỏi repo qua `.gitignore` vì là dữ liệu/kết quả có thể tái tạo
  hoặc dung lượng lớn. Chỉ mã nguồn và tài liệu Markdown được theo dõi.
- Nhật ký phiên làm việc: [SESSION_LOG.md](SESSION_LOG.md).
