---
name: overlay
description: Overlay and combine multiple spatial layers to find intersections, unions, and differences
requires: {"bins": ["gdal", "ogr2ogr"], "env": []}
always: false
---

# Overlay Analysis Skill

## Overview

Overlay operations combine spatial layers to analyze their relationships. Common operations include:

- **Clip**: Cut one layer by the boundary of another
- **Intersect**: Find areas where layers overlap
- **Union**: Combine all features from multiple layers
- **Difference**: Remove area of one layer that overlaps with another

## Usage

### Clipping Data

```
Clip the districts layer by the city boundary:
```

### Finding Intersections

```
Find areas where both schools and parks exist:
```

### Combining Layers

```
Merge all city zones into a single layer:
```

## Parameters

Each overlay operation requires:
- `input_data`: First layer (GeoJSON)
- `overlay_data`: Second layer (GeoJSON)
- `operation`: "clip", "intersect", "union", or "difference"

## Tips

- Ensure both layers have compatible CRS (the tool handles this)
- Clip is the fastest operation for large datasets
- Union creates complex geometries - may take longer
- Results are returned as a new GeoJSON string

## Common Patterns

1. **Service Areas**: Buffer features → Intersect with study area
2. **Exclusion Zones**: Union of layers → Difference with study area
3. **Multi-criteria Analysis**: Multiple overlays with different weights