# -*- coding: utf-8 -*-

""" HMS Hospital Status Assessment and Request Management System

    @author: nursix

"""

module = "hms"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # Hospitals
    #

    # Use government-assigned UUIDs instead of internal UUIDs
    HMS_HOSPITAL_USE_GOVUUID = True

    hms_facility_type_opts = {
        1: T("Hospital"),
        2: T("Field Hospital"),
        3: T("Specialized Hospital"),
        11: T("Health center"),
        12: T("Health center with beds"),
        13: T("Health center without beds"),
        21: T("Dispensary"),
        98: T("Other"),
        99: T("Unknown type of facility"),
    } #: Facility Type Options

    hms_facility_status_opts = {
        1: T("Normal"),
        2: T("Compromised"),
        3: T("Evacuating"),
        4: T("Closed")
    } #: Facility Status Options

    hms_clinical_status_opts = {
        1: T("Normal"),
        2: T("Full"),
        3: T("Closed")
    } #: Clinical Status Options

    hms_morgue_status_opts = {
        1: T("Open"),
        2: T("Full"),
        3: T("Exceeded"),
        4: T("Closed")
    } #: Morgue Status Options

    hms_security_status_opts = {
        1: T("Normal"),
        2: T("Elevated"),
        3: T("Restricted Access"),
        4: T("Lockdown"),
        5: T("Quarantine"),
        6: T("Closed")
    } #: Security Status Options

    hms_resource_status_opts = {
        1: T("Adequate"),
        2: T("Insufficient")
    } #: Resource Status Options

    hms_ems_traffic_opts = {
        1: T("Normal"),
        2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: EMS Traffic Options

    hms_or_status_opts = {
        1: T("Normal"),
        #2: T("Advisory"),
        3: T("Closed"),
        4: T("Not Applicable")
    } #: Operating Room Status Options

    resourcename = "hospital"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                    super_link(db.org_site),
                    Field("paho_uuid", unique=True, length=128,
                          requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                              "%s.paho_uuid" % tablename)),
                          label = T("PAHO UID")),
                    # UID assigned by Local Government
                    Field("gov_uuid", unique=True, length=128,
                          requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                              "%s.gov_uuid" % tablename)),
                          label = T("Government UID")),
                    # Alternate ids found in data feeds
                    Field("other_ids", length=128),
                    # Mayon compatibility
                    #Field("code",
                    #      length=10,
                    #      notnull=True,
                    #      unique=True, label=T("Code")),
                    Field("name", notnull=True,                 # Name of the facility
                          length=64,            # Mayon compatibility
                          label = T("Name")),
                    Field("aka1", label = T("Other Name")),     # Alternate name, or name in local language
                    Field("aka2",label = T("Other Name")),      # Alternate name, or name in local language
                    Field("facility_type", "integer",
                          requires = IS_NULL_OR(IS_IN_SET(hms_facility_type_opts)),
                          default = 1,
                          label = T("Facility Type"),
                          represent = lambda opt: hms_facility_type_opts.get(opt, T("not specified"))),
                    organisation_id(),
                    location_id(),
                    Field("address", label = T("Address")),                                  # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("postcode", label = deployment_settings.get_ui_label_postcode()),  # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("city"),                                                           # @ToDo: Deprecate these & use location_id in HAVE exporter
                    Field("phone_exchange", label = T("Phone/Exchange (Switchboard)"),
                          requires = IS_NULL_OR(s3_phone_requires)),
                    Field("phone_business", label = T("Phone/Business"),
                          requires = IS_NULL_OR(s3_phone_requires)),
                    Field("phone_emergency", label = T("Phone/Emergency"),
                          requires = IS_NULL_OR(s3_phone_requires)),
                    Field("website", label=T("Website"),
                          requires = IS_NULL_OR(IS_URL()),
                          represent = s3_url_represent),
                    Field("email", label = T("Email"),
                          requires = IS_NULL_OR(IS_EMAIL())),
                    Field("fax", label = T("Fax"),
                          requires = IS_NULL_OR(s3_phone_requires)),
                    Field("total_beds", "integer",
                          readable = False,
                          writable = False,
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                          label = T("Total Beds")),
                    Field("available_beds", "integer",
                          readable = False,
                          writable = False,
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                          label = T("Available Beds")),
                    Field("ems_status", "integer",              # Emergency Room Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_ems_traffic_opts)),
                          label = T("ER Status"),
                          represent = lambda opt: hms_ems_traffic_opts.get(opt, UNKNOWN_OPT)),
                    Field("ems_reason", length=128,             # Reason for EMS Status
                          label = T("ER Status Reason")),
                    Field("or_status", "integer",               # Operating Room Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_or_status_opts)),
                          label = T("OR Status"),
                          represent = lambda opt: hms_or_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("or_reason", length=128,              # Reason for OR Status
                          label = T("OR Status Reason")),
                    Field("facility_status", "integer",
                          requires = IS_NULL_OR(IS_IN_SET(hms_facility_status_opts)),
                          label = T("Facility Status"),
                          represent = lambda opt: hms_facility_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_status", "integer",
                          requires = IS_NULL_OR(IS_IN_SET(hms_clinical_status_opts)),
                          label = T("Clinical Status"),
                          represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_status", "integer",
                          requires = IS_NULL_OR(IS_IN_SET(hms_morgue_status_opts)),
                          label = T("Morgue Status"),
                          represent = lambda opt: hms_clinical_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("morgue_units", "integer",           # Number of available/vacant morgue units
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                          label = T("Morgue Units Available")),
                    Field("security_status", "integer",
                          requires = IS_NULL_OR(IS_IN_SET(hms_security_status_opts)),
                          label = T("Security Status"),
                          represent = lambda opt: hms_security_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("doctors", "integer", label = T("Number of doctors"),
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                    Field("nurses", "integer", label = T("Number of nurses"),
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                    Field("non_medical_staff", "integer",
                          requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                          label = T("Number of non-medical staff")),
                    Field("staffing", "integer",                # Staffing status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Staffing"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("facility_operations", "integer",     # Facility Operations Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Facility Operations"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("clinical_operations", "integer",     # Clinical Operations Status
                          requires = IS_NULL_OR(IS_IN_SET(hms_resource_status_opts)),
                          label = T("Clinical Operations"),
                          represent = lambda opt: hms_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("access_status", label = T("Road Conditions")),
                    #document_id(),                             # Better to have multiple Documents on a Tab
                    comments(),
                    *s3_meta_fields())

    # CRUD Strings
    LIST_HOSPITALS = T("List Hospitals")
    ADD_HOSPITAL = T("Add Hospital")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_HOSPITAL,
        title_display = T("Hospital Details"),
        title_list = LIST_HOSPITALS,
        title_update = T("Edit Hospital"),
        title_search = T("Find Hospital"),
        subtitle_create = T("Add New Hospital"),
        subtitle_list = T("Hospitals"),
        label_list_button = LIST_HOSPITALS,
        label_create_button = ADD_HOSPITAL,
        label_delete_button = T("Delete Hospital"),
        msg_record_created = T("Hospital information added"),
        msg_record_modified = T("Hospital information updated"),
        msg_record_deleted = T("Hospital information deleted"),
        msg_list_empty = T("No Hospitals currently registered"))

    # Reusable field for other tables to reference

    hms_hospital_id_comment = DIV(A(ADD_HOSPITAL,
                                    _class="colorbox",
                                    _href=URL(c="hms", f="hospital",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_HOSPITAL),
                                  DIV(DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Hospital"),
                                                            T("If you don't see the Hospital in the list, you can add a new one by clicking link 'Add Hospital'.")))))
                                                            # If using Autocomplete Widget
                                                            #T("Enter some characters to bring up a list of possible matches")))))
    hospital_id = S3ReusableField("hospital_id", db.hms_hospital,
                                  sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "hms_hospital.id", "%(name)s")),
                                  represent = lambda id: \
                                    (id and [db(db.hms_hospital.id == id).select(db.hms_hospital.name,
                                                                                 limitby=(0, 1)).first().name] or ["None"])[0],
                                  label = T("Hospital"),
                                  comment = hms_hospital_id_comment,
                                  ondelete = "RESTRICT")

    s3mgr.configure(tablename,
                    super_entity=db.org_site,
                    list_fields=[
                        "id",
                        "gov_uuid",
                        "name",
                        "organisation_id",
                        "location_id",
                        "phone_exchange",
                        "ems_status",
                        "facility_status",
                        "clinical_status",
                        "security_status",
                        "total_beds",
                        "available_beds"
                    ])
    # -------------------------------------------------------------------------
    def hms_hospital_rheader(r, tabs=[]):

        """ Page header for component resources """

        rheader = None
        if r.representation == "html":
            tablename, record = s3_rheader_resource(r)
            if tablename == "hms_hospital" and record:
                hospital = record
                if not tabs:
                    tabs = [(T("Status Report"), ""),
                            (T("Services"), "services"),
                            (T("Contacts"), "contact"),
                            (T("Bed Capacity"), "bed_capacity"),
                            (T("Cholera Treatment Capability"),
                             "ctc_capability"), # @ToDo: make this a deployment_setting?
                            (T("Activity Report"), "activity"),
                            (T("Images"), "image"),
                            (T("Staff"), "human_resource")]

                    try:
                        tabs = tabs + response.s3.req_tabs(r)
                    except:
                        pass
                    try:
                        tabs = tabs + response.s3.inv_tabs(r)
                    except:
                        pass

                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = db.hms_hospital

                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                        hospital.name,
                        TH("%s: " % T("EMS Status")),
                        table.ems_status.represent(hospital.ems_status)),

                    TR(TH("%s: " % T("Location")),
                        db.gis_location[hospital.location_id] and \
                            db.gis_location[hospital.location_id].name or "unknown",
                        TH("%s: " % T("Facility Status")),
                        table.facility_status.represent(hospital.facility_status)),

                    TR(TH("%s: " % T("Total Beds")),
                        hospital.total_beds,
                        TH("%s: " % T("Clinical Status")),
                        table.clinical_status.represent(hospital.clinical_status)),

                    TR(TH("%s: " % T("Available Beds")),
                        hospital.available_beds,
                        TH("%s: " % T("Security Status")),
                        table.security_status.represent(hospital.security_status))

                        ), rheader_tabs)

            if rheader and r.component and r.component.name == "req":
                # Inject the helptext script
                s3mgr.load("req_req")
                rheader.append(response.s3.req_helptext_script)

        return rheader
    # -------------------------------------------------------------------------
    # Contacts
    #
    resourcename = "contact"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            person_id(label = T("Contact"),
                                      requires = IS_ONE_OF(db, "pr_person.id",
                                                           person_represent,
                                                           orderby="pr_person.first_name",
                                                           sort=True)),
                            Field("title", label = T("Job Title")),
                            Field("phone", label = T("Phone"),
                                  requires = IS_NULL_OR(s3_phone_requires)),
                            Field("mobile", label = T("Mobile"),
                                  requires = IS_NULL_OR(s3_phone_requires)),
                            Field("email", label = T("Email"),
                                  requires = IS_NULL_OR(IS_EMAIL())),
                            Field("fax", label = T("Fax"),
                                  requires = IS_NULL_OR(s3_phone_requires)),
                            Field("skype", label = T("Skype ID")),
                            Field("website", label=T("Website")),

                            *(s3_timestamp() + s3_deletion_status()))

    s3mgr.model.add_component(table, hms_hospital="hospital_id")

    s3mgr.configure(tablename,
                    mark_required = ["person_id"],
                    list_fields=[
                        "id",
                        "person_id",
                        "title",
                        "phone",
                        "mobile",
                        "email",
                        "fax",
                        "skype"
                    ],
                    main="person_id",
                    extra="title")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contacts"),
        title_update = T("Edit Contact"),
        title_search = T("Search Contacts"),
        subtitle_create = T("Add New Contact"),
        subtitle_list = T("Contacts"),
        label_list_button = T("List Contacts"),
        label_create_button = T("Add Contact"),
        msg_record_created = T("Contact information added"),
        msg_record_modified = T("Contact information updated"),
        msg_record_deleted = T("Contact information deleted"),
        msg_list_empty = T("No contacts currently registered"))

    # -------------------------------------------------------------------------
    # Activity
    #
    resourcename = "activity"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("date", "datetime", unique=True,  # Date&Time the entry applies to
                                  requires = IS_UTC_DATETIME(allow_future=False),
                                  represent = lambda val: s3_datetime_represent(val, utc=True),
                                  widget = S3DateTimeWidget(future=0),
                                  label = T("Date & Time")),
                            Field("patients", "integer",            # Current Number of Patients
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  default = 0,
                                  label = T("Number of Patients")),
                            Field("admissions24", "integer",        # Admissions in the past 24 hours
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  default = 0,
                                  label = T("Admissions/24hrs")),
                            Field("discharges24", "integer",        # Discharges in the past 24 hours
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  default = 0,
                                  label = T("Discharges/24hrs")),
                            Field("deaths24", "integer",            # Deaths in the past 24 hours
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  default = 0,
                                  label = T("Deaths/24hrs")),
                            Field("comment", length=128),
                            *s3_meta_fields())

    def hms_activity_onaccept(form):

        table = db.hms_activity
        query = ((table.id == form.vars.id) & (db.hms_hospital.id == table.hospital_id))
        hospital = db(query).select(db.hms_hospital.id,
                                    db.hms_hospital.modified_on,
                                    limitby=(0, 1)).first()
        timestmp = form.vars.date
        if hospital and hospital.modified_on < timestmp:
            hospital.update_record(modified_on=timestmp)

    s3mgr.model.add_component(table, hms_hospital="hospital_id")

    s3mgr.configure(tablename,
                    onaccept = hms_activity_onaccept,
                    list_fields=[
                        "id",
                        "date",
                        "patients",
                        "admissions24",
                        "discharges24",
                        "deaths24",
                        "comment"
                    ],
                    main="hospital_id",
                    extra="id")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Activity Report"),
        title_display = T("Activity Report"),
        title_list = T("Activity Reports"),
        title_update = T("Update Activity Report"),
        title_search = T("Search Activity Report"),
        subtitle_create = T("Add Activity Report"),
        subtitle_list = T("Activity Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Report"),
        label_delete_button = T("Delete Report"),
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No reports currently available"))

    # -------------------------------------------------------------------------
    # Bed Capacity
    #
    hms_bed_type_opts = {
        1: T("Adult ICU"),
        2: T("Pediatric ICU"),
        3: T("Neonatal ICU"),
        4: T("Emergency Department"),
        5: T("Nursery Beds"),
        6: T("General Medical/Surgical"),
        7: T("Rehabilitation/Long Term Care"),
        8: T("Burn ICU"),
        9: T("Pediatrics"),
        10: T("Adult Psychiatric"),
        11: T("Pediatric Psychiatric"),
        12: T("Negative Flow Isolation"),
        13: T("Other Isolation"),
        14: T("Operating Rooms"),
        15: T("Cholera Treatment"),
        99: T("Other")
    }

    resourcename = "bed_capacity"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("unit_id", length=128, unique=True,
                                  readable=False,
                                  writable=False),
                            Field("bed_type", "integer",
                                  requires = IS_IN_SET(hms_bed_type_opts,
                                                       zero=None),
                                  default = 6,
                                  label = T("Bed Type"),
                                  represent = lambda opt: \
                                    hms_bed_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("date", "datetime",
                                  requires = IS_UTC_DATETIME(allow_future=False),
                                  represent = lambda val: s3_datetime_represent(val, utc=True),
                                  widget = S3DateTimeWidget(future=0),
                                  label = T("Date of Report")),
                            Field("beds_baseline", "integer",
                                  default = 0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  label = T("Baseline Number of Beds")),
                            Field("beds_available", "integer",
                                  default = 0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  label = T("Available Beds")),
                            Field("beds_add24", "integer",
                                  default = 0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                  label = T("Additional Beds / 24hrs")),
                            comments(),
                            *s3_meta_fields())

    def hms_bed_capacity_onvalidation(form):

        """ Bed Capacity Validation """

        table = db.hms_bed_capacity
        hospital_id = table.hospital_id.update
        bed_type = form.vars.bed_type
        row = db((table.hospital_id == hospital_id) &
                 (table.bed_type == bed_type)).select(table.id,
                                                      limitby=(0, 1)).first()
        if row and str(row.id) != request.post_vars.id:
            form.errors["bed_type"] = T("Bed type already registered")
        elif "unit_id" not in form.vars:
            hospitals = db.hms_hospital
            hospital = db(hospitals.id == hospital_id).select(hospitals.uuid,
                                                              limitby=(0, 1)).first()
            if hospital:
                form.vars.unit_id = "%s-%s" % (hospital.uuid, bed_type)

    def hms_bed_capacity_onaccept(form):

        """ Updates the number of total/available beds of a hospital """

        if isinstance(form, Row):
            formvars = form
        else:
            formvars = form.vars

        table = db.hms_bed_capacity
        query = ((table.id == formvars.id) &
                 (db.hms_hospital.id == table.hospital_id))
        hospital = db(query).select(db.hms_hospital.id, limitby=(0, 1))

        if hospital:
            hospital = hospital.first()

            a_beds = table.beds_available.sum()
            t_beds = table.beds_baseline.sum()
            query = (table.hospital_id == hospital.id) & (table.deleted == False)
            count = db(query).select(a_beds, t_beds)
            if count:
               a_beds = count[0]._extra[a_beds]
               t_beds = count[0]._extra[t_beds]

            db(db.hms_hospital.id == hospital.id).update(
                total_beds=t_beds,
                available_beds=a_beds)

    s3mgr.model.add_component(table, hms_hospital="hospital_id")

    s3mgr.configure(tablename,
                    onvalidation = hms_bed_capacity_onvalidation,
                    onaccept = hms_bed_capacity_onaccept,
                    ondelete = hms_bed_capacity_onaccept,
                    list_fields=[
                        "id",
                        "unit_name",
                        "bed_type",
                        "date",
                        "beds_baseline",
                        "beds_available",
                        "beds_add24"
                    ],
                    main="hospital_id",
                    extra="id")

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Bed Type"),
        title_display = T("Bed Capacity"),
        title_list = T("Bed Capacity"),
        title_update = T("Update Unit"),
        title_search = T("Search Units"),
        subtitle_create = T("Add Unit"),
        subtitle_list = T("Bed Capacity per Unit"),
        label_list_button = T("List Units"),
        label_create_button = T("Add Unit"),
        label_delete_button = T("Delete Unit"),
        msg_record_created = T("Unit added"),
        msg_record_modified = T("Unit updated"),
        msg_record_deleted = T("Unit deleted"),
        msg_list_empty = T("No units currently registered"))

    # -------------------------------------------------------------------------
    # Services
    #
    resourcename = "services"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("burn", "boolean", default=False,
                                  label = T("Burn")),
                            Field("card", "boolean", default=False,
                                  label = T("Cardiology")),
                            Field("dial", "boolean", default=False,
                                  label = T("Dialysis")),
                            Field("emsd", "boolean", default=False,
                                  label = T("Emergency Department")),
                            Field("infd", "boolean", default=False,
                                  label = T("Infectious Diseases")),
                            Field("neon", "boolean", default=False,
                                  label = T("Neonatology")),
                            Field("neur", "boolean", default=False,
                                  label = T("Neurology")),
                            Field("pedi", "boolean", default=False,
                                  label = T("Pediatrics")),
                            Field("surg", "boolean", default=False,
                                  label = T("Surgery")),
                            Field("labs", "boolean", default=False,
                                  label = T("Clinical Laboratory")),
                            Field("tran", "boolean", default=False,
                                  label = T("Ambulance Service")),
                            Field("tair", "boolean", default=False,
                                  label = T("Air Transport Service")),
                            Field("trac", "boolean", default=False,
                                  label = T("Trauma Center")),
                            Field("psya", "boolean", default=False,
                                  label = T("Psychiatrics/Adult")),
                            Field("psyp", "boolean", default=False,
                                  label = T("Psychiatrics/Pediatric")),
                            Field("obgy", "boolean", default=False,
                                  label = T("Obstetrics/Gynecology")),
                            *s3_meta_fields())

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Service Profile"),
        title_display = T("Services Available"),
        title_list = T("Services Available"),
        title_update = T("Update Service Profile"),
        title_search = T("Search Service Profiles"),
        subtitle_create = T("Add Service Profile"),
        subtitle_list = T("Services Available"),
        label_list_button = T("List Service Profiles"),
        label_create_button = T("Add Service Profile"),
        label_delete_button = T("Delete Service Profile"),
        msg_record_created = T("Service profile added"),
        msg_record_modified = T("Service profile updated"),
        msg_record_deleted = T("Service profile deleted"),
        msg_list_empty = T("No service profile available"))

    s3mgr.model.add_component(table,
                              hms_hospital=dict(joinby="hospital_id",
                                                multiple=False))

    s3mgr.configure(tablename,
                    list_fields = ["id"],
                    main="hospital_id",
                    extra="id")

    # -------------------------------------------------------------------------
    # Cholera Treatment Capability
    #
    hms_problem_types = {
        1: T("Security problems"),
        2: T("Hygiene problems"),
        3: T("Sanitation problems"),
        4: T("Improper handling of dead bodies"),
        5: T("Improper decontamination"),
        6: T("Understaffed"),
        7: T("Lack of material"),
        8: T("Communication problems"),
        9: T("Information gaps")
    }
    resourcename = "ctc_capability"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("ctc", "boolean", default=False,
                                  represent = lambda opt: \
                                    opt and T("yes") or T("no"),
                                  label = T("Cholera-Treatment-Center")),
                            Field("number_of_patients", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                  label = T("Current number of patients")),
                            Field("cases_24", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                  label = T("New cases in the past 24h")),
                            Field("deaths_24", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                  label = T("Deaths in the past 24h")),
                            #Field("staff_total", "integer", default=0),
                            Field("icaths_available", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Infusion catheters available")),
                            Field("icaths_needed_24", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Infusion catheters needed per 24h")),
                            Field("infusions_available", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Infusions available")),
                            Field("infusions_needed_24", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Infusions needed per 24h")),
                            #Field("infset_available", "integer", default=0),
                            #Field("infset_needed_24", "integer", default=0),
                            Field("antibiotics_available", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Antibiotics available")),
                            Field("antibiotics_needed_24", "integer", default=0,
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                  label = T("Antibiotics needed per 24h")),
                            Field("problem_types", "list:integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(hms_problem_types,
                                                                   zero=None,
                                                                   multiple=True)),
                                  represent = lambda optlist: \
                                    optlist and ", ".join(map(str,optlist)) or T("N/A"),
                                  label = T("Current problems, categories")),
                            Field("problem_details", "text",
                                  label = T("Current problems, details")),
                            comments(),
                            *s3_meta_fields())

    table.modified_on.label = T("Last updated on")
    table.modified_on.readable = True
    table.modified_by.label = T("Last updated by")
    table.modified_by.readable = True

    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Cholera Treatment Capability Information"),
        title_display = T("Cholera Treatment Capability"),
        title_list = T("Cholera Treatment Capability"),
        title_update = T("Update Cholera Treatment Capability Information"),
        title_search = T("Search Status"),
        subtitle_create = T("Add Status"),
        subtitle_list = T("Current Status"),
        label_list_button = T("List Status"),
        label_create_button = T("Add Status"),
        label_delete_button = T("Delete Status"),
        msg_record_created = T("Status added"),
        msg_record_modified = T("Status updated"),
        msg_record_deleted = T("Status deleted"),
        msg_list_empty = T("No status information available"))

    s3mgr.model.add_component(table,
                              hms_hospital=dict(joinby="hospital_id",
                                                multiple=False))

    s3mgr.configure(tablename,
                    list_fields = ["id"],
                    subheadings = {
                        "Activities": "ctc",
                        "Medical Supplies Availability": "icaths_available",
                        "Current Problems": "problem_types",
                        "Comments": "comments"
                    })

    # -------------------------------------------------------------------------
    # Images
    #
    hms_image_type_opts = {
        1:T("Photograph"),
        2:T("Map"),
        3:T("Document Scan"),
        99:T("other")
    }

    resourcename = "image"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            #Field("title"),
                            Field("type", "integer",
                                  requires = IS_IN_SET(hms_image_type_opts,
                                                       zero=None),
                                  default = 1,
                                  label = T("Image Type"),
                                  represent = lambda opt: \
                                    hms_image_type_opts.get(opt,
                                                            T("not specified"))),
                            Field("image", "upload", autodelete=True,
                                  label = T("Image Upload")),
                            Field("url", label = T("URL"),
                                  represent = lambda url: \
                                    url and DIV(A(IMG(_src=url,
                                                      _height=60),
                                                      _href=url)) or T("None")),
                            Field("description", label = T("Description")),
                            Field("tags", label = T("Tags")),
                            *s3_meta_fields())

    table.image.represent = lambda image: image and \
            DIV(A(IMG(_src=URL(c="default", f="download", args=image),
                      _height=60, _alt=T("View Image")),
                  _href=URL(c="default", f="download", args=image))) or \
            T("No Image")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Image"),
        title_display = T("Image Details"),
        title_list = T("List Images"),
        title_update = T("Edit Image Details"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = T("List Images"),
        label_create_button = T("Add Image"),
        label_delete_button = T("Delete Image"),
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered")
    )

    s3mgr.model.add_component(table, hms_hospital="hospital_id")

    s3mgr.configure(tablename,
                    list_fields=[
                        "id",
                        "type",
                        "image",
                        "url",
                        "description",
                        "tags"
                    ])

    # -------------------------------------------------------------------------
    # Resources (multiple) - TODO: to be completed!
    #
    resourcename = "resources"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            hospital_id(),
                            Field("type"),
                            Field("description"),
                            Field("quantity"),
                            Field("comment"),   # ToDo: Change to comments()
                            *s3_meta_fields())


    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Report Resource"),
        title_display = T("Resource Details"),
        title_list = T("Resources"),
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = T("Resources"),
        label_list_button = T("List Resources"),
        label_create_button = T("Add Resource"),
        label_delete_button = T("Delete Resource"),
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently reported"))

    # Add as component
    s3mgr.model.add_component(table, hms_hospital="hospital_id")

    s3mgr.configure(tablename,
                    list_fields=["id"],
                    main="hospital_id",
                    extra="id")

    # -------------------------------------------------------------------------
    # Hospital Search Method
    #
    hms_hospital_search = s3base.S3Search(
        #name="hospital_search_simple",
        #label=T("Name and/or ID"),
        #comment=T("To search for a hospital, enter any of the names or IDs of the hospital, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
        #field=["gov_uuid", "name", "aka1", "aka2"],
        advanced=(s3base.S3SearchSimpleWidget(
                    name="hospital_search_advanced",
                    label=T("Name, Org and/or ID"),
                    comment=T("To search for a hospital, enter any of the names or IDs of the hospital, or the organisation name or acronym, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
                    field=["gov_uuid", "name", "aka1", "aka2",
                        "organisation_id$name", "organisation_id$acronym"]
                  ),
                  # for testing:
                  s3base.S3SearchOptionsWidget(
                    name="hospital_facility_type",
                    label=T("Facility Type"),
                    field=["facility_type"]
                  ),
                  # for testing:
                  s3base.S3SearchMinMaxWidget(
                    name="hospital_search_bedcount",
                    method="range",
                    label=T("Total Beds"),
                    comment=T("Select a range for the number of total beds"),
                    field=["total_beds"]
                  ),
        ))

    # Set as standard search method for hospitals
    s3mgr.configure("hms_hospital",
                    search_method=hms_hospital_search)

else:
    def hospital_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("hospital_id", "integer", readable=False, writable=False)

# END =========================================================================

