
"""
    Climate Data Module

    @author: Mike Amy
"""

# datasets are stored in actual tables
#   - e.g. rainfall_mm

# data collection points in dataset
# values at a point within a time range

# e.g. observed temperature in Kathmandu between Feb 2006 - April 2007


sample_types = dict(
    O = "Observed",
    G = "Gridded",
    
    r = "Projected (RC)",
    g = "Projected (GC)",
    s = "Scenario",
)

sample_codes = {}

import re
for code, name in sample_types.iteritems():
    globals()[re.sub("\W", "", name)] = code
    sample_codes[name] = code

def define_models(env):
    """
        Define Climate Data models.
    """    
    db = env.db
    Field = env.Field

    def create_index(table_name, field_name):
        # Moved this to 1st_run as IF NOT EXISTS is not cross-database portable
        db.executesql(
            """
            CREATE INDEX IF NOT EXISTS 
            "index_%(table_name)s__%(field_name)s" 
            ON "%(table_name)s" ("%(field_name)s");
            """ % locals()
        )

    place = db.define_table(
        "place",
        Field(
            "longitude",
            "double",
            notnull=True,
            required=True,
        ),
        Field(
            "latitude",
            "double",
            notnull=True,
            required=True,
        )
    )

    # not all places are stations with elevations
    # as in the case of "gridded" data
    # a station can only be in one place
    observation_station = db.define_table(
        "observation_station",
        Field(
            "id",
            "id", # must be a place,
            notnull=True,
            required=True,
        ),
        Field(
            "name",
            "string",
            notnull=True,
            unique=False,
            required=True,
        ),
        Field(
            "elevation_metres",
            "integer"
        )
    )

    def sample_table(name, value_type):
        table = db.define_table(
            name,
            Field(
                "sample_type",
                "string",
                length = 1,
                notnull=True,
                # web2py requires a default value for not null fields
                default="-1", 
                required=True
            ),
            Field(
                "time_period",
                "integer",
                notnull=True,
                default=-1000,
                required=True
            ),
            Field(
                # this should become a GIS field
                "place_id",
                place,
                notnull=True,
                required=True
            ),
            Field(
                "value",
                value_type,
                notnull = True,
                required=True,
            ),
        )
        
        # Can't be made robust cross-database, so moved to 1st_run.
        ##create_index(name, "id") # id field always indexed already
        #create_index(name, "sample_type")
        #create_index(name, "time_period")
        #create_index(name, "place_id")

        return table

    rainfall_mm = sample_table("climate_rainfall_mm", "double")
    min_temperature_celsius = sample_table("climate_min_temperature_celsius", "double")
    max_temperature_celsius = sample_table("climate_max_temperature_celsius", "double")
    
    tables = {
        "Rainfall mm": ("climate_rainfall_mm", rainfall_mm),
        "Max Temperature C": ("climate_max_temperature_celsius", max_temperature_celsius),
        "Min Temperature C": ("climate_min_temperature_celsius", min_temperature_celsius),
    }
    
    def year_month_to_month_number(year, month):
        """Time periods are integers representing months in years, 
        from 1960 onwards.
        
        e.g. 0 = Jan 1960, 1 = Feb 1960, 12 = Jan 1961
        
        This function converts a year and month to a month number.
        """
        return ((year-1960) * 12) + (month-1)
    
    def date_to_month_number(date):
        """This function converts a date to a month number.
        
        See also year_month_to_month_number(year, month)
        """
        return year_month_to_month_number(date.year, date.month)
    
#    def month_number_to_date(month_number):
#        ret
    
    from .MapPlugin import define 
    define(
        env,
        place,
        tables,
        date_to_month_number,
        sample_codes,
        globals()
    )

    # exports:
    globals().update(
        sample_types = sample_types,
        
        place = place,
        observation_station = observation_station,
        
        tables = tables,
        
        rainfall_mm = rainfall_mm,
        max_temperature_celsius = max_temperature_celsius,
        min_temperature_celsius = min_temperature_celsius,
    
        date_to_month_number = date_to_month_number,
        year_month_to_month_number = year_month_to_month_number,
    )
    
    def redefine_models(env):
        # avoid risking insidious aliasing bugs
        # by not defining things more than once 
        env.db.update(
            climate_rainfall_mm = rainfall_mm,
            climate_max_temperature_celsius = max_temperature_celsius,
            climate_min_temperature_celsius = min_temperature_celsius,
            place = place,
            observation_station = observation_station,
        )
    globals()["define_models"] = redefine_models
