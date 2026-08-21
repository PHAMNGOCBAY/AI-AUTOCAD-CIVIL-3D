import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 50)
print("KIEM TRA KET NOI CIVIL 3D 2027 QUA COM API")
print("=" * 50)

# 1. Kiem tra pywin32
try:
    import win32com.client
    print("[OK] pywin32 da cai dat")
except ImportError:
    print("[LOI] pywin32 chua cai -> chay: pip install pywin32")
    sys.exit(1)

# 2. Ket noi AutoCAD
try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    print(f"[OK] Ket noi AutoCAD thanh cong!")
    print(f"     Phien ban: {acad.Version}")
    print(f"     San pham : {acad.Name}")
except Exception as e:
    print(f"[LOI] Khong the ket noi AutoCAD: {e}")
    print("      -> Dam bao Civil 3D 2027 dang chay va co ban ve dang mo")
    sys.exit(1)

# 3. Thong tin ban ve hien tai
try:
    doc = acad.ActiveDocument
    print(f"\n[BAN VE]")
    print(f"  Ten          : {doc.Name}")
    saved_path = doc.FullName
    print(f"  Duong dan    : {saved_path if saved_path else '[Chua luu]'}")
    print(f"  Trang thai   : {'Da luu' if doc.Saved else 'Chua luu (co thay doi)'}")

    # Don vi ve
    insunits = doc.GetVariable("INSUNITS")
    units_map = {0:"Khong xac dinh", 1:"Inches", 4:"mm", 6:"m", 7:"km"}
    print(f"  Don vi       : {units_map.get(insunits, str(insunits))}")

    # Dem doi tuong
    model_space = doc.ModelSpace
    print(f"  ModelSpace   : {model_space.Count} doi tuong")

    # Layer hien tai
    print(f"  Layer hien tai: {doc.ActiveLayer.Name}")

except Exception as e:
    print(f"[LOI] Khong lay duoc thong tin ban ve: {e}")

# 4. Thu ket noi Civil 3D namespace
print(f"\n[CIVIL 3D API]")
try:
    # Thu COM Civil 3D
    civil_app = win32com.client.Dispatch("AeccXUiLand.AeccApplication.13.5")
    print(f"  COM Civil 3D : OK")
except Exception as e:
    print(f"  COM Civil 3D : Khong kha dung qua COM truc tiep (binh thuong)")
    print(f"  -> Su dung Managed.NET qua Dynamo/CivilPython la cach chinh xac hon")

print(f"\n[HUONG DAN TIEP THEO]")
print(f"  1. Trong Civil 3D, go lenh: APPLOAD")
print(f"  2. Load file: civil3d-mcp-plugin.dll")
print(f"  3. Khoi dong MCP Server: node dist\\index.js")
print(f"  4. Xac nhan icon hammer xuat hien trong AI client")
print("=" * 50)
