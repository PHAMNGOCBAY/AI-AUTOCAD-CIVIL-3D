# API_REFERENCE.md — Tra cứu .NET API AutoCAD Civil 3D
> Phiên bản: Civil 3D **2027** | CPython 3.x | 2026-05-09

---

## 1. Bình đồ (Alignment)

**Lớp**: `Autodesk.Civil.DatabaseServices.Alignment`

| Phương thức / Thuộc tính | Mô tả | Ghi chú |
|---|---|---|
| `Alignment.Create(db, name, siteId, layerId, alignStyle, labelStyle)` | Tạo Bình đồ mới | Cần AlignmentCreationOptions |
| `align.AddFixedLine(startPt, endPt)` | Thêm đoạn thẳng cố định | Point2d |
| `align.AddFreeCurve(entBefore, entAfter, radius, solution)` | Thêm đường cong tiếp xúc | |
| `align.AddFixedSpiral(startPt, endPt, clothoidParam, direction)` | Thêm đường xoắn ốc chuyển tiếp | Clothoid |
| `align.Name` | Tên Bình đồ | string |
| `align.Length` | Chiều dài tổng | double (m) |
| `align.StartingStation` | Lý trình bắt đầu | double |
| `align.EndingStation` | Lý trình kết thúc | double |
| `align.GetPointAtStation(station)` | Lấy tọa độ tại lý trình | Point3d |
| `civil_db.GetAlignmentIds()` | Lấy tất cả Alignment trong bản vẽ | ObjectIdCollection |

---

## 2. Trắc dọc (Profile)

**Lớp**: `Autodesk.Civil.DatabaseServices.Profile`

| Phương thức / Thuộc tính | Mô tả | Ghi chú |
|---|---|---|
| `Profile.CreateFromFeatureLine(alignId, featureLineId, ...)` | Tạo trắc dọc TN từ Feature Line | EG tự động cập nhật |
| `Profile.CreateByLayout(name, alignId, profileViewId, styleId, labelStyleId)` | Tạo trắc dọc thiết kế (FG) | Layout-based |
| `profile.Name` | Tên Profile | |
| `profile.MinimumElevation` | Cao độ thấp nhất | double |
| `profile.MaximumElevation` | Cao độ cao nhất | double |
| `pvi.Station`, `pvi.Elevation` | Điểm gãy trắc dọc | ProfilePVI |
| `profile.PVIs` | Danh sách PVI | ProfilePVICollection |
| `align.GetProfileIds()` | Lấy Profile thuộc Alignment | |

---

## 3. Hành lang Tuyến (Corridor)

**Lớp**: `Autodesk.Civil.DatabaseServices.Corridor`

| Phương thức / Thuộc tính | Mô tả | Ghi chú |
|---|---|---|
| `Corridor.Create(db, name, alignId, profileId, assemblyId, ...)` | Tạo Corridor | |
| `corridor.Rebuild()` | Rebuild sau khi thay đổi tham số | Bắt buộc sau edit |
| `corridor.Name` | Tên Corridor | |
| `corridor.Baselines` | Danh sách Baseline | BaselineCollection |
| `baseline.GetSortedStations()` | Lấy tất cả Station | double[] |
| `corridor.CorridorSurfaces` | Bề mặt sinh ra từ Corridor | |

**Subassembly**: `Autodesk.Civil.DatabaseServices.Subassembly`

---

## 4. Mạng lưới Ống Trọng lực (Gravity Pipe Network)

**Lớp**: `Autodesk.Civil.DatabaseServices.Network`

| Phương thức / Thuộc tính | Mô tả | Ghi chú |
|---|---|---|
| `civil_db.GetPipeNetworkIds()` | Lấy tất cả Pipe Network | |
| `network.GetPipeIds()` | Lấy tất cả Pipe | |
| `network.GetStructureIds()` | Lấy tất cả hố ga | |
| `pipe.StartPoint`, `pipe.EndPoint` | Điểm đầu/cuối ống | Point3d |
| `pipe.InnerDiameterOrWidth` | Đường kính trong | double |
| `pipe.Slope` | Độ dốc ống | double |
| `pipe.StartInvert`, `pipe.EndInvert` | Cao độ đáy ống 2 đầu | double |
| `struct.Name` | Tên hố ga | |
| `struct.InsertionPoint` | Tọa độ hố ga | Point3d |
| `struct.WallThickness` | Độ dày thành ống | **Chỉ qua Managed.NET** |
| `catchment.BoundaryPolyline3d` | Đường biên lưu vực | Point3dCollection |

---

## 5. Mạng lưới Ống Áp lực (Pressure Pipe Network)

**Lớp**: `Autodesk.Civil.DatabaseServices.PressurePipe` *(C3D 2021+)*

| Phương thức / Thuộc tính | Mô tả | Ghi chú |
|---|---|---|
| `PressurePipeNetwork.AddPipe(partSize, startPt, endPt)` | Thêm đoạn ống | C3D 2021+ |
| `network.AddAppurtenance(appurtenanceType, location)` | Thêm van/phụ kiện | Reflection required |
| `pressurePipe.AllowableWorkingPressure` | Áp lực làm việc | |
| `pressurePipe.CoverDepth` | Độ chôn sâu | |

> **Lưu ý**: Thêm Fittings/Appurtenances cần kỹ thuật reflection phức tạp (Autodesk chưa mở hoàn toàn API).

---

## 6. Điểm COGO (CogoPoint)

**Lớp**: `Autodesk.Civil.DatabaseServices.CogoPoint`

| Phương thức / Thuộc tính | Mô tả |
|---|---|
| `civil_db.CogoPoints.Add(point3d, description)` | Tạo điểm COGO |
| `cogoPoint.Northing`, `.Easting`, `.Elevation` | Tọa độ |
| `cogoPoint.PointNumber` | Số thứ tự điểm |
| `cogoPoint.FullDescription` | Mô tả điểm |

---

## 7. Bề mặt (Surface / TIN)

**Lớp**: `Autodesk.Civil.DatabaseServices.TinSurface`

| Phương thức / Thuộc tính | Mô tả |
|---|---|
| `TinSurface.Create(db, name)` | Tạo bề mặt TIN |
| `surface.AddBreakline(breakline3d)` | Thêm đường đứt gãy |
| `surface.FindElevationAtXY(x, y)` | Lấy cao độ tại tọa độ |
| `surface.Volume` | Thể tích bề mặt |
| `civil_db.GetSurfaceIds()` | Lấy tất cả Surface |

---

## 8. Bóc tách Khối lượng (QTO)

| Phương thức / Lệnh | Mô tả |
|---|---|
| `AeccTakeoff` (lệnh nội bộ) | Quyết toán bộ môi lưới |
| Handle ID (ObjectId) | Trích xuất mã nhận dạng đối tượng |
| Xuất CSV/ATT/XML | Định dạng chuẩn QTO Manager |

---

## 9. Đường sắt (Railway — Cant & Turnout)

| Thuộc tính / Collection | Mô tả |
|---|---|
| `align.CANTCriticalStationCollection` | Tập hợp Station siêu cao |
| `align.SuperElevationCurves` | Các đoạn siêu cao |
| `cantCurve.CantValue` | Giá trị siêu cao (mm) |
| `cantCurve.TransitionLength` | Chiều dài đoạn chuyển tiếp |
| Turnout JSON | `C:\ProgramData\Autodesk\C3D 20xx\enu\Data\Railway Design Standards\Turnout\*.json` |

**Công thức tính siêu cao**:
```
Cant (mm) = 11.8 × V² / R
V = vận tốc thiết kế (km/h)
R = bán kính cong (m)
```

---

## 10. So sánh COM vs Managed.NET

| Tiêu chí | COM API | Managed.NET API |
|---|---|---|
| Truy cập | Ngoại vi (pywin32) | Nội vi (Dynamo/CivilPython) |
| Dữ liệu chuyên sâu | ❌ Bị giới hạn | ✅ Đầy đủ |
| WallThickness | ❌ Lỗi | ✅ OK |
| Tốc độ | Chậm (IPC overhead) | Nhanh (in-process) |
| Quản lý | Độc lập | Cần Lock + Transaction |
