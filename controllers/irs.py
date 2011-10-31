# -*- coding: utf-8 -*-

""" Incident Reporting System - Controllers

    @author: Sahana Taiwan Team

"""

module = request.controller
resourcename = request.function

simileTimeline = local_import('timeline/simile')

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Options Menu (available in all Functions' Views)
s3_menu(module)

# -----------------------------------------------------------------------------
def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def icategory():

    """
        Incident Categories, RESTful controller
        Note: This just defines which categories are visible to end-users
        The full list of hard-coded categories are visible to admins & should remain unchanged for sync
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def irs_timeline():
    tl = simileTimeline.SimileTimeline()
    tl.addEventSource(table=db.irs_ireport, title='name', desc='message', start='datetime')
    timeline = tl.generateCode()
    return dict(timeline=timeline)

# -----------------------------------------------------------------------------
def ireport():

    """ Incident Reports, RESTful controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Load Models
    #s3mgr.load("irs_ireport")
    s3mgr.load("impact_impact")

    # Don't send the locations list to client (pulled by AJAX instead)
    #table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

    # Non-Editors should only see a limited set of options
    if not s3_has_role(EDITOR):
        allowed_opts = [irs_incident_type_opts.get(opt.code, opt.code) for opt in db().select(db.irs_icategory.code)]
        allowed_opts.sort()
        table.category.requires = IS_NULL_OR(IS_IN_SET(allowed_opts))

    # Pre-processor
    def prep(r):
        table = r.table
        if r.method == "ushahidi":
            auth.settings.on_failed_authorization = r.url(method="", vars=None)
            # Allow the 'XX' levels
            db.gis_location.level.requires = IS_NULL_OR(IS_IN_SET(
                gis.get_all_current_levels()))
        elif r.interactive:
            if r.method == "update":
                table.verified.writable = True
            elif r.method == "create" or r.method == None:
                table.datetime.default = request.utcnow
                table.person_id.default = s3_logged_in_person()
            if r.component:
                if r.component.name == "staff":
                    table = db.org_staff
                    table.focal_point.readable = table.focal_point.writable = False
                    table.supervisor.readable = table.supervisor.writable = False
                    table.no_access.readable = table.no_access.writable = False
                elif r.component.name == "task":
                    table = db.project_task
                    table.project_id.readable = table.project_id.writable = False

        return True
    response.s3.prep = prep

    # Post-processor
    def user_postp(r, output):
        if not r.component:
            s3_action_buttons(r, deletable=False)
            if deployment_settings.has_module("assess"):
                response.s3.actions.append({"url" : URL(c="assess", f="basic_assess",
                                                        vars = {"ireport_id":"[id]"}),
                                            "_class" : "action-btn",
                                            "label" : "Assess"})
        return output
    response.s3.postp = user_postp

    tabs = [(T("Report Details"), None),
            (T("Documents"), "document"),
            (T("Images"), "image")
           ]
    if deployment_settings.has_module("project"):
        tabs.append((T("Tasks"), "task"))

    rheader = lambda r: irs_rheader(r, tabs)

    output = s3_rest_controller(module, resourcename, rheader=rheader)
    return output

# -----------------------------------------------------------------------------

