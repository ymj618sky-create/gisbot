"""ArcPy Tools for GIS Agent.

This module provides a set of tools that wrap ArcGIS geoprocessing tools
for use with the GIS Agent system.
"""
from pathlib import Path
from typing import Any, Optional
import re

from core.tools.base import Tool


class ArcPyToolBase(Tool):
    """Base class for ArcPy tools."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()
        self._arcpy = None
        self._check_arcpy()

    def _check_arcpy(self) -> None:
        """Check if ArcPy is available."""
        try:
            import arcpy
            self._arcpy = arcpy
        except ImportError:
            self._arcpy = None

    @property
    def available(self) -> bool:
        """Check if ArcPy is available."""
        return self._arcpy is not None

    def _ensure_arcpy(self) -> Any:
        """Ensure ArcPy is available, raise error otherwise."""
        if not self.available:
            raise ImportError(
                "ArcPy not available. Please install ArcGIS Pro or ArcMap, "
                "or ensure you are running in the ArcGIS Pro Python environment."
            )
        return self._arcpy

    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to workspace."""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        return str(p)


class BufferToolArcPy(ArcPyToolBase):
    """Buffer analysis tool using ArcPy."""

    @property
    def name(self) -> str:
        return "buffer_arcpy"

    @property
    def description(self) -> str:
        return "Create buffer zones around features using ArcPy buffer tool."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "string",
                    "description": "Path to input feature class or layer"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "buffer_distance": {
                    "type": "string",
                    "description": "Buffer distance (e.g., '100 meters', '1 kilometer')"
                },
                "side": {
                    "type": "string",
                    "enum": ["FULL", "LEFT", "RIGHT", "OUTSIDE_ONLY"],
                    "description": "Side of features to buffer",
                    "default": "FULL"
                },
                "dissolve": {
                    "type": "boolean",
                    "description": "Dissolve overlapping buffers",
                    "default": False
                }
            },
            "required": ["input_features", "output_features", "buffer_distance"]
        }

    async def execute(
        self,
        input_features: str,
        output_features: str,
        buffer_distance: str,
        side: str = "FULL",
        dissolve: bool = False,
        **kwargs
    ) -> str:
        """Execute buffer analysis."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_features)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.analysis.Buffer(
                in_features=input_path,
                out_feature_class=output_path,
                buffer_distance_or_field=buffer_distance,
                side_option=side,
                dissolve_option="ALL" if dissolve else "NONE"
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Buffer analysis completed successfully.\n"
                f"Input: {input_features}\n"
                f"Output: {output_features}\n"
                f"Buffer distance: {buffer_distance}\n"
                f"Features created: {count}\n"
                f"Dissolved: {'Yes' if dissolve else 'No'}"
            )

        except Exception as e:
            return f"✗ Buffer analysis failed: {str(e)}"


class ClipToolArcPy(ArcPyToolBase):
    """Clip analysis tool using ArcPy."""

    @property
    def name(self) -> str:
        return "clip_arcpy"

    @property
    def description(self) -> str:
        return "Extract features that overlap with clip features using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "string",
                    "description": "Path to input feature class"
                },
                "clip_features": {
                    "type": "string",
                    "description": "Path to clip feature class"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                }
            },
            "required": ["input_features", "clip_features", "output_features"]
        }

    async def execute(
        self,
        input_features: str,
        clip_features: str,
        output_features: str,
        **kwargs
    ) -> str:
        """Execute clip analysis."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_features)
            clip_path = self._resolve_path(clip_features)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.analysis.Clip(
                in_features=input_path,
                clip_features=clip_path,
                out_feature_class=output_path
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Clip analysis completed successfully.\n"
                f"Input: {input_features}\n"
                f"Clip: {clip_features}\n"
                f"Output: {output_features}\n"
                f"Features clipped: {count}"
            )

        except Exception as e:
            return f"✗ Clip analysis failed: {str(e)}"


class IntersectToolArcPy(ArcPyToolBase):
    """Intersect analysis tool using ArcPy."""

    @property
    def name(self) -> str:
        return "intersect_arcpy"

    @property
    def description(self) -> str:
        return "Compute geometric intersection of features using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of input feature class paths"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "join_attributes": {
                    "type": "string",
                    "enum": ["ALL", "NO_FID", "ONLY_FID"],
                    "description": "Join attributes from input features",
                    "default": "ALL"
                }
            },
            "required": ["input_features", "output_features"]
        }

    async def execute(
        self,
        input_features: list[str],
        output_features: str,
        join_attributes: str = "ALL",
        **kwargs
    ) -> str:
        """Execute intersect analysis."""
        arcpy = self._ensure_arcpy()

        try:
            input_paths = [self._resolve_path(p) for p in input_features]
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.analysis.Intersect(
                in_features=input_paths,
                out_feature_class=output_path,
                join_attributes=join_attributes
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Intersect analysis completed successfully.\n"
                f"Inputs: {', '.join(input_features)}\n"
                f"Output: {output_features}\n"
                f"Intersections found: {count}"
            )

        except Exception as e:
            return f"✗ Intersect analysis failed: {str(e)}"


class ProjectToolArcPy(ArcPyToolBase):
    """Project coordinate system tool using ArcPy."""

    @property
    def name(self) -> str:
        return "project_arcpy"

    @property
    def description(self) -> str:
        return "Project features to a new coordinate system using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "string",
                    "description": "Path to input feature class"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "output_crs": {
                    "type": "string",
                    "description": "Output coordinate system (EPSG code, WKT, or path to .prj file)"
                }
            },
            "required": ["input_features", "output_features", "output_crs"]
        }

    async def execute(
        self,
        input_features: str,
        output_features: str,
        output_crs: str,
        **kwargs
    ) -> str:
        """Execute project transformation."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_features)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            # Parse CRS (handle EPSG codes)
            spatial_ref = arcpy.SpatialReference()
            if output_crs.upper().startswith("EPSG:"):
                epsg_code = int(output_crs.split(":")[1])
                spatial_ref.factoryCode = epsg_code
                spatial_ref.create()
            else:
                spatial_ref.loadFromString(output_crs)

            result = arcpy.management.Project(
                in_dataset=input_path,
                out_dataset=output_path,
                out_coor_system=spatial_ref
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            desc = arcpy.Describe(output_path)
            crs_name = desc.spatialReference.name

            return (
                f"✓ Project transformation completed successfully.\n"
                f"Input: {input_features}\n"
                f"Output: {output_features}\n"
                f"Output CRS: {crs_name}\n"
                f"Features projected: {count}"
            )

        except Exception as e:
            return f"✗ Project transformation failed: {str(e)}"


class DissolveToolArcPy(ArcPyToolBase):
    """Dissolve boundaries tool using ArcPy."""

    @property
    def name(self) -> str:
        return "dissolve_arcpy"

    @property
    def description(self) -> str:
        return "Aggregate features based on specified attributes using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "string",
                    "description": "Path to input feature class"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "dissolve_field": {
                    "type": "string",
                    "description": "Field to dissolve on (leave empty for all)"
                },
                "statistics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Statistics fields (e.g., ['population SUM', 'area MEAN'])"
                }
            },
            "required": ["input_features", "output_features"]
        }

    async def execute(
        self,
        input_features: str,
        output_features: str,
        dissolve_field: str = "",
        statistics: list[str] | None = None,
        **kwargs
    ) -> str:
        """Execute dissolve analysis."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_features)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            # Parse statistics fields
            stat_fields = None
            if statistics:
                stat_fields = []
                for stat in statistics:
                    parts = stat.split()
                    if len(parts) >= 2:
                        stat_fields.append([[parts[0]], parts[-1]])

            result = arcpy.management.Dissolve(
                in_features=input_path,
                out_feature_class=output_path,
                dissolve_field=dissolve_field or None,
                statistics_fields=stat_fields
            )

            input_count = int(arcpy.management.GetCount(input_path).getOutput(0))
            output_count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Dissolve completed successfully.\n"
                f"Input: {input_features} ({input_count} features)\n"
                f"Output: {output_features} ({output_count} features)\n"
                f"Dissolve field: {dissolve_field or 'All'}\n"
                f"Statistics: {', '.join(statistics) if statistics else 'None'}"
            )

        except Exception as e:
            return f"✗ Dissolve failed: {str(e)}"


class FeatureToRasterToolArcPy(ArcPyToolBase):
    """Convert features to raster using ArcPy."""

    @property
    def name(self) -> str:
        return "feature_to_raster_arcpy"

    @property
    def description(self) -> str:
        return "Convert features to raster format using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_features": {
                    "type": "string",
                    "description": "Path to input feature class"
                },
                "field": {
                    "type": "string",
                    "description": "Field to use for raster values"
                },
                "output_raster": {
                    "type": "string",
                    "description": "Path to output raster"
                },
                "cell_size": {
                    "type": "string",
                    "description": "Output cell size (e.g., '100', '100 meters')"
                }
            },
            "required": ["input_features", "field", "output_raster"]
        }

    async def execute(
        self,
        input_features: str,
        field: str,
        output_raster: str,
        cell_size: str = "",
        **kwargs
    ) -> str:
        """Execute feature to raster conversion."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_features)
            output_path = self._resolve_path(output_raster)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.conversion.FeatureToRaster(
                in_features=input_path,
                field=field,
                out_raster=output_path,
                cell_size=cell_size or None
            )

            return (
                f"✓ Feature to raster conversion completed.\n"
                f"Input: {input_features}\n"
                f"Field: {field}\n"
                f"Output: {output_raster}\n"
                f"Cell size: {cell_size or 'Default'}"
            )

        except Exception as e:
            return f"✗ Feature to raster failed: {str(e)}"


class RasterToPolygonToolArcPy(ArcPyToolBase):
    """Convert raster to polygon using ArcPy."""

    @property
    def name(self) -> str:
        return "raster_to_polygon_arcpy"

    @property
    def description(self) -> str:
        return "Convert raster to polygon features using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_raster": {
                    "type": "string",
                    "description": "Path to input raster"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "simplify": {
                    "type": "boolean",
                    "description": "Simplify polygon boundaries",
                    "default": True
                }
            },
            "required": ["input_raster", "output_features"]
        }

    async def execute(
        self,
        input_raster: str,
        output_features: str,
        simplify: bool = True,
        **kwargs
    ) -> str:
        """Execute raster to polygon conversion."""
        arcpy = self._ensure_arcpy()

        try:
            input_path = self._resolve_path(input_raster)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.conversion.RasterToPolygon(
                in_raster=input_path,
                out_polygon_features=output_path,
                simplify=simplify
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Raster to polygon conversion completed.\n"
                f"Input: {input_raster}\n"
                f"Output: {output_features}\n"
                f"Simplified: {'Yes' if simplify else 'No'}\n"
                f"Polygons created: {count}"
            )

        except Exception as e:
            return f"✗ Raster to polygon failed: {str(e)}"


class SpatialJoinToolArcPy(ArcPyToolBase):
    """Spatial join tool using ArcPy."""

    @property
    def name(self) -> str:
        return "spatial_join_arcpy"

    @property
    def description(self) -> str:
        return "Join attributes based on spatial location using ArcPy."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_features": {
                    "type": "string",
                    "description": "Path to target feature class"
                },
                "join_features": {
                    "type": "string",
                    "description": "Path to join feature class"
                },
                "output_features": {
                    "type": "string",
                    "description": "Path to output feature class"
                },
                "join_operation": {
                    "type": "string",
                    "enum": ["JOIN_ONE_TO_ONE", "JOIN_ONE_TO_MANY"],
                    "description": "Join operation type",
                    "default": "JOIN_ONE_TO_ONE"
                },
                "match_option": {
                    "type": "string",
                    "enum": ["HAVE_THEIR_CENTER_IN", "CONTAINS", "ARE_IDENTICAL_TO", "ARE_WITHIN", "INTERSECT", "BOUNDARY_TOUCHES", "SHARE_A_LINE_SEGMENT_WITH", "CROSSED_BY_THE_OUTLINE_OF", "CONTAINS_CLEMENTINI", "ARE_WITHIN_CLEMENTINI", "CLOSEST"],
                    "description": "Spatial relationship",
                    "default": "INTERSECT"
                }
            },
            "required": ["target_features", "join_features", "output_features"]
        }

    async def execute(
        self,
        target_features: str,
        join_features: str,
        output_features: str,
        join_operation: str = "JOIN_ONE_TO_ONE",
        match_option: str = "INTERSECT",
        **kwargs
    ) -> str:
        """Execute spatial join."""
        arcpy = self._ensure_arcpy()

        try:
            target_path = self._resolve_path(target_features)
            join_path = self._resolve_path(join_features)
            output_path = self._resolve_path(output_features)

            arcpy.env.workspace = str(self.workspace)
            arcpy.env.overwriteOutput = True

            result = arcpy.analysis.SpatialJoin(
                target_features=target_path,
                join_features=join_path,
                out_feature_class=output_path,
                join_operation=join_operation,
                match_option=match_option
            )

            count = int(arcpy.management.GetCount(output_path).getOutput(0))

            return (
                f"✓ Spatial join completed successfully.\n"
                f"Target: {target_features}\n"
                f"Join: {join_features}\n"
                f"Output: {output_features}\n"
                f"Match option: {match_option}\n"
                f"Features created: {count}"
            )

        except Exception as e:
            return f"✗ Spatial join failed: {str(e)}"


# List of all ArcPy tools
ARCPY_TOOLS = [
    BufferToolArcPy,
    ClipToolArcPy,
    IntersectToolArcPy,
    ProjectToolArcPy,
    DissolveToolArcPy,
    FeatureToRasterToolArcPy,
    RasterToPolygonToolArcPy,
    SpatialJoinToolArcPy,
]