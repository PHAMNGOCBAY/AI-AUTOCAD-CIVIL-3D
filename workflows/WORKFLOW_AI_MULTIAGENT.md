# WORKFLOW_AI_MULTIAGENT.md — Kiến trúc AI Đa Tác tử
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Mục đích

Phác thảo **kiến trúc điều phối AI đa tác tử (Multi-Agent System)** kết nối toàn bộ các thư viện Python trong một pipeline tự động hóa khép kín: từ dữ liệu đầu vào → mô phỏng FEM → kiểm toán tiêu chuẩn → xuất bản vẽ CAD → thuyết minh tính toán.

---

## Kiến trúc Tổng thể

```
Kỹ sư → [Yêu cầu] → AGENTS.md (Điều phối trung tâm)
                          │
            ┌─────────────┼──────────────────┐
            ▼             ▼                  ▼
    [Agent Kết cấu]  [Agent Địa kỹ]   [Agent BIM/CAD]
    SKILL_FEM.md     SKILL_GEO.md     SKILL_CAD.md
         │                │                 │
    OpenSeesPy       OpenPile          ezdxf/pyRevit
    PyNite           geofound          pyautocad
    PyCBA            PySlope
         │                │                 │
         └────────────────┼─────────────────┘
                          ▼
                 [Agent Kiểm toán]
                 SKILL_CHECK.md
                 ConcreteProperties
                 EurocodePy / PyCivil
                          │
                          ▼
                 [Agent Báo cáo]
                 SKILL_REPORT.md
                 PyLaTeX / docxtpl
                 OpenConstructionERP
                          │
                          ▼
              [OUTPUT: PDF + DXF + BOQ]
```

---

## Cấu trúc Thư mục Tiêu chuẩn

```
G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\[TEN_DU_AN]\
├── AGENTS.md                     ← Điều phối toàn cục (đọc đầu tiên)
├── PROJECT_INFO.md               ← Thông tin dự án
├── input\
│   ├── loads.json                ← Tải trọng đầu vào
│   ├── geometry.json             ← Hình học kết cấu
│   └── soil_layers.json          ← Hồ sơ địa chất
├── skills\
│   ├── structural_analysis\
│   │   └── SKILL.md             ← Agent kết cấu: PyNite / OpenSeesPy
│   ├── design_check_tcvn\
│   │   └── SKILL.md             ← Agent kiểm toán: TCVN 5574 / Eurocode
│   ├── geotech\
│   │   └── SKILL.md             ← Agent địa kỹ: OpenPile / geofound
│   ├── bim_cad\
│   │   └── SKILL.md             ← Agent CAD: ezdxf / pyRevit
│   └── reporting\
│       └── SKILL.md             ← Agent báo cáo: PyLaTeX / docxtpl
├── output\
│   ├── internal_forces.json      ← Kết quả nội lực (PyNite)
│   ├── col_C1_result.json        ← Kết quả kiểm toán (Pydantic)
│   ├── *.dxf                     ← Bản vẽ chi tiết (ezdxf)
│   └── *.pdf                     ← Thuyết minh (PyLaTeX)
└── assets\
    └── diagrams\
        ├── pm_col_C1.png
        └── pile_capacity_curve.png
```

---

## Pha 1: Thu thập & Lên kế hoạch

```python
# AGENTS.md → Tự động đọc và phân tích yêu cầu kỹ sư
import json

def phan_tich_yeu_cau(yeu_cau_text: str) -> dict:
    """
    Agent Lập kế hoạch: phân tích yêu cầu và xác định
    các agent phụ cần kích hoạt.
    """
    # LLM phân tích yêu cầu → routing
    tasks = {
        'structural': False,
        'geotech': False,
        'design_check': False,
        'bim_cad': False,
        'reporting': False
    }

    keywords = {
        'structural': ['khung', 'dầm', 'cột', 'FEM', 'nội lực', 'phản lực'],
        'geotech':    ['cọc', 'móng', 'mái dốc', 'đất nền', 'SPT', 'CPT'],
        'design_check': ['kiểm toán', 'TCVN', 'Eurocode', 'thép yêu cầu'],
        'bim_cad':    ['bản vẽ', 'DXF', 'Revit', 'cốt thép 3D', 'AutoCAD'],
        'reporting':  ['thuyết minh', 'báo cáo', 'PDF', 'dự toán', 'BOQ']
    }

    for task, kws in keywords.items():
        if any(kw in yeu_cau_text for kw in kws):
            tasks[task] = True

    # Luôn chạy reporting nếu có bất kỳ task nào
    if any(tasks.values()):
        tasks['reporting'] = True

    return tasks

# Ví dụ
yeu_cau = "Tính toán và kiểm toán khung bê tông cốt thép, xuất thuyết minh PDF"
ke_hoach = phan_tich_yeu_cau(yeu_cau)
print("Kế hoạch:", {k: v for k, v in ke_hoach.items() if v})
```

---

## Pha 2: Mô phỏng Cơ học

```python
# Agent Kết cấu — Đọc SKILL_FEM.md → chạy PyNite
from PyNite import FEModel3D
import json

def chay_fem_pynite(geometry_file: str,
                    loads_file: str,
                    output_file: str) -> dict:
    """Giải FEM và xuất kết quả JSON"""

    with open(geometry_file, 'r', encoding='utf-8') as f:
        geom = json.load(f)
    with open(loads_file, 'r', encoding='utf-8') as f:
        loads = json.load(f)

    frame = FEModel3D()

    # Tạo mô hình từ dữ liệu JSON
    for node in geom['nodes']:
        frame.add_node(node['id'], node['x'], node['y'], node['z'])

    for member in geom['members']:
        frame.add_member(member['id'],
            member['start'], member['end'],
            **member['properties'])

    for support in geom['supports']:
        frame.def_support(support['node'],
            *support['restraints'])

    for load in loads['point_loads']:
        frame.add_node_load(load['node'],
            load['direction'], load['value'],
            case=load.get('case', 'D'))

    # Giải
    frame.analyze(check_statics=True)

    # Trích xuất nội lực lớn nhất
    results = {}
    for m_id, member in frame.members.items():
        results[m_id] = {
            'M_max_kNm': member.max_moment('Mz') / 1e3,
            'V_max_kN':  member.max_shear('Fy') / 1e3,
            'N_max_kN':  member.max_axial() / 1e3
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[OK] Kết quả FEM → {output_file}")
    return results
```

---

## Pha 3: Kiểm toán Chuyên môn

```python
# Agent Kiểm toán — Đọc internal_forces.json → chạy ConcreteProperties
from pydantic import BaseModel
from typing import Literal

class ElementCheckResult(BaseModel):
    element_id:              str
    status:                  Literal['PASS', 'FAIL']
    min_reinforcement_cm2:   float
    utilization_ratio:       float
    governing_load_case:     str
    diagram_path:            str

def kiem_toan_tat_ca_cot(fem_results: dict,
                          section_params: dict) -> list:
    """Kiểm toán tất cả cột từ kết quả FEM"""
    check_results = []
    for el_id, forces in fem_results.items():
        if 'C' not in el_id:  # Chỉ kiểm cột
            continue

        # (Gọi ConcreteProperties / PyCivil ở đây)
        ratio = abs(forces['N_max_kN']) / section_params['Nd_kN']

        result = ElementCheckResult(
            element_id=el_id,
            status='PASS' if ratio <= 1.0 else 'FAIL',
            min_reinforcement_cm2=section_params['As_min_cm2'],
            utilization_ratio=round(ratio, 3),
            governing_load_case='LC_05_WindX',
            diagram_path=f"assets/diagrams/pm_{el_id}.png"
        )
        check_results.append(result.dict())

    return check_results
```

---

## Pha 4: Sản xuất Hồ sơ

```python
# Agent Báo cáo — Gọi PyLaTeX + ezdxf + OpenConstructionERP
import subprocess

def san_xuat_ho_so(check_results: list, project_id: str):
    """Pipeline xuất hồ sơ tự động"""

    # 1. Sinh bản vẽ DXF cho tất cả cấu kiện FAIL
    fail_elements = [r for r in check_results if r['status'] == 'FAIL']
    for el in fail_elements:
        print(f"[CAD] Sinh bản vẽ tăng cường cho {el['element_id']}")
        # → Gọi hàm ezdxf từ PYTHON_LIBS_BIM_CAD.md

    # 2. Xuất thuyết minh PDF (PyLaTeX)
    for result in check_results:
        print(f"[PDF] Xuất thuyết minh: {result['element_id']}")
        # → Gọi tao_thuyet_minh_cot() từ PYTHON_LIBS_REPORTING.md

    # 3. Đẩy khối lượng vào BOQ
    total_concrete_m3 = sum(
        r.get('concrete_volume_m3', 0) for r in check_results
    )
    # → Gọi day_khoi_luong_beton_vao_boq() từ PYTHON_LIBS_REPORTING.md

    print(f"\n✅ Hoàn thành! {len(check_results)} cấu kiện | "
          f"{len(fail_elements)} cần xem xét lại")
```

---

## Quy tắc Vận hành Agent

| Quy tắc | Nội dung |
|---|---|
| **Đọc trước** | Agent PHẢI đọc SKILL.md tương ứng trước khi chạy code |
| **JSON Schema** | Mọi output dùng Pydantic model — không tự suy đoán cấu trúc |
| **Không suy đoán số liệu vật lý** | Tham số $R_b$, $f_{ck}$ tra từ database JSON chuẩn hóa |
| **Log quyết định** | Mọi lý do chọn đường kính thép ghi vào JSON log |
| **Lưu ảnh biểu đồ** | Biểu đồ P-M, đường ảnh hưởng → `assets/diagrams/` |
| **Rollback khi lỗi** | Lỗi bất kỳ bước nào → báo exception đầy đủ, dừng pipeline |

---

## Checklist Triển khai

- [ ] Tạo cấu trúc thư mục `skills/` theo template trên
- [ ] Đặt AGENTS.md tại thư mục gốc dự án
- [ ] Mỗi SKILL.md có 2 khối: **định tuyến ngữ cảnh** + **hướng dẫn thực thi**
- [ ] Cài đặt: `pip install crewai` hoặc dùng n8n (tự host)
- [ ] Test từng Agent độc lập trước khi chạy full pipeline
- [ ] Kiểm tra MiKTeX (PyLaTeX) và AutoCAD (pyautocad) trước khi deploy
