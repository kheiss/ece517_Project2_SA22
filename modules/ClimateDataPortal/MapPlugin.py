
# notes:

# dependencies:
# R

# create folder for cache:
# mkdir -p /tmp/climate_data_portal/images/recent/
# mkdir -p /tmp/climate_data_portal/images/older/

MAX_CACHE_FOLDER_SIZE = 2**24 # 16 MiB

class TwoStageCache(object):
    def __init__(self, folder, max_size):
        self.folder = folder
        self.max_size
    
    def purge(self):
        pass
    
    def retrieve(self, file_name, generate_if_not_found):
        pass

import os, errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

def define(env, place, tables, date_to_month_number, sample_codes, exports):
    # This starts an R interpreter.
    # As we are sharing it (restarting it every time is inefficient), 
    # we have to be somewhat careful to make sure objects are garbage collected
    # better to just not stick anything in R's globals 
    try:
        import rpy2.robjects as robjects
    except ImportError:
        import logging
        logging.getLogger().error(
"""R is required by the climate data portal to generate charts

To install R: refer to:
http://cran.r-project.org/doc/manuals/R-admin.html


rpy2 is required to interact with python.

To install rpy2, refer to:
http://rpy.sourceforge.net/rpy2/doc-dev/html/overview.html
""")
        raise

    R = robjects.r
    
    from rpy2.robjects.packages import importr

    base = importr("base")
    
    from math import fsum
    def average(values):
        "Safe float average"
        l = len(values)
        if l is 0:
            return None
        else:
            return fsum(values)/l
    
    def Aggregation(name, SQL_function_name, field_type_name = None):
        def __init__(self, column, add_query_term):
            db = column.db
            if field_type_name is None:
                field_type_name = column.type
            self.aggregation = aggregation = Expression(
                db,
                db._adapter.AGGREGATE,
                column,
                SQL_function_name,
                field_type_name
            )
            add_query_term(aggregation)
    
        return type(
            name,
            (object,),
            dict(
                __init__ = __init__,
                __call__ = lambda self, row: (
                    return row._extra[self.aggregation]
                )
            )
        )
    
    Maximum = Aggregation("MAX")
    Minimum = Aggregation("MIN")
#    Sum = Aggregation("SUM")
#    Count = Aggregation("COUNT", "integer")
    Average = Aggregation("AVG")
    StandardDeviation = Aggregation("STDEV")

    class CoefficientOfVariation(object):
        def __init__(self, column, add_query_term):
            self.average = average = Average(
                column,
                add_query_term
            )
            self.standard_deviation = standard_deviation = StandardDeviation(
                column,
                add_query_term
            )
            
        def __call__(self, row):
            return self.standard_deviation(row) / self.average(row)

    aggregators = {
        "Maximum": Maximum,
        "Minimum": Minimum,
        "Average": Average,
        "Standard Deviation": StandardDeviation,
        "Coefficient Of Variation": CoefficientOfVariation,
    }

    def get_cached_or_generated_file(cache_file_name, generate):
        from os.path import join, exists
        from os import stat, makedirs
        # this needs to become a setting
        climate_data_image_cache_path = join(
            "/tmp","climate_data_portal","images"
        )
        recent_cache = join(climate_data_image_cache_path, "recent")
        mkdir_p(recent_cache)
        older_cache = join(climate_data_image_cache_path, "older")
        mkdir_p(older_cache)
        recent_cache_path = join(recent_cache, cache_file_name)
        if not exists(recent_cache_path):
            older_cache_path = join(older_cache, cache_file_name)
            if exists(older_cache_path):
                # move the older cache to the recent folder
                rename(older_cache_path, recent_cache_path)
            else:
                generate(recent_cache_path)
            file_path = recent_cache_path
                
            # update the folder size file (race condition?)
            folder_size_file_path = join(climate_data_image_cache_path, "size")
            folder_size_file = open(folder_size_file_path, "w+")
            folder_size_file_contents = folder_size_file.read()
            try:
                folder_size = int(folder_size_file_contents)
            except ValueError:
                folder_size = 0
            folder_size_file.seek(0)
            folder_size_file.truncate()
            folder_size += stat(file_path).st_size
            if folder_size > MAX_CACHE_FOLDER_SIZE:
                rmdir(older_cache)

            folder_size_file.write(str(folder_size))
            folder_size_file.close()
        else:
            # use the existing cached image
            file_path = recent_cache_path
        return file_path

    class MapPlugin(object):
        def __init__(
            self,
            data_type_option_names,
            parameter_names,
            year_min,
            year_max
        ):
            self.data_type_option_names = data_type_option_names
            self.parameter_names = parameter_names
            self.year_min = year_min 
            self.year_max = year_max

        def extend_gis_map(self, add_javascript, add_configuration):
            add_javascript("scripts/S3/s3.gis.climate.js")
            SCRIPT = env.SCRIPT
            T = env.T
            import json
            
            add_configuration(
                SCRIPT(
                    "\n".join((
                        "registerPlugin(",
                        "    new ClimateDataMapPlugin("+
                                json.dumps(
                                    dict(
                                        data_type_option_names = self.data_type_option_names,
                                        parameter_names = self.parameter_names,
                                        year_min = self.year_min,
                                        year_max = self.year_max,
                                        overlay_data_URL = "/%s/climate/climate_overlay_data" % (
                                            env.request.application
                                        ),
                                        chart_URL = "/%s/climate/climate_chart" % (
                                            env.request.application
                                        ),
                                        data_type_label = str(T("Data Type")),
                                        projected_option_type_label = str(
                                            T("Projection Type")
                                        )
                                    ),
                                    indent = 4
                                )+
                            ")",
                        ")",
                    ))
                )
            )
            
                
        def get_overlay_data(
            self,
            env,
            data_type,
            parameter,
            from_date,
            to_date,
            statistic
        ):            
            from_month = date_to_month_number(from_date)
            to_month = date_to_month_number(to_date)
            def generate_map_overlay_data(file_path):
                # generate the new file in the recent folder
                
                db = env.db
                sample_table_name, sample_table = tables[parameter]
                place = db.place
                #sample_table = db[sample_table_name]
                
                query = [
                    place.id,
                    place.longitude,
                    place.latitude,
                ]
                aggregator = aggregators[statistic](
                    sample_table.value,
                    query.append
                )
                
                sample_rows = db(
                    (sample_table.time_period >= from_month) &
                    (sample_table.time_period <= to_month) & 
                    (sample_table.sample_type == sample_codes[data_type]) & 
                    (place.id == sample_table.place_id)
                ).select(
                    *query,
                    groupby=sample_table.place_id
                )
                
                # map positions to data
                # find max and min value
                positions = {}
                aggregated_values = []
                for row in sample_rows:
                    place = row.place
                    aggregated_value = aggregator(row)
                    aggregated_values.append(aggregated_value)
                    positions[place.id] = (
                        place.latitude,
                        place.longitude,
                        aggregated_value
                    )
                # these will be associated with the actual table
                max_aggregated_value = max(aggregated_values)
                min_aggregated_value = min(aggregated_values)
                aggregated_range = max_aggregated_value - min_aggregated_value
                
                data_lines = []
                write = data_lines.append
                from colorsys import hsv_to_rgb
                for id, (lat, lon, aggregated_value) in positions.iteritems():
                    north = lat + 0.05
                    south = lat - 0.05
                    east = lon + 0.05
                    west = lon - 0.05
                    # only hue changes
                    # hue range is from 2/3 (blue, low) to 0 (red, high) 
                    normalised_value = 1.0-((aggregated_value - min_aggregated_value) / aggregated_range)
                    r,g,b = hsv_to_rgb(normalised_value *(2.0/3.0), 1.0, 1.0)
                    hex_colour = "%02x%02x%02x" % (r*255, g*255, b*255)
                    write(
                        "Vector("
                            "Polygon(["
                                "LinearRing(["
                                    "Point(%(north)f,%(west)f),"
                                    "Point(%(north)f,%(east)f),"
                                    "Point(%(south)f,%(east)f),"
                                    "Point(%(south)f,%(west)f)"
                                "])"
                            "]),"
                            "{"
                                "value:%(aggregated_value)f,"
                                "id:%(id)i"
                            "},"
                            "{"
                                "fillColor:'#%(hex_colour)s'"
                            "}"
                        ")," % locals()
                    )
                overlay_data_file = open(file_path, "w")
                write = overlay_data_file.write
                write("{")
                if max_aggregated_value < 10:
                    float_format = "%0.2f"
                if max_aggregated_value < 100:
                    float_format = "%0.1f"
                elif max_aggregated_value < 10000:
                    float_format = "%0.0f"
                else:
                    float_format = "%0.2e"
                write("max:%s," % float_format % max_aggregated_value)
                write("min:%s," % float_format % min_aggregated_value)
                write("features:[")
                write("".join(data_lines))
                overlay_data_file.seek(-1, 1) # delete last ",'
                write("]}")
                overlay_data_file.close()
                
            return get_cached_or_generated_file(
                "_".join((
                    statistic,
                    data_type,
                    parameter,
                    str(from_month),
                    str(to_month),
                    ".js"
                )),
                generate_map_overlay_data
            )
        
        def render_plots(
            self,
            env,
            specs
        ):
            def generate_chart(file_path):
                def render_plot(
                    data_type,
                    parameter,
                    from_date,
                    to_date,
                    place_ids
                ):
                    from_month = date_to_month_number(from_date)
                    to_month = date_to_month_number(to_date)
                    
                    db = env.db
                    sample_table_name, sample_table = tables[parameter]
                    place = db.place
                    #sample_table = db[sample_table_name]
                    sample_rows = db(
                        (sample_table.time_period >= from_month) &
                        (sample_table.time_period <= to_month) & 
                        (sample_table.sample_type == sample_codes[data_type]) & 
                        (sample_table.place_id.belongs(place_ids))
                    ).select(
                        sample_table.value,
                        sample_table.time_period,
                    )
                    
                    # coalesce values by time_period:
                    aggregated_values = {}
                    for sample_row in sample_rows:
                        time_period = sample_row.time_period
                        value = sample_row.value
                        try:
                            aggregated_values[time_period]
                        except KeyError:
                            aggregated_values[time_period] = value
                        else:
                            aggregated_values[time_period] += value
                    
                    values = []
                    time_periods = aggregated_values.keys()
                    time_periods.sort() 
                    for time_period in time_periods:
                        values.append(aggregated_values[time_period])                    
                    return from_date, to_date, data_type, parameter, values

                time_serieses = []
                c = R("c")
                for spec in specs:
                    from_date, to_date, data_type, parameter, values = render_plot(**spec)
                    time_serieses.append(
                        R("ts")(
                            robjects.FloatVector(values),
                            start = c(from_date.year, from_date.month),
                            end = c(to_date.year, to_date.month),
                            frequency = 12
                        )
                    )
                
                R("png(filename = '%s', width=640, height=480)" % file_path)
                plot_chart = R(
                    "function (xlab, ylab, n, ...) {"
                        "ts.plot(...,"
                            "gpars=list(xlab=xlab, ylab=ylab, col=c(1:n))"
                        ")"
                    "}"
                )

                plot_chart(
                    "Date",
                    "Combined %s %s" % (data_type, parameter),
                    len(time_serieses),
                    *time_serieses
                )
                R("dev.off()")

            import md5
            import gluon.contrib.simplejson as JSON

            import datetime
            def serialiseDate(obj):
                if isinstance(
                    obj,
                    (
                        datetime.date, 
                        datetime.datetime, 
                        datetime.time
                    )
                ): 
                    return obj.isoformat()[:19].replace("T"," ") 
                raise TypeError("%r is not JSON serializable" % (obj,)) 
            
            return get_cached_or_generated_file(
                "_".join((
                    md5.md5(
                        JSON.dumps(
                            specs,
                            sort_keys=True,
                            default=serialiseDate
                        )
                    ).hexdigest(),
                    ".png"
                )),
                generate_chart
            )
            
    exports.update(
        MapPlugin = MapPlugin
    )
    
    del globals()["define"]
