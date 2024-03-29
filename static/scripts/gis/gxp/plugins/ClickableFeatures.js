/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = ClickableFeatures
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: ClickableFeatures(config)
 *
 *    Base class for tools that need to handle feature clicks. Don't create
 *    instances of this base class.
 */   
gxp.plugins.ClickableFeatures = Ext.extend(gxp.plugins.Tool, {
    
    /** api: config[featureManager]
     *  ``String`` The id of the :class:`gxp.plugins.FeatureManager` to use
     *  with this tool.
     */
    featureManager: null,
    
    /** api: config[tolerance]
     *  ``Number`` 
     *  Optional pixel tolerance to use when selecting features.  By default,
     *  the server decides whether a pixel click intersects a feature based on 
     *  its own rules.  If a pixel tolerance is provided, it will be included in
     *  requests for features to inform the server to look in a buffer around 
     *  features.
     */
    
    /** private: property[toleranceParameters]
     *  ``Array``
     *  List of parameter names to use in a GetFeatureInfo request when a 
     * ``tolerance`` is provided.  Default is ["BUFFER", "RADIUS"].
     */
    toleranceParameters: ["BUFFER", "RADIUS"],
    
    /** private: property[selectControl]
     *  ``OpenLayers.Control.SelectFeature`` the SelectFeature control used in
     *  the SelectionModel of the grid. Usually created by subclasses. If not,
     *  then a generic SelectFeature control which is not added to the map
     *  will be created when ``noFeatureClick`` is called for the first time.
     */
    
    /** private: method[noFeatureClick]
     *  :arg evt: ``Object``
     */
    noFeatureClick: function(evt) {
        if (!this.selectControl) {
            this.selectControl = new OpenLayers.Control.SelectFeature(
                this.target.tools[this.featureManager].featureLayer
            );
        }
        var evtLL = this.target.mapPanel.map.getLonLatFromPixel(evt.xy);
        var featureManager = this.target.tools[this.featureManager];
        var page = featureManager.page;
        if (featureManager.visible() == "all" && featureManager.paging && page && page.extent.containsLonLat(evtLL)) {
            // no need to load a different page if the clicked location is
            // inside the current page bounds and all features are visible
            return;
        }

        var layer = featureManager.layerRecord && featureManager.layerRecord.getLayer();
        if (!layer) {
            // if the feature manager has no layer currently set, do nothing
            return;
        }
        
        // construct params for GetFeatureInfo request
        // layer is not added to map, so we do this manually
        var map = this.target.mapPanel.map;
        var size = map.getSize();
        var params = Ext.applyIf({
            REQUEST: "GetFeatureInfo",
            BBOX: map.getExtent().toBBOX(),
            WIDTH: size.w,
            HEIGHT: size.h,
            X: evt.xy.x,
            Y: evt.xy.y,
            QUERY_LAYERS: layer.params.LAYERS,
            INFO_FORMAT: "application/vnd.ogc.gml",
            EXCEPTIONS: "application/vnd.ogc.se_xml",
            FEATURE_COUNT: 1
        }, layer.params);
        if (typeof this.tolerance === "number") {
            for (var i=0, ii=this.toleranceParameters.length; i<ii; ++i) {
                params[this.toleranceParameters[i]] = this.tolerance;
            }
        }

        var projection = map.getProjectionObject();
        var layerProj = layer.projection;
        if (layerProj && layerProj.equals(projection)) {
            projection = layerProj;
        }
        if (parseFloat(layer.params.VERSION) >= 1.3) {
            params.CRS = projection.getCode();
        } else {
            params.SRS = projection.getCode();
        }
        
        var store = new GeoExt.data.FeatureStore({
            fields: {},
            proxy: new GeoExt.data.ProtocolProxy({
                protocol: new OpenLayers.Protocol.HTTP({
                    url: (typeof layer.url === "string") ? layer.url : layer.url[0],
                    params: params,
                    format: new OpenLayers.Format.WMSGetFeatureInfo()
                })
            }),
            autoLoad: true,
            listeners: {
                "load": function(store, records) {
                    if (records.length > 0) {
                        var fid = records[0].get("fid");
                        var filter = new OpenLayers.Filter.FeatureId({
                            fids: [fid] 
                        });

                        var autoLoad = function() {
                            featureManager.loadFeatures(
                                filter, function(features) {
                                    this.autoLoadedFeature = features[0];
                                    this.select(features[0]);
                                }, this
                            );
                        }.createDelegate(this);
                        
                        var feature = featureManager.featureLayer.getFeatureByFid(fid);                        
                        if (feature) {
                            this.select(feature);
                        } else if (featureManager.paging && featureManager.pagingType === gxp.plugins.FeatureManager.QUADTREE_PAGING) {
                            var lonLat = this.target.mapPanel.map.getLonLatFromPixel(evt.xy);
                            featureManager.setPage({lonLat: lonLat}, function() {
                                var feature = featureManager.featureLayer.getFeatureByFid(fid);
                                if (feature) {
                                    this.select(feature);
                                } else if (this.autoLoadFeatures === true) {
                                    autoLoad();
                                }
                            }, this);
                        } else {
                            autoLoad();
                        }
                    }
                },
                scope: this
            }
        });
    },
    
    /** api: method[select]
     *  :arg feature: ``OpenLayers.Feature.Vector``
     *
     *  Action to perform when a feature is selected. The default action is to
     *  unselect existing selections and select the feature using the built-in
     *  SelectFeature control. To be overridden by subclasses.
     */
    select: function(feature) {
        this.selectControl.unselectAll();
        this.selectControl.select(feature);
    }
    
});
