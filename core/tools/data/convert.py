"""Convert data tool for converting between GIS formats."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool
from core.tools.data.formats import VECTOR_FORMATS, get_driver_from_extension


class ConvertDataTool(Tool):
    """Tool for converting GIS data between formats."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "convert_data"

    @property
    def description(self) -> str:
        return "Convert GIS data from one format to another (e.g., GeoJSON to Shapefile). Paths are relative to workspace unless absolute."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Input file path (relative to workspace or absolute)"
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path (relative to workspace or absolute)"
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
                input_path = self.workspace / input_path
            if not output_path.is_absolute():
                output_path = self.workspace / output_path

            if not input_path.exists():
                return f"Error: Input file not found: {input_path}"

            # Read input
            gdf = gpd.read_file(input_path)

            if len(gdf) == 0:
                return f"Error: No features found in input file"

            # Determine driver from output_format or extension
            if output_format:
                driver = get_driver_from_extension(f".{output_format.lstrip('.')}")
                if driver is None:
                    # Try direct driver name
                    driver_map = {
                        "geojson": "GeoJSON",
                        "gpkg": "GPKG",
                        "shapefile": "ESRI Shapefile",
                        "shp": "ESRI Shapefile",
                        "geopackage": "GPKG",
                        "kml": "KML",
                        "gml": "GML",
                        "gpx": "GPX",
                        "csv": "CSV",
                        "dxf": "DXF",
                        "sqlite": "SQLite",
                    }
                    driver = driver_map.get(output_format.lower())
                if driver is None:
                    return f"Error: Unsupported output format '{output_format}'. Supported: geojson, gpkg, shp, kml, gml, gpx, csv, dxf, sqlite"
            else:
                # Auto-detect from extension
                ext = output_path.suffix.lower()
                driver = get_driver_from_extension(ext)
                if driver is None:
                    # Fallback
                    driver_map = {
                        ".geojson": "GeoJSON",
                        ".gpkg": "GPKG",
                        ".shp": "ESRI Shapefile",
                        ".json": "GeoJSON",
                    }
                    driver = driver_map.get(ext, "GeoJSON")

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            gdf.to_file(output_path, driver=driver, index=False)

            # Show relative paths if inside workspace
            input_display = input_file
            output_display = output_file
            try:
                rel_in = input_path.relative_to(self.workspace)
                rel_out = output_path.relative_to(self.workspace)
                input_display = f"workspace/{rel_in}"
                output_display = f"workspace/{rel_out}"
            except ValueError:
                pass

            return f"Successfully converted {len(gdf)} features from {input_display} to {output_display} (format: {driver})"

        except ImportError:
            return "Error: geopandas library is required. Install with: pip install geopandas"
        except Exception as e:
            return f"Error converting data: {str(e)}"