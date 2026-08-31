from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEPTHS = [0.0, 50.0, 100.0, 200.0, 500.0]
TIMESTAMPS = [
    datetime(2026, 8, 24, 0, 0, tzinfo=timezone.utc) + timedelta(hours=offset)
    for offset in range(0, 24, 4)
]
LATITUDES = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
LONGITUDES = [45.0, 55.0, 65.0, 75.0, 85.0, 95.0]


def to_iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')


def temperature_for(lat: float, lon: float, depth: float, timestamp_index: int) -> float:
    depth_term = depth * 0.012
    seasonal_wave = 0.6 * math.sin((lon - 45.0) / 18.0 + timestamp_index * 0.9)
    return 31.0 - 0.22 * lat - 0.08 * (lon - 45.0) / 15.0 - depth_term + seasonal_wave


def salinity_for(lat: float, lon: float, depth: float, timestamp_index: int) -> float:
    spatial = 0.12 * math.sin((lon - 60.0) / 12.0 + timestamp_index * 0.7)
    depth_term = 0.0035 * depth
    return 34.7 + 0.08 * (lat / 30.0) + spatial + depth_term


def current_u_for(lat: float, lon: float, depth: float, timestamp_index: int) -> float:
    return 0.18 * math.sin((lon - 45.0) / 15.0 + timestamp_index * 0.8) + 0.12 * math.cos(lat / 18.0) - (depth / 1000.0)


def current_v_for(lat: float, lon: float, depth: float, timestamp_index: int) -> float:
    return -0.15 * math.cos((lat - 10.0) / 20.0 + timestamp_index * 0.7) + 0.08 * math.sin((lon - 60.0) / 18.0) - (depth / 1500.0)


def build_records() -> list[dict]:
    records: list[dict] = []
    for time_index, timestamp in enumerate(TIMESTAMPS):
        for lat in LATITUDES:
            for lon in LONGITUDES:
                for depth in DEPTHS:
                    temp = temperature_for(lat, lon, depth, time_index)
                    sal = salinity_for(lat, lon, depth, time_index)
                    u = current_u_for(lat, lon, depth, time_index)
                    v = current_v_for(lat, lon, depth, time_index)

                    records.append(
                        {
                            'model_id': f'model-{time_index + 1:02d}-{len(records) + 1:04d}',
                            'dataset_id': 'demo-indian-ocean-model',
                            'source_type': 'model',
                            'source': 'demo-synthetic-model',
                            'timestamp': to_iso_utc(timestamp),
                            'latitude': round(lat, 2),
                            'longitude': round(lon, 2),
                            'depth': float(depth),
                            'temperature': round(temp, 2),
                            'salinity': round(sal, 2),
                            'current_u': round(u, 3),
                            'current_v': round(v, 3),
                        }
                    )
    return records


if __name__ == '__main__':
    output_path = Path(__file__).resolve().with_name('model_data.json')
    payload = build_records()
    output_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(payload)} demo model records to {output_path}')
