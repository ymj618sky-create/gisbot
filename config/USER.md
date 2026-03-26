# USER.md

## Expected User Behavior

### How to Interact

**Be Specific About Your Spatial Needs**
- "Create a 500m buffer around all schools in the dataset"
- "Clip the roads layer to the city boundary"
- "Convert these points to polygons using Thiessen polygons"

**Provide Context When Possible**
- Describe your study area (city, region, country)
- Specify coordinate system if known
- Mention data quality issues you're aware of
- State your analysis goals and constraints

**Ask Questions When Uncertain**
- "What CRS should I use for analysis in Beijing?"
- "Which format is better for my use case: Shapefile or GeoPackage?"
- "How do I handle overlapping polygons?"

### Common User Mistakes to Avoid

❌ **Don't**: Upload corrupted or invalid geometry data
✅ **Do**: Validate geometries before analysis or ask me to check

❌ **Don't**: Mix coordinate systems without specifying
✅ **Do**: Tell me the source CRS and desired output CRS

❌ **Don't**: Expect perfect results from poor-quality data
✅ **Do**: Describe data limitations so I can account for them

❌ **Don't**: Skip validation steps in production workflows
✅ **Do**: Ask me to include quality checks and validation

### File Upload Guidelines

**Supported Formats**:
- Vector: GeoJSON, Shapefile, GeoPackage, KML, GeoTIFF
- Raster: GeoTIFF, TIFF, IMG, ASCII Grid
- Tabular: CSV, Excel (with coordinate columns)

**Best Practices**:
- Use compressed formats (GeoPackage over Shapefile) for faster uploads
- Include metadata files when available
- Remove unnecessary attributes to reduce file size
- Use WGS84 (EPSG:4326) for data sharing, but specify original CRS if different

### Typical Use Cases

**Data Preparation**
- "Clean up these invalid geometries"
- "Merge multiple shapefiles into one"
- "Convert from WGS84 to a local projection"

**Spatial Analysis**
- "Find all features within 1km of point X"
- "Calculate the area of all polygons"
- "Identify clusters in this point dataset"

**Data Visualization**
- "Create a choropleth map of population density"
- "Generate a heatmap from these point measurements"
- "Style this layer by attribute values"

**Advanced Processing**
- "Perform spatial join between parcels and zoning"
- "Calculate network distances between points"
- "Generalize this layer for smaller scale display"

### Feedback Loop

**If Results Are Wrong**:
- Tell me specifically what's incorrect
- Provide sample correct output if available
- Describe expected vs. actual behavior

**If You Need Something Different**:
- Describe your exact requirements
- Show examples of desired output format
- Mention any constraints (time, resources, tools)

**If Something Is Confusing**:
- Ask for clarification on technical terms
- Request step-by-step explanations
- Ask for alternatives to suggested approaches

---

*I'm here to help - the clearer your request, the better I can assist.*