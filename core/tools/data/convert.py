"""Convert data tool for converting between GIS formats."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool


class ConvertDataTool(Tool):
    """Tool for converting GIS data between formats."""

    @property
    def name(self) -> str:
        return "convert_data"

    @property
    def description(self) -> str:
        return "Convert GIS data from one format to another (e.g., GeoJSON to Shapefile)."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Input file path"
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path"
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format (e.g., geojson, shapefile, gpkg). Auto-detected from output_file extension if not specified."
                }
            },
            "required": ["input_file", "output_file"]
        }

    async def execute(
        self,
        input_file: str,
        output_file: str,
        output_format: str | None = None,
        **kwargs
    ) -> str:
        try:
            import geopandas as gpd

            input_path = Path(input_file)
            output_path = Path(output_file)

            if not input_path.is_absolute():
                input_path = Path.cwd() / input_path
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path

            if not input_path.exists():
                return f"Error: Input file not found: {input_path}"

            # Read input
            gdf = gpd.read_file(input_path)

            if len(gdf) == 0:
                return f"Error: No features found in input file"

            # Determine driver from output_format or extension
            driver_map = {
                "geojson": "GeoJSON",
                "gpkg": "GPKG",
                "shapefile": "ESRI Shapefile",
                "shp": "ESRI Shapefile",
                "geopackage": "GPKG"
            }

            if output_format:
                driver = driver_map.get(output_format.lower())
                if not driver:
                    return f"Error: Unsupported output format '{output_format}'. Supported: {', '.join(driver_map.keys())}"
            else:
                # Auto-detect from extension
                ext = output_path.suffix.lower().lstrip('.')
                driver = driver_map.get(ext, "GeoJSON")

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            gdf.to_file(output_path, driver=driver, index=False)

            return f"Successfully converted {len(gdf)} features from {input_path} to {output_path} (format: {driver})"

        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except Exception as e:
            return f"Error converting data: {str(e)}"