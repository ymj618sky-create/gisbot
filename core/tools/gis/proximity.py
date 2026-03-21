"""Proximity analysis tools."""

from typing import Any
from core.tools.base import Tool, GISError, EmptyResultError


class BufferTool(Tool):
    """Create buffer zones around features."""

    @property
    def name(self) -> str:
        return "buffer"

    @property
    def description(self) -> str:
        return "Create a buffer zone around input features at a specified distance."

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

            # Ensure CRS is set (default to WGS84 if not set)
            if gdf.crs is None:
                gdf.crs = "EPSG:4326"

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
            buffered = gdf_proj.geometry.buffer(distance_meters)

            # Create result GeoDataFrame
            result_gdf = gpd.GeoDataFrame(
                {"original_index": gdf.index, "buffer_distance": distance_meters},
                geometry=buffered,
                crs=gdf_proj.crs
            )

            # Calculate buffer areas in square kilometers
            result_gdf["buffer_area_sqkm"] = result_gdf.geometry.area / 1_000_000
            total_area = result_gdf["buffer_area_sqkm"].sum()

            # Revert to original CRS for consistency
            result_gdf = result_gdf.to_crs(gdf.crs)

            return f"""Successfully created buffer zones:
- Input features: {len(gdf)}
- Buffer distance: {distance} {unit}
- Total buffer area: {total_area:.2f} km²
- CRS: {gdf.crs}"""

        except EmptyResultError:
            raise
        except json.JSONDecodeError:
            return "Error: Invalid GeoJSON data. Please provide valid JSON string."
        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except Exception as e:
            raise GISError(f"Buffer operation failed: {str(e)}")