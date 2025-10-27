# -*- coding: utf-8 -*-
"""
Geometry utility functions for the ERMES QGIS plugin.
Handles geometry transformations and AOI processing.
"""
from qgis.core import (
    QgsGeometry,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProject,
)


def transform_geometry_to_epsg4326(geometry, source_crs):
    """
    Transform a geometry to EPSG:4326 if needed.
    
    :param geometry: QgsGeometry to transform
    :param source_crs: Source CRS of the geometry
    :return: Tuple (transformed_geometry, was_transformed, error_message)
    """
    target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
    
    if source_crs == target_crs:
        return geometry, False, None
    
    try:
        transform = QgsCoordinateTransform(
            source_crs, target_crs, QgsProject.instance()
        )
        geometry.transform(transform)
        return geometry, True, None
    except Exception as e:
        return None, False, str(e)


def create_geometry_from_rectangle(minx, miny, maxx, maxy):
    """
    Create a QgsGeometry from bounding box coordinates.
    
    :param minx: Minimum X coordinate
    :param miny: Minimum Y coordinate
    :param maxx: Maximum X coordinate
    :param maxy: Maximum Y coordinate
    :return: QgsGeometry representing the rectangle
    """
    rect = QgsRectangle(minx, miny, maxx, maxy)
    return QgsGeometry.fromRect(rect)


def unify_layer_geometries(layer):
    """
    Create a unified geometry from all features in a layer.
    
    :param layer: QgsVectorLayer to process
    :return: Tuple (unified_geometry, error_message)
    """
    all_geoms = [feature.geometry() for feature in layer.getFeatures()]
    
    if not all_geoms:
        return None, "The selected layer has no features."
    
    unified_geom = QgsGeometry.unaryUnion(all_geoms)
    
    if unified_geom.isEmpty():
        return None, "Could not create a valid geometry from the layer."
    
    return unified_geom, None


def geometry_to_json(geometry):
    """
    Convert QgsGeometry to JSON string.
    
    :param geometry: QgsGeometry to convert
    :return: JSON string representation of the geometry
    """
    return geometry.asJson()

