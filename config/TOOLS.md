# TOOLS.md

## Tool Registry

This document lists all available tools organized by category.

### GIS Data Tools

#### read_data
Read GIS data files (GeoJSON, Shapefile, GeoPackage, etc.)
- **Parameters**: `file_path` (string)
- **Returns**: Layer info, feature count, CRS, bounds, geometry types, column names
- **Use When**: You need to inspect a GIS file or load data for analysis

#### write_data
Write GeoDataFrame to a file (GeoJSON, Shapefile, GeoPackage, etc.)
- **Parameters**: `file_path` (string), `data` (GeoJSON string), `driver` (optional)
- **Returns**: Success message with file info
- **Use When**: You need to save analysis results or transform data formats

#### convert_data
Convert between GIS data formats
- **Parameters**: `input_file`, `output_file`, `output_driver` (optional)
- **Returns**: Conversion result with file info
- **Use When**: You need to change data format for compatibility

### Spatial Analysis Tools

#### buffer
Create buffer zones around input features at a specified distance
- **Parameters**: `input_data` (GeoJSON), `distance` (number), `unit` (meter/kilometer/degree)
- **Returns**: Buffered features as GeoJSON
- **Use When**: You need to create proximity zones or analyze influence areas

### ArcPy Tools (Advanced GIS Processing)

> Note: ArcPy tools require ArcGIS Pro or ArcMap installation

#### buffer_arcpy
Create buffer zones using ArcPy (supports side options, dissolve)
- **Parameters**: `input_features`, `output_features`, `buffer_distance`, `side`, `dissolve`
- **Returns**: Buffer operation results with feature count

#### clip_arcpy
Clip features by extent using ArcPy
- **Parameters**: `input_features`, `clip_features`, `output_features`
- **Returns**: Clipped features count and extent info

#### intersect_arcpy
Find geometric intersections between layers
- **Parameters**: `input_features` (array), `output_features`, `join_attributes`
- **Returns**: Intersections found count

#### project_arcpy
Transform coordinate systems
- **Parameters**: `input_features`, `output_features`, `output_crs` (EPSG or WKT)
- **Returns**: Projection results with CRS info

#### dissolve_arcpy
Aggregate features by attributes with statistics
- **Parameters**: `input_features`, `output_features`, `dissolve_field`, `statistics`
- **Returns**: Dissolved feature count

#### feature_to_raster_arcpy
Convert vector features to raster format
- **Parameters**: `input_features`, `field`, `output_raster`, `cell_size`
- **Returns**: Raster conversion results

#### raster_to_polygon_arcpy
Convert raster to polygon features
- **Parameters**: `input_raster`, `output_features`, `simplify`
- **Returns**: Polygon count and simplification status

#### spatial_join_arcpy
Join attributes based on spatial relationships
- **Parameters**: `target_features`, `join_features`, `output_features`, `join_operation`, `match_option`
- **Returns**: Features joined and match relationship

#### run_arcpy
Execute any ArcGIS geoprocessing tool directly
- **Parameters**: `toolbox`, `tool`, `parameters` (array)
- **Returns**: Tool execution results
- **Use When**: You need to run custom or specialized ArcGIS tools

### System Tools

#### list_files
List files and directories
- **Parameters**: `path` (relative to workspace)
- **Returns**: Directory listing with file icons
- **Use When**: You need to explore workspace or check file locations

#### read_file
Read text file contents
- **Parameters**: `path` (relative to workspace)
- **Returns**: File contents (truncated if too large)
- **Use When**: You need to inspect configuration or script files

#### write_file
Write content to a text file
- **Parameters**: `path`, `content`
- **Returns**: Success message with bytes written
- **Use When**: You need to save analysis scripts, logs, or results

#### edit_file
Edit a file by replacing old_text with new_text
- **Parameters**: `path`, `old_text`, `new_text`
- **Returns**: Success or error with context
- **Use When**: You need to modify configuration or code files

#### exec
Execute shell commands
- **Parameters**: `command`, `working_dir` (optional)
- **Returns**: Command output with exit code
- **Use When**: You need to run system utilities or scripts

#### run_python
Execute Python script file
- **Parameters**: `path`, `args` (optional array)
- **Returns**: Script output with exit code
- **Use When**: You need to run Python analysis scripts

#### web_search
Search the web using Tavily or Brave Search
- **Parameters**: `query`, `count` (1-10), `provider` (tavily/brave)
- **Returns**: Search results with titles, URLs, and snippets
- **Use When**: You need up-to-date information or need to research GIS topics

#### web_fetch
Fetch URL and extract readable content
- **Parameters**: `url`, `max_chars` (optional)
- **Returns**: Extracted text content from web pages
- **Use When**: You need to analyze documentation or online resources

### Tool Selection Guidelines

**Start with**: `read_data` to understand your input
**Then**: Use spatial analysis tools (`buffer`, ArcPy tools) as needed
**Finally**: `write_data` to save results
**As needed**: System tools for file management and research

---

*Use tools efficiently - multiple tools can be called in sequence to complete complex workflows.*