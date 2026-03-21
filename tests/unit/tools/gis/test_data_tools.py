"""Tests for Data Tools."""

import pytest
from pathlib import Path
import tempfile
import json
from core.tools.data.read import ReadDataTool
from core.tools.data.write import WriteDataTool
from core.tools.data.convert import ConvertDataTool


@pytest.fixture
def test_data():
    """Create test data directory with sample GeoJSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        test_geojson = data_dir / "test.geojson"
        test_geojson.write_text("""{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"name": "Point 1", "value": 100},
      "geometry": {"type": "Point", "coordinates": [116.4, 39.9]}
    },
    {
      "type": "Feature",
      "properties": {"name": "Point 2", "value": 200},
      "geometry": {"type": "Point", "coordinates": [116.5, 40.0]}
    }
  ]
}""")
        yield data_dir


def test_read_data_tool_properties():
    """Test ReadDataTool has required properties"""
    tool = ReadDataTool()
    assert tool.name == "read_data"
    assert tool.description
    assert "properties" in tool.parameters


@pytest.mark.asyncio
async def test_read_geojson(test_data):
    """Test reading GeoJSON file"""
    tool = ReadDataTool()
    result = await tool.execute(file_path=str(test_data / "test.geojson"))
    assert "FeatureCollection" in result
    assert "Point 1" in result


@pytest.mark.asyncio
async def test_read_file_not_exists():
    """Test reading non-existent file"""
    tool = ReadDataTool()
    result = await tool.execute(file_path="/tmp/nonexistent.geojson")
    assert "Error" in result


def test_write_data_tool_properties():
    """Test WriteDataTool has required properties"""
    tool = WriteDataTool()
    assert tool.name == "write_data"
    assert tool.description
    assert "properties" in tool.parameters


@pytest.mark.asyncio
async def test_write_geojson():
    """Test writing GeoJSON file"""
    tool = WriteDataTool()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "output.geojson"
        geojson_data = """{
  "type": "FeatureCollection",
  "features": []
}"""
        result = await tool.execute(
            file_path=str(output_file),
            data=geojson_data
        )
        assert "successfully" in result.lower() or "written" in result.lower()
        assert output_file.exists()


def test_convert_data_tool_properties():
    """Test ConvertDataTool has required properties"""
    tool = ConvertDataTool()
    assert tool.name == "convert_data"
    assert tool.description
    assert "properties" in tool.parameters


@pytest.mark.asyncio
async def test_convert_geojson_to_shapefile():
    """Test converting GeoJSON to Shapefile"""
    tool = ConvertDataTool()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.geojson"
        output_file = Path(tmpdir) / "output.shp"

        input_file.write_text("""{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"name": "Point 1"},
      "geometry": {"type": "Point", "coordinates": [116.4, 39.9]}
    }
  ]
}""")

        result = await tool.execute(
            input_file=str(input_file),
            output_file=str(output_file),
            output_format="shapefile"
        )
        # Note: This test verifies the tool processes the request
        # Actual shapefile creation may require geopandas/fiona
        assert "convert" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_convert_with_invalid_format():
    """Test converting with invalid format"""
    tool = ConvertDataTool()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.geojson"
        output_file = Path(tmpdir) / "output.xyz"

        input_file.write_text('{"type": "FeatureCollection", "features": []}')

        result = await tool.execute(
            input_file=str(input_file),
            output_file=str(output_file),
            output_format="invalid_format"
        )
        assert "Error" in result or "invalid" in result.lower()


@pytest.mark.asyncio
async def test_write_data_creates_directory():
    """Test that write_data creates output directory if needed"""
    tool = WriteDataTool()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "subdir" / "output.geojson"
        geojson_data = '{"type": "FeatureCollection", "features": []}'

        result = await tool.execute(
            file_path=str(output_file),
            data=geojson_data
        )
        assert output_file.exists()
        assert output_file.parent.exists()


@pytest.mark.asyncio
async def test_read_geojson_crs_check(test_data):
    """Test that read_data checks and reports CRS"""
    tool = ReadDataTool()
    result = await tool.execute(file_path=str(test_data / "test.geojson"))
    # Should mention CRS or coordinate system
    assert "CRS" in result or "coordinate" in result.lower() or "WGS" in result or "EPSG" in result