# -*- coding: utf-8 -*-

"""
    Vehicle

    @author: Fran Boon
    @date-created: 2011-06-20

    Vehicle Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Vehicle
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Vehicle Module depends on Assets
if not deployment_settings.has_module("asset"):
    raise HTTP(404, body="Module disabled: %s" % "asset")

s3_menu(module)

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to vehicle/create """
    redirect(URL(f="vehicle", args="create"))

# -----------------------------------------------------------------------------
def vehicle():
    """
        RESTful CRUD controller
        Filtered version of the asset_asset resource
    """

    # Load the models
    s3mgr.load("vehicle_vehicle")
    module = "asset"
    resourcename = "asset"
    tablename = "asset_asset"
    table = db[tablename]

    # Type is Vehicle
    table.type.default = s3.asset.ASSET_TYPE_VEHICLE
    table.type.writable = False

    # Only show vehicles
    response.s3.filter = (db.asset_asset.type == s3.asset.ASSET_TYPE_VEHICLE)

    # Remove type from list_fields
    list_fields = s3mgr.model.get_config("asset_asset", "list_fields")
    list_fields.remove("type")
    s3mgr.configure(tablename, list_fields=list_fields)

    # Label changes
    table.sn.label = T("License Plate")
    db.asset_log.room_id.label = T("Parking Area")

    # CRUD strings
    ADD_VEHICLE = T("Add Vehicle")
    LIST_VEHICLE = T("List Vehicles")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VEHICLE,
        title_display = T("Vehicle Details"),
        title_list = LIST_VEHICLE,
        title_update = T("Edit Vehicle"),
        title_search = T("Search Vehicles"),
        subtitle_create = T("Add New Vehicle"),
        subtitle_list = T("Vehicles"),
        label_list_button = LIST_VEHICLE,
        label_create_button = ADD_VEHICLE,
        label_delete_button = T("Delete Vehicle"),
        msg_record_created = T("Vehicle added"),
        msg_record_modified = T("Vehicle updated"),
        msg_record_deleted = T("Vehicle deleted"),
        msg_list_empty = T("No Vehicles currently registered"))

    # Tweak the search method labels
    vehicle_search = s3base.S3Search(
        # Advanced Search only
        advanced=(s3base.S3SearchSimpleWidget(
                    name="vehicle_search_text",
                    label=T("Search"),
                    comment=T("Search for a vehicle by text."),
                    field=[
                            "number",
                            "item_id$name",
                            #"item_id$category_id$name",
                            "comments"
                        ]
                  ),
                s3base.S3SearchLocationHierarchyWidget(
                    gis,
                    name="vehicle_search_location",
                    comment=T("Search for vehicle by location."),
                    represent ="%(name)s",
                    cols = 3
                ),
                s3base.S3SearchLocationWidget(
                    name="vehicle_search_map",
                    label=T("Map"),
                ),
        ))
    s3mgr.configure(tablename,
                    search_method = vehicle_search)

    # Defined in Model
    return s3.asset.controller()

# END =========================================================================

