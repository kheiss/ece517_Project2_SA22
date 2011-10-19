# -*- coding: utf-8 -*-

"""
    Asset

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-03-18

    Asset Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Assets
"""

if deployment_settings.has_module("asset"):

    # Global to put things on which need to be visible in different scopes
    s3.asset = Storage()

    s3.asset.ASSET_TYPE_VEHICLE    = 1 # => Extra Tab(s) for Registration Documents, Fuel Efficiency
    #s3.asset.ASSET_TYPE_RADIO      = 2 # => Extra Tab(s) for Radio Channels/Frequencies
    #s3.asset.ASSET_TYPE_TELEPHONE  = 2 # => Extra Tab(s) for Contact Details & Airtime Billing
    s3.asset.ASSET_TYPE_OTHER      = 9 # => No extra Tabs

    # =========================================================================
    # Assets
    #
    #  'Fixed' Assets
    #
    def asset_tables():
        """ Load the Assets Tables when needed """

        asset_type_opts = { s3.asset.ASSET_TYPE_VEHICLE    : T("Vehicle"),
                            #s3.asset.ASSET_TYPE_RADIO      : T("Radio"),
                            #s3.asset.ASSET_TYPE_TELEPHONE  : T("Telephone"),
                            s3.asset.ASSET_TYPE_OTHER      : T("Other")
                           }
        # Assets depend on Supply Items/Brands
        s3mgr.load("supply_item")
        item_id = response.s3.item_id
        item_represent = response.s3.item_represent

        asset_item_represent = lambda id: item_represent(id,
                                                         show_um = False)

        tablename = "asset_asset"
        table = db.define_table(tablename,
                                super_link(db.sit_trackable), # track_id
                                Field("number",
                                      label = T("Asset Number")),
                                item_id(represent = asset_item_represent,
                                        requires = IS_ONE_OF(db, "supply_item.id",
                                                             asset_item_represent,
                                                             sort=True,
                                                             # @todo filter the item_category field
                                                             #filterby = "can_be_asset",
                                                             #filter_opts = [False]
                                                             ),
                                        script = None, # No Item Pack Filter
                                        ),
                                # @ToDo: Can we set this automatically based on Item Category?
                                Field("type", "integer",
                                      requires = IS_IN_SET(asset_type_opts),
                                      default = s3.asset.ASSET_TYPE_OTHER,
                                      represent = lambda opt: \
                                        asset_type_opts.get(opt, UNKNOWN_OPT),
                                      label = T("Type")),
                                Field("sn",
                                      label = T("Serial Number")),
                                Field("supplier"),
                                Field("purchase_date", "date",
                                      label = T("Purchase Date")),
                                Field("purchase_price", "double", default=0.00),
                                currency_type("purchase_currency"),
                                # Base Location, which should always be a Site & set via Log
                                location_id( readable=False,
                                             writable=False),
                                comments(),
                                *(address_fields() + s3_meta_fields()))

        # CRUD strings
        ADD_ASSET = T("Add Asset")
        LIST_ASSET = T("List Assets")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ASSET,
            title_display = T("Asset Details"),
            title_list = LIST_ASSET,
            title_update = T("Edit Asset"),
            title_search = T("Search Assets"),
            subtitle_create = T("Add New Asset"),
            subtitle_list = T("Assets"),
            label_list_button = LIST_ASSET,
            label_create_button = ADD_ASSET,
            label_delete_button = T("Delete Asset"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset deleted"),
            msg_list_empty = T("No Assets currently registered"))

        def asset_asset_represent(id):
            table = db.asset_asset
            itable = db.supply_item
            btable = db.supply_brand
            query = (table.id == id) & \
                    (itable.id == table.item_id)
            r = db(query).select(table.number,
                                 itable.name,
                                 btable.name,
                                 left = btable.on(itable.brand_id == btable.id),
                                 limitby=(0, 1)).first()
            if r:
                represent = "%s (%s" % (r.asset_asset.number,
                                        r.supply_item.name)
                if r.supply_brand.name:
                    represent = "%s, %s)" % (represent,
                                             r.supply_brand.name)
                else:
                    represent = "%s)" % represent
            else:
                represent = NONE
            return represent

        # Reusable Field
        asset_id = S3ReusableField("asset_id", db.asset_asset, sortby="number",
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "asset_asset.id",
                                                                   asset_asset_represent,
                                                                   sort=True)),
                                   represent = asset_asset_represent,
                                   label = T("Asset"),
                                   ondelete = "RESTRICT")

        s3mgr.configure(tablename,
                        super_entity=db.sit_trackable)

        #--------------------------------------------------------------------------
        # Asset Search Method
        #
        asset_search = s3base.S3Search(
            # Advanced Search only
            advanced=(s3base.S3SearchSimpleWidget(
                        name="asset_search_text",
                        label=T("Search"),
                        comment=T("Search for an asset by text."),
                        field=[
                                "number",
                                "item_id$name",
                                #"item_id$category_id$name",
                                "comments"
                            ]
                      ),
                    s3base.S3SearchLocationHierarchyWidget(
                        gis,
                        name="asset_search_location",
                        comment=T("Search for asset by location."),
                        represent ="%(name)s",
                        cols = 3
                    ),
                    s3base.S3SearchLocationWidget(
                        name="asset_search_map",
                        label=T("Map"),
                    ),
            ))

        #--------------------------------------------------------------------------
        # Update owned_by_role to the site's owned_by_role
        s3mgr.configure(tablename,
                        search_method = asset_search,
                        list_fields=["id",
                                     "number",
                                     "item_id",
                                     "type",
                                     "purchase_date",
                                     #"organisation_id",
                                     "location_id",
                                     "L0",
                                     "L1",
                                     #"L2",
                                     #"L3",
                                     "comments"
                                    ])

        # asset as component of organisation and site
        # @ToDo: Join components (No organisation or site field in primary resource)
        #s3mgr.model.add_component(table, org_organisation="organisation_id")

        # =====================================================================
        # Asset Log
        #

        ASSET_LOG_SET_BASE = 1
        ASSET_LOG_ASSIGN   = 2
        ASSET_LOG_RETURN   = 3
        ASSET_LOG_CHECK    = 4
        ASSET_LOG_REPAIR   = 5
        ASSET_LOG_DONATED  = 32
        ASSET_LOG_LOST     = 33
        ASSET_LOG_STOLEN   = 34
        ASSET_LOG_DESTROY  = 35

        # Useful in global scope for init.py
        s3.asset.ASSET_LOG_SET_BASE = ASSET_LOG_SET_BASE

        asset_log_status_opts = {ASSET_LOG_SET_BASE : T("Base Site Set"),
                                 ASSET_LOG_ASSIGN   : T("Assigned"),
                                 ASSET_LOG_RETURN   : T("Returned"),
                                 ASSET_LOG_CHECK    : T("Checked"),
                                 ASSET_LOG_REPAIR   : T("Repaired"),
                                 ASSET_LOG_DONATED  : T("Donated"),
                                 ASSET_LOG_LOST     : T("Lost"),
                                 ASSET_LOG_STOLEN   : T("Stolen"),
                                 ASSET_LOG_DESTROY  : T("Destroyed"),
                                 }
        SITE = 1
        LOCATION = 2
        site_or_location_opts = {SITE     :T("Site"),
                                 LOCATION :T("Location")}

        asset_condition_opts = {
                                1:T("Good Condition"),
                                2:T("Minor Damage"),
                                3:T("Major Damage"),
                                4:T("Un-Repairable"),
                                5:T("Needs Maintenance"),
                               }

        resourcename = "log"
        tablename = "asset_log"
        table = db.define_table(tablename,
                                asset_id(),
                                Field("status",
                                      "integer",
                                      label = T("Status"),
                                      requires = IS_IN_SET(asset_log_status_opts),
                                      represent = lambda opt: \
                                        asset_log_status_opts.get(opt, UNKNOWN_OPT)
                                      ),
                                Field("datetime",
                                      "datetime",
                                      label = T("Date"),
                                      default=request.utcnow,
                                      requires = IS_EMPTY_OR(IS_UTC_DATETIME()),
                                      widget = S3DateTimeWidget(),
                                      represent = s3_utc_represent
                                      ),
                                Field("datetime_until",
                                      "datetime",
                                      label = T("Date Until"),
                                      requires = IS_EMPTY_OR(IS_UTC_DATETIME()),
                                      widget = S3DateTimeWidget(),
                                      represent = s3_utc_represent
                                      ),
                                person_id(label = T("Assigned To")),
                                Field("check_in_to_person",
                                      "boolean",
                                      #label = T("Mobile"),      # Relabel?
                                      label = T("Track with this Person?"),
                                      comment = DIV(_class="tooltip",
                                                    #_title="%s|%s" % (T("Mobile"),
                                                    _title="%s|%s" % (T("Track with this Person?"),
                                                                      T("If selected, then this Asset's Location will be updated whenever the Person's Location is updated."))),
                                      readable = False,
                                      writable = False),
                                organisation_id(),      # This is the Organisation to whom the loan is made
                                Field("site_or_location",
                                      "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(site_or_location_opts)),
                                      represent = lambda opt: \
                                        site_or_location_opts.get(opt, UNKNOWN_OPT),
                                      widget = RadioWidget.widget,
                                      label = T("Facility or Location")),
                                site_id,
                                room_id(),
                                location_id(),
                                # @ToDo: Add Room field
                                Field("cancel", #
                                      "boolean",
                                      default = False,
                                      label = T("Cancel Log Entry"),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Cancel Log Entry"),
                                                                      T("'Cancel' will indicate an asset log entry did not occur")))
                                                    ),
                                Field("cond", "integer",  # condition is a MySQL reserved word
                                      requires = IS_IN_SET(asset_condition_opts,
                                                           zero = "%s..." % T("Please select")),
                                      represent = lambda opt: \
                                        asset_condition_opts.get(opt, UNKNOWN_OPT),
                                      label = T("Condition")),
                                person_id("by_person_id",
                                          label = T("Assigned By"),           # This can either be the Asset controller if signed-out from the store
                                          default = s3_logged_in_person(),    # or the previous owner if passed on directly (e.g. to successor in their post)
                                         ),
                                comments(),
                                *s3_meta_fields())

        table.site_id.readable = True
        table.site_id.writable = True
        table.site_id.widget = None
        table.site_id.comment = (DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Facility"),
                                                       T("Enter some characters to bring up a list of possible matches")),
                                     
                                     ),
SCRIPT("""
    $(document).ready(function() {
        S3FilterFieldChange({
            'FilterField':   'organisation_id',
            'Field':         'site_id',
            'FieldPrefix':   'org',
            'FieldResource': 'site',
            'FieldID'      : 'site_id',
        });
    });""")
                                 )


        # CRUD strings
        ADD_ASSIGN = T("Add Asset Log Entry - Change Label")
        LIST_ASSIGN = T("Asset Log")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ASSIGN,
            title_display = T("Asset Log Details"),
            title_list = LIST_ASSIGN,
            title_update = T("Edit Asset Log Entry"),
            title_search = T("Search Asset Log"),
            subtitle_create = ADD_ASSIGN,
            subtitle_list = T("Asset Log"),
            label_list_button = LIST_ASSIGN,
            label_create_button = ADD_ASSIGN,
            label_delete_button = T("Delete Asset Log Entry"),
            msg_record_created = T("Asset Log Entry Added - Change Label"),
            msg_record_modified = T("Asset Log Entry updated"),
            msg_record_deleted = T("Asset Log Entry deleted"),
            msg_list_empty = T("Asset Log Empty"))

        # log as component of asset
        s3mgr.model.add_component(table, asset_asset="asset_id")

        # ---------------------------------------------------------------------
        def s3_asset_get_current_log(asset_id):
            table = db.asset_log
            query = ( table.asset_id == asset_id ) & \
                    ( table.cancel == False ) & \
                    ( table.deleted == False )
            # Get the log with the maximum time
            asset_log = db(query).select(table.id,
                                         table.status,
                                         table.datetime,
                                         table.cond,
                                         table.person_id,
                                         table.site_id,
                                         table.location_id,
                                         orderby = ~table.datetime,
                                         limitby=(0, 1)).first()
            if asset_log:
                return Storage(datetime = asset_log.datetime,
                               person_id = asset_log.person_id,
                               cond = int(asset_log.cond or 0),
                               status = int(asset_log.status or 0),
                               site_id = asset_log.site_id,
                               location_id = asset_log.location_id
                               )
            else:
                return Storage()

        # ---------------------------------------------------------------------
        def s3_asset_log_prep(r):
            table = db.asset_log
            if r.record:
                asset = Storage(r.record)
            else:
                # This is a new record
                asset = Storage()
                table.cancel.readable = False
                table.cancel.writable = False

            # This causes an error with the dataTables paginate
            # if used only in r.interactive & not also r.representation=="aadata"
            if r.method != "read" and r.method != "update":
                table.cancel.readable = False
                table.cancel.writable = False
            current_log = s3_asset_get_current_log(asset.id)
            status = request.vars.status

            if status:
                table.status.default = status
                table.status.readable = False
                table.status.writable = False

            if status == ASSET_LOG_SET_BASE:
                s3.crud_strings.asset_log.subtitle_create = T("Set Base Site")
                s3.crud_strings.asset_log.msg_record_created = T("Base Site Set")
                table.by_person_id.label = T("Set By")
                table.site_id.writable = True
                table.site_id.requires = IS_ONE_OF(db, "org_site.id",
                                                   site_id.represent)
                table.datetime_until.readable = False
                table.datetime_until.writable = False
                table.person_id.readable = False
                table.person_id.writable = False
                table.site_or_location.readable = False
                table.site_or_location.writable = False
                table.location_id.readable = False
                table.location_id.writable = False

            elif status == ASSET_LOG_RETURN:
                s3.crud_strings.asset_log.subtitle_create = T("Return")
                s3.crud_strings.asset_log.msg_record_created = T("Returned")
                table.person_id.label = T("Returned From")
                table.person_id.default = current_log.person_id
                table.site_or_location.readable = False
                table.site_or_location.writable = False
                table.site_id.readable = False
                table.site_id.writable = False
                table.location_id.readable = False
                table.location_id.writable = False

            elif status == ASSET_LOG_ASSIGN:
                type = request.vars.type
                # table["%s_id" % type].required = True
                if type == "person":#
                    s3.crud_strings.asset_log.subtitle_create = T("Assign to Person")
                    s3.crud_strings.asset_log.msg_record_created = T("Assigned to Person")
                    table["person_id"].requires = IS_ONE_OF(db, "pr_person.id",
                                                            person_represent,
                                                            orderby="pr_person.first_name",
                                                            sort=True,
                                                            error_message="Person must be specified!")
                    table.check_in_to_person.readable = True
                    table.check_in_to_person.writable = True
                elif type == "site":
                    s3.crud_strings.asset_log.subtitle_create = T("Assign to Site")
                    s3.crud_strings.asset_log.msg_record_created = T("Assigned to Site")
                    table["site_id"].requires = IS_ONE_OF(db, "org_site.id",
                                                          site_id.represent)
                    table.site_or_location.readable = False
                    table.site_or_location.writable = False
                    table.location_id.readable = False
                    table.location_id.writable = False
                elif type == "organisation":
                    s3.crud_strings.asset_log.subtitle_create = T("Assign to Organisation")
                    s3.crud_strings.asset_log.msg_record_created = T("Assigned to Organisation")
                    table["organisation_id"].requires = IS_ONE_OF(db, "org_organisation.id",
                                                                  organisation_represent,
                                                                  orderby="org_organisation.name",
                                                                  sort=True)
                    table.site_or_location.required = True
            elif status in request.vars:
                s3.crud_strings.asset_log.subtitle_create = T("Update Status")
                s3.crud_strings.asset_log.msg_record_created = T("Status Updated")
                table.person_id.label = T("Updated By")
                table.status.readable = True
                table.status.writable = True
                table.status.requires = IS_IN_SET({ASSET_LOG_CHECK    : T("Check"),
                                                   ASSET_LOG_REPAIR   : T("Repair"),
                                                   ASSET_LOG_DONATED  : T("Donated"),
                                                   ASSET_LOG_LOST     : T("Lost"),
                                                   ASSET_LOG_STOLEN   : T("Stolen"),
                                                   ASSET_LOG_DESTROY  : T("Destroyed"),
                                                  })

        # ---------------------------------------------------------------------
        def s3_asset_log_onvalidation(form):
            status = int(request.vars.status or 0)
            type = request.vars.type
            if  status == ASSET_LOG_ASSIGN and type == "organisation":
                # Site or Location is required
                if not form.vars.site_id and not form.vars.location_id:
                    response.error = T("The asset must be assigned to a site OR location.")
                    form.errors.site_or_location = T("Please enter a site OR a location")

        # ---------------------------------------------------------------------
        def s3_asset_log_onaccept(form):
            r = form.vars
            asset_id = db.asset_log[r.id].asset_id
            current_log = s3_asset_get_current_log(asset_id)

            status = int( form.vars.status or request.vars.status )
            request.get_vars.pop("status", None)
            request.get_vars.pop("type", None)
            r.datetime = r.datetime.replace(tzinfo=None)
            
            if r.datetime and \
                ( not current_log.datetime or \
                  current_log.datetime <= r.datetime):
                # This is a current assignment
                asset_tracker = s3tracker(db.asset_asset,asset_id)

                if status == ASSET_LOG_SET_BASE:
                    # Set Base Location
                    asset_tracker.set_base_location(s3tracker( db.org_site,
                                                               r.site_id ))
                    # Populate the address fields
                    address_update(db.asset_asset, asset_id)
                if status == ASSET_LOG_ASSIGN:
                    if type == "person":#
                        if r.check_in_to_person:
                            asset_tracker.check_in(db.pr_person, r.person_id,
                                                   timestmp = r.datetime)
                        else:
                            asset_tracker.set_location( db.pr_person, r.person_id,
                                                        timestmp = r.datetime)
                    elif type == "site":
                        asset_tracker.check_in(db.org_site, r.site_id,
                                               timestmp = r.datetime)
                    elif type == "organisation":
                        if r.site_or_location == SITE:
                            asset_tracker.check_in(db.org_site, r.site_id,
                                                   timestmp = r.datetime)
                        if r.site_or_location == LOCATION:
                            asset_tracker.set_location( r.location_id )

                if status == ASSET_LOG_RETURN:
                    # Set location to base location
                    asset_tracker.set_location( asset_tracker,
                                                timestmp = r.datetime)
            return

        # ---------------------------------------------------------------------
        # Update owned_by_role to the site's owned_by_role
        s3mgr.configure(tablename,
                        onvalidation = s3_asset_log_onvalidation,
                        onaccept = s3_asset_log_onaccept,
                        listadd = False,
                        list_fields = ["id",
                                       "status",
                                       "datetime",
                                       "datetime_until",
                                       "organisation_id",
                                       "site_or_location",
                                       "site_id",
                                       "room_id",
                                       "location_id",
                                       "cancel",
                                       "cond",
                                       "comments"]
                        )

        # ---------------------------------------------------------------------
        def asset_rest_controller():
            """ RESTful CRUD controller """

            tablename = "asset_asset"
            table = db[tablename]

            # Assets can optionally have Documents
            if deployment_settings.has_module("doc"):
                s3mgr.load("doc_document")

            # Pre-process
            def prep(r):
                if r.interactive:
                    address_hide(r.table)
                if r.component_name == "log":
                    s3_asset_log_prep(r)
                    #if r.method == "update":
                        # We don't want to exclude fields in update forms
                        #pass
                    #elif r.method != "read":
                        # Don't want to see in Create forms
                        # inc list_create (list_fields over-rides)
                        #table = r.component.table
                        #table.returned.readable = table.returned.writable = False
                        #table.returned_status.readable = table.returned_status.writable = False
                        # Process Base Site
                        #s3mgr.configure(table._tablename,
                        #                onaccept=asset_transfer_onaccept)
                #else:
                    # @ToDo: Add Virtual Fields to the List view for 'Currently assigned to' & 'Current Location'

                return True
            response.s3.prep = prep

            # Post-processor
            def postp(r, output):
                if r.method != "import":
                    s3_action_buttons(r, deletable=False)
                    #if not r.component:
                        #response.s3.actions.append({"url" : URL(c="asset", f="asset",
                        #                                            args = ["[id]", "log", "create"],
                        #                                            vars = {"status" : ASSET_LOG_ASSIGN,
                        #                                                    "type" : "person"}),
                        #                            "_class" : "action-btn",
                        #                            "label" : str(T("Assign"))})
                return output
            response.s3.postp = postp

            output = s3_rest_controller("asset", "asset",
                                        rheader=asset_rheader)
            return output

        # Have this visible in the global scope (for Scenarios/Events)
        s3.asset.controller = asset_rest_controller

        # ---------------------------------------------------------------------
        def asset_rheader(r):
            """ Resource Header for Assets """

            if r.representation == "html":
                record = r.record
                if record:
                    status = None
                    condition = None
                    current_log = s3_asset_get_current_log(record.id)
                    tabs = [(T("Edit Details"), None)]
                    if record.type == s3.asset.ASSET_TYPE_VEHICLE:
                        tabs.append((T("Vehicle Details"), "vehicle"))
                        tabs.append((T("GPS Data"), "gps"))
                    #elif record.type == s3.asset.ASSET_TYPE_RADIO:
                    #    tabs.append((T("Radio Details"), "radio"))
                    #elif record.type == s3.asset.ASSET_TYPE_TELEPHONE:
                    #    tabs.append((T("Telephone Details"), "phone"))
                    tabs.append((T("Log"), "log"))
                    if deployment_settings.has_module("doc"):
                        tabs.append((T("Documents"), "document"))

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    # @ToDo: Check permissions before displaying buttons

                    asset_action_btns = [ A( T("Set Base Site"),
                                             _href = URL(c="asset", f="asset",
                                                          args = [record.id, "log", "create"],
                                                          vars = dict(status = ASSET_LOG_SET_BASE)
                                                          ),
                                             _class = "action-btn"
                                             )
                                        ]

                    status = current_log.status
                    condition = current_log.cond

                    if record.location_id:
                        # A Base Site has been set
                        if status == ASSET_LOG_ASSIGN:
                            asset_action_btns += [ A( T("Return"),
                                                      _href = URL(c="asset", f="asset",
                                                                   args = [record.id, "log", "create"],
                                                                   vars = dict(status = ASSET_LOG_RETURN)
                                                                   ),
                                                      _class = "action-btn"
                                                    )
                                                   ]
                        if status < ASSET_LOG_DONATED:
                            # @ToDo: deployment setting to prevent assigning assets before returning them
                            # The Asset is available for assignment (not disposed)
                            asset_action_btns += [ A( T("Assign to Person"),
                                                      _href = URL(c="asset", f="asset",
                                                                   args = [record.id, "log", "create"],
                                                                   vars = dict(status = ASSET_LOG_ASSIGN,
                                                                               type = "person")
                                                                   ),
                                                      _class = "action-btn"
                                                    ),
                                                  A( T("Assign to Site"),
                                                      _href = URL(c="asset", f="asset",
                                                                   args = [record.id, "log", "create"],
                                                                   vars = dict(status = ASSET_LOG_ASSIGN,
                                                                               type = "site")
                                                                   ),
                                                      _class = "action-btn"
                                                    ),
                                                  A( T("Assign to Organization"),
                                                     _href = URL(c="asset", f="asset",
                                                                  args = [record.id, "log", "create"],
                                                                  vars = dict(status = ASSET_LOG_ASSIGN,
                                                                              type = "organisation")
                                                                  ),
                                                     _class = "action-btn"
                                                   ),
                                                ]
                        asset_action_btns += [  A( T("Update Status"),
                                                   _href = URL(c="asset", f="asset",
                                                                args = [record.id, "log", "create"],
                                                                vars = dict(status = None)
                                                                ),
                                                   _class = "action-btn"
                                                 ),
                                              ]

                    item = asset_item_represent(record.item_id)
                    rheader = DIV(TABLE(TR( TH("%s: " % T("Asset Number")),
                                            record.number,
                                            TH("%s: " % T("Item")),
                                            item
                                          ),
                                        TR( TH("%s: " % T("Condition")),
                                            asset_condition_opts.get(condition,
                                                                     NONE),
                                            TH("%s: " % T("Status")),
                                            asset_log_status_opts.get(status,
                                                                      NONE),
                                          ),
                                        TR( TH("%s: " % T("Person")),
                                            db.asset_log.person_id.represent(current_log.person_id),
                                            TH("%s: " % T("Facility")),
                                            db.asset_log.site_id.represent(current_log.site_id),
                                           TH("%s: " % T("Location")),
                                            db.asset_log.location_id.represent(current_log.location_id),
                                          ),
                                       ),
                                  DIV(_style = "margin-top:5px;",
                                      *asset_action_btns
                                      ),
                                  rheader_tabs
                                 )
                    return rheader
            return None

        # Return to Global Scope
        return dict(
            asset_id = asset_id,
            asset_rheader = asset_rheader
            )

    # Provide a handle to this load function
    s3mgr.model.loader(asset_tables,
                       "asset_asset",
                       "asset_log")


else:
    def asset_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("asset_id", "integer", readable=False, writable=False)
    response.s3.asset_id = asset_id

# END =========================================================================

