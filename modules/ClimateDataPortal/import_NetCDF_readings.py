
ClimateDataPortal = local_import("ClimateDataPortal")


def get_or_create(dict, key, creator):
    try:
        value = dict[key]
    except KeyError:
        value = dict[key] = creator()
    return value

def get_or_create_record(table, query):
    query_terms = []
    for key, value in query.iteritems():
        query_terms.append(getattr(table, key) == value)
    reduced_query = reduce(
        (lambda left, right: left & right),
        query_terms
    )
    records = db(reduced_query).select()
    count = len(records)
    assert count <= 1, "Multiple records for %s" % query
    if count == 0:
        record = table.insert(**query)
        db.commit()
    else:
        record = records.first()
    return record.id

def nearly(expected_float, actual_float):
    difference_ratio = actual_float / expected_float
    return 0.999 < abs(difference_ratio) < 1.001

def add_reading_if_none(
    database_table,
    sample_type,
    time_period,
    place_id,
    value
):
    records = db(
        (database_table.sample_type == sample_type) &
        (database_table.time_period == time_period) &
        (database_table.place_id == place_id)
    ).select(database_table.value, database_table.id)
    count = len(records)
    assert count <= 1
    if count == 0:
        database_table.insert(
            sample_type = sample_type,
            time_period = time_period,
            place_id = place_id,
            value = value
        )
    else:
        existing = records.first()
        assert nearly(existing.value, value), (existing.value, value, place_id)


def just_add_reading_without_checking_for_existing_readings(
    database_table,
    sample_type,
    time_period,
    place_id,
    value
):
    database_table.insert(
        sample_type = sample_type,
        time_period = time_period,
        place_id = place_id,
        value = value
    )

import datetime

def import_climate_readings(
    netcdf_file,
    database_table,
    add_reading,
    start_time = datetime.date(1971,1,1),
    is_undefined = lambda x: -99.900003 < x < -99.9
):
    """
    Assumptions:
        * there are no places
        * the data is in order of places
    """
    variables = netcdf_file.variables
    
    # create grid of places
    place_ids = {}
    
    def to_list(variable):
        result = []
        for i in range(len(variable)):
            result.append(variable[i])
        return result
    
    def iter_pairs(list):
        for index in range(len(list)):
            yield index, list[index]
    
    times = to_list(variables["time"])
    lat = to_list(variables["lat"])
    lon = to_list(variables["lon"])
    for latitude in lat:
        for longitude in lon:
            record = get_or_create_record(
                ClimateDataPortal.place,
                dict(
                    longitude = longitude,
                    latitude = latitude
                )
            )
            place_ids[(latitude, longitude)] = record
            #print longitude, latitude, record
    
    tt = variables["tt"]
    print "up to:", len(times)
    for time_index, time in iter_pairs(times):
        print time_index, "%i%%" % int((time_index*100) / len(times)) 
        time_period = start_time+datetime.timedelta(hours=time)
        for latitude_index, latitude in iter_pairs(lat):
            for longitude_index, longitude in iter_pairs(lon):
                value = tt[time_index][latitude_index][longitude_index]
                if not is_undefined(value):
                    add_reading(
                        database_table = database_table,
                        sample_type = ClimateDataPortal.Gridded,
                        time_period = ClimateDataPortal.date_to_month_number(time_period),
                        place_id = place_ids[(latitude, longitude)],
                        value = value
                    )
    db.commit()
    print 

import sys

from Scientific.IO import NetCDF

styles = {
    "quickly": just_add_reading_without_checking_for_existing_readings,
    "safely": add_reading_if_none
}

def show_usage():
    sys.stderr.write("""Usage:
    %(command)s file_name parameter_name style
    
file_name: file to import
parameter_name: one of %(parameter_names)s
style: one of %(style_names)s
    quickly: just insert readings into the database
    safely: check that there are no reading conflicts

""" % dict(
        command = "... import_NetCDF_readings.py",
        parameter_names = ClimateDataPortal.tables.keys(),
        style_names = styles.keys()
    ))

try:
    file_name = sys.argv[1]
    parameter_name = sys.argv[2]
    style = sys.argv[3]
    assert sys.argv[4:] == []
except:
    show_usage()
else:
    try:
        netcdf_file = NetCDF.NetCDFFile(file_name)
        table = ClimateDataPortal.tables[parameter_name][1]
        style = styles[style]
    except:
        show_usage()
        raise
    import_climate_readings(
        netcdf_file,
        table,
        style
    )
