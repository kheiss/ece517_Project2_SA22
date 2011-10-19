
ClimateDataPortal = local_import("ClimateDataPortal")

from decimal import Decimal

def import_stations(file_name):
    """
    Expects a file containing lines of the form e.g.:
226     JALESORE             1122       172     26.65     85.78
275     PHIDIM (PANCHTH      1419      1205     27.15     87.75
unused  Station name         <-id    <-elev     <-lat     <-lon
0123456789012345678901234567890123456789012345678901234567890123456789
0         1         2         3         4         5         6
    """
    place = ClimateDataPortal.place
    observation_station = ClimateDataPortal.observation_station
    observation_station.truncate()
    place.truncate()
    db.commit()

    for line in open(file_name, "r").readlines():
        try:
            place_id_text = line[27:33]
        except IndexError:
            continue
        else:            
            try:
                place_id = int(place_id_text)
            except ValueError:
                continue
            else:
                station_name = line[8:25].strip() # don't restrict if they add more
                elevation_metres = int(line[37:43])
                
                latitude = Decimal(line[47:53])
                longitude = Decimal(line[57:623])
                
                assert place.insert(
                    id  = place_id,
                    longitude = longitude,
                    latitude = latitude
                ) == place_id
                
                station_id = observation_station.insert(
                    id = place_id,
                    name = station_name,
                    elevation_metres = elevation_metres
                )
                print place_id, station_name, latitude, longitude, elevation_metres 
    db.commit()

import sys
import_stations(sys.argv[1])
