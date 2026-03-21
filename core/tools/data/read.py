"""Read data tool for loading GIS data files."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool


class ReadDataTool(Tool):
    """Tool for reading GIS data from various formats."""

    @property
    def name(self) -> str:
        return "read_data"

    @property
    def description(self) -> str:
        return (
            "Read a GIS data file (GeoJSON, Shapefile, GeoPackage, etc.). "
            "Returns layer info, feature count, CRS, and spatial bounds."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the data file (relative to workspace or absolute)"
                },
                "layer": {
                    "type": "string",
                    "description": "Layer name for multi-layer formats like GeoPackage (optional)"
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str, layer: str | None = None, **kwargs) -> str:
        try:
            # Import geopandas
            import geopandas as gpd

            path = Path(file_path)
            if not path.is_absolute():
                path = Path.cwd() / path

            if not path.exists():
                return f"Error: File not found: {path}"

            # Read the data
            if layer:
                gdf = gpd.read_file(path, layer=layer)
            else:
                gdf = gpd.read_file(path)

            # Get layer info
            layer_name = layer or getattr(gdf, 'name', 'main')
            feature_count = len(gdf)

            if feature_count == 0:
                return f"Successfully read {file_path}: No features found"

            # Get CRS info
            crs_str = str(gdf.crs) if gdf.crs else "No CRS defined"

            # Get bounds
            bounds = gdf.total_bounds.tolist()

            # Get geometry types
            geom_types = gdf.geometry.type.unique().tolist()

            # Get columns
            columns = ', '.join(gdf.columns.tolist())

            return f"""Successfully read {file_path}:
- FeatureCollection type: {gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'Unknown'}
- Format: {path.suffix[1:].upper() if path.suffix else 'Unknown'}
- Layer: {layer_name}
- Features: {feature_count}
- Columns: {columns}
- CRS: {crs_str}
- Bounds: [{bounds[0]:.4f}, {bounds[1]:.4f}, {bounds[2]:.4f}, {bounds[3]:.4f}]
- Geometry types: {', '.join(geom_types)}"""

        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except Exception as e:
            return f"Error reading data file: {str(e)}"