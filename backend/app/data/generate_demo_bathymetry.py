"""Generate synthetic deterministic bathymetry data for Indian Ocean demo region."""

from __future__ import annotations

import json
import math
from pathlib import Path

# Indian Ocean demo region
LATITUDES = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
LONGITUDES = [45.0, 55.0, 65.0, 75.0, 85.0, 95.0]


def seafloor_depth_for(lat: float, lon: float) -> float:
    """
    Deterministic smooth bathymetry function for Indian Ocean.
    
    Returns seafloor depth in meters (positive value below sea level).
    Uses smooth sinusoidal/cosine functions to vary depth geographically.
    """
    # Base depth increases with latitude (mimics ridge/basin structure)
    base_depth = 3500.0 + 800.0 * (lat / 30.0)
    
    # East-west variation (ridge-like features)
    ew_variation = 1200.0 * math.cos((lon - 45.0) / 25.0)
    
    # North-south undulation
    ns_variation = 600.0 * math.sin((lat - 5.0) / 15.0)
    
    # Combined depth with slight noise for realism
    depth = base_depth + ew_variation + ns_variation
    
    # Ensure depth is within plausible ocean range (100m to 7000m)
    depth = max(100.0, min(7000.0, depth))
    
    return round(depth, 1)


def is_land(lat: float, lon: float) -> bool:
    """
    Determine if location is land or ocean.
    For Indian Ocean demo, we'll mark no locations as land.
    """
    return False


def build_records() -> list[dict]:
    """Generate synthetic bathymetry records for demo region."""
    records: list[dict] = []
    
    for lat in LATITUDES:
        for lon in LONGITUDES:
            depth = seafloor_depth_for(lat, lon)
            land = is_land(lat, lon)
            
            records.append({
                'bathymetry_id': f'bathy-{len(records) + 1:04d}',
                'dataset_id': 'demo-indian-ocean-bathymetry',
                'source_type': 'bathymetry',
                'source': 'demo-synthetic-bathymetry',
                'latitude': round(lat, 2),
                'longitude': round(lon, 2),
                'seafloor_depth': depth,
                'is_land': land,
            })
    
    return records


def generate_bathymetry_file(output_path: Path | None = None) -> None:
    """Generate and write bathymetry JSON file."""
    if output_path is None:
        output_path = Path(__file__).resolve().parent / 'bathymetry.json'
    
    records = build_records()
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    
    print(f'Generated {len(records)} bathymetry records to {output_path}')


if __name__ == '__main__':
    generate_bathymetry_file()
