# PROJECT_INFO.md — Thông tin Dự án
> Template: Copy thư mục `_TEMPLATE` → đổi tên theo tên dự án thực tế

---

## Thông tin Chung

| Trường | Giá trị |
|---|---|
| **Tên dự án** | [TÊN DỰ ÁN ĐẦY ĐỦ] |
| **Mã số dự án** | [DU-AN-2026-XXX] |
| **Loại công trình** | [ ] Đường bộ  [ ] Thoát nước  [ ] Cấp nước  [ ] Đường sắt |
| **Giai đoạn thiết kế** | [ ] Nghiên cứu khả thi  [ ] TKCS  [ ] BVTC |
| **Chủ đầu tư** | [Tên chủ đầu tư] |
| **Đơn vị tư vấn** | [Tên công ty tư vấn] |
| **Bắt đầu** | YYYY-MM-DD |
| **Hoàn thành dự kiến** | YYYY-MM-DD |

---

## Thông số Kỹ thuật

| Trường | Giá trị |
|---|---|
| **Hệ tọa độ** | [ ] VN2000  [ ] WGS84  [ ] Tọa độ giả định |
| **Múi chiếu** | [ ] 3°  [ ] 6°  Kinh tuyến trục: _____° |
| **Hệ cao độ** | [ ] Quốc gia (Mực nước biển Hòn Dấu)  [ ] Giả định |
| **Đơn vị chiều dài** | Mét |
| **Đơn vị góc** | Độ thập phân |
| **Tiêu chuẩn thiết kế** | [TCVN / 22TCN / UIC / AASHTO] |
| **Phiên bản Civil 3D** | **2027** |
| **Launch Command** | `"C:\Program Files\Autodesk\AutoCAD 2027\acad.exe" /ld "...\AecBase.dbx" /p "<<C3D_Metric>>" /product C3D /language en-US` |

---

## Thông số Tuyến (Đường bộ / Đường sắt)

| Trường | Giá trị |
|---|---|
| **Tên tuyến** | [VD: Quốc lộ XX đoạn A-B] |
| **Chiều dài** | _____ km |
| **Vận tốc thiết kế** | _____ km/h |
| **Bán kính cong tối thiểu** | _____ m |
| **Độ dốc dọc tối đa** | _____ % |
| **Lý trình đầu** | KM___+___ |
| **Lý trình cuối** | KM___+___ |

---

## File DWG Chính

```
G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\[TEN_DU_AN]\
├── [TEN_DU_AN]_MASTER.dwg          ← File tổng hợp chính
├── [TEN_DU_AN]_ALIGNMENT.dwg       ← Bình đồ
├── [TEN_DU_AN]_PROFILE.dwg         ← Trắc dọc
├── [TEN_DU_AN]_CORRIDOR.dwg        ← Hành lang tuyến
├── [TEN_DU_AN]_DRAINAGE.dwg        ← Thoát nước
└── [TEN_DU_AN]_UTILITY.dwg         ← Hạ tầng kỹ thuật khác
```

---

## Phạm vi AI Agent

| Quyền hạn | Trạng thái |
|---|---|
| Đọc toàn bộ model | ✅ Được phép |
| Tạo đối tượng mới (layer AI_DRAFT) | ✅ Được phép |
| Promote lên layer chính | ⚠️ Cần xác nhận người dùng |
| Xóa dữ liệu gốc khảo sát | ❌ Không được phép |
| Xuất file (CSV, Excel, PDF) | ✅ Được phép |

---

## Danh bạ Dự án

| Vai trò | Họ tên | Email | Điện thoại |
|---|---|---|---|
| Chủ nhiệm | | | |
| Kỹ sư bình đồ | | | |
| Kỹ sư trắc dọc | | | |
| Kỹ sư thoát nước | | | |
| Người duyệt | | | |
