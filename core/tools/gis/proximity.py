"""Proximity analysis tools."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool, GISError, EmptyResultError


class BufferTool(Tool):
    """Create buffer zones around features."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "buffer"

    @property
    def description(self) -> str:
        return "Create a buffer zone around input features at a specified distance. Input is GeoJSON string, output is returned as GeoJSON."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_data": {
                    "type": "string",
                    "description": "Input GeoDataFrame as GeoJSON string"
                },
                "distance": {
                    "type": "number",
                    "description": "Buffer distance"
                },
                "unit": {
                    "type": "string",
                    "description": "Distance unit (meter, kilometer, degree)",
                    "enum": ["meter", "kilometer", "degree"]
                }
            },
            "required": ["input_data", "distance"]
        }

    async def execute(self, input_data: str, distance: float, unit: str = "meter", **kwargs) -> str:
        try:
            import json
            import geopandas as gpd

            # Parse GeoJSON
            geojson_data = json.loads(input_data)
            features = geojson_data.get("features", [])

            if not features:
                # Return error message for empty features
                return "Error: Input GeoDataFrame has no features"

            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(features)

            # Handle distance units
            if unit == "kilometer":
                distance_meters = distance * 1000  # Convert to meters
            elif unit == "degree":
                # Approximate: 1 degree ≈ 111 km at equator
                distance_meters = distance * 111000
            else:  # meter
                distance_meters = distance

            # Ensure CRS is set (default to CGCS2000 zone 40 if not set)
            if gdf.crs is None:
                gdf.crs = "EPSG:4528"

            # Reproject to appropriate CRS for distance calculations if needed
            if gdf.crs.is_geographic:
                # Use estimated UTM zone for accurate distance calculations
                try:
                    target_crs = gdf.estimate_utm_crs()
                    gdf_proj = gdf.to_crs(target_crs)
                except Exception:
                    # Fallback to a projected CRS (e.g., WGS84 Web Mercator)
                    gdf_proj = gdf.to_crs("EPSG:3857")
            else:
                gdf_proj = gdf

            # Create buffer
            gdf_buffered = gdf_proj.buffer(distance_meters)

            # Convert back to original CRS if we projected
            if gdf.crs.is_geographic:
                gdf_buffered = gdf_buffered.to_crs(gdf.crs)
            else:
                gdf_buffered = gdf_buffered

            # Create result GeoDataFrame
            gdf_result = gpd.GeoDataFrame(geometry=gdf_buffered, crs=gdf.crs)

            # Return as GeoJSON
            return gdf_result.to_json()

        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except Exception as e:
            return f"Error creating buffer: {str(e)}"