# -*- coding: utf-8 -*-

"""
    Event Module - Controllers

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
    """ Redirect to event/create """
    redirect(URL(f="event", args="create"))

# =============================================================================
# Events
# =============================================================================
def event():

    """
        RESTful CRUD controller

        An Event is an instantiation of a template
    """

    tablename = "event_event"
    s3mgr.load(tablename)
    table = db[tablename]

    if "req" in request.args:
        s3mgr.load("req_req")

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component:

                if r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        response.s3.req_create_form_mods()
                else:
                    s3.crud.submit_button = T("Add")

            elif r.method != "update" and r.method != "read":
                # Create or ListCreate
                r.table.closed.writable = r.table.closed.readable = False

            elif r.method == "update":
                # Can't change details after event activation
                r.table.scenario_id.writable = False
                r.table.exercise.writable = False
                r.table.exercise.comment = None
                r.table.zero_hour.writable = False

        return True
    response.s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.component:
                if r.component.name == "asset":
                    update_url = "openPopup('%s');return false" % \
                        URL(f="asset",
                            args = "[id].plain",
                            # Open the linked record, not just the link table
                            vars = {"link" : "event"})
                    delete_url = URL(f="asset",
                                     args=["[id]", "delete"])
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
                            vars = {"link" : "event"})
                    delete_url = URL(f="human_resource",
                                     args=["[id]", "delete"])
                    response.s3.actions = [
                        dict(label=str(T("Details")), _class="action-btn",
                             _onclick=update_url),
                        dict(label=str(T("Remove")), _class="delete-btn",
                             url=delete_url),
                        ]
                    if "msg" in deployment_settings.modules:
                        response.s3.actions.append({
                            "url": URL(f="compose",
                                       vars = {"hrm_id": "[id]"}),
                            "_class": "action-btn",
                            "label": str(T("Send Notification"))})

                elif r.component.name == "site":
                    update_url = "openPopup('%s');return false" % \
                        URL(f="site",
                            args = "[id].plain",
                            # Open the linked record, not just the link table
                            vars = {"link" : "event"})
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
                            vars = {"link" : "event"})
                    delete_url = URL(f="task",
                                     args=["[id]", "delete"])
                    response.s3.actions = [
                        dict(label=str(T("Details")), _class="action-btn",
                             _onclick=update_url),
                        dict(label=str(T("Remove")), _class="delete-btn",
                             url=delete_url),
                        ]

                elif r.component.name == "activity":
                    update_url = "openPopup('%s');return false" % \
                        URL(f="activity",
                            args = "[id].plain",
                            # Open the linked record, not just the link table
                            vars = {"link" : "event"})
                    delete_url = URL(f="activity",
                                     args=["[id]", "delete"])
                    response.s3.actions = [
                        dict(label=str(T("Details")), _class="action-btn",
                             _onclick=update_url),
                        dict(label=str(T("Remove")), _class="delete-btn",
                             url=delete_url),
                        ]

            elif r.method == "create":
                # Redirect to update view to open tabs
                r.next = r.url(method="update",
                               id=s3mgr.get_session("event", "event"))

        return output
    response.s3.postp = postp

    tabs = [(T("Event Details"), None)]
    if deployment_settings.has_module("hrm"):
        tabs.append((T("Human Resources"), "human_resource"))
    if deployment_settings.has_module("asset"):
        tabs.append((T("Assets"), "asset"))
    tabs.append((T("Facilities"), "site"))
    if deployment_settings.has_module("req"):
        tabs.append((T("Requests"), "req"))
    if deployment_settings.has_module("project"):
        tabs.append((T("Tasks"), "task"))
        tabs.append((T("Activities"), "activity"))
    tabs.append((T("Map Configuration"), "config"))

    rheader = lambda r, tabs=tabs: event_rheader(r, tabs)
    output = s3_rest_controller("event", resourcename,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
# Components
# -----------------------------------------------------------------------------
def asset():
    """ RESTful CRUD controller """

    # Load the Models
    s3mgr.load("event_event")

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
            delete_btn=A(T("Remove this asset from this event"),
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
            delete_btn=A(T("Remove this human resource from this event"),
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
            delete_btn=A(T("Remove this facility from this event"),
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
    s3mgr.load("event_event")

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
            delete_btn=A(T("Remove this task from this event"),
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
def event_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    rheader_tabs = s3_rheader_tabs(r, tabs)

    if r.representation == "html":

        if r.name == "event":
            # Event Controller
            event = r.record
            if event:
                if event.exercise:
                    exercise = TH(T("EXERCISE"))
                else:
                    exercise = TH()
                if event.closed:
                    closed = TH(T("CLOSED"))
                else:
                    closed = TH()
                rheader = DIV(TABLE(TR(exercise),
                                    TR(TH("%s: " % T("Name")),
                                       event.name),
                                       TH("%s: " % T("Comments")),
                                       event.comments,
                                    TR(TH("%s: " % T("Zero Hour")),
                                       event.zero_hour),
                                    TR(closed),
                                    ), rheader_tabs)

    return rheader

# =============================================================================
# Messaging
# =============================================================================

def compose():

    """ Send message to people/teams """

    s3mgr.load("msg_outbox")

    if "hrm_id" in request.vars:
        id = request.vars.hrm_id
        fieldname = "hrm_id"
        table = db.pr_person
        htable = db.hrm_human_resource
        pe_id_query = (htable.id == id) & \
                      (htable.person_id == table.id)
        title = T("Send a message to this person")

    pe = db(pe_id_query).select(table.pe_id,
                                limitby=(0, 1)).first()
    if not pe:
        session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id
    request.vars.pe_id = pe_id

    # Get the individual's communications options & preference
    table = db.pr_contact
    contact = db(table.pe_id == pe_id).select(table.contact_method,
                                              orderby="priority",
                                              limitby=(0, 1)).first()
    if contact:
        db.msg_outbox.pr_message_method.default = contact.contact_method
    else:
        session.error = T("No contact method found")
        redirect(URL(f="index"))

    return response.s3.msg_compose(redirect_module = module,
                                   redirect_function = "compose",
                                   redirect_vars = {fieldname: id},
                                   title_name = title)

# END =========================================================================

