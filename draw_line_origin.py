import win32com.client
import pythoncom
import sys

def connect_acad():
    prog_ids = [
        "AutoCAD.Application",
        "AutoCAD.Application.24",
        "AutoCAD.Application.24.1",
        "AutoCAD.Application.24.2",
        "AutoCAD.Application.24.3",
        "AeccXUiLand.AeccApplication",
        "AeccXUiLand.AeccApplication.13.3"
    ]
    for prog_id in prog_ids:
        try:
            acad = win32com.client.GetActiveObject(prog_id)
            print(f"Successfully connected using ProgID: {prog_id}")
            return acad
        except Exception:
            pass
    raise Exception("Could not connect to any AutoCAD/Civil 3D COM object.")

def main():
    try:
        print("Connecting to AutoCAD/Civil 3D via COM...")
        acad = connect_acad()
        doc = acad.ActiveDocument
        print(f"Connected to: {doc.Name}")
        
        model_space = doc.ModelSpace
        
        pt1 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (0.0, 0.0, 0.0))
        pt2 = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (8.0, 0.0, 0.0))
        
        model_space.AddLine(pt1, pt2)
        print("Successfully drew an 8m line from origin (0,0) to (8,0).")
    except Exception as e:
        print(f"Error connecting to Civil 3D or drawing line: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
