import ezdxf

def inspect():
    try:
        doc = ezdxf.readfile("Parcel-3A.dxf")
        msp = doc.modelspace()
        
        entities = {}
        layers = set()
        
        for e in msp:
            layer = e.dxf.layer
            etype = e.dxftype()
            layers.add(layer)
            if etype not in entities:
                entities[etype] = 1
            else:
                entities[etype] += 1
                
        print("=== DXF Inspection ===")
        print("Entity types:", entities)
        print("Layers:", sorted(list(layers)))
        
        # Look for LWPOLYLINEs specifically
        lwpolylines = msp.query('LWPOLYLINE')
        print(f"\nFound {len(lwpolylines)} LWPOLYLINEs.")
        if len(lwpolylines) > 0:
            # Check if they are closed
            closed_count = sum(1 for p in lwpolylines if p.is_closed)
            print(f"Closed LWPOLYLINEs: {closed_count}")
            print(f"Sample LWPOLYLINE layer: {lwpolylines[0].dxf.layer}")
            
    except Exception as e:
        print(f"Error reading DXF: {e}")

if __name__ == "__main__":
    inspect()
