
function each(array, fn) {
    for (
        var i = 0;
        i < array.length;
        ++i
    ) {
        fn(array[i], i)
    }
}

ClimateDataMapPlugin = function (config) {
    var plugin = this // let's be explicit!
    plugin.data_type_option_names = config.data_type_option_names
    plugin.parameter_names = config.parameter_names
    plugin.year_min = config.year_min 
    plugin.year_max = config.year_max

    plugin.data_type_label = config.data_type_label
    plugin.overlay_data_URL = config.overlay_data_URL
    plugin.chart_URL = config.chart_URL
    delete config

    plugin.setup = function () {
        var overlay_layer = plugin.overlay_layer = new OpenLayers.Layer.Vector(
            'Climate data map overlay',
            {
                isBaseLayer:false,                                
            }
        );
        map.addLayer(overlay_layer);

        // selection
        OpenLayers.Feature.Vector.style['default']['strokeWidth'] = '2'
        var selectCtrl = new OpenLayers.Control.SelectFeature(
            overlay_layer,
            {
                clickout: true,
                toggle: false,
                multiple: false,
                hover: false,
                toggleKey: 'altKey',
                multipleKey: 'shiftKey',
                box: true,
                onSelect: function (feature) {
                    feature.style.strokeColor = 'black'
                    feature.style.strokeDashstyle = 'dash'
                    overlay_layer.drawFeature(feature)
                },
                onUnselect: function (feature) {
                    feature.style.strokeColor = 'none'
                    overlay_layer.drawFeature(feature)
                },
            }
        );
        
        map.addControl(selectCtrl);

        selectCtrl.activate();
    }
    plugin.addToMapWindow = function (items) {
        var combo_box_size = {
            width: 120,
            heigth:25
        }

        function make_combo_box(
            data,
            fieldLabel,
            hiddenName
        ) {
            var options = []
            each(
                data,
                function (option) {
                    options.push([option, option])
                }
            )
            var combo_box = new Ext.form.ComboBox({
                fieldLabel: fieldLabel,
                hiddenName: hiddenName,
                store: new Ext.data.SimpleStore({
                    fields: ['name', 'option'],
                    data: options
                }),
                displayField: 'name',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                emptyText:'Choose...',
                selectOnFocus:true
            })
            combo_box.setSize(combo_box_size)
            return combo_box
        }
        var data_type_combo_box = make_combo_box(
            plugin.data_type_option_names,
            'Data type',
            'data_type'
        )

        var variable_combo_box = make_combo_box(
            plugin.parameter_names,
            'Variable',
            'parameter'
        )
        
        var statistic_combo_box = make_combo_box(
            ['Minimum','Maximum','Average'],
            'Aggregate values',
            'statistic'
        )
        
        var month_filter = []
        each('DNOSAJJMAMFJ',
            function (
                month_letter,
                month_index
            ) {
                month_filter.unshift(
                    { html:month_letter, border: false }
                )
                month_filter.push(
                    new Ext.form.Checkbox({
                        name: 'month-'+month_index,
                        checked: true,
                        'class': 'month_checkbox'
                    })
                )
            }
        )
        var climate_data_panel = new Ext.FormPanel({
            id: 'climate_data_panel',
            title: 'Climate data map overlay',
            collapsible: true,
            collapseMode: 'mini',
            items: [{
                region: 'center',
                items: [
                    new Ext.form.FieldSet({
                        title: 'Data set',
                        items: [
                            data_type_combo_box,
                            variable_combo_box
                        ]
                    }),
                    new Ext.form.FieldSet({
                        title: 'Period',
                        items: [
                            new Ext.form.NumberField({
                                fieldLabel: 'From',
                                name: 'from_date',
                                minValue: plugin.year_min,
                                maxValue: plugin.year_max,
                                value: plugin.year_min
                            }),
                            new Ext.form.NumberField({
                                fieldLabel: 'To',
                                name: 'to_date',
                                minValue: plugin.year_min,
                                maxValue: plugin.year_max,
                                value: plugin.year_max,
                                size: combo_box_size
                            }),
                            // month filter checkboxes
                            {
                                border: false,
                                layout: {
                                    type: 'table',
                                    columns: 12
                                },
                                defaults: {
                                    width: '100%',
                                    height: '1.3em',
                                    style: 'margin: 0.1em;'
                                },
                                items: month_filter
                            }
                        ]
                    }),
                    new Ext.form.FieldSet({
                        title: 'Map overlay colours',
                        items: [
                            statistic_combo_box,
                        ]
                    })
                ]
            }]
        });
                
        var update_map_layer_button = new Ext.Button({
            text: 'Update map layer',
            disabled: true,
            handler: function() {
                plugin.overlay_layer.destroyFeatures()
                
                // request new features
                var form_values = climate_data_panel.getForm().getValues()
                var error_div = $("#error_div")
                error_div.html("Updating...")
                function done() {
                    error_div.html("")
                }
                var query_parameters = {
                    data_type: form_values.data_type,
                    statistic: form_values.statistic,
                    parameter: form_values.parameter,
                    from_date: form_values.from_date,
                    to_date: form_values.to_date
                }
                // add new features
                $.ajax({
                    url: plugin.overlay_data_URL,
                    data: query_parameters,
                    success: function(feature_data, status_code) {
                        function Vector(geometry, attributes, style) {
                            style.strokeColor= 'none'
                            style.fillOpacity= 0.8
                            style.strokeWidth = 1

                            return new OpenLayers.Feature.Vector(
                                geometry, attributes, style
                            )
                        }
                        function Polygon(components) {
                            return new OpenLayers.Geometry.Polygon(components)
                        }
                        function Point(lon, lat) {
                            var point = new OpenLayers.Geometry.Point(lat, lon)
                            return point.transform(
                                S3.gis.proj4326,
                                S3.gis.projection_current
                            )
                        }
                        function LinearRing(point_list) {
                            point_list.push(point_list[0])
                            return new OpenLayers.Geometry.LinearRing(point_list)
                        }
                        eval('var data = '+feature_data)
                        $('#id_key_min_value').html(data.min)
                        $('#id_key_max_value').html(data.max)
                        if (data.features.length == 0) {
                            error_div.html("Data unavailable. Has it been imported?")
                        } else {
                            plugin.overlay_layer.addFeatures(data.features)
                            done()
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        window.jqXHR = jqXHR
                        error_div.html(
                            '<a target= "_blank" href="'+
                                plugin.overlay_data_URL+'?'+
                                $.param(query_parameters)+
                            '">Error</a>'
                        )
                    }
                });
            }
        });

        function enable_update_layer_button_if_form_complete(
            box, record, index
        ) {
            if (
                !!data_type_combo_box.getValue() &&
                !!variable_combo_box.getValue() &&
                !!statistic_combo_box.getValue()
            ) {
                update_map_layer_button.enable()
            }
        }
        data_type_combo_box.on(
            'change',
            enable_update_layer_button_if_form_complete
        );
        variable_combo_box.on(
            'change',
            enable_update_layer_button_if_form_complete
        );
        statistic_combo_box.on(
            'change',
            enable_update_layer_button_if_form_complete
        );
        climate_data_panel.addButton(update_map_layer_button)
        
        var show_chart_button = new Ext.Button({
            text: 'Show chart',
            disabled: true,
            handler: function() {
                // create URL
                var place_ids = []
                each(
                    plugin.overlay_layer.selectedFeatures, 
                    function (feature) {
                        place_ids.push(feature.data.id)
                    }
                )
                var months = []
                each(
                    $('.month_checkbox'),
                    function (
                        month_checkbox
                    ) {
                        if (
                            month_checkbox.attr('selected') == 'selected'
                        ) {
                            months.push(
                                parseInt(
                                    month_checkbox.attr('name').substring(6)
                                )
                            )
                        }
                    }
                )
                var form_values = climate_data_panel.getForm().getValues(),
                    data_type = form_values.data_type,
                    parameter = form_values.parameter,
                    from_date = form_values.from_date,
                    to_date = form_values.to_date,
                    statistic = form_values.statistic
                ;
                
                var spec = JSON.stringify({
                    data_type: data_type,
                    parameter: parameter,
                    from_date: from_date,
                    to_date: to_date,
                    place_ids: place_ids,
                    aggregation_name: statistic,
                    months: months
                })
                
                function month_range_text() {
                    // keep the number of characters down
                    // slide window to find minimum number of ranges 
                }
                
                var chart_name = [
                    statistic, data_type, parameter,
                    'from', from_date,
                    'to', to_date,
                    'for', (
                        place_ids.length < 3?
                        'places: '+ place_ids:
                        place_ids.length+' places'
                    ),
                    'months'
                ].join(' ')

                // get hold of a chart manager instance
                if (!plugin.chart_window) {
                    var chart_window = plugin.chart_window = window.open(
                        'climate/chart_popup.html',
                        'chart', 
                        'width=660,height=600,toolbar=0,resizable=0'
                    )
                    chart_window.onload = function () {
                        chart_window.chart_manager = new chart_window.ChartManager(plugin.chart_URL)
                        chart_window.chart_manager.addChartSpec(spec, chart_name)
                    }
                    chart_window.onbeforeunload = function () {
                        delete plugin.chart_window
                    }
                } else {
                    // some duplication here:
                    plugin.chart_window. chart_manager.addChartSpec(spec, chart_name)
                }
                
            }
        });
        
        
        function enable_show_chart_button_if_data_and_variable_selected(
            box, record, index
        ) {
            if (
                !!data_type_combo_box.getValue() &&
                !!variable_combo_box.getValue()
            ) {
                show_chart_button.enable()
            }
        }
        
        data_type_combo_box.on(
            'change',
            enable_show_chart_button_if_data_and_variable_selected
        );
        
        variable_combo_box.on(
            'change',
            enable_show_chart_button_if_data_and_variable_selected
        );


        
        climate_data_panel.addButton(show_chart_button)
        
        items.push(climate_data_panel)
        items.push({
            autoEl: {
                    tag: 'div',
                    id: 'error_div'
                }                
            }
        )
        
        var key_panel = new Ext.Panel({
            id: 'key_panel',
            title: 'Key',
            collapsible: true,
            collapseMode: 'mini',
            items: [
                {
                    layout: {
                        type: 'table',
                        columns: 3,
                    },
                    defaults: {
                        width: '100%',
                        height: 20,
                        style: 'margin: 10px'
                    },
                    items: [
                        {
                            tag: 'span',
                            id: 'id_key_min_value',
                            style: 'margin: 5px; text-align: center;',
                            border: false,
                            items: [
                                {
                                    html:'Min',
                                    border: false
                                }
                            ]
                        },
                        new Ext.BoxComponent({
                            autoEl: {
                                tag: 'img',
                                width: 128,
                                height: 15,
                                src: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAAABCAYAAAAW0qa2AAAAc0lEQVQoz42QSw6AIAxEX40JEO9/VlBjxg3gD9TFpG06aTrPJjYlYBsNvCAALvce8JZrVuA6X6Snv+kpdwXBwAlsBiIoAQksV536Mr/te3rxDay4r2iNmAFwBcsdVwdfRagDwbC031M8op5j96L8RVEVYQf3hFgEX0OMvQAAAABJRU5ErkJggg=='
                            }
                        }),
                        {
                            tag: 'span',
                            id: 'id_key_max_value',
                            style: 'margin: 5px; text-align: center',
                            border: false,
                            items: [
                                {
                                    html:'Max',
                                    border: false
                                }
                            ]
                        }
                    ]                
                }
            ]
        })
        
        items.push(key_panel)
    }
}
