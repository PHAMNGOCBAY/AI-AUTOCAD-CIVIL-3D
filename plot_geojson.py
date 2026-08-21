import json
import matplotlib.pyplot as plt

def plot_geojson():
    with open('parcels_web.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for feature in data.get('features', []):
        geom = feature.get('geometry')
        if not geom:
            continue
            
        geom_type = geom.get('type')
        coords = geom.get('coordinates')
        
        if geom_type == 'LineString':
            x = [p[0] for p in coords]
            y = [p[1] for p in coords]
            ax.plot(x, y, color='blue', linewidth=1)
            
    ax.set_aspect('equal')
    ax.set_title('Parcels Web GeoJSON Plot', fontsize=16)
    ax.axis('off')  # Hide axes for cleaner look
    
    plt.tight_layout()
    output_path = r"C:\Users\bayng\.gemini\antigravity-ide\brain\d38fe9db-91f3-4676-b0db-86765e1db3c3\parcels_web.png"
    plt.savefig(output_path, dpi=300)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    plot_geojson()
