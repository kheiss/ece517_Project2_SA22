# -*- coding: utf-8 -*-

"""
    Scenario Module - Controllers

    http://eden.sahanafoundation.org/wiki/BluePrintScenario

    @author: Fran Boon
"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Options Menu (available in all Functions' Views)
s3_menu(module)

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to scenario/create """
    redirect(URL(f="scenario", args="create"))


# =============================================================================
# Sceenarios
# =============================================================================
def scenario():

    """ RESTful CRUD controller """

    tablename = "scenario_scenario"

    # Load the Models
    s3mgr.load(tablename)
    table = db[tablename]

    # Parse the Request
    r = s3mgr.parse_request()

    # Pre-process
    if r.interactive and r.component and r.component.name != "config":
        s3.crud.submit_button = T("Add")

    # Redirect to update view to open tabs
    s3mgr.configure(table,
                    create_next = r.url(method="", id="[id]"))

    # Execute the request
    output = r()

    # Post-Process
    if r.interactive:
        if r.record:
            tabs = [(T("Scenario Details"), None)]
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Human Resources"), "human_resource"))
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Assets"), "asset"))
            tabs.append((T("Facilities"), "site"))
            if deployment_settings.has_module("project"):
                tabs.append((T("Tasks"), "task"))
            tabs.append((T("Map Configuration"), "config"))
            rheader = scenario_rheader(r, tabs)
            output.update(rheader=rheader)
        s3_action_buttons(r)
        if r.component:
            if r.component.name == "asset":
                update_url = "openPopup('%s');return false" % \
                    URL(f="asset",
                        args = "[id].plain",
                        # Open the linked record, not just the link table
                        vars = {"link" : "scenario"})
                delete_url = URL(f="asset", args=["[id]", "delete"])
                response.s3.actions = [
                    dict(label=str(T("Details")), _class="action-btn",
                         _onclick=update_url),
                    dict(label=str(T("Remove")), _class="delete-btn",
                         url=delete_url),
                    ]
            elif r.component.name == "human_resource":
                update_url = "openPopup('%s');return false" % \
                    URL(f="human_resource",
                        args = "[id].plain",
                        # Open the linked record, not just the link table
                        vars = {"link" : "scenario"})
                delete_url = URL(f="human_resource",
                                 args=["[id]", "delete"])
                response.s3.actions = [
                    dict(label=str(T("Details")), _class="action-btn",
                         _onclick=update_url),
                    dict(label=str(T("Remove")), _class="delete-btn",
                         url=delete_url),
                    ]
            elif r.component.name == "site":
                update_url = "openPopup('%s');return false" % \
                    URL(f="site",
                        args = "[id].plain",
                        # Open the linked record, not just the link table
                        vars = {"link" : "scenario"})
                delete_url = URL(f="site",
                                 args=["[id]", "delete"])
                response.s3.actions = [
                    dict(label=str(T("Details")), _class="action-btn",
                         _onclick=update_url),
                    dict(label=str(T("Remove")), _class="delete-btn",
                         url=delete_url),
                    ]
            elif r.component.name == "task":
                update_url = "openPopup('%s');return false" % \
                    URL(f="task",
                        args = "[id].plain",
                        # Open the linked record, not just the link table
                        vars = {"link" : "scenario"})
                delete_url = URL(f="task",
                                 args=["[id]", "delete"])
                response.s3.actions = [
                    dict(label=str(T("Details")), _class="action-btn",
                         _onclick=update_url),
                    dict(label=str(T("Remove")), _class="delete-btn",
                         url=delete_url),
                    ]
            elif r.component.name == "config":
                del output["delete_btn"]
                # Which Map Config do we  use?
                #ltable = r.component.table
                #ctable = db.gis_config
                #query = (ltable.scenario_id == r.id) & \
                #        (ctable.id == ltable.config_id)
                #config = db(query).select(ctable.id, limitby=(0, 1)).first()
                #if config:
                #    # Prepare the form
                #    gis_config_form_setup()
                #    # Parse alternate request
                #    r2 = s3mgr.parse_request(prefix="gis", name="config", args=str(config.id))
                #    output2 = r2()
                #    output.update(form = output2["form"])
                #    output.update(modified_on = output2["modified_on"])
                #else:
                #    # Update once we have a widget
                del output["form"][0][-1]

    return output

# -----------------------------------------------------------------------------
# Components
# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("scenario_scenario")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the asset list of the scenario/event after removing the asset
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "asset"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this asset from this scenario"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            asset_id = r.record.asset_id
            r = s3base.S3Request(s3mgr,
                                 c="asset", f="asset",
                                 args=[str(asset_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def human_resource():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the human_resource list of the scenario/event after removing the human_resource
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "human_resource"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this human resource from this scenario"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            hrm_id = r.record.human_resource_id
            r = s3base.S3Request(s3mgr,
                                 c="hrm", f="human_resource",
                                 args=[str(hrm_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

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

# -----------------------------------------------------------------------------
def site():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the facility list of the scenario/event after removing the facility
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "site"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this facility from this scenario"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            site_id = r.record.site_id
            r = s3base.S3Request(s3mgr,
                                 c="org", f="site",
                                 args=[str(site_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def task():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("project_task")

    # Parse the Request
    r = s3mgr.parse_request()

    link = request.vars.get("link", None)

    # Pre-Process
    if r.id and link:
        # Go back to the task list of the scenario/event after removing the task
        s3mgr.configure(r.tablename,
                        delete_next=URL(link,
                                        args=[r.record["%s_id" % link],
                                              "task"]))

    edit_btn = None
    if link:
        if r.method in ("update", None) and r.id:
            # Store the edit & delete buttons
            edit_btn = A(T("Edit"),
                         _href=r.url(method="update",
                                     representation="html"),
                         _target="_blank")
            delete_btn=A(T("Remove this task from this scenario"),
                         _href=r.url(method="delete",
                                     representation="html"),
                         _class="delete-btn")
            # Switch to the other request
            task_id = r.record.task_id
            r = s3base.S3Request(s3mgr,
                                 c="project", f="task",
                                 args=[str(task_id)],
                                 extension=auth.permission.format)
    # Execute the request
    output = r()

    # Post-Process
    s3_action_buttons(r)

    # Restore the edit & delete buttons with the correct ID
    if r.representation == "plain" and edit_btn:
        output.update(edit_btn=edit_btn)
    elif r.interactive and "delete_btn" in output:
        output.update(delete_btn=delete_btn)

    return output

# -----------------------------------------------------------------------------
def scenario_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None

    if r.representation == "html":

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if r.name == "scenario":
            # Scenario Controller
            scenario = r.record
            if scenario:
                rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                       scenario.name),
                                    TR(TH("%s: " % T("Comments")),
                                       scenario.comments),
                                    ), rheader_tabs)

    return rheader

# END =========================================================================

