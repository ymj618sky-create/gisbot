"""Supported GIS data formats for vector and raster data."""

# Vector format mappings (extension -> GDAL driver)
VECTOR_FORMATS = {
    # Common vector formats
    ".shp": "ESRI Shapefile",
    ".geojson": "GeoJSON",
    ".json": "GeoJSON",
    ".geojsonl": "GeoJSONSeq",
    ".gpkg": "GPKG",
    ".kml": "KML",
    ".kmz": "LIBKML",
    ".gml": "GML",
    ".gpx": "GPX",
    ".topojson": "TopoJSON",
    ".wkt": "WKT",
    ".wkb": "WKB",
    ".csv": "CSV",
    ".dbf": "DBF",
    ".dxf": "DXF",
    ".dgn": "DGN",
    ".tab": "MapInfo File",
    ".mif": "MapInfo File",
    ".vrt": "VRT",
    ".osm": "OSM",
    ".pbf": "OSM",
    ".fgdb": "OpenFileGDB",
    ".gdb": "OpenFileGDB",
    ".mdb": "PGeo",
    ".sqlite": "SQLite",
    ".ods": "ODS",
    ".xls": "XLS",
    ".xlsx": "XLSX",
    ".geo": "Geoconcept",
    ".gmt": "GMT",
    ".bna": "BNA",
    ".gxt": "GXT",
    ".nitf": "NITF",
    ".rte": "GPX",
    ".trk": "GPX",
    ".wpt": "GPX",
    ".xml": "GML",
    ".zip": "KML",  # KMZ is ZIP format
    ".geojson.gz": "GeoJSON",
    ".geojson.bz2": "GeoJSON",
}

# Raster format mappings (extension -> GDAL driver)
RASTER_FORMATS = {
    # Common raster formats
    ".tif": "GTiff",
    ".tiff": "GTiff",
    ".geotiff": "GTiff",
    ".img": "HFA",  # ERDAS Imagine
    ".bil": "EHdr",  # ESRI BIL
    ".bip": "EHdr",  # ESRI BIP
    ".bsq": "EHdr",  # ESRI BSQ
    ".asc": "AAIGrid",  # ASCII Grid
    ".grd": "SAGA",  # SAGA GIS
    ".nc": "netCDF",
    ".cdf": "netCDF",
    ".h5": "HDF5",
    ".hdf": "HDF5",
    ".hdf4": "HDF4",
    ".hdf5": "HDF5",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".bmp": "BMP",
    ".gif": "GIF",
    ".webp": "WEBP",
    ".ecw": "ECW",
    ".jp2": "JP2OpenJPEG",
    ".j2k": "JP2OpenJPEG",
    ".mrf": "MRF",
    ".vrt": "VRT",  # Virtual Raster
    ".adf": "AIG",  # ArcInfo Grid
    ".dem": "SDTS",
    ".dt0": "DTED",
    ".dt1": "DTED",
    ".dt2": "DTED",
    ".nitf": "NITF",
    ".ntf": "NITF",
    ".nsf": "NITF",
    ".hdr": "ENVI",
    ".bil": "ENVI",
    ".bip": "ENVI",
    ".bsq": "ENVI",
    ".pix": "PCIDSK",
    ".rgb": "SGI",
    ".rgba": "SGI",
    ".sgi": "SGI",
    ".int": "ERS",
    ".rrd": "RRaster",
    ".gri": "RRASTER",
    ".grd": "RRASTER",
    ".zmap": "ZMap",
    ".xpm": "XPM",
    ".pdf": "PDF",
    ".rpf": "RPF",
    ".idb": "RST",  # Idrisi Raster
    ".rst": "RST",
    ".kea": "KEA",
    ".fits": "FITS",
    ".cog": "GTiff",  # Cloud Optimized GeoTIFF
    ".zarr": "Zarr",
    ".tms": "TMS",
    ".mbtiles": "MBTiles",
    ".xyz": "XYZ",
}

# All formats combined
ALL_FORMATS = {**VECTOR_FORMATS, **RASTER_FORMATS}

# Format descriptions for user documentation
VECTOR_FORMAT_DESCRIPTIONS = {
    "ESRI Shapefile": "Industry standard vector format (requires .shp, .shx, .dbf files)",
    "GeoJSON": "Open standard format for encoding geospatial data (JSON-based)",
    "GeoJSONSeq": "GeoJSON Sequence format (one GeoJSON feature per line)",
    "GPKG": "GeoPackage - open, standards-based, platform-independent, self-describing format",
    "KML": "Keyhole Markup Language - XML notation for expressing geographic data",
    "LIBKML": "KML format in KMZ archive (compressed)",
    "GML": "Geography Markup Language - XML grammar for expressing geographical features",
    "GPX": "GPS Exchange Format - schema for GPS data",
    "TopoJSON": "Extension of GeoJSON that encodes topology",
    "WKT": "Well-Known Text representation of geometry",
    "WKB": "Well-Known Binary representation of geometry",
    "CSV": "Comma-separated values (with X/Y or WKT geometry columns)",
    "DXF": "Drawing Exchange Format - CAD data format",
    "DGN": "MicroStation Design file format",
    "MapInfo File": "MapInfo TAB and MIF formats",
    "VRT": "Virtual Format - wrapper for other data sources",
    "OSM": "OpenStreetMap data format",
    "OpenFileGDB": "ESRI File Geodatabase",
    "PGeo": "ESRI Personal Geodatabase (MDB format)",
    "SQLite": "SpatiaLite (SQLite spatial extension)",
    "XLS": "Microsoft Excel spreadsheet",
    "XLSX": "Microsoft Excel Open XML spreadsheet",
    "ODS": "OpenDocument Spreadsheet",
}

RASTER_FORMAT_DESCRIPTIONS = {
    "GTiff": "GeoTIFF - TIFF with georeferencing info (most common raster format)",
    "HFA": "ERDAS Imagine format",
    "EHdr": "ESRI BIL/BIP/BSQ formats",
    "AAIGrid": "ASCII Grid format (ESRI)",
    "SAGA": "SAGA GIS grid format",
    "netCDF": "Network Common Data Form (multi-dimensional scientific data)",
    "HDF5": "Hierarchical Data Format version 5",
    "HDF4": "Hierarchical Data Format version 4",
    "PNG": "Portable Network Graphics (with world file for georeferencing)",
    "JPEG": "JPEG image format (with world file for georeferencing)",
    "BMP": "Bitmap image format",
    "GIF": "Graphics Interchange Format",
    "WEBP": "WebP image format",
    "ECW": "Enhanced Compression Wavelet (proprietary)",
    "JP2OpenJPEG": "JPEG 2000 format",
    "MRF": "Meta Raster Format",
    "VRT": "Virtual Raster Format",
    "AIG": "ArcInfo Binary Grid",
    "SDTS": "Spatial Data Transfer Standard",
    "DTED": "Digital Terrain Elevation Data",
    "ENVI": "ENVI binary raster format",
    "PCIDSK": "PCI Geomatics database file",
    "SGI": "SGI image format",
    "ERS": "ERMapper raster format",
    "RRaster": "R raster data format",
    "ZMap": "ZMap grid format",
    "PDF": "PDF with embedded geospatial data",
    "RST": "Idrisi Raster format",
    "KEA": "KEA image format (Kakadu)",
    "FITS": "Flexible Image Transport System (astronomy)",
    "MBTiles": "Map tiles in SQLite database",
    "XYZ": "XYZ tile format",
}

ALL_FORMAT_DESCRIPTIONS = {**VECTOR_FORMAT_DESCRIPTIONS, **RASTER_FORMAT_DESCRIPTIONS}


def get_driver_from_extension(ext: str) -> str | None:
    """Get GDAL driver name from file extension."""
    ext = ext.lower()
    return ALL_FORMATS.get(ext)


def is_vector_format(ext: str) -> bool:
    """Check if extension is a vector format."""
    ext = ext.lower()
    return ext in VECTOR_FORMATS


def is_raster_format(ext: str) -> bool:
    """Check if extension is a raster format."""
    ext = ext.lower()
    return ext in RASTER_FORMATS


def get_supported_extensions() -> list[str]:
    """Get all supported file extensions."""
    return sorted(ALL_FORMATS.keys())


def get_vector_extensions() -> list[str]:
    """Get supported vector format extensions."""
    return sorted(VECTOR_FORMATS.keys())


def get_raster_extensions() -> list[str]:
    """Get supported raster format extensions."""
    return sorted(RASTER_FORMATS.keys())


def get_format_description(driver: str) -> str:
    """Get human-readable description for a format driver."""
    return ALL_FORMAT_DESCRIPTIONS.get(driver, "Unknown format")