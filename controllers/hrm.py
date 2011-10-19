# -*- coding: utf-8 -*-

"""
    Human Resource Management

    @author: Dominic König <dominic AT aidiq DOT com>
    @author: Fran Boon <fran AT aidiq DOT com>
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

roles = session.s3.roles or []
if session.s3.hrm is None:
    session.s3.hrm = Storage()
session.s3.hrm.mode = request.vars.get("mode", None)

# =============================================================================
def org_filter():
    """
        Find the Organisation(s) this user is entitled to view
        i.e. they have the organisation access role or a site access role
    """

    table = db.org_organisation
    orgs = db(table.owned_by_organisation.belongs(roles)).select(table.id)
    orgs = [org.id for org in orgs]
    
    stable = db.org_site
    siteorgs = db(stable.owned_by_facility.belongs(roles)).select(stable.organisation_id)
    for org in siteorgs:
        if org.organisation_id not in orgs:
            orgs.append(org.organisation_id)

    if orgs:
        session.s3.hrm.orgs = orgs
    else:
        session.s3.hrm.orgs = None

# =============================================================================
@auth.requires_login()
def s3_menu_prep():
    """ Application Menu """

    # Module Name
    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Human Resources Management")
    response.title = module_name

    # Automatically choose an organisation
    if session.s3.hrm.orgs is None:
        org_filter()

    # Set mode
    if session.s3.hrm.mode != "personal" and \
       (ADMIN in roles or session.s3.hrm.orgs):
        session.s3.hrm.mode = None
    else:
        session.s3.hrm.mode = "personal"

s3_menu(module, prep=s3_menu_prep)

# =============================================================================
def index():
    """ Dashboard """

    if session.error:
        return dict()

    mode = session.s3.hrm.mode
    if mode is not None:
        redirect(URL(f="person"))

    # Load Models
    s3mgr.load("hrm_skill")

    tablename = "hrm_human_resource"
    table = db.hrm_human_resource

    if ADMIN not in roles:
        orgs = session.s3.hrm.orgs or [None]
        org_filter = (table.organisation_id.belongs(orgs))
    else:
        # Admin can see all Orgs
        org_filter = (table.organisation_id > 0)

    s3mgr.configure(tablename,
                    insertable=False,
                    list_fields=["id",
                                 "person_id",
                                 "job_title",
                                 "type",
                                 "site_id"])

    response.s3.filter = org_filter
    # Parse the Request
    r = s3base.S3Request(s3mgr, prefix="hrm", name="human_resource")
    # Pre-process
    # Only set the method to search if it is not an ajax dataTable call
    # This fixes a problem with the dataTable where the the filter had a
    # distinct in the sql which cause a ticket to be raised
    if r.representation != "aadata":
        r.method = "search"
    r.custom_action = human_resource_search
    # Execute the request
    output = r()
    if r.representation == "aadata":
        return output
    # Post-process
    response.s3.actions = [dict(label=str(T("Details")),
                                _class="action-btn",
                                url=URL(f="person",
                                        args=["human_resource"],
                                        vars={"human_resource.id": "[id]"}))]

    if r.interactive:
        output.update(module_name=response.title)
        if session.s3.hrm.orgname:
            output.update(orgname=session.s3.hrm.orgname)
        response.view = "hrm/index.html"
        query = (table.deleted != True) & \
                (table.status == 1) & org_filter
        ns = db(query & (table.type == 1)).count()
        nv = db(query & (table.type == 2)).count()
        output.update(ns=ns, nv=nv)

        module_name = deployment_settings.modules[module].name_nice
        output.update(title=module_name)

    return output

# =============================================================================
# People
# =============================================================================
def human_resource():
    """
        HR Controller
        - designed for use in Map popups or non-interactive use only
    """

    # Load Models
    s3mgr.load("pr_address")
    s3mgr.load("hrm_skill")

    tablename = "hrm_human_resource"
    table = db[tablename]
    ptable = db.pr_person

    # Configure CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Staff Member"),
        title_display = T("Staff Member Details"),
        title_list = T("Staff and Volunteers"),
        title_update = T("Edit Record"),
        title_search = T("Search Staff or Volunteer"),
        subtitle_create = T("Add New Staff Member"),
        subtitle_list = T("Staff Members"),
        label_list_button = T("List All Records"),
        label_create_button = T("Add Staff Member"),
        label_delete_button = T("Delete Record"),
        msg_record_created = T("Staff member added"),
        msg_record_modified = T("Record updated"),
        msg_record_deleted = T("Record deleted"),
        msg_list_empty = T("No staff or volunteers currently registered"))

    # Must specify a group to create HRs
    group = request.vars.get("group", None)
    # Not certain if request.vars.group exists anymore...  Graeme
    if group == None:
        groupCode = request.vars.get("human_resource.type", "1")
        if groupCode == "2":
            group = "volunteer"
        else:
            group = "staff"
    if group == "volunteer":
        table.type.default = 2
        table.location_id.writable = True
        table.location_id.readable = True
        s3.crud_strings[tablename].update(
            title_create = T("Add Volunteer"),
            title_display = T("Volunteer Information"),
            subtitle_create = T("Add New Volunteer"),
            subtitle_list = T("Volunteers"),
            label_create_button = T("Add Volunteer"),
            msg_record_created = T("Volunteer added"))
    #elif group == "staff":
    else:
        #s3mgr.configure(table._tablename, insertable=False)
        # Default to Staff
        table.type.default = 1
        table.site_id.writable = True
        table.site_id.readable = True
        s3.crud_strings[tablename].update(title_create = T("Add Staff Member"))

    ## Test Code
    #class MyVirtualFields:
        #extra_fields = ["person_id$first_name",
                        #"person_id$last_name"]
        #def fullname(self):
            #return "%s %s" % (self.pr_person.first_name,
                              #self.pr_person.last_name)
    #table.virtualfields.append(MyVirtualFields())

    s3mgr.configure(tablename,
                    list_fields = ["id",
                                   "person_id",
                                   #(T("Person Name"), "fullname"),
                                   "job_title",
                                   #"person_id$occupation",
                                   "organisation_id",
                                   "site_id",
                                   "location_id",
                                   "type",
                                   "status",
                                ])

    def prep(r):
        if r.interactive:
            # Assume volunteers only between 12-81
            db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-144)

            r.table.site_id.comment = DIV(DIV(_class="tooltip",
                                              _title="%s|%s|%s" % (T("Facility"),
                                                                   T("The site where this position is based."),
                                                                   T("Enter some characters to bring up a list of possible matches."))))
            if r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                r.table.status.writable = False
                r.table.status.readable = False

            if r.method == "create" and r.component is None:
                if group in (1, 2):
                    table.type.readable = False
                    table.type.writable = False
            elif r.representation == "plain":
                # Don't redirect Map popups
                pass
            elif r.id:
                redirect(URL(f="person",
                             #args=["human_resource"],
                             vars={"human_resource.id": r.id,
                                   "group": group}))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                s3_action_buttons(r, deletable=False)
                if "msg" in deployment_settings.modules:
                    # @ToDo: Remove this now that we have it in Events?
                    response.s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"hrm_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Notification"))})
        elif r.representation == "plain":
            # Map Popups
            output = hrm_map_popup(r)
        return output
    response.s3.postp = postp

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def hrm_map_popup(r):
    """
        Custom output to place inside a Map Popup
        - called from postp of human_resource controller
    """

    # Load Model
    s3mgr.load("pr_address")
    #s3mgr.load("hrm_skill")

    output = TABLE()
    # First name, last name
    output.append(TR(TD(B("%s:" % T("Name"))),
                     TD(s3_fullname(r.record.person_id))))
    # Occupation (Job Title?)
    if r.record.job_title:
        output.append(TR(TD(B("%s:" % r.table.job_title.label)),
                         TD(r.record.job_title)))
    # Organization (better with just name rather than Represent)
    table = db.org_organisation
    query = (table.id == r.record.organisation_id)
    name = db(query).select(table.name,
                            limitby=(0, 1)).first().name
    output.append(TR(TD(B("%s:" % r.table.organisation_id.label)),
                     TD(name)))
    if r.record.location_id:
        table = db.gis_location
        query = (table.id == r.record.location_id)
        location = db(query).select(table.path,
                                    table.addr_street,
                                    limitby=(0, 1)).first()
        # City
        # Street address
        if location.addr_street:
            output.append(TR(TD(B("%s:" % table.addr_street.label)),
                             TD(location.addr_street)))
    # Mobile phone number
    table = db.pr_person
    query = (table.id == r.record.person_id)
    pe_id = db(query).select(table.pe_id,
                             limitby=(0, 1)).first().pe_id
    table = db.pr_contact
    query = (table.pe_id == pe_id)
    contacts = db(query).select(table.contact_method,
                                table.value)
    email = mobile_phone = ""
    for contact in contacts:
        if contact.contact_method == "EMAIL":
            email = contact.value
        elif contact.contact_method == "SMS":
            mobile_phone = contact.value
    if mobile_phone:
        output.append(TR(TD(B("%s:" % pr_contact_method_opts.get("SMS"))),
                         TD(mobile_phone)))
    # Office number
    if r.record.site_id:
        table = db.org_office
        query = (table.site_id == r.record.site_id)
        office = db(query).select(table.phone1,
                                  limitby=(0, 1)).first()
        if office and office.phone1:
            output.append(TR(TD(B("%s:" % T("Office Phone"))),
                             TD(office.phone1)))
        else:
            # @ToDo: Support other Facility Types (Hospitals & Shelters)
            pass
    # Email address (as hyperlink)
    if email:
        output.append(TR(TD(B("%s:" % pr_contact_method_opts.get("EMAIL"))),
                         TD(A(email, _href="mailto:%s" % email))))

    return output

# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - includes components relevant to HRM

        @ToDo: Volunteers should be redirected to vol/person
    """

    s3mgr.model.add_component("hrm_human_resource",
                              pr_person="person_id")

    group = request.vars.get("group", "staff")
    hr_id = request.vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    mode = session.s3.hrm.mode

    # Configure human resource table
    tablename = "hrm_human_resource"
    table = db[tablename]
    if hr_id and str(hr_id).isdigit():
        hr = table[hr_id]
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
    org = session.s3.hrm.org
    if org is not None:
        table.organisation_id.default = org
        table.organisation_id.comment = None
        table.organisation_id.readable = False
        table.organisation_id.writable = False
        table.site_id.requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                    "org_site.%s" % super_key(db.org_site),
                                    org_site_represent,
                                    filterby="organisation_id",
                                    filter_opts=[session.s3.hrm.org]))
    table.type.readable = True
    table.type.writable = True
    if group == "staff" and hr_id:
        table.site_id.writable = True
        table.site_id.readable = True
    elif group == "volunteer" and hr_id:
        table.location_id.writable = True
        table.location_id.readable = True
    elif not hr_id:
        table.location_id.readable = True
        table.site_id.readable = True
    if session.s3.hrm.mode is not None:
        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "organisation_id",
                                     "type",
                                     "job_title",
                                     "status",
                                     "location_id",
                                     "site_id"])
    else:
        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "type",
                                     "job_title",
                                     "status",
                                     "location_id",
                                     "site_id"])

    # Configure person table
    # - hide fields
    tablename = "pr_person"
    table = db[tablename]
    table.pe_label.readable = False
    table.pe_label.writable = False
    table.missing.readable = False
    table.missing.writable = False
    table.age_group.readable = False
    table.age_group.writable = False
    s3mgr.configure(tablename,
                    deletable=False)
    if group == "staff":
        # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
        table.occupation.readable = False
        table.occupation.writable = False
        # Just have a Home Address
        table = db.pr_address
        table.type.default = 1
        table.type.readable = False
        table.type.writable = False
        _crud = s3.crud_strings.pr_address
        _crud.title_create = T("Add Home Address")
        _crud.title_update = T("Edit Home Address")
        s3mgr.model.add_component("pr_address",
                                  pr_pentity=dict(joinby=super_key(db.pr_pentity),
                                                  multiple=False))
        address_tab_name = T("Home Address")
    else:
        address_tab_name = T("Addresses")

    # Configure for personal mode
    if session.s3.hrm.mode is not None:
        db.hrm_human_resource.organisation_id.readable = True
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        s3mgr.configure("hrm_human_resource",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_certification",
                        insertable = True,
                        editable = True,
                        deletable = True)
        s3mgr.configure("hrm_credential",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_competency",
                        insertable = True,  # Can add unconfirmed
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_training",    # Can add but not provide grade
                        insertable = True,
                        editable = False,
                        deletable = False)
        s3mgr.configure("hrm_experience",
                        insertable = False,
                        editable = False,
                        deletable = False)
        s3mgr.configure("pr_group_membership",
                        insertable = False,
                        editable = False,
                        deletable = False)
        tabs = [(T("Person Details"), None),
                (address_tab_name, "address"),
                (T("Contact Details"), "contact"),
                (T("Skills"), "competency"),
                #(T("Credentials"), "credential"),
                (T("Certificates"), "certification"),
                (T("Trainings"), "training"),
                (T("Mission Record"), "experience"),
                (T("Positions"), "human_resource"),
                (T("Teams"), "group_membership")]

    # Configure for HR manager mode
    else:
        if group == "staff":
            s3.crud_strings[tablename].update(
                title_display = T("Staff Member Details"),
                title_update = T("Staff Member Details"))
            hr_record = T("Staff Record")
        elif group == "volunteer":
            s3.crud_strings[tablename].update(
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details"))
            hr_record = T("Volunteer Record")
        tabs = [(T("Person Details"), None),
                (hr_record, "human_resource"),
                (T("Home Address"), "address"),
                (T("Contact Data"), "contact"),
                (T("Skills"), "competency"),
                (T("Credentials"), "credential"),
                (T("Trainings"), "training"),
                (T("Mission Record"), "experience"),
                (T("Teams"), "group_membership")]

    # Prepare CRUD
    def prep(r):
        if r.representation == "s3json":
            s3mgr.show_ids = True
        elif r.interactive:
            resource = r.resource

            # Assume volunteers only between 12-81
            r.table.date_of_birth.widget = S3DateWidget(past=972, future=-144)

            if mode is not None:
                r.resource.build_query(id=s3_logged_in_person())
            else:
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="human_resource"))
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if not r.record:
                session.error = T("Record not found")
                redirect(URL(group, args=["search"]))
            if hr_id and r.component_name == "human_resource":
                r.component_id = hr_id
            s3mgr.configure("hrm_human_resource",
                            insertable = False)
            if not r.component_id or r.method in ("create", "update"):
                address_hide(db.pr_address)
        return True
    response.s3.prep = prep

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname=session.s3.hrm.orgname
    else:
        orgname=None
    rheader = lambda r, tabs=tabs: hrm_rheader(r, tabs)

    output = s3_rest_controller("pr", resourcename,
                                native=False,
                                rheader=rheader,
                                orgname=orgname)
    return output

# -----------------------------------------------------------------------------
def hrm_rheader(r, tabs=[]):
    """ Resource headers for component views """

    rheader = None
    rheader_tabs = s3_rheader_tabs(r, tabs)

    if r.representation == "html":

        if r.name == "person":
            # Person Controller
            person = r.record
            if person:
                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       s3_fullname(person),
                       TH(""),
                       ""),

                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH(""),
                       ""),

                    ), rheader_tabs)

        elif r.name == "human_resource":
            # Human Resource Controller
            hr = r.record
            if hr:
                pass

        elif r.name == "organisation":
            # Organisation Controller
            org = r.record
            if org:
                pass

    return rheader

# =============================================================================
# Teams
# =============================================================================
def group():

    """
        Team controller
        - uses the group table from PR
    """

    tablename = "pr_group"
    table = db[tablename]

    table.group_type.label = T("Team Type")
    table.description.label = T("Team Description")
    table.name.label = T("Team Name")
    db.pr_group_membership.group_id.label = T("Team ID")
    db.pr_group_membership.group_head.label = T("Team Leader")

    # Set Defaults
    table.group_type.default = 3  # 'Relief Team'
    table.group_type.readable = table.group_type.writable = False

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = LIST_TEAMS,
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        subtitle_list = T("Teams"),
        label_list_button = LIST_TEAMS,
        label_create_button = ADD_TEAM,
        label_search_button = T("Search Teams"),
        msg_record_created = T("Team added"),
        msg_record_modified = T("Team updated"),
        msg_record_deleted = T("Team deleted"),
        msg_list_empty = T("No Teams currently registered"))

    s3.crud_strings["pr_group_membership"] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Team Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Team Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Team Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

    response.s3.filter = (table.system == False) # do not show system groups

    s3mgr.configure(tablename, main="name", extra="description",
                    # Redirect to member list when a new group has been created
                    create_next = URL(f="group",
                                      args=["[id]", "group_membership"]))
    s3mgr.configure("pr_group_membership",
                    list_fields=["id",
                                 "person_id",
                                 "group_head",
                                 "description"])

    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                s3_action_buttons(r, deletable=False)
                if "msg" in deployment_settings.modules:
                    response.s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"group_id": "[id]"}),
                        "_class": "action-btn",
                        "label": str(T("Send Notification"))})

        return output
    response.s3.postp = postp

    tabs = [
            (T("Team Details"), None),
            # Team should be contacted either via the Leader or
            # simply by sending a message to the group as a whole.
            #(T("Contact Data"), "contact"),
            (T("Members"), "group_membership")]

    output = s3_rest_controller("pr", resourcename,
                                rheader=lambda r: pr_rheader(r, tabs = tabs))

    return output


# =============================================================================
# Jobs
# =============================================================================
def job_role():
    """ Job Roles Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    output = s3_rest_controller(module, resourcename)
    return output

# =============================================================================
# Skills
# =============================================================================
def skill():
    """ Skills Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output


def skill_type():
    """ Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def competency_rating():
    """ Competency Rating for Skill Types Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def skill_competencies():
    """
        Called by S3FilterFieldChange to provide the competency options for a
            particular Skill Type
    """

    # Load Models
    s3mgr.load("hrm_skill")

    table = db.hrm_skill
    ttable = db.hrm_skill_type
    rtable = db.hrm_competency_rating
    query = (table.id == request.args[0]) & \
            (table.skill_type_id == ttable.id) & \
            (rtable.skill_type_id == table.skill_type_id)
    records = db(query).select(rtable.id,
                               rtable.name)

    response.headers["Content-Type"] = "application/json"
    return records.json()

# -----------------------------------------------------------------------------
def skill_provision():
    """ Skill Provisions Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def course():
    """ Courses Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def course_certificate():
    """ Courses to Certificates Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def certificate():
    """ Certificates Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# -----------------------------------------------------------------------------
def certificate_skill():
    """ Certificates to Skills Controller """

    mode = session.s3.hrm.mode
    if mode is not None:
        session.error = T("Access denied")
        redirect(URL(f="index"))

    # Load Models
    s3mgr.load("hrm_skill")

    output = s3_rest_controller(module, resourcename)
    return output

# =============================================================================
def staff_org_site_json():
    """
        Used by the Asset - Assign to Person page
    """

    table = db.hrm_human_resource
    otable = db.org_organisation
    #db.req_commit.date.represent = lambda dt: dt[:10]
    query = (table.person_id == request.args[0]) & \
            (table.organisation_id == otable.id)
    records = db(query).select(table.site_id,
                               otable.id,
                               otable.name)

    response.headers["Content-Type"] = "application/json"
    return records.json()

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
