# -*- coding: utf-8 -*-

"""
    Project Tracking & Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25
"""

module = request.controller
resourcename = request.function

s3_menu(module)

# Load Models
s3mgr.load("project_project")

# =============================================================================
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to project/create """
    redirect(URL(f="project", args="create"))

# =============================================================================
def need():

    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def need_type():

    """ RESTful CRUD controller """

    return s3_rest_controller(module, resourcename)

# =============================================================================
def project():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    db.hrm_human_resource.person_id.comment = DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("Person"),
                                                                    T("Select the person assigned to this role for this project.")))

    tabs = [(T("Basic Details"), None),
            (T("Staff"), "staff"),
            #(T("Activities"), "activity"),
            #(T("Tasks"), "task"),
            (T("Documents"), "document"),
            (T("Photos"), "image"),
            #(T("Donors"), "organisation"),
            #(T("Facilities"), "site"),  # Ticket 195
           ]

    rheader = lambda r: response.s3.project_rheader(r, tabs)

    return s3_rest_controller(module, resourcename, rheader=rheader)

# =============================================================================
def activity():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    tabs = [
            (T("Details"), None),
            (T("Requests"), "req"),
            (T("Documents"), "document"),
            (T("Photos"), "image"),
            #(T("Shipments To"), "rms_req"),
           ]
    rheader = lambda r: activity_rheader(r, tabs)

    if "create"  in request.args:
        # Default values (from gap_report) set for fields
        default_fieldnames = ["location_id", "need_type_id"]
        for fieldname in default_fieldnames:
            if fieldname in request.vars:
                table[fieldname].default = request.vars[fieldname]
                table[fieldname].writable = False
                table[fieldname].comment = None

    return s3_rest_controller(module, resourcename,
                              rheader = rheader)

# -----------------------------------------------------------------------------
def activity_rheader(r, tabs=[]):
    """ Resource Header for Activities"""

    if r.representation == "html":
        record = r.record
        if record:
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV( TABLE(
                               TR( TH( "%s: " % T("Short Description")),
                                   record.name,
                                  ),
                               TR( TH( "%s: " % T("Location")),
                                   gis_location_represent(record.location_id),
                                   TH( "%s: " % T("Duration")),
                                   "%s to %s" % (record.start_date,
                                                 record.end_date),
                                  ),
                               TR( TH( "%s: " % T("Organization")),
                                   organisation_represent(record.organisation_id),
                                   TH( "%s: " % SECTOR),
                                   org_sector_represent(record.sector_id),
                                 ),
                                ),
                            rheader_tabs
                            )
            return rheader
    return None

# =============================================================================
def task():

    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:
                if r.component_name == "req":
                    if deployment_settings.has_module("hrm"):
                        r.component.table.type.default = 3
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        response.s3.req_create_form_mods()
                elif r.component_name == "human_resource":
                    r.component.table.organisation_id.writable = r.component.table.organisation_id.readable = False
                    r.component.table.organisation_id.default = r.record.organisation_id
                    r.component.table.type.default = 2
            elif r.method != "update" and r.method != "read":
                # Create or ListCreate
                r.table.organisation_id.writable = True
                r.table.organisation_id.default
                r.table.status.writable = r.table.status.readable = False

        return True
    response.s3.prep = prep

    tabs = [(T("Details"), None)]
    if deployment_settings.has_module("hrm"):
        tabs.append((T("Roles"), "task_job_role"))
    if deployment_settings.has_module("hrm"):
        tabs.append((T("Requests"), "task_req"))
    if deployment_settings.has_module("hrm"):
        tabs.append((T("Assignments"), "task_human_resource"))

    rheader = lambda r: task_rheader(r, tabs)

    return s3_rest_controller(module, resourcename,
                              rheader = rheader)

# -----------------------------------------------------------------------------
def task_rheader(r, tabs=[]):
    """ Resource Header for Tasks"""

    if r.representation == "html":
        record = r.record
        if record:
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV( TABLE(
                               TR( TH( "%s: " % T("Subject")),
                                   record.name,
                                   TH( "%s: " % T("Organization")),
                                   organisation_represent(record.organisation_id)
                                  ),
                               TR( TH( "%s: " % T("Location")),
                                   gis_location_represent(record.location_id)
                                  ),
                               TR( TH( "%s: " % T("Description")),
                                   record.description
                                 ),
                                ),
                            rheader_tabs
                            )
            return rheader
    return None

# -----------------------------------------------------------------------------
def person():
    """ Person controller for AddPersonWidget """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            s3mgr.show_ids = True
        return True
    response.s3.prep = prep

    return s3_rest_controller("pr", "person")

# =============================================================================
def gap_report():

    """ Provide a Report on Gaps between Activities & Needs Assessments """

    # Get all assess_summary
    assess_need_rows = db((db.project_need.id > 0) &\
                          (db.project_need.assess_id == db.assess_assess.id) &\
                          (db.assess_assess.location_id > 0) &\
                          (db.assess_assess.deleted != True)
                          ).select(db.assess_assess.id,
                                   db.assess_assess.location_id,
                                   db.assess_assess.datetime,
                                   db.project_need.need_type_id,
                                   db.project_need.value
                                   )

    patable = db.project_activity
    query = (patable.id > 0) & \
            (patable.location_id > 0) & \
            (patable.deleted != True)
    activity_rows = db(query).select(patable.id,
                                     patable.location_id,
                                     patable.need_type_id,
                                     patable.organisation_id,
                                     patable.total_bnf,
                                     patable.start_date,
                                     patable.end_date
                                    )

    def map_assess_to_gap(row):
        return Storage( assess_id = row.assess_assess.id,
                        location_id = row.assess_assess.location_id,
                        datetime = row.assess_assess.datetime,
                        need_type_id = row.project_need.need_type_id,
                        value = row.project_need.value,
                        activity_id = None,
                        organisation_id = None,
                        start_date = NONE,
                        end_date = NONE,
                        total_bnf = NONE,
                        )

    gap_rows = map(map_assess_to_gap, assess_need_rows)

    for activity_row in activity_rows:
        add_new_gap_row = True
        # Check if there is an Assessment of this location & subsector_id
        for gap_row in gap_rows:
            if activity_row.location_id == gap_row.location_id and \
               activity_row.need_type_id == gap_row.need_type_id:

                add_new_gap_row = False

                gap_row.activity_id = activity_row.id,
                gap_row.organisation_id = activity_row.organisation_id
                gap_row.start_date = activity_row.start_date
                gap_row.end_date = activity_row.end_date
                gap_row.total_bnf = activity_row.total_bnf
                break

        if add_new_gap_row:
            gap_rows.append(Storage(location_id = activity_row.location_id,
                                    need_type_id = activity_row.need_type_id,
                                    activity_id = activity_row.id,
                                    organisation_id = activity_row.organisation_id,
                                    start_date = activity_row.start_date,
                                    end_date = activity_row.end_date,
                                    total_bnf = activity_row.total_bnf,
                                    )
                            )

    headings = ("Location",
                "Needs",
                "Assessment",
                "Date",
                "Activity",
                "Start Date",
                "End Date",
                "Total Beneficiaries",
                "Organization",
                "Gap (% Needs Met)",
                )
    gap_table = TABLE(THEAD(TR(*[TH(header) for header in headings])),
                      _id = "list",
                      _class = "dataTable display"
                      )

    for gap_row in gap_rows:
        if gap_row.assess_id:
            assess_action_btn = A(T("Open"),
                                  _href = URL(c="assess", f="assess",
                                              args = (gap_row.assess_id, "need")
                                              ),
                                  _target = "blank",
                                  _id = "show-add-btn",
                                  _class="action-btn"
                                  )
        else:
            assess_action_btn = NONE

        if gap_row.activity_id:
            activity_action_btn =A(T("Open"),
                                   _href = URL(c="project", f="activity",
                                               args = (gap_row.activity_id)
                                               ),
                                   _target = "blank",
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),
        else:
            activity_action_btn = A(T("Add"),
                                   _href = URL(c="project", f="activity",
                                               args = ("create"),
                                               vars = {"location_id":gap_row.location_id,
                                                       "need_type_id":gap_row.need_type_id,
                                                       }
                                               ),
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),

        need_str = response.s3.need_type_represent(gap_row.need_type_id)
        if gap_row.value:
            need_str = "%d %s" % (gap_row.value, need_str)

        #Calculate the Gap
        if not gap_row.value:
            gap_str = NONE
        elif gap_row.total_bnf and gap_row.total_bnf != NONE:
            gap_str = "%d%%" % min((gap_row.total_bnf / gap_row.value) * 100, 100)
        else:
            gap_str = "0%"

        gap_table.append(TR( gis_location_represent(gap_row.location_id),
                             need_str,
                             assess_action_btn,
                             gap_row.datetime or NONE,
                             activity_action_btn,
                             gap_row.start_date or NONE,
                             gap_row.end_date or NONE,
                             gap_row.total_bnf or NONE,
                             organisation_represent(gap_row.organisation_id),
                             gap_str
                            )
                        )

    return dict(title = T("Gap Analysis Report"),
                subtitle = T("Assessments Needs vs. Activities"),
                gap_table = gap_table,
                # Stop dataTables crashing
                r = None
                )

# =============================================================================
def gap_map():
    """
       Provide a Map Report on Gaps between Activities & Needs Assessments

       For every Need Type, there is a Layer showing the Assessments (Inactive)
       & the Activities (Inactive, Blue)

       @ToDo: popup_url
       @ToDo: Colour code the Assessments based on quantity of need
    """

    # NB Currently the colour-coding isn't used (all needs are red)
    assess_summary_colour_code = {0:"#008000", # green
                                  1:"#FFFF00", # yellow
                                  2:"#FFA500", # orange
                                  3:"#FF0000", # red
                                  }

    atable = db.project_activity
    ntable = db.project_need
    ltable = db.gis_location
    astable = db.assess_assess
    feature_queries = []

    need_type_rows = db(db.project_need_type.id > 0).select()
    need_type_represent = response.s3.need_type_represent

    for need_type in need_type_rows:

        need_type_id = need_type.id
        need_type = need_type_represent(need_type_id)

        # Add Activities layer
        query = (atable.id > 0) & \
                (atable.need_type_id == need_type_id) & \
                (atable.location_id > 0) & \
                (atable.deleted != True) & \
                (atable.location_id == ltable.id)
        activity_rows = db(query).select(atable.id,
                                         atable.location_id,
                                         #atable.need_type_id,
                                         ltable.uuid,
                                         ltable.id,
                                         ltable.name,
                                         ltable.code,
                                         ltable.lat,
                                         ltable.lon)
        if len(activity_rows):
            for i in range( 0 , len( activity_rows) ):
                # Insert how we want this to appear on the map
                activity_rows[i].gis_location.shape = "circle"
                activity_rows[i].gis_location.size = 6
                activity_rows[i].gis_location.colour = "#0000FF" # blue
            feature_queries.append({ "name": "%s: Activities" % need_type,
                                     "query": activity_rows,
                                     "active": False })

        # Add Assessments layer
        query = (ntable.id > 0) & \
                (ntable.need_type_id == need_type_id) & \
                (ntable.assess_id == astable.id) & \
                (astable.location_id > 0) & \
                (astable.deleted != True) & \
                (astable.location_id == ltable.id)
        assess_need_rows = db(query).select(astable.id,
                                            astable.location_id,
                                            astable.datetime,
                                            #ntable.need_type_id,
                                            #ntable.value,
                                            ltable.uuid,
                                            ltable.id,
                                            ltable.name,
                                            ltable.code,
                                            ltable.lat,
                                            ltable.lon)

        if len(assess_need_rows):
            for i in range( 0 , len( assess_need_rows) ):
                # Insert how we want this to appear on the map
                assess_need_rows[i].gis_location.shape = "circle"
                assess_need_rows[i].gis_location.size = 4
                #assess_need_rows[i].gis_location.colour = assess_summary_colour_code[assess_need_rows[i].assess_summary.value]
                assess_need_rows[i].gis_location.colour = assess_summary_colour_code[3] # red

            feature_queries.append({ "name": "%s: Assessments" % need_type,
                                     "query": assess_need_rows,
                                     "active": False })

    map = gis.show_map(feature_queries = feature_queries)

    return dict(map = map,
                title = T("Gap Analysis Map"),
                subtitle = T("Assessments and Activities") )

# END =========================================================================
