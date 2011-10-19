# -*- coding: utf-8 -*-

"""
    Vehicle

    @author: Fran Boon
    @date-created: 2011-06-20

    Vehicle Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
"""

if deployment_settings.has_module("vehicle"):

    # =========================================================================
    # Vehicles
    #
    def vehicle_tables():
        """ Load the Vehicles Tables when needed """

        # If Assets module is available then load it's Models
        if deployment_settings.has_module("asset"):
            s3mgr.load("asset_asset")
        asset_id = response.s3.asset_id

        # Vehicles are a component of Assets
        tablename = "vehicle_vehicle"
        table = db.define_table(tablename,
                                asset_id(),
                                Field("gps",
                                      label=T("GPS ID")),
                                Field("mileage", "integer",
                                      label=T("Current Mileage")),
                                Field("service_mileage", "integer",
                                      label=T("Service Due"),
                                      comment=T("Mileage")),
                                Field("service_date", "date",
                                      label=T("Service Due"),
                                      comment=T("Date")),
                                Field("insurance_date", "date",
                                      label=T("Insurance Renewal Due")),
                                comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_VEHICLE_DETAILS = T("Add Vehicle Detail")
        LIST_VEHICLE_DETAILS = T("List Vehicle Details")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_VEHICLE_DETAILS,
            title_display = T("Vehicle Details"),
            title_list = LIST_VEHICLE_DETAILS,
            title_update = T("Edit Vehicle Details"),
            title_search = T("Search Vehicle Details"),
            subtitle_create = T("Add Vehicle Details"),
            subtitle_list = T("Vehicle Details"),
            label_list_button = LIST_VEHICLE_DETAILS,
            label_create_button = ADD_VEHICLE_DETAILS,
            label_delete_button = T("Delete Vehicle Details"),
            msg_record_created = T("Vehicle Details added"),
            msg_record_modified = T("Vehicle Details updated"),
            msg_record_deleted = T("Vehicle Details deleted"),
            msg_list_empty = T("No Vehicle Details currently defined"))

        s3mgr.model.add_component(table,
                                  asset_asset=dict(joinby="asset_id",
                                                   multiple=False))

        # ---------------------------------------------------------------------
        # GPS records
        # - designed to be pulled in automaticaly, not entered manually
        #
        tablename = "vehicle_gps"
        table = db.define_table(tablename,
                                asset_id(),
                                Field("lat",
                                      requires=IS_LAT(),
                                      label=T("Latitude")),
                                Field("lon",
                                      requires=IS_LON(),
                                      label=T("Longitude")),
                                Field("direction",
                                      label=T("Direction")),
                                Field("speed",
                                      label=T("Speed")),
                                *s3_meta_fields())

        # CRUD strings
        ADD_GPS = T("Add GPS data")
        LIST_GPS = T("List GPS data")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_GPS,
            title_display = T("GPS data"),
            title_list = LIST_GPS,
            title_update = T("Edit GPS data"),
            title_search = T("Search GPS data"),
            subtitle_create = T("Add GPS data"),
            subtitle_list = T("GPS data"),
            label_list_button = LIST_GPS,
            label_create_button = ADD_GPS,
            label_delete_button = T("Delete GPS data"),
            msg_record_created = T("GPS data added"),
            msg_record_modified = T("GPS data updated"),
            msg_record_deleted = T("GPS data deleted"),
            msg_list_empty = T("No GPS data currently registered"))

        def vehicle_gps_onaccept(form):
            """ Set the current location from the latest GPS record """
            lat = form.vars.lat
            lon = form.vars.lon
            if lat is not None and lon is not None:
                # Lookup the Asset Code
                table = db.asset_asset
                vehicle = db(table.id == form.vars.id).select(table.number,
                                                              limitby=(0, 1)).first()
                if vehicle:
                    name = vehicle.number
                else:
                    name = "vehicle_%i" % form.vars.id
                # Insert a record into the locations table
                ltable = db.gis_location
                location = ltable.insert(name=name, lat=lat, lon=lon)
                # Set the Current Location of the Asset to this Location
                # @ToDo: Currently we set the Base Location as Mapping doesn't support S3Track!
                db(table.id == form.vars.id).update(location_id=location)

        # Add as a component
        s3mgr.model.add_component(table, asset_asset="asset_id")

        # Return to Global Scope
        #return dict(vehicle_id=vehicle_id)

    # Provide a handle to this load function
    s3mgr.model.loader(vehicle_tables,
                       "vehicle_vehicle",
                       "vehicle_gps")

# END =========================================================================

