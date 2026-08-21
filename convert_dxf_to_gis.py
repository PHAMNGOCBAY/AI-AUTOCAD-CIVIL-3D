import ezdxf
from shapely.geometry import LineString, mapping
import shapefile
import json
import math
import os

def convert():
    print("Loading DXF...")
    doc = ezdxf.readfile("Parcel-3A.dxf")
    msp = doc.modelspace()
    
    # Layers that usually contain property lines
    target_layers = {'C-PROP-SUBD', 'V-PROP-LINE', 'C-PROP-ROAD', 'C-ROAD-CNTR', 'C-ROAD'}
    
    lines = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    # 1. Extract geometries and find bounding box
    print("Extracting geometries...")
    for e in msp:
        if e.dxf.layer in target_layers:
            pts = []
            if e.dxftype() == 'LINE':
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            elif e.dxftype() == 'LWPOLYLINE':
                pts = [(p[0], p[1]) for p in e.get_points()]
            elif e.dxftype() == 'ARC':
                try:
                    path = ezdxf.path.make_path(e)
                    pts = [(v.x, v.y) for v in path.flattening(0.1)]
                except Exception:
                    pass
            
            if len(pts) >= 2:
                lines.append((pts, e.dxf.layer))
                for x, y in pts:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    
    print(f"Extracted {len(lines)} line segments.")
    if len(lines) == 0:
        print("No lines found on target layers.")
        return

    # Calculate center of the project
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 2. Export original coordinates to Shapefile
    shp_path = "parcels_original"
    print(f"Writing {shp_path}.shp (Original coords)...")
    with shapefile.Writer(shp_path, shapeType=shapefile.POLYLINE) as shp:
        shp.field("ID", "N")
        shp.field("Layer", "C", 50)
        
        for i, (pts, layer) in enumerate(lines):
            shp.line([pts])
            shp.record(i + 1, layer)
            
    # 3. Export WGS84 normalized coordinates to GeoJSON
    # We will simulate the project being in Vietnam (Long: 106.0, Lat: 10.0)
    # 1 degree is roughly 111,000 meters.
    geojson_path = "parcels_web.geojson"
    print(f"Writing {geojson_path} (WGS84 fake coords)...")
    
    features = []
    for i, (pts, layer) in enumerate(lines):
        # Translate and scale
        wgs84_pts = []
        for x, y in pts:
            # Convert local meters to degrees and shift to Vietnam
            lon = ((x - center_x) / 111320.0) + 106.0 
            lat = ((y - center_y) / 110574.0) + 10.0
            wgs84_pts.append((lon, lat))
            
        line = LineString(wgs84_pts)
        feature = {
            "type": "Feature",
            "properties": {
                "ID": i + 1,
                "Layer": layer
            },
            "geometry": mapping(line)
        }
        features.append(feature)
        
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, ensure_ascii=False, indent=2)
        
    print("Conversion completed successfully!")

if __name__ == "__main__":
    convert()
