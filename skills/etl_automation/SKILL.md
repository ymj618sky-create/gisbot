---
name: etl_automation
description: Automated data extraction, transformation, and loading workflows
requires: {"bins": ["gdal", "ogr2ogr"], "env": []}
always: false
---

# ETL Automation Skill

## Overview

ETL (Extract, Transform, Load) automation handles complete data workflows:

- **Extract**: Read from multiple sources (Shapefile, GeoJSON, PostGIS, etc.)
- **Transform**: Reproject, clean, validate, merge datasets
- **Load**: Write to target format or database

## Usage

### Simple Conversion

```
Convert this Shapefile to GeoJSON:
```

### Reprojection

```
Convert this data from WGS84 (EPSG:4326) to UTM:
```

### Data Cleaning

```
Remove invalid geometries and fix this dataset:
```

### Complex Workflow

```
Read the 5 city datasets, merge them, reproject to EPSG:3857, and save as GeoPackage:
```

## Parameters

- `input_data`: Input GeoJSON or file path
- `output_format`: Target format ("geojson", "gpkg", "shp", etc.)
- `target_crs`: Optional target coordinate system
- `clean_geometries`: Whether to fix invalid geometries (true/false)
- `merge_multiple`: For multi-file workflows

## Tips

- Always specify `target_crs` when combining datasets from different sources
- Use `clean_geometries: true` when data comes from unreliable sources
- GeoPackage (.gpkg) is the best format for storing multiple layers
- The tool automatically handles format-specific requirements

## Common Workflows

### Standardization Pipeline
```
1. Read data
2. Reproject to standard CRS (EPSG:3857 or EPSG:4326)
3. Clean geometries
4. Write to target format
```

### Data Integration
```
1. Read multiple datasets
2. Merge them
3. Standardize schema
4. Write combined output
```

### Database Import
```
1. Read data files
2. Validate schema
3. Load into PostGIS database
```