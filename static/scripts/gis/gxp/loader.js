(function() {

    var jsfiles = new Array(
        "util.js",
        "data/AutoCompleteProxy.js",
        "data/AutoCompleteReader.js",
        "data/WFSFeatureStore.js",
        "data/WFSProtocolProxy.js",
        "menu/LayerMenu.js",
        "widgets/EmbedMapDialog.js",
        "widgets/FeatureEditPopup.js",
        "widgets/FilterBuilder.js",
        "widgets/QueryPanel.js",
        "widgets/StylePropertiesDialog.js",
        "widgets/WMSLayerPanel.js",
        "widgets/WMSStylesDialog.js",
        "widgets/NewSourceWindow.js",
        "widgets/FillSymbolizer.js",
        "widgets/StrokeSymbolizer.js",
        "widgets/PointSymbolizer.js",
        "widgets/LayerUploadPanel.js",
        "widgets/LineSymbolizer.js",
        "widgets/PolygonSymbolizer.js",
        "widgets/RulePanel.js",
        "widgets/ScaleLimitPanel.js",
        "widgets/TextSymbolizer.js",
        "widgets/Viewer.js",
        "widgets/form/AutoCompleteComboBox.js",
        "widgets/form/ComparisonComboBox.js",
        "widgets/form/ColorField.js",
        "widgets/form/FilterField.js",
        "widgets/form/FontComboBox.js",
        "widgets/form/GoogleGeocoderComboBox.js",
        "widgets/form/ViewerField.js",
        "widgets/grid/CapabilitiesGrid.js",
        "widgets/grid/FeatureGrid.js",
        "widgets/GoogleEarthPanel.js",
        "widgets/GoogleStreetViewPanel.js",
        "widgets/tips/SliderTip.js",
        "plugins/LayerSource.js",
        "plugins/BingSource.js",
        "plugins/WMSSource.js",
        "plugins/WMSCSource.js",
        "plugins/OSMSource.js",
        "plugins/GoogleSource.js",
        "plugins/OLSource.js",
        "plugins/MapBoxSource.js",
        "plugins/MapQuestSource.js",
        "plugins/StyleWriter.js",
        "plugins/GeoServerStyleWriter.js",
        "plugins/Tool.js",
        "plugins/ClickableFeatures.js",
        "plugins/DeleteSelectedFeatures.js",
        "plugins/GoogleGeocoder.js",
        "plugins/GoogleEarth.js",
        "plugins/WMSFilterView.js",
        "plugins/WMSRasterStylesDialog.js",
        "plugins/WMSGetFeatureInfo.js",
        "plugins/FeatureEditor.js",
        "plugins/FeatureGrid.js",
        "plugins/FeatureManager.js",
        "plugins/FeatureToField.js",
        "plugins/QueryForm.js",
        "plugins/LayerTree.js",
        "plugins/AddLayers.js",
        "plugins/RemoveLayer.js",
        "plugins/SelectedFeatureActions.js",
        "plugins/SnappingAgent.js",
        "plugins/Styler.js",
        "plugins/NavigationHistory.js",
        "plugins/Zoom.js",
        "plugins/ZoomToExtent.js",
        "plugins/ZoomToDataExtent.js",
        "plugins/ZoomToLayerExtent.js",
        "plugins/ZoomToSelectedFeatures.js",
        "plugins/Measure.js",
        "plugins/Navigation.js",
        "plugins/LayerProperties.js",
        "plugins/Legend.js",
        "plugins/Print.js"
        //"locale/es.js",
        //"locale/ca.js"
    );
    
    var scripts = document.getElementsByTagName("script");
    var parts = scripts[scripts.length-1].src.split("/");
    parts.pop();
    var path = parts.join("/");

    var len = jsfiles.length;
    var pieces = new Array(len);

    for (var i=0; i<len; i++) {
        pieces[i] = "<script src='" + path + "/" + jsfiles[i] + "'></script>"; 
    }
    document.write(pieces.join(""));
    
    if (GeoExt.Lang) {
        GeoExt.Lang.set(OpenLayers.Util.getParameters()["lang"] || GeoExt.Lang.locale);
    }

})();

