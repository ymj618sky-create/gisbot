---
name: spatial_join
description: Join attributes from one layer to another based on spatial relationships
requires: {"bins": ["gdal", "ogr2ogr"], "env": []}
always: false
---

# Spatial Join Skill

## Overview

Spatial join transfers attributes between layers based on their spatial relationship. Common use cases:

- Count points in polygons (e.g., schools per district)
- Transfer polygon attributes to points (e.g., district name for addresses)
- Find nearest features and get their attributes

## Usage

### Point in Polygon Count

```
Count the number of schools in each district:
```

### Point Attribute Transfer

```
Assign each address to its district:
```

### Nearest Neighbor

```
Find the nearest school for each house:
```

## Parameters

- `input_data`: Target layer (GeoJSON) - receives attributes
- `join_data`: Source layer (GeoJSON) - provides attributes
- `operation`: "contains", "within", "intersects", "nearest"

## Tips

- "contains" works for polygon → point (points inside polygons)
- "within" works for point → polygon (points inside polygons)
- "intersects" works for any geometry type (overlapping areas)
- "nearest" finds the closest feature regardless of overlap
- Results include all fields from the source layer

## Output

The tool returns:
- Number of matches found
- Joined features count
- List of transferred field names