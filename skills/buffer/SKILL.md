---
name: buffer
description: Create buffer zones around features and analyze impact areas
requires: {"bins": ["gdal", "ogr2ogr"], "env": []}
always: false
---

# Buffer Analysis Skill

## Overview

The buffer tool creates zones of specified distance around spatial features. This is useful for:

- Service area analysis (e.g., 1km around schools)
- Environmental impact zones
- Flood risk areas
- Sales territory mapping

## Usage

### Basic Buffer

```
Create a 500 meter buffer around all schools:
```

The agent will use the `buffer` tool to:
1. Read the input data (schools)
2. Apply the buffer distance
3. Return statistics about the buffer area

## Parameters

- `input_data`: GeoJSON string containing the features to buffer
- `distance`: Buffer distance
- `unit`: Distance unit - "meter", "kilometer", or "degree"

## Tips

- Use "meter" for local scale analysis
- Use "kilometer" for city/regional analysis
- Use "degree" for very large areas (approximate)
- The tool automatically handles CRS transformations for accurate distance calculations

## Output

The tool returns:
- Number of input features
- Buffer distance
- Total buffer area in km²
- Coordinate reference system (CRS) used