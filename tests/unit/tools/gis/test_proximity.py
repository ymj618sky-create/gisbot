"""Tests for GIS Proximity Tools."""

import pytest
import geopandas as gpd
from shapely.geometry import Point
import tempfile
import json
from pathlib import Path
from core.tools.gis.proximity import BufferTool


@pytest.fixture
def sample_geojson_data():
    """Create sample GeoJSON data for testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Point A", "value": 100},
                "geometry": {"type": "Point", "coordinates": [116.4, 39.9]}
            },
            {
                "type": "Feature",
                "properties": {"name": "Point B", "value": 200},
                "geometry": {"type": "Point", "coordinates": [116.5, 40.0]}
            }
        ]
    }


def test_buffer_tool_properties():
    """Test BufferTool has required properties"""
    tool = BufferTool()
    assert tool.name == "buffer"
    assert tool.description
    assert "properties" in tool.parameters
    assert "input_data" in tool.parameters["properties"]
    assert "distance" in tool.parameters["properties"]


@pytest.mark.asyncio
async def test_buffer_tool_with_valid_data(sample_geojson_data):
    """Test buffer tool with valid GeoJSON data"""
    tool = BufferTool()
    geojson_str = json.dumps(sample_geojson_data)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1000,
        unit="meter"
    )

    assert "buffer" in result.lower()
    assert "1000" in result
    assert "meter" in result.lower()


@pytest.mark.asyncio
async def test_buffer_tool_with_kilometer_unit(sample_geojson_data):
    """Test buffer tool with kilometer unit"""
    tool = BufferTool()
    geojson_str = json.dumps(sample_geojson_data)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1,
        unit="kilometer"
    )

    assert "buffer" in result.lower()
    # 1 kilometer = 1000 meters
    assert "1 kilometer" in result.lower() or "1000 meter" in result.lower()


@pytest.mark.asyncio
async def test_buffer_tool_with_degree_unit(sample_geojson_data):
    """Test buffer tool with degree unit"""
    tool = BufferTool()
    geojson_str = json.dumps(sample_geojson_data)

    result = await tool.execute(
        input_data=geojson_str,
        distance=0.01,
        unit="degree"
    )

    assert "buffer" in result.lower()


@pytest.mark.asyncio
async def test_buffer_tool_with_invalid_geojson():
    """Test buffer tool with invalid GeoJSON"""
    tool = BufferTool()

    result = await tool.execute(
        input_data="invalid json",
        distance=1000
    )

    assert "Error" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_buffer_tool_with_empty_features():
    """Test buffer tool with empty features"""
    tool = BufferTool()
    empty_geojson = {"type": "FeatureCollection", "features": []}
    geojson_str = json.dumps(empty_geojson)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1000
    )

    assert "empty" in result.lower() or "no features" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_buffer_tool_calculates_area(sample_geojson_data):
    """Test that buffer tool calculates buffer area"""
    tool = BufferTool()
    geojson_str = json.dumps(sample_geojson_data)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1000,
        unit="meter"
    )

    assert "area" in result.lower() or "km²" in result or "sqkm" in result.lower()


@pytest.mark.asyncio
async def test_buffer_tool_reports_crs(sample_geojson_data):
    """Test that buffer tool reports CRS information"""
    tool = BufferTool()
    geojson_str = json.dumps(sample_geojson_data)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1000,
        unit="meter"
    )

    assert "CRS" in result or "coordinate" in result.lower() or "EPSG" in result


@pytest.mark.asyncio
async def test_buffer_tool_with_single_point():
    """Test buffer tool with single point feature"""
    tool = BufferTool()
    single_point = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Single Point"},
                "geometry": {"type": "Point", "coordinates": [0, 0]}
            }
        ]
    }
    geojson_str = json.dumps(single_point)

    result = await tool.execute(
        input_data=geojson_str,
        distance=1000,
        unit="meter"
    )

    assert "buffer" in result.lower()
    assert "1" in result  # Single feature