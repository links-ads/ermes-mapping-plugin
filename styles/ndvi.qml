<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" version="3.36.3-Maidenhead">
  <pipe>
    <provider>
      <resampling zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false" zoomedInResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer band="1" classificationMax="1" nodataColor="" classificationMin="-1" opacity="1" alphaBand="-1" type="singlebandpseudocolor">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0" maximumValue="1" minimumValue="-1" labelPrecision="2" classificationMode="1">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option value="139,69,19,255" type="QString" name="color1"/>
              <Option value="34,139,34,255" type="QString" name="color2"/>
              <Option value="0" type="QString" name="discrete"/>
              <Option value="gradient" type="QString" name="rampType"/>
              <Option value="rgb" type="QString" name="spec"/>
            </Option>
          </colorramp>
          <item label="-1 (water/bare)" value="-1" color="#8b4513" alpha="255"/>
          <item label="0" value="0" color="#bdb76b" alpha="255"/>
          <item label="1 (vegetation)" value="1" color="#228b22" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" gamma="1" contrast="0"/>
    <huesaturation colorizeStrength="100" saturation="0" colorizeGreen="128" colorizeRed="255" invertColors="0" colorizeBlue="128" colorizeOn="0" grayscaleMode="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
