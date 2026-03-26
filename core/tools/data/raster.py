"""Read raster data tool for loading GIS raster files."""

from pathlib import Path
from typing import Any
from core.tools.base import Tool
from core.tools.data.formats import get_driver_from_extension, is_raster_format


class ReadRasterTool(Tool):
    """Tool for reading raster data from various formats."""

    _MAX_BANDS = 10  # Limit bands for large rasters
    _MAX_HISTOGRAM = 256  # Histogram bins

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "read_raster"

    @property
    def description(self) -> str:
        return (
            "Read a raster data file (GeoTIFF, TIFF, IMG, PNG, JPG, ECW, JP2, etc.). "
            "Returns raster dimensions, bands, data type, CRS, bounds, and statistics. "
            "File paths are relative to workspace unless absolute."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the raster file (relative to workspace or absolute)"
                },
                "band": {
                    "type": "integer",
                    "description": "Specific band to read (optional, reads all if not specified)"
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str, band: int | None = None, **kwargs) -> str:
        try:
            import numpy as np
            import rasterio
            from rasterio.warp import calculate_default_transform, reproject, Resampling

            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace / path

            if not path.exists():
                return f"Error: File not found: {path}"

            # Check if it's a raster format
            if not is_raster_format(path.suffix):
                # Still try to open, might be a valid raster
                pass

            with rasterio.open(path) as src:
                # Get basic info
                width = src.width
                height = src.height
                count = src.count
                dtype = src.dtypes[0] if count > 0 else "None"
                crs_str = str(src.crs) if src.crs else "No CRS defined"

                # Get bounds
                bounds = src.bounds
                bounds_list = [bounds.left, bounds.bottom, bounds.right, bounds.top]

                # Get transform
                transform_str = f"pixel_size={src.res[0]:.4f} x {src.res[1]:.4f}"

                # Build result
                result_lines = [
                    f"Successfully read {file_path}:",
                    f"- Format: {src.driver} ({get_driver_from_extension(path.suffix) or 'Unknown'})",
                    f"- Dimensions: {width} x {height} pixels",
                    f"- Bands: {count}",
                    f"- Data type: {dtype}",
                    f"- CRS: {crs_str}",
                    f"- Bounds: [{bounds_list[0]:.4f}, {bounds_list[1]:.4f}, {bounds_list[2]:.4f}, {bounds_list[3]:.4f}]",
                    f"- Transform: {transform_str}",
                ]

                # Get band info
                result_lines.append("\nBand Information:")

                band_to_read = [band] if band else range(1, min(count + 1, self._MAX_BANDS + 1))

                for i in band_to_read:
                    if i > count:
                        continue

                    try:
                        band_data = src.read(i)
                        nodata = src.nodatavals[i - 1]

                        # Statistics
                        if np.issubdtype(band_data.dtype, np.number):
                            valid_data = band_data[band_data != nodata] if nodata is not None else band_data
                            if len(valid_data) > 0:
                                stats = {
                                    "min": float(np.min(valid_data)),
                                    "max": float(np.max(valid_data)),
                                    "mean": float(np.mean(valid_data)),
                                    "std": float(np.std(valid_data))
                                }
                                result_lines.append(
                                    f"  Band {i}: min={stats['min']:.4f}, max={stats['max']:.4f}, "
                                    f"mean={stats['mean']:.4f}, std={stats['std']:.4f}, "
                                    f"nodata={nodata}"
                                )
                            else:
                                result_lines.append(f"  Band {i}: No valid data, nodata={nodata}")
                        else:
                            result_lines.append(f"  Band {i}: Non-numeric data type {dtype}")

                    except Exception as e:
                        result_lines.append(f"  Band {i}: Error reading - {str(e)}")

                if count > self._MAX_BANDS:
                    result_lines.append(f"\n... ({count - self._MAX_BANDS} more bands not shown)")

                return "\n".join(result_lines)

        except ImportError:
            return "Error: rasterio library is required. Install with: pip install rasterio"
        except Exception as e:
            return f"Error reading raster file: {str(e)}"


class WriteRasterTool(Tool):
    """Tool for writing raster data to various formats."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "write_raster"

    @property
    def description(self) -> str:
        return (
            "Write raster data to a file (GeoTIFF, TIFF, PNG, etc.). "
            "Data must be provided as base64-encoded numpy array or array data. "
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
                    "description": "Raster data as base64-encoded numpy array or reference to existing file"
                },
                "driver": {
                    "type": "string",
                    "description": "GDAL driver name (e.g., GTiff, PNG, JPEG). Auto-detected from extension if not specified."
                },
                "dtype": {
                    "type": "string",
                    "description": "Data type (e.g., uint8, float32, int16). Default: float32"
                },
                "crs": {
                    "type": "string",
                    "description": "Coordinate reference system (e.g., EPSG:4528). Default: EPSG:4528"
                },
                "transform": {
                    "type": "string",
                    "description": "Affine transform as comma-separated values (e.g., '10,0,0,0,-10,500'). Optional"
                }
            },
            "required": ["file_path"]
        }

    async def execute(
        self,
        file_path: str,
        data: str | None = None,
        driver: str | None = None,
        dtype: str = "float32",
        crs: str = "EPSG:4528",
        transform: str | None = None,
        **kwargs
    ) -> str:
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_bounds
            from rasterio.crs import CRS

            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace / path

            # Create parent directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Determine driver from extension if not specified
            if driver is None:
                driver = get_driver_from_extension(path.suffix)
                if driver is None:
                    return f"Error: Unknown raster format '{path.suffix}'. Supported: GeoTIFF (.tif), PNG (.png), JPG (.jpg), etc."

            # If data is not provided, create a minimal placeholder
            if data is None or data == "":
                # Create a 100x100 placeholder raster
                raster_data = np.zeros((1, 100, 100), dtype=dtype)
                bounds = [0, 0, 100, 100]
            else:
                # Parse data - try as existing file path first
                data_path = Path(data)
                if data_path.exists():
                    # Read from existing file
                    with rasterio.open(data_path) as src:
                        raster_data = src.read()
                        bounds = list(src.bounds)
                        if not crs:
                            crs = str(src.crs) if src.crs else crs
                else:
                    # Try to parse as base64 encoded array
                    try:
                        import base64
                        import pickle
                        decoded = base64.b64decode(data)
                        raster_data = pickle.loads(decoded)
                        bounds = [0, 0, raster_data.shape[2] if raster_data.ndim == 3 else raster_data.shape[1],
                                  raster_data.shape[1] if raster_data.ndim == 3 else raster_data.shape[0], 0]
                    except Exception:
                        return "Error: Could not parse data. Provide a valid file path or base64-encoded array."

            # Handle transform
            if transform:
                try:
                    # Parse comma-separated transform values
                    transform_values = [float(x) for x in transform.split(',')]
                    from rasterio.transform import Affine
                    if len(transform_values) == 6:
                        affine_transform = Affine(transform_values[0], transform_values[1], transform_values[2],
                                                transform_values[3], transform_values[4], transform_values[5])
                    else:
                        affine_transform = None
                except Exception:
                    affine_transform = None
            else:
                # Create transform from bounds
                if len(bounds) == 4:
                    affine_transform = from_bounds(*bounds, raster_data.shape[2], raster_data.shape[1])
                else:
                    affine_transform = from_bounds(0, 0, raster_data.shape[2], raster_data.shape[1],
                                                   raster_data.shape[2], raster_data.shape[1])

            # Parse CRS
            try:
                raster_crs = CRS.from_string(crs)
            except Exception:
                raster_crs = None

            # Write raster
            height, width = raster_data.shape[1], raster_data.shape[2]
            with rasterio.open(
                path,
                'w',
                driver=driver,
                height=height,
                width=width,
                count=raster_data.shape[0],
                dtype=raster_data.dtype,
                crs=raster_crs,
                transform=affine_transform
            ) as dst:
                dst.write(raster_data)

            # Show relative path if inside workspace
            display_path = file_path
            try:
                rel = path.relative_to(self.workspace)
                display_path = f"workspace/{rel}"
            except ValueError:
                pass

            return f"Successfully wrote raster to {display_path} (driver: {driver}, bands: {raster_data.shape[0]}, size: {width}x{height})"

        except ImportError:
            return "Error: rasterio library is required. Install with: pip install rasterio"
        except Exception as e:
            return f"Error writing raster file: {str(e)}"


class ConvertRasterTool(Tool):
    """Tool for converting raster data between formats."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "convert_raster"

    @property
    def description(self) -> str:
        return "Convert raster data from one format to another (e.g., GeoTIFF to PNG). Paths are relative to workspace unless absolute."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_file": {
                    "type": "string",
                    "description": "Input raster file path (relative to workspace or absolute)"
                },
                "output_file": {
                    "type": "string",
                    "description": "Output raster file path (relative to workspace or absolute)"
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format (e.g., gtiff, png, jpeg). Auto-detected from output_file extension if not specified."
                },
                "resampling": {
                    "type": "string",
                    "description": "Resampling method (nearest, bilinear, cubic, average). Default: nearest",
                    "enum": ["nearest", "bilinear", "cubic", "average"]
                }
            },
            "required": ["input_file", "output_file"]
        }

    async def execute(
        self,
        input_file: str,
        output_file: str,
        output_format: str | None = None,
        resampling: str = "nearest",
        **kwargs
    ) -> str:
        try:
            import rasterio
            from rasterio.warp import reproject, Resampling

            input_path = Path(input_file)
            output_path = Path(output_file)

            if not input_path.is_absolute():
                input_path = self.workspace / input_path
            if not output_path.is_absolute():
                output_path = self.workspace / output_path

            if not input_path.exists():
                return f"Error: Input file not found: {input_path}"

            # Map resampling string to Resampling enum
            resampling_map = {
                "nearest": Resampling.nearest,
                "bilinear": Resampling.bilinear,
                "cubic": Resampling.cubic,
                "average": Resampling.average
            }
            resample_method = resampling_map.get(resampling.lower(), Resampling.nearest)

            # Determine driver from output_format or extension
            driver = get_driver_from_extension(output_path.suffix)
            if output_format:
                driver = get_driver_from_extension(f".{output_format}")

            if driver is None:
                return f"Error: Unknown output format '{output_path.suffix}'. Supported: GeoTIFF (.tif), PNG (.png), etc."

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Read input and write output
            with rasterio.open(input_path) as src:
                # Handle format-specific conversions
                if driver == "PNG":
                    # For PNG, clip values to 0-255 and convert to uint8
                    profile = src.profile
                    profile.update({
                        "driver": driver,
                        "dtype": "uint8",
                        "count": min(src.count, 4)  # PNG supports up to 4 bands (RGBA)
                    })
                elif driver == "JPEG":
                    profile = src.profile
                    profile.update({
                        "driver": driver,
                        "dtype": "uint8",
                        "count": 3  # JPEG only supports 3 bands (RGB)
                    })
                else:
                    profile = src.profile
                    profile.update({"driver": driver})

                with rasterio.open(output_path, 'w', **profile) as dst:
                    for i in range(1, src.count + 1):
                        if driver == "JPEG" and i > 3:
                            break  # Skip extra bands for JPEG
                        if driver == "PNG" and i > 4:
                            break  # Skip extra bands for PNG

                        # Read and write band
                        data = src.read(i)

                        # Convert to uint8 for image formats
                        if driver in ["PNG", "JPEG"]:
                            data = data.astype(float)
                            data_min, data_max = data.min(), data.max()
                            if data_max > data_min:
                                data = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)
                            else:
                                data = np.zeros_like(data, dtype=np.uint8)

                        dst.write(data, i)

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

            return f"Successfully converted raster from {input_display} to {output_display} (format: {driver})"

        except ImportError:
            return "Error: rasterio library is required. Install with: pip install rasterio"
        except Exception as e:
            return f"Error converting raster: {str(e)}"