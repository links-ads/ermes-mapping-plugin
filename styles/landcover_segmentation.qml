<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Symbology3D|Labeling|Fields|Forms|Actions|Diagrams|GeometryOptions|Relations|Legend" version="3.40.0-Bratislava">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option type="QString" name="name" value=""/>
      <Option name="properties"/>
      <Option type="QString" name="type" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling enabled="false" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer opacity="1" type="paletted" nodataColor="" band="1" alphaBand="-1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry alpha="255" value="0" label="Roads" color="#f95849"/>
        <paletteEntry alpha="255" value="1" label="Artificial" color="#d63a3d"/>
        <paletteEntry alpha="255" value="2" label="Bare" color="#9a9a9a"/>
        <paletteEntry alpha="255" value="3" label="Wetlands" color="#966bc4"/>
        <paletteEntry alpha="255" value="4" label="Water" color="#2b50c6"/>
        <paletteEntry alpha="255" value="5" label="Grassland" color="#f99f27"/>
        <paletteEntry alpha="255" value="6" label="Agricultural" color="#fdd327"/>
        <paletteEntry alpha="255" value="7" label="Broadleaves" color="#249801"/>
        <paletteEntry alpha="255" value="8" label="Coniferous" color="#086200"/>
        <paletteEntry alpha="255" value="9" label="Shrubs" color="#8d8c00"/>
        <paletteEntry alpha="255" value="10" label="Clouds" color="#ffffff"/>
        <paletteEntry alpha="0" value="255" label="Ignored" color="#2c2c2c"/>
      </colorPalette>
      <colorramp type="randomcolors" name="[source]">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation colorizeRed="255" colorizeGreen="128" saturation="0" colorizeStrength="100" grayscaleMode="0" colorizeOn="0" colorizeBlue="128" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
