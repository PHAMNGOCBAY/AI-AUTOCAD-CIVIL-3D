import sqlite3
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def plot_smallest():
    conn = sqlite3.connect('bim_data.sqlite')
    cursor = conn.cursor()
    
    # Query the smallest parcels by Area
    cursor.execute("""
        SELECT e.name, 
               CAST(p_area.prop_value AS REAL) as area,
               g.bbox_min_x, g.bbox_min_y, g.bbox_max_x, g.bbox_max_y
        FROM elements e
        JOIN element_geometry g ON e.element_id = g.element_id
        LEFT JOIN element_properties p_area ON e.element_id = p_area.element_id AND p_area.prop_name = 'Area'
        WHERE e.object_type = 'Parcel' AND p_area.prop_value IS NOT NULL
        ORDER BY area ASC
        LIMIT 5
    """)
    
    smallest_parcels = cursor.fetchall()
    
    if not smallest_parcels:
        print("No parcels found.")
        return
        
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # We will plot each parcel in its own subplot or space, but since they have global coordinates,
    # they might be far apart. So we'll plot them on a grid relative to their own center.
    
    for i, row in enumerate(smallest_parcels):
        name, area, minx, miny, maxx, maxy = row
        width = maxx - minx
        height = maxy - miny
        
        # Add a subplot for each parcel
        ax = plt.subplot(2, 3, i + 1)
        rect = patches.Rectangle((0, 0), width, height, linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        
        # Annotate dimensions
        ax.text(width/2, -height*0.1, f"W: {width:.2f}", ha='center', fontsize=9)
        ax.text(-width*0.1, height/2, f"H: {height:.2f}", va='center', rotation=90, fontsize=9)
        
        ax.set_xlim(-width*0.2, width*1.2)
        ax.set_ylim(-height*0.2, height*1.2)
        ax.set_title(f"Lô: {name}\nDiện tích: {area:.1f}", fontsize=10)
        ax.axis('off')
        
    plt.tight_layout()
    
    output_path = r"C:\Users\bayng\.gemini\antigravity-ide\brain\d38fe9db-91f3-4676-b0db-86765e1db3c3\smallest_parcels.png"
    plt.savefig(output_path, dpi=150)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    plot_smallest()
