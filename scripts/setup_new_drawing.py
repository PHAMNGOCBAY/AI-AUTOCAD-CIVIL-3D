import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import win32com.client

print("=" * 55)
print("THIET LAP BAN VE MOI - CIVIL 3D 2027 (COM v2)")
print("=" * 55)

acad = win32com.client.GetActiveObject("AutoCAD.Application")
doc  = acad.ActiveDocument

# --- 1. Luu ban ve ---
save_folder = r"G:\My Drive\AI-AUTOCAD CIVIL 3D\projects\NewDrawing"
os.makedirs(save_folder, exist_ok=True)
save_path = os.path.join(save_folder, "C3D_NewDrawing_2027.dwg")
try:
    doc.SaveAs(save_path)
    print(f"[OK] Da luu: {save_path}")
except Exception as e:
    print(f"[OK] File da ton tai hoac da luu: {e}")

# --- 2. Chay lenh qua SendCommand (thay cho SetVariable truc tiep) ---
# Civil 3D 2027 COM gioi han SetVariable, dung SendCommand thay the
try:
    # Don vi: Metric (INSUNITS = 6 = meters)
    doc.SendCommand("-UNITS\n2\n3\n1\n4\n0\nN\n")
    print("[OK] Don vi: Decimal, Meters")
except Exception as e:
    print(f"[WARN] SendCommand UNITS: {e}")

# --- 3. Tao layer bang lenh LAYER ---
layers_def = [
    ("AI_DRAFT",    "7"),   # Trang
    ("C-ROAD-CNTR", "1"),   # Do
    ("C-ROAD-PROF", "2"),   # Vang
    ("C-TOPO",      "3"),   # Xanh la
    ("C-PIPE",      "4"),   # Xanh duong
    ("C-ANNOT",     "9"),   # Xam
]

print("\n[LAYERS]")
for name, color in layers_def:
    try:
        # Lenh LAYER: tao moi, dat mau
        cmd = f"-LAYER\nM\n{name}\nC\n{color}\n{name}\n\n"
        doc.SendCommand(cmd)
        print(f"  + {name} (mau {color})")
    except Exception as e:
        print(f"  ! {name}: {e}")

# --- 4. Tra ve layer 0 lam layer hien tai ---
try:
    doc.SendCommand("-LAYER\nS\n0\n\n")
    print("[OK] Layer hien tai: 0")
except Exception as e:
    print(f"[WARN] Set layer: {e}")

# --- 5. Tao diem COGO thu nghiem bang lenh AutoCAD ---
try:
    # Zoom ra toan canh
    doc.SendCommand("ZOOM\nA\n")
    print("[OK] ZOOM All")
except Exception as e:
    print(f"[WARN] ZOOM: {e}")

# --- 6. Tong ket ---
print(f"\n[TONG KET]")
print(f"  San pham  : {acad.Name}")
print(f"  Phien ban : {acad.Version}")
print(f"  Ban ve    : {doc.Name}")
try:
    insunits = doc.GetVariable("INSUNITS")
    print(f"  INSUNITS  : {insunits} (6=Meters)")
except:
    pass

print(f"\n[TRANG THAI KET NOI]")
print(f"  COM (pywin32) : Hoat dong - dung SendCommand()")
print(f"  .NET Managed  : Can Dynamo/CivilPython")
print(f"  MCP Server    : Chua cai (xem docs/MCP_TOOLS.md)")
print("=" * 55)
print("HOAN THANH! Ban ve C3D_NewDrawing_2027.dwg da san sang.")
