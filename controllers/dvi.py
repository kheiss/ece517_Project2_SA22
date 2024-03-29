# -*- coding: utf-8 -*-

"""
    Disaster Victim Identification, Controllers

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# Load Models
s3mgr.load("dvi_body")

# -----------------------------------------------------------------------------
def s3_menu_postp():
    menu_selected = []
    body_id = s3mgr.get_session("dvi", "body")
    if body_id:
        body = db.dvi_body
        query = (body.id == body_id)
        record = db(query).select(body.id, body.pe_label,
                                  limitby=(0,1)).first()
        if record:
            label = record.pe_label
            response.menu_options[-3][-1].append(
                [T("Candidate Matches for Body %s" % label),
                 False, URL(f="person",
                            vars=dict(match=record.id))]
            )
            menu_selected.append(
                ["%s: %s" % (T("Body"), label),
                 False, URL(f="body", args=[record.id])]
            )
    person_id = s3mgr.get_session("pr", "person")
    if person_id:
        person = db.pr_person
        query = (person.id == person_id)
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = person_represent(record.id)
            menu_selected.append(
                ["%s: %s" % (T("Person"), name),
                 False, URL(f="person", args=[record.id])]
            )
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

s3_menu(module, s3_menu_postp)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Disaster Victim Identification")

    table = db.dvi_body
    total = db(table.deleted == False).count()

    itable = db.dvi_identification
    query = (table.deleted == False) & \
            (itable.pe_id == table.pe_id) & \
            (itable.deleted == False) & \
            (itable.status == 3)
    identified = db(query).count()

    status = [[str(T("identified")), int(identified)],
              [str(T("unidentified")), int(total-identified)]]

    response.title = module_name
    return dict(module_name=module_name,
                total=total,
                status=json.dumps(status))

# -----------------------------------------------------------------------------
def recreq():
    """ Recovery Requests List """

    resourcename = request.function

    table = db.dvi_recreq
    table.person_id.default = s3_logged_in_person()

    def prep(r):
        if r.interactive and not r.record:
            table.status.readable = False
            table.status.writable = False
            table.bodies_recovered.readable = False
            table.bodies_recovered.writable = False
        return True
    response.s3.prep = prep
    output = s3_rest_controller(module, resourcename)

    s3_menu(module, s3_menu_postp)
    return output

# -----------------------------------------------------------------------------
def morgue():
    """ Morgue Registry """

    resourcename = request.function
    morgue_tabs = [(T("Morgue Details"), ""),
                   (T("Bodies"), "body")]

    rheader = response.s3.dvi_rheader
    output = s3_rest_controller(module, resourcename,
                                rheader=lambda r: \
                                        rheader(r, tabs=morgue_tabs))
    s3_menu(module, s3_menu_postp)
    return output

# -----------------------------------------------------------------------------
def body():
    """ Dead Bodies Registry """

    resourcename = request.function

    status = request.get_vars.get("status", None)
    if status == "unidentified":
        query = (db.dvi_identification.deleted == False) & \
                (db.dvi_identification.status == 3)
        ids = db(query).select(db.dvi_identification.pe_id)
        ids = [i.pe_id for i in ids]
        if ids:
            response.s3.filter = (~(db.dvi_body.pe_id.belongs(ids)))

    s3mgr.configure("dvi_body", main="pe_label", extra="gender")

    db.pr_note.status.readable = False
    db.pr_note.status.writable = False

    dvi_tabs = [(T("Recovery"), ""),
                (T("Checklist"), "checklist"),
                (T("Images"), "pimage"),
                (T("Physical Description"), "physical_description"),
                (T("Effects Inventory"), "effects"),
                (T("Journal"), "note"),
                (T("Identification"), "identification")]

    rheader = response.s3.dvi_rheader
    output = s3_rest_controller(module, resourcename,
                                 rheader=lambda r: rheader(r, tabs=dvi_tabs))
    s3_menu(module, s3_menu_postp)
    return output

# -----------------------------------------------------------------------------
def person():
    """ Missing Persons Registry (Match Finder) """

    resourcename = request.function

    s3.crud_strings["pr_person"].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons"),
        subtitle_list = T("List of Missing Persons"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons found"),
        msg_no_match = T("No Persons currently reported missing"))

    s3mgr.configure("pr_group_membership",
                    list_fields=["id",
                                 "group_id",
                                 "group_head",
                                 "description"
                                ])

    s3mgr.configure("pr_person",
                    listadd=False,
                    editable=False,
                    deletable=False,
                    list_fields=["id",
                                 "first_name",
                                 "middle_name",
                                 "last_name",
                                 "picture",
                                 "gender",
                                 "age_group"
                                ])

    def prep(r):
        if not r.id and not r.method and not r.component:
            body_id = r.get_vars.get("match", None)
            body = db(db.dvi_body.id == body_id).select(
                      db.dvi_body.pe_label, limitby=(0, 1)).first()
            label = body and body.pe_label or "#%s" % body_id
            if body_id:
                query = vita.match_query(body_id)
                r.resource.add_filter(query)
                s3.crud_strings["pr_person"].update(
                    subtitle_list = T("Candidate Matches for Body %s" % label),
                    msg_no_match = T("No matching records found"))
        return True
    response.s3.prep = prep

    db.pr_person.missing.readable = False
    db.pr_person.missing.writable = False
    db.pr_person.missing.default = True

    # Show only missing persons in list views
    if len(request.args) == 0:
        response.s3.filter = (db.pr_person.missing == True)

    mpr_tabs = [
                (T("Missing Report"), "missing_report"),
                (T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "pimage"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "contact"),
                (T("Journal"), "note"),
               ]

    rheader = lambda r: pr_rheader(r, tabs=mpr_tabs)

    output = s3_rest_controller("pr", resourcename,
                                 main="first_name",
                                 extra="last_name",
                                 rheader=rheader)
    s3_menu(module, s3_menu_postp)
    return output

# -----------------------------------------------------------------------------
def tooltip():
    """ Ajax Tooltips """

    formfield = request.vars.get("formfield", None)
    if formfield:
        response.view = "pr/ajaxtips/%s.html" % formfield
    return dict()

# -----------------------------------------------------------------------------

