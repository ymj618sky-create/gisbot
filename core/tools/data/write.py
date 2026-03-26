"""Write data tool for saving GIS data files."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool
from core.tools.data.formats import VECTOR_FORMATS, get_driver_from_extension


class WriteDataTool(Tool):
    """Tool for writing GIS data to various formats."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "write_data"

    @property
    def description(self) -> str:
        return (
            "Write a GeoDataFrame to a file (GeoJSON, Shapefile, GeoPackage, etc.). "
            "Data must be provided as a serialized GeoJSON string. "
            "File paths are relative to workspace unless absolute."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Output file path (relative to workspace, or absolute)"
                },
                "data": {
                    "type": "string",
                    "description": "GeoDataFrame as GeoJSON string"
                },
                "driver": {
                    "type": "string",
                    "description": "GDAL driver name (e.g., GeoJSON, GPKG, ESRI Shapefile). Auto-detected from extension if not specified."
                }
            },
            "required": ["file_path", "data"]
        }

    async def execute(self, file_path: str, data: str, driver: str | None = None, **kwargs) -> str:
        try:
            import json
            import geopandas as gpd

            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace / path

            # Create parent directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Parse GeoJSON and create GeoDataFrame
            geojson_data = json.loads(data)
            features = geojson_data.get("features", [])

            # Allow empty feature collections (some GIS operations start with empty data)
            if features:
                gdf = gpd.GeoDataFrame.from_features(features)
            else:
                # Create empty GeoDataFrame with proper schema
                gdf = gpd.GeoDataFrame(columns=['geometry'], crs='EPSG:4528')

            # Determine driver from extension if not specified
            if driver is None:
                ext = path.suffix.lower()
                driver = get_driver_from_extension(ext)
                if driver is None:
                    # Fallback for common formats
                    driver_map = {
                        ".geojson": "GeoJSON",
                        ".gpkg": "GPKG",
                        ".shp": "ESRI Shapefile",
                        ".json": "GeoJSON",
                        ".geojsonl": "GeoJSONSeq",
                    }
                    driver = driver_map.get(ext, "GeoJSON")

            # Write the data
            gdf.to_file(path, driver=driver, index=False)

            # Show relative path if inside workspace
            display_path = path
            try:
                rel = path.relative_to(self.workspace)
                display_path = f"workspace/{rel}"
            except ValueError:
                pass

            return f"Successfully wrote {len(gdf)} features to {display_path} (driver: {driver})"

        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except json.JSONDecodeError as e:
            return f"Error parsing GeoJSON: {str(e)}"
        except Exception as e:
            return f"Error writing data file: {str(e)}"