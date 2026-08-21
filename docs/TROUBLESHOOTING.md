# TROUBLESHOOTING.md — Lỗi Thường Gặp & Cách Xử lý
> Civil 3D **2027** | Python Managed.NET | MCP civil3d-mcp | 2026-05-09

---

## 1. Lỗi Python / Transaction

### `eNotOpenForWrite`
```
Autodesk.AutoCAD.Runtime.Exception: eNotOpenForWrite
```
**Nguyên nhân**: Cố ghi vào đối tượng đang ở chế độ `ForRead`.
**Fix**:
```python
obj = tr.GetObject(obj_id, OpenMode.ForWrite)  # Đúng
# Hoặc nếu đã mở ForRead:
obj.UpgradeOpen()
```

### `DocumentLockViolation`
**Nguyên nhân**: Thao tác ghi không có `LockDocument()`.
**Fix**: Luôn bọc trong `with doc.LockDocument():`.

### `eWasErased`
**Nguyên nhân**: Đối tượng đã bị xóa khỏi database.
**Fix**:
```python
obj = tr.GetObject(obj_id, OpenMode.ForRead)
if not obj.IsErased:
    # Xử lý tiếp
```

### `NullReferenceException` trên Collection
**Nguyên nhân**: Collection rỗng, cố truy cập `[0]`.
**Fix**:
```python
ids = civil_db.GetAlignmentIds()
if ids.Count > 0:
    align = tr.GetObject(ids[0], OpenMode.ForRead)
```

---

## 2. Lỗi COM API (pywin32)

### `WallThickness` trả về lỗi
**Nguyên nhân**: COM không có quyền truy cập thuộc tính chuyên sâu của Civil 3D.
**Fix**: Chuyển sang **Managed.NET API** qua Dynamo / CivilPython.

### `AttributeError: IronPython does not support ...`
**Nguyên nhân**: Script đang chạy trên IronPython 2.7 (C3D 2020/2021).
**Fix**: C3D **2027** dùng CPython 3.x — không còn vấn đề này. Nếu vẫn bị: kiểm tra Dynamo version ≥ 2.x.

---

## 3. Lỗi MCP Server

### `CONNECTION_REFUSED` (localhost:3000)
**Nguyên nhân**: MCP Server chưa khởi động.
**Fix**:
```bash
cd C:\path\to\civil3d-mcp
node dist\index.js
```

### `PLUGIN_NOT_LOADED`
**Nguyên nhân**: Add-in `civil3d-mcp-plugin.dll` chưa được load trong Civil 3D.
**Fix**:
1. Trong Civil 3D: gõ lệnh `APPLOAD`
2. Browse đến `civil3d-mcp-plugin.dll`
3. Hoặc đặt vào thư mục `C:\Users\[User]\AppData\Roaming\Autodesk\ApplicationPlugins`

### `TRANSACTION_FAILED` từ MCP
**Nguyên nhân**: Có lệnh khác đang chạy trong Civil 3D (Document Lock bị chiếm).
**Fix**: Nhấn `Esc` trong Civil 3D để thoát lệnh hiện tại → thử lại.

### `OBJECT_NOT_FOUND` (Handle ID)
**Nguyên nhân**: Handle ID không còn hợp lệ (đối tượng bị xóa hoặc Undo).
**Fix**: Gọi lại `list_civil_object_types` để làm mới danh sách ID.

---

## 4. Lỗi Dữ liệu / Geometry

### Alignment tạo ra nhưng không hiển thị
**Nguyên nhân**: Layer bị frozen hoặc tắt.
**Fix**:
```python
layer_id = db.LayerZero  # Dùng Layer 0 để chắc chắn hiển thị
# Hoặc tạo layer mới và đảm bảo không freeze
```

### Bề mặt TIN bị lỗi hình học (Surface error)
**Nguyên nhân**: Điểm trùng tọa độ, breakline cắt nhau.
**Fix**:
```python
surface.Rebuild()  # Rebuild sau khi thêm dữ liệu
# Kiểm tra: surface.BoundingBox có hợp lệ không
```

### Profile không cắt được với Surface
**Nguyên nhân**: Alignment nằm ngoài giới hạn Surface.
**Fix**: Kiểm tra extents của Surface và Alignment có giao nhau không.

---

## 5. Lỗi Hiệu suất

### Script chạy chậm (>30 giây)
**Nguyên nhân**: Mở nhiều Transaction lồng nhau, hoặc dùng COM thay Managed.NET.
**Fix**:
- Dùng **một Transaction duy nhất** cho toàn bộ batch
- Tránh `Rebuild()` ở mỗi vòng lặp — chỉ Rebuild một lần sau khi xong
- Dùng `Managed.NET` thay COM

### Civil 3D bị đứng (Freeze)
**Nguyên nhân**: Transaction giữ Document Lock quá lâu.
**Fix**: Chia nhỏ batch thành chunks 500-1000 đối tượng / Transaction.

---

## 6. Lỗi Đường sắt (Railway)

### `CANTCriticalStationCollection` trống
**Nguyên nhân**: Alignment không có phần tử đường cong (chỉ có đoạn thẳng).
**Fix**: Đảm bảo Alignment có `HorizontalCurve` trước khi truy cập CANT.

### Turnout không load được
**Nguyên nhân**: File JSON Turnout Catalog bị lỗi cú pháp.
**Fix**:
```bash
# Validate JSON file
python -c "import json; json.load(open('TurnoutName.json', encoding='utf-8'))"
# Đường dẫn catalog Civil 3D 2027:
# C:\ProgramData\Autodesk\C3D 2027\enu\Data\Railway Design Standards\Turnout\
```

---

## 7. Kiểm tra Phiên bản Python trong Dynamo

```python
# Chạy trong Dynamo Python Node để xác nhận runtime
import sys
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
# Civil 3D 2027 → CPython 3.x (OK để dùng pandas, numpy, geopandas, scipy)
# Nếu hiển thị IronPython → Dynamo cũ — cập nhật Dynamo lên phiên bản mới nhất
```
