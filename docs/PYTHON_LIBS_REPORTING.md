# PYTHON_LIBS_REPORTING.md — Xuất Báo cáo & Dự toán
> Nguồn: PNAY-PYTHON FOR CIVIL.docx | Cập nhật: 2026-05-09

---

## Tổng quan

| Thư viện | Định dạng đầu ra | Phạm vi |
|---|---|---|
| `PyLaTeX` | PDF (LaTeX) | Thuyết minh học thuật có công thức toán |
| `python-docx` + `docxtpl` | Word (.docx) | Báo cáo kỹ thuật có template Jinja2 |
| `OpenConstructionERP` | REST API | Dự toán BOQ, quản trị chi phí |
| `xlwings` / `openpyxl` | Excel (.xlsx) | Bảng tính, bóc tách khối lượng |

---

## 1. PyLaTeX — Thuyết minh Chuẩn Học thuật

> **Ưu điểm:** Xuất PDF với công thức toán học đẹp, layout chuyên nghiệp, tham chiếu tài liệu tự động.

### Cài đặt yêu cầu
```
pip install pylatex
# Cần cài thêm MiKTeX hoặc TeX Live (để biên dịch .tex → .pdf)
# Windows: https://miktex.org/download
```

### Ví dụ: Thuyết minh kiểm toán cột (TCVN 5574:2018)
```python
from pylatex import (
    Document, Section, Subsection, Command,
    Math, Matrix, Alignat, Figure, NoEscape,
    Package, Tabular, NewLine, LineBreak
)
from pylatex.utils import italic, bold
import numpy as np

def tao_thuyet_minh_cot(result: dict, output_path: str = "output/thuyet_minh_cot"):
    """
    Xuất thuyết minh tính toán cột theo TCVN 5574:2018 sang PDF.
    result: dict từ bước kiểm toán ConcreteProperties/PyCivil
    """

    # ---- Khởi tạo tài liệu ----
    geometry_options = {
        "a4paper": True,
        "margin": "2.5cm",
        "top": "2cm",
        "bottom": "2cm"
    }
    doc = Document(geometry_options=geometry_options)

    # Packages cần thiết
    doc.packages.append(Package('babel', options='vietnamese'))
    doc.packages.append(Package('fontenc', options='T5'))
    doc.packages.append(Package('inputenc', options='utf8'))
    doc.packages.append(Package('amsmath'))
    doc.packages.append(Package('amssymb'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('graphicx'))
    doc.packages.append(Package('xcolor'))
    doc.packages.append(Package('hyperref'))

    # ---- Tiêu đề tài liệu ----
    doc.preamble.append(Command('title',
        'Thuyết minh Kiểm toán Cột Bê tông Cốt thép\\\\'
        '\\large Theo TCVN 5574:2018'))
    doc.preamble.append(Command('author', 'AI Agent — Civil 3D Automation'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))
    doc.append(NoEscape(r'\tableofcontents'))
    doc.append(NoEscape(r'\newpage'))

    # ---- 1. Thông số Đầu vào ----
    with doc.create(Section('Thông số Đầu vào')):

        with doc.create(Subsection('Mặt cắt cột')):
            with doc.create(Tabular('|l|r|l|')) as table:
                table.add_hline()
                table.add_row(["Thông số", "Giá trị", "Đơn vị"])
                table.add_hline()
                table.add_row(["Chiều rộng b", result['b_mm'], "mm"])
                table.add_row(["Chiều cao h", result['h_mm'], "mm"])
                table.add_row(["Cấp độ bền bê tông", result['concrete_grade'], ""])
                table.add_row(["Cốt thép", result['steel_grade'], ""])
                table.add_row(["Lớp bảo vệ a", result['cover_mm'], "mm"])
                table.add_hline()

        with doc.create(Subsection('Nội lực thiết kế')):
            doc.append("Nội lực bất lợi nhất (tổ hợp ")
            doc.append(italic(result['governing_load_case']))
            doc.append("):")

            # Công thức hiển thị nội lực
            with doc.create(Alignat(numbering=False, escape=False)) as math:
                math.append(
                    r'N_{Ed} &= ' + f"{result['N_Ed_kN']:.1f}" + r'\text{ kN}\\')
                math.append(
                    r'M_{Ed,x} &= ' + f"{result['M_Ed_kNm']:.1f}" + r'\text{ kN.m}')

    # ---- 2. Cơ sở Lý thuyết ----
    with doc.create(Section('Cơ sở Lý thuyết — TCVN 5574:2018')):

        with doc.create(Subsection('Mô hình Phi tuyến Vật liệu (NLDM)')):
            doc.append("Theo TCVN 5574:2018 §7.1.3, quan hệ ứng suất-biến dạng "
                      "của bê tông chịu nén được mô tả bằng mô hình tam tuyến tính:")

            with doc.create(Alignat(numbering=False, escape=False)) as eq:
                eq.append(r'\sigma_b &= E_b \cdot \varepsilon_b'
                          r'\quad \text{khi } \varepsilon_b \leq \varepsilon_{b0}\\')
                eq.append(r'\sigma_b &= R_b'
                          r'\quad \text{khi } \varepsilon_{b0} < \varepsilon_b \leq \varepsilon_{b1}\\')
                eq.append(r'\sigma_b &= R_b \cdot \left(1 - \frac{\varepsilon_b - \varepsilon_{b1}}'
                          r'{\varepsilon_{bu} - \varepsilon_{b1}}\right)'
                          r'\quad \text{khi } \varepsilon_{b1} < \varepsilon_b \leq \varepsilon_{bu}')

            doc.append(NoEscape(r'\vspace{0.3cm}'))
            doc.append("Trong đó:")

            with doc.create(Alignat(numbering=False, escape=False)) as params:
                params.append(r'R_b &= ' + f"{result['Rb_MPa']:.1f}" +
                              r'\text{ MPa — Cường độ chịu nén tính toán}\\')
                params.append(r'\varepsilon_{b0} &= 0.002 \text{ (biến dạng tại đỉnh)}\\')
                params.append(r'\varepsilon_{bu} &= 0.0035 \text{ (biến dạng cực hạn)}')

        with doc.create(Subsection('Điều kiện Cân bằng Lực')):
            doc.append("Trục trung hòa xác định từ điều kiện cân bằng lực dọc:")

            with doc.create(Math(escape=False)):
                pass
            doc.append(NoEscape(
                r'\begin{equation}'
                r'N_{Ed} = \int_A \sigma_b \, dA + \sum_{i} \sigma_{si} \cdot A_{si}'
                r'\end{equation}'
            ))

    # ---- 3. Kết quả Kiểm toán ----
    with doc.create(Section('Kết quả Kiểm toán')):

        # Nhúng biểu đồ P-M
        diagram_path = result.get('diagram_path', '')
        if diagram_path:
            with doc.create(Figure(position='h!')) as fig:
                fig.add_image(diagram_path, width=NoEscape(r'0.7\textwidth'))
                fig.add_caption(
                    f"Biểu đồ tương tác P-M — Cột {result['element_id']}")

        # Bảng kết luận
        ratio = result['utilization_ratio']
        status_color = 'green' if ratio <= 1.0 else 'red'
        status_text = 'ĐẠT' if ratio <= 1.0 else 'KHÔNG ĐẠT'

        doc.append(NoEscape(
            r'\begin{center}'
            r'\Large\textbf{Kết luận: }'
            r'\textcolor{' + status_color + r'}{' + status_text + r'}'
            r'\end{center}'
        ))

        with doc.create(Tabular('|l|r|')) as table:
            table.add_hline()
            table.add_row(["Diện tích thép tối thiểu yêu cầu",
                          f"{result['min_reinforcement_cm2']:.2f} cm²"])
            table.add_row(["Hệ số sử dụng (Utilization Ratio)",
                          f"{ratio:.3f}"])
            table.add_row(["Tổ hợp bất lợi nhất",
                          result['governing_load_case']])
            table.add_hline()

    # ---- Biên dịch PDF ----
    doc.generate_pdf(output_path, clean_tex=False, compiler='pdflatex')
    print(f"[OK] Xuất thuyết minh PDF: {output_path}.pdf")

# ---- Gọi hàm ví dụ ----
sample_result = {
    'element_id': 'Column_C1',
    'b_mm': 400, 'h_mm': 500,
    'concrete_grade': 'B25', 'steel_grade': 'CB400V',
    'cover_mm': 40,
    'governing_load_case': 'LC_05_WindX',
    'N_Ed_kN': -850.0, 'M_Ed_kNm': 125.0,
    'Rb_MPa': 14.5,
    'utilization_ratio': 0.87,
    'min_reinforcement_cm2': 24.5,
    'diagram_path': 'assets/diagrams/pm_col_C1.png',
    'status': 'PASS'
}
tao_thuyet_minh_cot(sample_result, output_path="output/thuyet_minh_col_C1")
```

---

## 2. docxtpl + Jinja2 — Báo cáo Word Template

```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import pandas as pd

def tao_bao_cao_word(template_path: str,
                     results: list,
                     output_path: str):
    """
    Điền kết quả vào template Word có sẵn.
    Template sử dụng cú pháp Jinja2:
      {{ element_id }}, {{ status }}, {% if %}, {% for %}
    """
    tpl = DocxTemplate(template_path)

    # Chuẩn bị context dictionary
    context = {
        'project_name': 'Công trình XYZ',
        'date': '2026-05-09',
        'engineer': 'KS. Nguyễn Văn A',
        'elements': results,

        # Nhúng ảnh biểu đồ
        'pm_diagram': InlineImage(
            tpl,
            image_descriptor='assets/diagrams/pm_col_C1.png',
            width=Mm(120)
        ),

        # Bảng tổng hợp từ Pandas
        'summary_table': pd.DataFrame(results)[
            ['element_id', 'status', 'utilization_ratio', 'min_reinforcement_cm2']
        ].to_dict('records'),
    }

    tpl.render(context)
    tpl.save(output_path)
    print(f"[OK] Xuất báo cáo Word: {output_path}")
```

### Template Word mẫu (TEMPLATE_THUYET_MINH.docx)
```
# Trong file .docx, dùng cú pháp Jinja2:

Dự án: {{ project_name }}
Ngày:  {{ date }}

{% for el in elements %}
## Cấu kiện: {{ el.element_id }}
- Kết quả: **{{ el.status }}**
- Hệ số sử dụng: {{ "%.3f"|format(el.utilization_ratio) }}
{% if el.utilization_ratio > 1.0 %}
⚠️ CẢNH BÁO: Cần tăng tiết diện hoặc cốt thép!
{% endif %}
{% endfor %}
```

---

## 3. OpenConstructionERP — Dự toán BOQ

```python
import requests

ERP_BASE_URL = "http://localhost:8069/api"  # Tự host

def day_khoi_luong_beton_vao_boq(
    project_id: str,
    ten_hang_muc: str,
    the_tich_m3: float,
    cap_do_ben: str = "B25"
):
    """
    Đẩy khối lượng bê tông tự động vào bảng dự toán BOQ.
    Gọi REST API của OpenConstructionERP.
    """
    payload = {
        "project_id": project_id,
        "work_item": {
            "name": ten_hang_muc,
            "code": "BT-001",
            "unit": "m³",
            "quantity": round(the_tich_m3, 3),
            "resource_tags": {
                "concrete_grade": cap_do_ben,
                "placement_method": "pump"
            }
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ERP_TOKEN}"
    }

    resp = requests.post(
        f"{ERP_BASE_URL}/boq/items",
        json=payload, headers=headers
    )

    if resp.status_code == 201:
        item = resp.json()
        print(f"[OK] BOQ: {ten_hang_muc} | "
              f"{the_tich_m3:.3f} m³ | "
              f"Đơn giá: {item['unit_price']:,.0f} VND")
        return item
    else:
        print(f"[ERR] {resp.status_code}: {resp.text}")
        return None

# Ví dụ: Đẩy khối lượng từ mô hình ConcreteProperties
the_tich_cot = 0.4 * 0.5 * 3.5 * 10  # 10 cột tầng 1
day_khoi_luong_beton_vao_boq(
    project_id="PRJ-2026-001",
    ten_hang_muc="Bê tông cột tầng 1 (B25)",
    the_tich_m3=the_tich_cot
)
```

---

## So sánh Lựa chọn Định dạng Đầu ra

| Tiêu chí | PyLaTeX (PDF) | docxtpl (Word) |
|---|---|---|
| Công thức toán học | ⭐⭐⭐⭐⭐ LaTeX chuẩn | ⭐⭐ Hạn chế |
| Dễ chỉnh sửa template | ⭐⭐ Cần biết LaTeX | ⭐⭐⭐⭐⭐ Word thân quen |
| Hỗ trợ dân kỹ thuật VN | ⭐⭐⭐ (cần MiKTeX) | ⭐⭐⭐⭐⭐ |
| Nộp cơ quan nhà nước | ⭐⭐⭐ PDF chuẩn | ⭐⭐⭐⭐ Word phổ biến hơn |
| Học thuật / hội thảo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

> **Khuyến nghị**: Dùng **PyLaTeX** cho thuyết minh học thuật có nhiều công thức;
> dùng **docxtpl** cho hồ sơ thiết kế, hồ sơ mời thầu tiêu chuẩn.

---

## Checklist Xuất Báo cáo

- [ ] PyLaTeX: Cài MiKTeX trước khi chạy `generate_pdf()`
- [ ] PyLaTeX: Encode tiếng Việt → dùng `babel` + `fontenc T5` + `inputenc utf8`
- [ ] docxtpl: Mọi biến trong template phải có trong `context dict`
- [ ] Biểu đồ Matplotlib lưu `dpi=150` vào `assets/diagrams/` trước khi nhúng
- [ ] BOQ: Đơn vị khối lượng phải khớp với cơ sở dữ liệu đơn giá ERP
- [ ] Tất cả kết quả JSON lưu vào `output/` để Agent khác có thể đọc
