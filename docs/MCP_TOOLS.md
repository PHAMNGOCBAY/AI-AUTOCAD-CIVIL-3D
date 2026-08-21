# MCP_TOOLS.md — Danh sách Tool MCP civil3d-mcp
> MCP Server: civil3d-mcp | Phiên bản: C3D **2027** | 2026-05-09

---

## Tổng quan Kiến trúc MCP

```
AI Client (Claude / Antigravity)
    │ Ngôn ngữ tự nhiên
    ▼
MCP Server: civil3d-mcp (Node.js, localhost:3000)
    │ Socket JSON → CommandManager → SocketService
    ▼
Civil 3D Plugin Add-in (chạy ngầm trong C3D process)
    │ Managed.NET API → TransactionManager
    ▼
Civil 3D Model Database
    │ ExecuteResult (JSON)
    ▲
Báo cáo về AI
```

---

## Kiểm tra Kết nối

```bash
# Khởi động MCP Server
node C:\path\to\civil3d-mcp\dist\index.js

# Xác nhận: icon 🔨 xuất hiện trong Claude Desktop / Antigravity
# Test nhanh: gọi tool get_drawing_info → phải trả về metadata bản vẽ
```

---

## Danh sách Tool MCP — Nhóm Truy vấn (Read)

### `get_drawing_info`
**Mô tả**: Lấy metadata bản vẽ Civil 3D đang mở.
```json
Input:  {}
Output: {
  "drawing_name": "DuAnA_ThietKe.dwg",
  "units": "Meters",
  "coordinate_system": "VN2000",
  "extents": {"min": [x,y,z], "max": [x,y,z]},
  "civil3d_version": "2024"
}
```

### `list_civil_object_types`
**Mô tả**: Liệt kê các loại đối tượng Civil có trong model.
```json
Input:  {}
Output: {
  "alignments": ["AL-1", "AL-2"],
  "surfaces": ["EG", "FG"],
  "profiles": ["EG Profile", "FG Design"],
  "corridors": ["Corridor-1"],
  "pipe_networks": ["Drainage-North"],
  "pressure_networks": ["Water-Main"]
}
```

### `get_selected_civil_objects_info`
**Mô tả**: Phân tích sâu thuộc tính geometry của đối tượng được chọn.
```json
Input:  {"object_handle_ids": ["1A3F", "2B40"]}
Output: {
  "objects": [
    {
      "handle": "1A3F",
      "type": "Pipe",
      "start_invert": 12.45,
      "end_invert": 12.10,
      "slope": 0.0035,
      "diameter": 0.6,
      "length": 100.0
    }
  ]
}
```

### `get_alignment_stations`
**Mô tả**: Lấy danh sách lý trình + tọa độ của một Alignment.
```json
Input:  {"alignment_name": "AL-1", "interval": 20.0}
Output: {
  "stations": [
    {"station": 0.0,  "easting": 587000.0, "northing": 2345000.0},
    {"station": 20.0, "easting": 587015.3, "northing": 2345018.7}
  ]
}
```

### `get_surface_elevation`
**Mô tả**: Lấy cao độ tại tọa độ XY trên bề mặt TIN.
```json
Input:  {"surface_name": "EG", "x": 587000.0, "y": 2345000.0}
Output: {"elevation": 45.32}
```

### `get_pipe_network_summary`
**Mô tả**: Tổng hợp toàn bộ thông tin mạng lưới ống.
```json
Input:  {"network_name": "Drainage-North"}
Output: {
  "total_pipes": 45,
  "total_structures": 23,
  "pipes": [...],
  "structures": [...]
}
```

---

## Danh sách Tool MCP — Nhóm Tạo Mới (Create)

### `create_cogo_point`
**Mô tả**: Tạo điểm COGO từ tọa độ.
```json
Input:  {"x": 587100.0, "y": 2345200.0, "z": 45.5, "description": "KM0+100"}
Output: {"handle_id": "3C12", "point_number": 101}
```

### `create_line_segment`
**Mô tả**: Tạo đoạn thẳng cấu trúc.
```json
Input:  {
  "start_point": [587000, 2345000, 45.0],
  "end_point":   [587100, 2345050, 44.5],
  "layer": "AI_DRAFT"
}
Output: {"handle_id": "4D55"}
```

### `create_alignment_from_points`
**Mô tả**: Tạo Bình đồ từ mảng điểm tọa độ.
```json
Input:  {
  "name": "AL-TU_DONG",
  "points": [[e1,n1],[e2,n2],[e3,n3]],
  "site_name": "Site 1",
  "layer": "C-ROAD-CNTR"
}
Output: {"alignment_id": "5E67", "length": 1234.5}
```

### `create_profile_from_surface`
**Mô tả**: Cắt trắc dọc tự nhiên (EG) từ bề mặt theo Alignment.
```json
Input:  {"alignment_name": "AL-1", "surface_name": "EG"}
Output: {"profile_id": "6F78", "name": "EG - AL-1"}
```

---

## Danh sách Tool MCP — Nhóm Thực thi (Execute)

### `execute_python_script`
**Mô tả**: Thực thi đoạn Python qua CivilPython trực tiếp trong Civil 3D.
```json
Input:  {
  "script": "import clr\n...\nprint(civil_db.GetAlignmentIds().Count)"
}
Output: {
  "stdout": "5",
  "stderr": "",
  "execution_time_ms": 120
}
```

### `export_quantity_takeoff`
**Mô tả**: Xuất khối lượng QTO ra file.
```json
Input:  {
  "output_format": "csv",
  "output_path": "G:\\output\\qto_report.csv"
}
Output: {"success": true, "rows_exported": 342}
```

### `rebuild_corridor`
**Mô tả**: Rebuild Corridor sau khi thay đổi Alignment/Profile.
```json
Input:  {"corridor_name": "Corridor-1"}
Output: {"success": true, "rebuild_time_ms": 3200}
```

---

## Quy tắc Sử dụng Tool

1. **Luôn gọi `get_drawing_info` đầu tiên** trong mỗi phiên làm việc
2. **Luôn gọi `list_civil_object_types`** trước khi tạo/sửa đổi đối tượng
3. **Dùng `execute_python_script` thận trọng**: Bao giờ cũng gói trong Transaction
4. **Đặt layer `AI_DRAFT`** cho mọi đối tượng AI tạo ra (để dễ xóa nếu cần)
5. **Đối với thao tác ghi**: Xác nhận với người dùng trước khi Commit

---

## Xử lý Lỗi MCP

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `CONNECTION_REFUSED` | MCP Server chưa khởi động | Chạy `node dist/index.js` |
| `PLUGIN_NOT_LOADED` | Add-in chưa load trong C3D | Vào C3D → APPLOAD → civil3d-mcp-plugin.dll |
| `TRANSACTION_FAILED` | Xung đột Document Lock | Đóng lệnh đang chạy trong C3D, thử lại |
| `OBJECT_NOT_FOUND` | Handle ID không tồn tại | Gọi `list_civil_object_types` để làm mới |
