# coding: utf8

module = "climate"

ClimateDataPortal = local_import("ClimateDataPortal")

sample_type_names = ClimateDataPortal.sample_codes.keys()
variable_names = ClimateDataPortal.tables.keys()

map_plugin = ClimateDataPortal.MapPlugin(
    data_type_option_names = sample_type_names,
    parameter_names = variable_names,
    year_max = datetime.date.today().year,
    year_min = 1960,
)

def index():
    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Climate")

    # Include an embedded Overview Map on the index page
    config = gis.get_config()

    if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
        catalogue_toolbar = True
    else:
        catalogue_toolbar = False

    search = True
    catalogue_layers = False

    if config.wmsbrowser_url:
        wms_browser = {"name" : config.wmsbrowser_name,
                       "url" : config.wmsbrowser_url}
    else:
        wms_browser = None

    print_service = deployment_settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}
    
    map = gis.show_map(
        lat = 28.5,
        lon = 84.1,
        zoom = 7,
        toolbar = False,
#        catalogue_toolbar=catalogue_toolbar, # T/F, top tabs toolbar
        wms_browser = wms_browser, # dict
        plugins = [
            map_plugin
        ]
    )

    response.title = module_name
    return dict(
        module_name=module_name,
        map=map
    )
    
month_names = dict(
    January=1,
    February=2,
    March=3,
    April=4,
    May=5,
    June=6,
    July=7,
    August=8,
    September=9,
    October=10,
    November=11,
    December=12
)

for name, number in month_names.items():
    month_names[name[:3]] = number
for name, number in month_names.items():
    month_names[name.upper()] = number
for name, number in month_names.items():
    month_names[name.lower()] = number

def convert_date(default_month):
    def converter(year_month):
        components = year_month.split("-")
        year = int(components[0])
        assert 1960 <= year, "year must be >= 1960"
        
        try:
            month_value = components[1]
        except IndexError:
            month = default_month
        else:
            try:
                month = int(month_value)
            except TypeError:
                month = month_names[month_value]
        
        assert 1 <= month <= 12, "month must be in range 1:12"
        return datetime.date(year, month, 1)
    return converter

def one_of(options):
    def validator(choice):
        assert choice in options, "should be one of %s, not '%s'" % (
            options,
            choice
        )
        return choice
    return validator

aggregation_names = ("Maximum", "Minimum", "Average")

def climate_overlay_data():
    kwargs = dict(request.vars)
    kwargs["parameter"] = kwargs["parameter"].replace("+", " ")
    
    arguments = {}
    errors = []
    for kwarg_name, converter in dict(
        data_type = one_of(sample_type_names),
        statistic = one_of(aggregation_names),
        parameter = one_of(variable_names),
        from_date = convert_date(default_month = 1),
        to_date = convert_date(default_month = 12),
    ).iteritems():
        try:
            value = kwargs.pop(kwarg_name)
        except KeyError:
            errors.append("%s missing" % kwarg_name)
        else:
            try:
                arguments[kwarg_name] = converter(value)
            except TypeError:
                errors.append("%s is wrong type" % kwarg_name)
            except AssertionError, assertion_error:
                errors.append("%s: %s" % (kwarg_name, assertion_error))                
    if kwargs:
        errors.append("Unexpected arguments: %s" % kwargs.keys())
    
    if errors:
        raise HTTP(500, "<br />".join(errors))
    else:
        import gluon.contenttype
        data_path = map_plugin.get_overlay_data(
            env = Storage(globals()),
            **arguments
        )
        return response.stream(
            open(data_path,"rb"),
            chunk_size=4096
        )

def list_of(converter):
    def convert_list(choices):
        return map(converter, choices)
    return convert_list

def climate_chart():
    kwargs = dict(request.vars)
    import gluon.contrib.simplejson as JSON
    specs = JSON.loads(kwargs.pop("spec"))
    
    checked_specs = []
    for spec in specs:
        arguments = {}
        errors = []
        for name, converter in dict(
            data_type = one_of(sample_type_names),
            parameter = one_of(variable_names),
            from_date = convert_date(default_month = 1),
            to_date = convert_date(default_month = 12),
            place_ids = list_of(int),
            aggregation_name = one_of(aggregation_names)
        ).iteritems():
            try:
                value = spec.pop(name)
            except KeyError:
                errors.append("%s missing" % name)
            else:
                try:
                    arguments[name] = converter(value)
                except TypeError:
                    errors.append("%s is wrong type" % name)
                except AssertionError, assertion_error:
                    errors.append("%s: %s" % (name, assertion_error))
        if spec:
            errors.append("Unexpected arguments: %s" % spec.keys())
        checked_specs.append(arguments)
    
    if errors:
        raise HTTP(500, "<br />".join(errors))
    else:
        import gluon.contenttype
        response.headers["Content-Type"] = gluon.contenttype.contenttype(".png")
        data_image_file_path = map_plugin.render_plots(
            env = Storage(globals()),
            specs = checked_specs
        )
        return response.stream(
            open(data_image_file_path,"rb"),
            chunk_size=4096
        )
        
def chart_popup():
    return {}
    
