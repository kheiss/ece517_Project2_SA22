
ClimateDataPortal = local_import("ClimateDataPortal")

from decimal import Decimal


def get_or_create(dict, key, creator):
    try:
        value = dict[key]
    except KeyError:
        value = dict[key] = creator()
    return value

import os

class Readings(object):
    def __init__(
        self,
        database_table,
        null_value,
        maximum = None,
        minimum = None
    ):
        self.database_table = database_table
        db(database_table.sample_type == ClimateDataPortal.Observed).delete()
        self.null_value = null_value
        self.maximum = maximum
        self.minimum = minimum
        
        self.aggregated_values = {}
     
    def add_reading(self, time_period, reading, out_of_range):
        if reading != self.null_value:
            if (
                (self.minimum is not None and reading < self.minimum) or
                (self.maximum is not None and reading > self.maximum)
            ):
                out_of_range(reading)
            else:
                readings = get_or_create(
                    self.aggregated_values,
                    time_period,
                    list
                )
                readings.append(reading)

    def done(self, place_id):
        for month_number, values in self.aggregated_values.iteritems():
            self.database_table.insert(
                sample_type = ClimateDataPortal.Observed,
                time_period = month_number,
                place_id = place_id,
                value = sum(values) / len(values)
            )


            
import datetime


def import_tabbed_readings(
    folder_name,
    variables = [],
    place_ids = None
):
    """
    Expects a folder containing files with name rtXXXX.txt
    
    each file contains lines of the form e.g.:
1978\t1\t1\t0\t-99.9\t-99.9

representing year, month, day, rainfall(mm), minimum and maximum temperature
    """    
    observation_station = ClimateDataPortal.observation_station
    
    null_value = Decimal("-99.9") # seems to be
    
    for row in db(observation_station).select(observation_station.id):
        place_id = row.id
        if place_ids is not None:
            # avoid certain place ids (to allow importing particular places) 
            start_place, end_place = map(int, place_ids.split(":"))
            assert start_place <= end_place
            if place_id < start_place or place_id > end_place:
                continue
        print place_id

        data_file_path = os.path.join(folder_name, "rt%04i.txt" % place_id)
        if not os.path.exists(data_file_path):
            print "%s not found" % data_file_path
        else:
            try:
                line_number = 1
                for line in open(data_file_path, "r").readlines():
                    line_number += 1
                    if line:
                        data = line.split()
                        if data:
                            try:
                                year = int(data[0])
                                month = int(data[1])
                                day = int(data[2])
                                
                                time_period = ClimateDataPortal.year_month_to_month_number(year, month)
                                
                                for variable, reading_data in zip(
                                    variables,
                                    data[3:6]
                                ):
                                    def out_of_range(reading):
                                        print "%s/%s/%s: %s out of range" % (
                                            day, month, year, reading
                                        )
                                    reading = Decimal(reading_data)
                                    variable.add_reading(
                                        time_period,
                                        reading,
                                        out_of_range = out_of_range 
                                    )
                                
                            except Exception, exception:
                                print line_number, exception
                for variable in variables:
                    variable.done(place_id)
            except:
                print line
                raise
                
        db.commit()
    else:
        print "No stations!"

import sys
    
null_value = Decimal("-99.9")
import_tabbed_readings(
    folder_name = sys.argv[1],
    variables = [
        Readings(
            ClimateDataPortal.rainfall_mm,
            null_value = null_value,
            minimum = 0,
        ),
        Readings(
            database_table = ClimateDataPortal.min_temperature_celsius,
            null_value = null_value,
            minimum = -120,
            maximum = 55
        ),
        Readings(
            database_table = ClimateDataPortal.max_temperature_celsius,
            null_value = null_value,
            minimum = -120,
            maximum = 55
        ),
    ],
    place_ids = sys.argv[2:] or None
)
