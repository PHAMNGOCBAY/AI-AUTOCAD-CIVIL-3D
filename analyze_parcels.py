import sqlite3
import math

def analyze():
    conn = sqlite3.connect('bim_data.sqlite')
    cursor = conn.cursor()
    
    # Get all parcels
    cursor.execute("""
        SELECT e.element_id, e.name, 
               CAST(p_area.prop_value AS REAL) as area,
               CAST(p_perim.prop_value AS REAL) as perimeter,
               g.bbox_min_x, g.bbox_min_y, g.bbox_max_x, g.bbox_max_y
        FROM elements e
        JOIN element_geometry g ON e.element_id = g.element_id
        LEFT JOIN element_properties p_area ON e.element_id = p_area.element_id AND p_area.prop_name = 'Area'
        LEFT JOIN element_properties p_perim ON e.element_id = p_perim.element_id AND p_perim.prop_name = 'Perimeter'
        WHERE e.object_type = 'Parcel'
    """)
    
    parcels = cursor.fetchall()
    
    total_parcels = len(parcels)
    if total_parcels == 0:
        print("No parcels found.")
        return
        
    areas = []
    aspect_ratios = []
    small_parcels = []
    long_parcels = []
    
    for row in parcels:
        eid, name, area, perim, bminx, bminy, bmaxx, bmaxy = row
        
        if area is not None:
            areas.append(area)
            if area < 50:  # Assuming < 50 sq units is suspiciously small
                small_parcels.append((name, area))
                
        # Calculate aspect ratio of bounding box
        width = bmaxx - bminx
        height = bmaxy - bminy
        if width > 0 and height > 0:
            aspect_ratio = max(width/height, height/width)
            aspect_ratios.append(aspect_ratio)
            if aspect_ratio > 10: # Suspiciously long/narrow
                long_parcels.append((name, aspect_ratio))
                
    if not areas:
        print("No area data found for parcels.")
        return
        
    avg_area = sum(areas) / len(areas)
    min_area = min(areas)
    max_area = max(areas)
    
    print(f"Total Parcels: {total_parcels}")
    print(f"Area -> Min: {min_area:.2f}, Max: {max_area:.2f}, Avg: {avg_area:.2f}")
    
    avg_aspect = sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0
    max_aspect = max(aspect_ratios) if aspect_ratios else 0
    print(f"Aspect Ratio -> Max: {max_aspect:.2f}, Avg: {avg_aspect:.2f}")
    
    print(f"Parcels < 50 sq units: {len(small_parcels)}")
    if small_parcels:
        print("  Sample:", small_parcels[:5])
        
    print(f"Parcels with Aspect Ratio > 10: {len(long_parcels)}")
    if long_parcels:
        print("  Sample:", long_parcels[:5])
        
if __name__ == "__main__":
    analyze()
