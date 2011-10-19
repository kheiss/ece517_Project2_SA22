# -*- coding: utf-8 -*-

"""
    Person Registry

    @author: nursix
    @author: Pratyush Nigam <pratyush.nigam@gmail.com>
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "pr"

# =============================================================================
# Person
#
pr_gender_opts = {
    1:"",
    2:T("female"),
    3:T("male")
}
pr_gender = S3ReusableField("gender", "integer",
                            requires = IS_IN_SET(pr_gender_opts, zero=None),
                            default = 1,
                            label = T("Gender"),
                            represent = lambda opt: \
                                        pr_gender_opts.get(opt, UNKNOWN_OPT))

pr_age_group_opts = {
    1:T("unknown"),
    2:T("Infant (0-1)"),
    3:T("Child (2-11)"),
    4:T("Adolescent (12-20)"),
    5:T("Adult (21-50)"),
    6:T("Senior (50+)")
}
pr_age_group = S3ReusableField("age_group", "integer",
                               requires = IS_IN_SET(pr_age_group_opts,
                                                    zero=None),
                               default = 1,
                               label = T("Age Group"),
                               represent = lambda opt: \
                                           pr_age_group_opts.get(opt,
                                                                 UNKNOWN_OPT))

pr_marital_status_opts = {
    1:T("unknown"),
    2:T("single"),
    3:T("married"),
    4:T("separated"),
    5:T("divorced"),
    6:T("widowed"),
    9:T("other")
}

pr_religion_opts = deployment_settings.get_L10n_religions()

pr_impact_tags = {
    1: T("injured"),
    4: T("diseased"),
    2: T("displaced"),
    5: T("separated from family"),
    3: T("suffered financial losses")
}

if deployment_settings.get_L10n_mandatory_lastname():
    last_name_validate = IS_NOT_EMPTY(error_message = T("Please enter a last name"))
else:
    last_name_validate = None

tablename = "pr_person"
table = db.define_table(tablename,
                        super_link(db.pr_pentity),    # pe_id
                        super_link(db.sit_trackable), # track_id
                        location_id(readable=False,
                                    writable=False),  # base location
                        pe_label(comment = DIV(DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("ID Tag Number"),
                                                                     T("Number or Label on the identification tag this person is wearing (if any)."))))),
                        Field("missing", "boolean",
                              readable=False,
                              writable=False,
                              default=False,
                              represent = lambda missing: \
                                (missing and ["missing"] or [""])[0]),
                        Field("volunteer", "boolean",
                              readable=False,
                              writable=False,
                              default=False),
                        Field("first_name", notnull=True,
                              length=64, # Mayon Compatibility
                              # NB Not possible to have an IS_NAME() validator here
                              # http://eden.sahanafoundation.org/ticket/834
                              requires = IS_NOT_EMPTY(error_message = T("Please enter a first name")),
                              comment =  DIV(_class="tooltip",
                                             _title="%s|%s" % (T("First name"),
                                                               T("The first or only name of the person (mandatory)."))),
                              label = T("First Name")),
                        Field("middle_name",
                              length=64, # Mayon Compatibility
                              label = T("Middle Name")),
                        Field("last_name",
                              length=64, # Mayon Compatibility
                              label = T("Last Name"),
                              requires = last_name_validate),
                        Field("preferred_name",
                              comment = DIV(DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Preferred Name"),
                                                                  T("The name to be used when calling for or directly addressing the person (optional).")))),
                              length=64), # Mayon Compatibility
                        Field("local_name", label = T("Local Name"),
                              comment = DIV(DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Local Name"),
                                                                  T("Name of the person in local language and script (optional)."))))),
                        pr_gender(label = T("Gender")),
                        Field("date_of_birth", "date",
                              label = T("Date of Birth"),
                              requires = [IS_EMPTY_OR(IS_DATE_IN_RANGE(
                                            format = s3_date_format,
                                            maximum=request.utcnow.date(),
                                            error_message="%s %%(max)s!" %
                                                T("Enter a valid date before")))],
                              widget = S3DateWidget(past=1320,  # Months, so 110 years
                                                    future=0)),
                        pr_age_group(label = T("Age group")),
                        Field("nationality",
                              requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                  lambda: gis.get_countries(key_type="code"),
                                  zero = SELECT_LOCATION)),
                              label = T("Nationality"),
                              comment = DIV(DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Nationality"),
                                                                  T("Nationality of the person.")))),
                              represent = lambda code: \
                                  gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                        Field("occupation",
                              length=128),          # Mayon Compatibility
                        Field("picture", "upload",
                              autodelete=True,
                              requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                     error_message=T("Upload an image file (bmp, gif, jpeg or png), max. 300x300 pixels!"))),
                              represent = lambda image: image and \
                                            DIV(A(IMG(_src=URL(c="default", f="download",
                                                               args=image),
                                                      _height=60,
                                                      _alt=T("View Picture")),
                                                      _href=URL(c="default", f="download",
                                                                args=image))) or
                                            T("No Picture"),
                              comment =  DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Picture"),
                                                               T("Upload an image file here.")))),

                        # -------------------------------------------------------------------------
                        # superfluous => contained in home address
                        #Field("country",
                              #requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                            #gis.get_countries(key_type="code"))),
                              #label = T("Country of Residence"),
                              #represent = lambda code: \
                                  #gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                        # must be restricted for privacy reasons:
                        #Field("religion",
                              #requires = IS_EMPTY_OR(IS_IN_SET(pr_religion_opts)),
                              #label = T("Religion"),
                              #represent = lambda opt: \
                                          #pr_religion_opts.get(opt, UNKNOWN_OPT)),
                        # must be restricted for privacy reasons:
                        #Field("marital_status", "integer",
                              #requires = IS_NULL_OR(IS_IN_SET(
                                                    #pr_marital_status_opts)),
                              #default = 1,
                              #label = T("Marital Status"),
                              #represent = lambda opt: \
                                          #pr_marital_status_opts.get(opt,
                                                                     #UNKNOWN_OPT)),
                        # currently unused (except in TW version):
                        #Field("tags", "list:integer"),
                        comments(),
                        *s3_meta_fields())

#table.country.comment = DIV(DIV(_class="tooltip",
    #_title="%s|%s" % (T("Country of Residence"),
                      #T("The country the person usually lives in."))))
#table.tags.label = T("Personal impact of disaster")
#table.tags.comment = DIV(DIV(_class="tooltip",
    #_title="%s|%s" % (T("Personal impact of disaster"),
                      #T("How is this person affected by the disaster? (Select all that apply)"))))
#table.tags.requires = IS_EMPTY_OR(IS_IN_SET(pr_impact_tags, zero=None, multiple=True))
#table.tags.represent = lambda opt: opt and \
                       #", ".join([str(pr_impact_tags.get(o, UNKNOWN_OPT)) for o in opt]) or ""

def person_represent(id):

    def _represent(id):
        if isinstance(id, Row):
            person = id
            id = person.id
        else:
            table = db.pr_person
            person = db(table.id == id).select(table.first_name,
                                               table.middle_name,
                                               table.last_name,
                                               limitby=(0, 1)).first()
        if person:
            return s3_fullname(person)
        else:
            return None

    name = cache.ram("pr_person_%s" % id, lambda: _represent(id),
                     time_expire=10)
    return name

def pr_person_onvalidation(form):
    """ Ovalidation callback """

    try:
        age = int(form.vars.get("age_group", None))
    except (ValueError, TypeError):
        age = None
    dob = form.vars.get("date_of_birth", None)

    if age and age != 1 and dob:
        now = request.utcnow
        dy = int((now.date() - dob).days / 365.25)
        if dy < 0:
            ag = 1
        elif dy < 2:
            ag = 2
        elif dy < 12:
            ag = 3
        elif dy < 21:
            ag = 4
        elif dy < 51:
            ag = 5
        else:
            ag = 6

        if age != ag:
            form.errors.age_group = T("Age group does not match actual age.")
            return False

    return True

def pr_person_duplicate(job):
    """
        This callback will be called when importing person records it will look
        to see if the record being imported is a duplicate.

        @param job: An S3ImportJob object which includes all the details
                    of the record being imported

        If the record is a duplicate then it will set the job method to update

        Rules for finding a duplicate:
         - Look for a record with the same name (first name and last name), ignoring case
         - and the same email address (if provided)
    """

    # Ignore this processing if the id is set
    if job.id:
        return
    if job.tablename == "pr_person":
        ptable = db.pr_person
        ctable = db.pr_contact

       # Get the details from the job record
        fname = "first_name" in job.data and job.data.first_name
        lname = "last_name" in job.data and job.data.last_name
        if not fname or not lname:
            return
        query = (ptable.first_name.lower().like('%%%s%%' % fname.lower())) & \
                (ptable.last_name.lower().like('%%%s%%' % lname.lower()))
        email = False
        for cjob in job.components:
            if cjob.tablename == "pr_contact":
                if "contact_method" in cjob.data and \
                   cjob.data.contact_method == "EMAIL":
                    email = cjob.data.value
        if email != False:
            query = query & \
                    (ptable.pe_id == ctable.pe_id) & \
                    (ctable.value.lower() == email.lower())
        # Look for details on the database
        _duplicate = db(query).select(ptable.id,
                                      limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE
            for cjob in job.components:
                cjob.method = cjob.METHOD.UPDATE

pr_person_search = s3base.S3PersonSearch(
            name="person_search_simple",
            label=T("Name and/or ID"),
            comment=T("To search for a person, enter any of the first, middle or last names and/or an ID number of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
            field=["pe_label",
                   "first_name",
                   "middle_name",
                   "last_name",
                   "local_name",
                   "identity.value"
                ])

s3mgr.configure(tablename,
                super_entity=(db.pr_pentity, db.sit_trackable),
                list_fields = ["id",
                               "first_name",
                               "middle_name",
                               "last_name",
                               "picture",
                               "gender",
                               "age_group"
                            ],
                onvalidation=pr_person_onvalidation,
                search_method=pr_person_search,
                resolve=pr_person_duplicate,
                main="first_name",
                extra="last_name")

ADD_PERSON = T("Add Person")
LIST_PERSONS = T("List Persons")
s3.crud_strings[tablename] = Storage(
    title_create = T("Add a Person"),
    title_display = T("Person Details"),
    title_list = LIST_PERSONS,
    title_update = T("Edit Person Details"),
    title_search = T("Search Persons"),
    subtitle_create = ADD_PERSON,
    subtitle_list = T("Persons"),
    label_list_button = LIST_PERSONS,
    label_create_button = ADD_PERSON,
    label_delete_button = T("Delete Person"),
    msg_record_created = T("Person added"),
    msg_record_modified = T("Person details updated"),
    msg_record_deleted = T("Person deleted"),
    msg_list_empty = T("No Persons currently registered"))

s3_person_comment = lambda title, comment: \
    DIV(A(ADD_PERSON,
        _class="colorbox",
        _href=URL(c="pr", f="person", args="create",
                  vars=dict(format="popup")),
        _target="top",
        _title=ADD_PERSON),
    DIV(DIV(_class="tooltip",
        _title="%s|%s" % (title, comment))))

pr_person_id_comment = s3_person_comment(
    T("Person"),
    T("Type the first few characters of one of the Person's names."))

person_id = S3ReusableField("person_id", db.pr_person,
                            sortby = ["first_name", "middle_name", "last_name"],
                            requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id",
                                        person_represent,
                                        orderby="pr_person.first_name",
                                        sort=True,
                                        error_message=T("Person must be specified!"))),
                            represent = lambda id: (id and \
                                        [person_represent(id)] or [NONE])[0],
                            label = T("Person"),
                            comment = pr_person_id_comment,
                            ondelete = "RESTRICT",
                            widget = S3PersonAutocompleteWidget())


# =============================================================================
# Group
#
pr_group_types = {
    1:T("Family"),
    2:T("Tourist Group"),
    3:T("Relief Team"), # Don't change this number without changing vol/group()
    4:T("other")
}

tablename = "pr_group"
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("group_type", "integer",
                              requires = IS_IN_SET(pr_group_types, zero=None),
                              default = 4,
                              label = T("Group Type"),
                              represent = lambda opt: \
                                          pr_group_types.get(opt, UNKNOWN_OPT)),
                        Field("system", "boolean",
                              default=False,
                              readable=False,
                              writable=False),
                        Field("name",
                              label=T("Group Name"),
                              requires = IS_NOT_EMPTY()),
                        Field("description",
                              label=T("Group Description")),
                        comments(),
                        *s3_meta_fields())

table.description.comment = DIV(DIV(_class="tooltip",
    _title="%s|%s" % (T("Group description"),
                      T("A brief description of the group (optional)"))))

s3mgr.configure(tablename,
                super_entity=db.pr_pentity,
                main="name",
                extra="description")

ADD_GROUP = T("Add Group")
LIST_GROUPS = T("List Groups")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_GROUP,
    title_display = T("Group Details"),
    title_list = LIST_GROUPS,
    title_update = T("Edit Group"),
    title_search = T("Search Groups"),
    subtitle_create = T("Add New Group"),
    subtitle_list = T("Groups"),
    label_list_button = LIST_GROUPS,
    label_create_button = ADD_GROUP,
    label_delete_button = T("Delete Group"),
    msg_record_created = T("Group added"),
    msg_record_modified = T("Group updated"),
    msg_record_deleted = T("Group deleted"),
    msg_list_empty = T("No Groups currently registered"))

pr_group_represent = lambda id: (id and [db.pr_group[id].name] or [NONE])[0]

group_id = S3ReusableField("group_id", db.pr_group,
                           sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id",
                                                           "%(id)s: %(name)s",
                                                           filterby="system",
                                                           filter_opts=(False,))),
                           represent = pr_group_represent,
                           comment = \
                                DIV(A(s3.crud_strings.pr_group.label_create_button,
                                    _class="colorbox",
                                    _href=URL(c="pr", f="group", args="create", vars=dict(format="popup")),
                                    _target="top",
                                    _title=s3.crud_strings.pr_group.label_create_button),
                                DIV(DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Create Group Entry"),
                                                          T("Create a group entry in the registry."))))),
                           ondelete = "RESTRICT")


# =============================================================================
# Group membership
#
resourcename = "group_membership"
tablename = "pr_group_membership"
table = db.define_table(tablename,
                        group_id(label = T("Group")),
                        person_id(label = T("Person")),
                        Field("group_head", "boolean", default=False),
                        Field("description"),
                        comments(),
                        *s3_meta_fields())

table.group_head.represent = lambda group_head: \
                             (group_head and [T("yes")] or [""])[0]

s3mgr.configure(tablename,
                list_fields=["id",
                             "group_id",
                             "person_id",
                             "group_head",
                             "description"
                            ])

s3mgr.model.add_component(table, pr_group="group_id",
                                 pr_person="person_id")

if request.function in ("person", "group_membership"):
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Membership"),
        title_display = T("Membership Details"),
        title_list = T("Memberships"),
        title_update = T("Edit Membership"),
        title_search = T("Search Membership"),
        subtitle_create = T("Add New Membership"),
        subtitle_list = T("Current Memberships"),
        label_list_button = T("List All Memberships"),
        label_create_button = T("Add Membership"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Membership added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Memberships currently registered"))

elif request.function == "group":
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Group Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Group Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Group Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

# =============================================================================
# Contact
#
# @ToDo: Provide widgets which can be dropped into the main person form to have
#        the relevant ones for that deployment/context collected on that same
#        form
#
pr_contact_method_opts = msg.CONTACT_OPTS

tablename = "pr_contact"
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("contact_method",
                              length=32,
                              requires = IS_IN_SET(pr_contact_method_opts,
                                                   zero=None),
                              default = "SMS",
                              label = T("Contact Method"),
                              represent = lambda opt: \
                                pr_contact_method_opts.get(opt,
                                                           UNKNOWN_OPT)),
                        Field("value", notnull=True, label= T("Value"),
                              requires = IS_NOT_EMPTY()),
                        Field("priority", "integer", label= T("Priority"),
                              comment = DIV( _class="tooltip",
                                            _title="%s|%s" % (T("Priority"),
                                                              T("What order to be contacted in."))),
                              requires = IS_IN_SET(range(1, 10), zero=None)),
                        #Field("contact_person", label= T("Contact Person")),
                        comments(),
                        *s3_meta_fields())

tablename = "pr_contact"
table = db[tablename]
table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                    s3_pentity_represent,
                                    orderby="instance_type",
                                    filterby="instance_type",
                                    filter_opts=("pr_person", "pr_group"))

def contact_onvalidation(form):
    """ Contact form validation """

    if form.vars.contact_method == "EMAIL":
        email, error = IS_EMAIL()(form.vars.value)
        if error:
            form.errors.value = T("Enter a valid email")

    return False

s3mgr.configure(tablename,
                onvalidation=contact_onvalidation,
                list_fields=["id",
                                #"pe_id",
                                "contact_method",
                                "value",
                                "priority",
                                #"contact_person",
                                #"name",
                            ])

s3mgr.model.add_component(table, pr_pentity=super_key(db.pr_pentity))

s3.crud_strings[tablename] = Storage(
    title_create = T("Add Contact Information"),
    title_display = T("Contact Details"),
    title_list = T("Contact Information"),
    title_update = T("Edit Contact Information"),
    title_search = T("Search Contact Information"),
    subtitle_create = T("Add Contact Information"),
    subtitle_list = T("Contact Information"),
    label_list_button = T("List Contact Information"),
    label_create_button = T("Add Contact Information"),
    label_delete_button = T("Delete Contact Information"),
    msg_record_created = T("Contact Information Added"),
    msg_record_modified = T("Contact Information Updated"),
    msg_record_deleted = T("Contact Information Deleted"),
    msg_list_empty = T("No contact information available"))

# =============================================================================
def pr_component_tables():
    """ Load Person Component Tables when required """

    # =========================================================================
    # Address (address)
    #
    pr_address_type_opts = {
        1:T("Home Address"),
        2:T("Office Address"),
        3:T("Holiday Address"),
        9:T("other")
    }

    resourcename = "address"
    tablename = "pr_address"
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id
                            Field("type",
                                  "integer",
                                  requires = IS_IN_SET(pr_address_type_opts, zero=None),
                                  widget = RadioWidget.widget,
                                  default = 1,
                                  label = T("Address Type"),
                                  represent = lambda opt: \
                                              pr_address_type_opts.get(opt, UNKNOWN_OPT)),
                            #Field("co_name", label=T("c/o Name")),
                            location_id(),
                            comments(),
                            *(address_fields() + s3_meta_fields()))

    table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id", s3_pentity_represent,
                                     orderby="instance_type",
                                     filterby="instance_type",
                                     filter_opts=("pr_person", "pr_group"))

    def address_onaccept(form):
        """
            Updates the Base Location to be the same as the Address

            NB This doesn't apply globally but is only activated for specific
               parts of the workflow
        """

        if "location_id" in form.vars and \
           "base_location" in request.vars and request.vars.base_location == "on":
            location_id = form.vars.location_id
            pe_id = request.post_vars.pe_id
            s3tracker(db.pr_pentity, pe_id).set_base_location(location_id)

    if not deployment_settings.get_gis_building_name():
        table.building_name.readable = False

    s3mgr.configure(tablename,
                    onvalidation=address_onvalidation,
                    list_fields = ["id",
                                   "type",
                                   #"building_name",
                                   "address",
                                   "postcode",
                                   #"L4",
                                   "L3",
                                   "L2",
                                   "L1",
                                   "L0"
                                ])

    s3mgr.model.add_component(table,
                              pr_pentity=super_key(db.pr_pentity))

    ADD_ADDRESS = T("Add Address")
    LIST_ADDRESS = T("List of addresses")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ADDRESS,
        title_display = T("Address Details"),
        title_list = LIST_ADDRESS,
        title_update = T("Edit Address"),
        title_search = T("Search Addresses"),
        subtitle_create = T("Add New Address"),
        subtitle_list = T("Addresses"),
        label_list_button = LIST_ADDRESS,
        label_create_button = ADD_ADDRESS,
        msg_record_created = T("Address added"),
        msg_record_modified = T("Address updated"),
        msg_record_deleted = T("Address deleted"),
        msg_list_empty = T("There is no address for this person yet. Add new address."))


    # =========================================================================
    # Image
    #
    pr_pimage_type_opts = {
        1:T("Photograph"),
        2:T("Sketch"),
        3:T("Fingerprint"),
        4:T("X-Ray"),
        5:T("Document Scan"),
        9:T("other")
    }

    resourcename = "pimage"
    tablename = "pr_pimage"
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id
                            Field("type", "integer",
                                  requires = IS_IN_SET(pr_pimage_type_opts, zero=None),
                                  default = 1,
                                  label = T("Image Type"),
                                  represent = lambda opt: pr_pimage_type_opts.get(opt,
                                                                                 UNKNOWN_OPT)),
                            Field("title", label=T("Title"),
                                  requires = IS_NOT_EMPTY(),
                                  comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Title"),
                                                                  T("Specify a descriptive title for the image.")))),
                            Field("image", "upload", autodelete=True,
                                  represent = lambda image: image and \
                                                DIV(A(IMG(_src=URL(c="default", f="download",
                                                                   args=image),
                                                          _height=60, _alt=T("View Image")),
                                                          _href=URL(c="default", f="download",
                                                                    args=image))) or T("No Image"),
                                  comment =  DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Image"),
                                                                   T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field.")))),
                            Field("url", label = T("URL"),
                                  represent = lambda url: url and DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None"),
                                  comment =  DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("URL"),
                                                                   T("The URL of the image file. If you don't upload an image file, then you must specify its location here.")))),
                            Field("description", label=T("Description"),
                                  comment =  DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Description"),
                                                                   T("Give a brief description of the image, e.g. what can be seen where on the picture (optional).")))),
                            comments(),
                            *s3_meta_fields())

    def pr_pimage_onvalidation(form):

        """ Image form validation """

        table = db.pr_pimage
        image = form.vars.image

        if not hasattr(image, "file"):
            id = request.post_vars.id
            if id:
                record = db(table.id == id).select(table.image,
                                                   limitby=(0, 1)).first()
                if record:
                    image = record.image

        url = form.vars.url
        if not hasattr(image, "file") and not image and not url:
            form.errors.image = \
            form.errors.url = T("Either file upload or image URL required.")

        return False

    s3mgr.configure(tablename,
                    onvalidation = pr_pimage_onvalidation,
                    mark_required = ["url", "image"],
                    list_fields=["id",
                                 "title",
                                 "type",
                                 "image",
                                 "url",
                                 "description"
                                ])

    s3mgr.model.add_component(table, pr_pentity=super_key(db.pr_pentity))

    LIST_IMAGES = T("List Images")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Image"),
        title_display = T("Image Details"),
        title_list = LIST_IMAGES,
        title_update = T("Edit Image Details"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = LIST_IMAGES,
        label_create_button = T("Add Image"),
        label_delete_button = T("Delete Image"),
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered"))


    # =============================================================================
    # Identity
    #
    # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
    # <xs:simpleType name="DocumentTypeList">
    #  <xs:enumeration value="Passport"/>
    #  <xs:enumeration value="DriverLicense"/>
    #  <xs:enumeration value="CreditCard"/>
    #  <xs:enumeration value="BankCard"/>
    #  <xs:enumeration value="KeyCard"/>
    #  <xs:enumeration value="AccessCard"/>
    #  <xs:enumeration value="IdentificationCard"/>
    #  <xs:enumeration value="Certificate"/>
    #  <xs:enumeration value="MileageProgram"/>
    #

    pr_id_type_opts = {
        1:T("Passport"),
        2:T("National ID Card"),
        3:T("Driving License"),
        #4:T("Credit Card"),
        99:T("other")
    }

    resourcename = "identity"
    tablename = "pr_identity"
    table = db.define_table(tablename,
                            person_id(label = T("Person")),
                            Field("type", "integer",
                                  requires = IS_IN_SET(pr_id_type_opts, zero=None),
                                  default = 1,
                                  label = T("ID type"),
                                  represent = lambda opt: \
                                              pr_id_type_opts.get(opt,
                                                                  UNKNOWN_OPT)),
                            Field("value"),
                            Field("description"),
                            Field("country_code", length=4),
                            Field("ia_name", label = T("Issuing Authority")),
                            #Field("ia_subdivision"), # Name of issuing authority subdivision
                            #Field("ia_code"), # Code of issuing authority (if any)
                            comments(),
                            *s3_meta_fields())

    table.value.requires = [IS_NOT_EMPTY(),
                            IS_NOT_ONE_OF(db, "%s.value" % tablename)]

    s3mgr.configure(tablename,
                    list_fields=["id",
                                 "type",
                                 "type",
                                 "value",
                                 "country_code",
                                 "ia_name"
                                ])

    s3mgr.model.add_component(table, pr_person="person_id")

    ADD_IDENTITY = T("Add Identity")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_IDENTITY,
        title_display = T("Identity Details"),
        title_list = T("Known Identities"),
        title_update = T("Edit Identity"),
        title_search = T("Search Identity"),
        subtitle_create = T("Add New Identity"),
        subtitle_list = T("Current Identities"),
        label_list_button = T("List Identities"),
        label_create_button = ADD_IDENTITY,
        msg_record_created = T("Identity added"),
        msg_record_modified = T("Identity updated"),
        msg_record_deleted = T("Identity deleted"),
        msg_list_empty = T("No Identities currently registered"))

# Provide a handle to this load function
s3mgr.model.loader(pr_component_tables,
                   "pr_address",
                   "pr_pimage",
                   "pr_identity")


# =============================================================================
# Saved Searches
#
def saved_search_tables():
    tablename = "pr_save_search" 
    table = db.define_table(tablename,
                            Field("user_id", "integer",
                                  readable = False,
                                  writable = False,
                                  default = auth.user_id), 
                            Field("search_vars","string",
                                  label = T("Search Criteria")),
                            Field("subscribed","boolean", default=False),
                            person_id(label = T("Person"),
                                      default = s3_logged_in_person()),    
                            *s3_timestamp())

    import cPickle
    def get_criteria(id):
        s = ""
        try:
            id = id.replace("&apos;", "'")
            search_vars = cPickle.loads(id)
            s = "<p>"
            pat = '_'
            for var in search_vars.iterkeys():
                if var == "criteria" :
                    c_dict = search_vars[var]
                    #s = s + crud_string("pr_save_search", "Search Criteria")
                    for j in c_dict.iterkeys():
                        if not re.match(pat,j):
                            st = str(j)
                            st = st.replace("_search_", " ")
                            st = st.replace("_advanced", "")
                            st = st.replace("_simple", "")
                            st = st.replace("text", "text matching")
                            """st = st.replace(search_vars["function"], "")
                            st = st.replace(search_vars["prefix"], "")"""
                            st = st.replace("_", " ")
                            s = "%s <b> %s </b>: %s <br />" %(s, st.capitalize(), str(c_dict[j]))
                elif var == "simple" or var == "advanced":
                    continue
                else:
                    if var == "function":
                        v1 = "Resource Name"
                    elif var == "prefix":
                        v1 = "Module"
                    s = "%s<b>%s</b>: %s<br />" %(s, v1, str(search_vars[var]))
            s = s + "</p>"        
            return XML(s)
        except:
            return XML(s)

    table.search_vars.represent = lambda id : get_criteria(id = id)

    s3mgr.configure(tablename,
                    insertable = False,
                    editable = False,
                    listadd = False,
                    deletable = True,
                    list_fields=["search_vars"])
                
    s3mgr.model.add_component(table, pr_person="person_id")

    s3.crud_strings[tablename] = Storage(title_create = T("Save Search"),
                                         title_display = T("Saved Search Details"),
                                         title_list = T("Saved Searches"),
                                         title_update = T("Edit Saved Search"),
                                         title_search = T("Search Saved Searches"),
                                         subtitle_create = T("Add Saved Search"),
                                         subtitle_list = T("Saved Searches"),
                                         label_list_button = T("List Saved Searches"),
                                         label_create_button = T("Save Search"),
                                         label_delete_button = T("Delete Saved Search"),
                                         msg_record_created = T("Saved Search added"),
                                         msg_record_modified = T("Saved Search updated"),
                                         msg_record_deleted = T("Saved Search deleted"),
                                         msg_list_empty = T("No Search saved"))
    
# Provide a handle to this load function
s3mgr.model.loader(saved_search_tables,
                   "pr_save_search")


# =============================================================================
# Subscription (to a resource rather than a search)
# @deprecated
#
#resourcename = "pe_subscription"
#tablename = "pr_pe_subscription"
#table = db.define_table(tablename,
#                        super_link(db.pr_pentity), # pe_id
#                        Field("resource", label=T("Resource")),
#                        Field("record", label=T("Record")), # type="s3uuid"
#                        comments(),
#                        *s3_meta_fields())

#table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
#                                    s3_pentity_represent,
#                                    filterby="instance_type",
#                                    orderby="instance_type",
#                                    filter_opts=("pr_person", "pr_group"))

# Moved to controller to ensure all tables caught!
#table.resource.requires = IS_IN_SET(db.tables)

#s3mgr.configure(tablename,
#                list_fields=["id",
#                             "resource",
#                             "record"
#                            ])

#s3mgr.model.add_component(table,
#                          pr_pentity=super_key(db.pr_pentity))

#s3.crud_strings[tablename] = Storage(
#    title_create = T("Add Subscription"),
#    title_display = T("Subscription Details"),
#    title_list = T("Subscriptions"),
#    title_update = T("Edit Subscription"),
#    title_search = T("Search Subscriptions"),
#    subtitle_create = T("Add Subscription"),
#    subtitle_list = T("Subscriptions"),
#    label_list_button = T("List Subscriptions"),
#    label_create_button = T("Add Subscription"),
#    label_delete_button = T("Delete Subscription"),
#    msg_record_created = T("Subscription added"),
#    msg_record_modified = T("Subscription updated"),
#    msg_record_deleted = T("Subscription deleted"),
#    msg_list_empty = T("No Subscription available"))


# =============================================================================
# Presence
#  @ToDo: deprecate
#       Still used by CR & DVI
#
def old_presence_tables():
    """ Load the Presence Tables when needed """

    pr_presence_condition_opts = vita.presence_conditions

    resourcename = "presence"
    tablename = "pr_presence"
    table = db.define_table(tablename,
                            super_link(db.pr_pentity),      # pe_id
                            super_link(db.sit_situation),   # sit_id
                            person_id("observer",
                                      label=T("Observer"),
                                      default = s3_logged_in_person(),
                                      comment=s3_person_comment(T("Observer"),
                                                                T("Person who has actually seen the person/group."))),
                            Field("shelter_id", "integer",  # See 07_cr.py for field options
                                  readable = False,
                                  writable = False),
                            location_id(widget = S3LocationAutocompleteWidget(),
                                        comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                      _href=URL(c="gis", f="location", args="create", vars=dict(format="popup"))),
                                                  DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Current Location"),
                                                                        T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                            Field("location_details",
                                  comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Location Details"),
                                                                  T("Specific Area (e.g. Building/Room) within the Location that this Person/Group is seen.")))
                                 ),
                            Field("datetime", "datetime",
                                  label = T("Date/Time"),
                                  default = request.utcnow,
                                  requires = IS_UTC_DATETIME(allow_future=False),
                                  widget = S3DateTimeWidget(future=0),
                                  represent = lambda val: s3_datetime_represent(val, utc=True),
                                  ),
                            Field("presence_condition", "integer",
                                  requires = IS_IN_SET(pr_presence_condition_opts,
                                                       zero=None),
                                  default = vita.DEFAULT_PRESENCE,
                                  label = T("Presence Condition"),
                                  represent = lambda opt: \
                                              pr_presence_condition_opts.get(opt, UNKNOWN_OPT)),
                            Field("proc_desc", label = T("Procedure"),
                                  comment = DIV(DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Procedure"),
                                                                      T('Describe the procedure which this record relates to (e.g. "medical examination")'))))),
                            location_id("orig_id", label=T("Origin"), widget = S3LocationAutocompleteWidget(),
                                        comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                      _href=URL(c="gis", f="location", args="create", vars=dict(format="popup"))),
                                                  DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Origin"),
                                                                        T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                            location_id("dest_id", label=T("Destination"), widget = S3LocationAutocompleteWidget(),
                                        comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                      _href=URL(c="gis", f="location", args="create", vars=dict(format="popup"))),
                                                  DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Destination"),
                                                                        T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                            Field("comment"),
                            Field("closed", "boolean", default=False,
                                  readable = False,
                                  writable = False,
                                  #represent = lambda opt: opt and "closed" or ""
                                  ),
                            *s3_meta_fields())

    def s3_pr_presence_onvalidation(form):

        """ Presence record validation """

        table = db.pr_presence

        location = form.vars.location_id
        shelter = form.vars.shelter_id

        if shelter and "cr_shelter" in db:
            set = db(db.cr_shelter.id == shelter)
            row = set.select(db.cr_shelter.location_id, limitby=(0, 1)).first()
            if row:
                location = form.vars.location_id = row.location_id
            else:
                shelter = None

        if location or shelter:
            return

        condition = form.vars.presence_condition
        if condition:
            try:
                condition = int(condition)
            except ValueError:
                condition = None
        else:
            condition = table.presence_condition.default
            form.vars.presence_condition = condition

        if condition:
            if condition in vita.PERSISTANT_PRESENCE or \
               condition in vita.ABSENCE:
                if not form.vars.id:
                    if table.location_id.default or \
                       table.shelter_id.default:
                        return
                else:
                    record = db(table.id == form.vars.id).select(table.location_id,
                                                                 table.shelter_id,
                                                                 limitby=(0, 1)).first()
                    if record and \
                       record.location_id or record.shelter_id:
                        return
            else:
                return
        else:
            return

        form.errors.location_id = \
        form.errors.shelter_id = T("Either a shelter or a location must be specified")
        return

    s3mgr.configure(tablename,
                    super_entity = db.sit_situation,
                    onvalidation = s3_pr_presence_onvalidation,
                    onaccept = vita.presence_accept,
                    delete_onaccept = vita.presence_accept,
                    list_fields = ["id",
                                   "datetime",
                                   "location_id",
                                   "shelter_id",
                                   "presence_condition",
                                   "orig_id",
                                   "dest_id"
                                ],
                    main="time",
                    extra="location_details")

    #s3mgr.model.add_component(table, pr_pentity=super_key(db.pr_pentity))

    ADD_LOG_ENTRY = T("Add Log Entry")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOG_ENTRY,
        title_display = T("Log Entry Details"),
        title_list = T("Presence Log"),
        title_update = T("Edit Log Entry"),
        title_search = T("Search Log Entry"),
        subtitle_create = T("Add New Log Entry"),
        subtitle_list = T("Current Log Entries"),
        label_list_button = T("List Log Entries"),
        label_create_button = ADD_LOG_ENTRY,
        msg_record_created = T("Log entry added"),
        msg_record_modified = T("Log entry updated"),
        msg_record_deleted = T("Log entry deleted"),
        msg_list_empty = T("No Presence Log Entries currently registered"))

# Provide a handle to this load function
s3mgr.configure("pr_presence",
                load=old_presence_tables)

# =============================================================================
if deployment_settings.has_module("dvi") or \
   deployment_settings.has_module("mpr"):

    # -------------------------------------------------------------------------
    # Note
    #
    # used by PFIF

    pr_person_status = {
        1: T("missing"),
        2: T("found"),
        3: T("deceased"),
        9: T("none")
    }

    resourcename = "note"
    tablename = "pr_note"
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id
                            # Reporter
                            #person_id("reporter"),
                            # Note status flags
                            Field("confirmed", "boolean",
                                  default=False,
                                  readable=False,
                                  writable=False),
                            Field("closed", "boolean",
                                  default=False,
                                  readable=False,
                                  writable=False),
                            # Person status
                            Field("status", "integer",
                                  requires=IS_IN_SET(pr_person_status,
                                                     zero=None),
                                  default=9,
                                  label=T("Status"),
                                  represent=lambda opt: \
                                            pr_person_status.get(opt,
                                                               UNKNOWN_OPT)),
                            # Time stamp
                            Field("timestmp", "datetime",
                                  label=T("Date/Time"),
                                  default=request.utcnow),
                            # Note text
                            Field("note_text", "text",
                                  label=T("Text")),

                            # Contact Information (for missing-reports)
                            Field("note_contact", "text",
                                  label=T("Contact Info"),
                                  readable=False,   # not readable by default
                                  writable=False),  # not writable by default

                            # Location
                            location_id(label=T("Last known location")),
                            *s3_meta_fields())

    # Notes as component of person entities
    s3mgr.model.add_component(table, pr_pentity=super_key(db.pr_pentity))

    # CRUD strings
    ADD_NOTE = T("New Entry")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_NOTE,
        title_display = T("Journal Entry Details"),
        title_list = T("Journal"),
        title_update = T("Edit Entry"),
        title_search = T("Search Entries"),
        subtitle_create = T("Add New Entry"),
        subtitle_list = T("Current Entries"),
        label_list_button = T("See All Entries"),
        label_create_button = ADD_NOTE,
        msg_record_created = T("Journal entry added"),
        msg_record_modified = T("Journal entry updated"),
        msg_record_deleted = T("Journal entry deleted"),
        msg_list_empty = T("No entry available"))

    def pr_note_onaccept(form):
        """ Update missing status for person """

        pe_table = db.pr_pentity
        ntable = db.pr_note
        ptable = db.pr_person

        if isinstance(form, (int, long, str)):
            _id = form
        elif hasattr(form, "vars"):
            _id = form.vars.id
        else:
            _id = form.id

        note = ntable[_id]
        if not note:
            return

        query = (ntable.pe_id == note.pe_id) & \
                (ntable.deleted != True)
        mq = query & ntable.status == 1
        fq = query & ntable.status.belongs((2, 3))
        mr = db(mq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        fr = db(fq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        missing = False
        if mr and not fr or fr.timestmp < mr.timestmp:
            missing = True
        query = ptable.pe_id == note.pe_id
        db(query).update(missing=missing)
        if note.deleted:
            try:
                location_id = form.location_id
            except:
                pass
            else:
                ttable = db.sit_presence
                query = (ptable.pe_id == note.pe_id) & \
                        (ttable.uuid == ptable.uuid) & \
                        (ttable.location_id == location_id) & \
                        (ttable.timestmp == note.timestmp)
        if note.location_id:
            s3tracker(query).set_location(note.location_id,
                                          timestmp=note.timestmp)

    s3mgr.configure(tablename,
                    list_fields=["id",
                                 "timestmp",
                                 "location_id",
                                 "note_text",
                                 "status"],
                    editable=False,
                    onaccept=pr_note_onaccept,
                    ondelete=pr_note_onaccept)

    # =========================================================================
    # Physical Description
    #
    pr_race_opts = {
        1: T("caucasoid"),
        2: T("mongoloid"),
        3: T("negroid"),
        99: T("other")
    }

    pr_complexion_opts = {
        1: T("light"),
        2: T("medium"),
        3: T("dark"),
        99: T("other")
    }

    pr_height_opts = {
        1: T("short"),
        2: T("average"),
        3: T("tall")
    }

    pr_weight_opts = {
        1: T("slim"),
        2: T("average"),
        3: T("fat")
    }

    # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
    # <xs:simpleType name="BloodGroupList">
    #  <xs:enumeration value="A+"/>
    #  <xs:enumeration value="A-"/>
    #  <xs:enumeration value="B+"/>
    #  <xs:enumeration value="B-"/>
    #  <xs:enumeration value="AB+"/>
    #  <xs:enumeration value="AB-"/>
    #  <xs:enumeration value="O+"/>
    #  <xs:enumeration value="O-"/>
    pr_blood_type_opts = {
        1: "A",
        2: "B",
        3: "0",
        4: "AB"
    }

    pr_eye_color_opts = {
        1: T("blue"),
        2: T("grey"),
        3: T("green"),
        4: T("brown"),
        5: T("black"),
        99: T("other")
    }

    pr_hair_color_opts = {
        1: T("blond"),
        2: T("brown"),
        3: T("black"),
        4: T("red"),
        5: T("grey"),
        6: T("white"),
        99: T("see comment")
    }

    pr_hair_style_opts = {
        1: T("straight"),
        2: T("wavy"),
        3: T("curly"),
        99: T("see comment")
    }

    pr_hair_length_opts = {
        1: T("short<6cm"),
        2: T("medium<12cm"),
        3: T("long>12cm"),
        4: T("shaved"),
        99: T("see comment")
    }

    pr_hair_baldness_opts = {
        1: T("forehead"),
        2: T("sides"),
        3: T("tonsure"),
        4: T("total"),
        99: T("see comment")
    }

    pr_facial_hair_type_opts = {
        1: T("none"),
        2: T("Moustache"),
        3: T("Goatee"),
        4: T("Whiskers"),
        5: T("Full beard"),
        99: T("see comment")
    }

    pr_facial_hair_length_opts = {
        1: T("short"),
        2: T("medium"),
        3: T("long"),
        4: T("shaved")
    }

    # This set is suitable for use in the US
    pr_ethnicity_opts = [
        "American Indian",
        "Alaskan",
        "Asian",
        "African American",
        "Hispanic or Latino",
        "Native Hawaiian",
        "Pacific Islander",
        "Two or more",
        "Unspecified",
        "White"
    ]

    resourcename = "physical_description"
    tablename = "pr_physical_description"
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id

                            # Race and complexion
                            Field("race", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_race_opts)),
                                  label = T("Race"),
                                  represent = lambda opt: \
                                              pr_race_opts.get(opt, UNKNOWN_OPT)),
                            Field("complexion", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_complexion_opts)),
                                  label = T("Complexion"),
                                  represent = lambda opt: \
                                              pr_complexion_opts.get(opt, UNKNOWN_OPT)),
                            Field("ethnicity",
                                  #requires=IS_NULL_OR(IS_IN_SET(pr_ethnicity_opts)),
                                  length=64),   # Mayon Compatibility

                            # Height and weight
                            Field("height", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                                  label = T("Height"),
                                  represent = lambda opt: \
                                              pr_height_opts.get(opt, UNKNOWN_OPT)),
                            Field("height_cm", "integer",
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 300)),
                                  label = T("Height (cm)")),
                            Field("weight", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                                  label = T("Weight"),
                                  represent = lambda opt: \
                                              pr_weight_opts.get(opt, UNKNOWN_OPT)),
                            Field("weight_kg", "integer",
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 500)),
                                  label = T("Weight (kg)")),

                            # Blood type, eye color
                            Field("blood_type", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_blood_type_opts)),
                                  label = T("Blood Type (AB0)"),
                                  represent = lambda opt: \
                                              pr_blood_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("eye_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_eye_color_opts)),
                                  label = T("Eye Color"),
                                  represent = lambda opt: \
                                              pr_eye_color_opts.get(opt, UNKNOWN_OPT)),

                            # Hair of the head
                            Field("hair_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                  label = T("Hair Color"),
                                  represent = lambda opt: \
                                              pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_style", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_style_opts)),
                                  label = T("Hair Style"),
                                  represent = lambda opt: \
                                              pr_hair_style_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_length", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_length_opts)),
                                  label = T("Hair Length"),
                                  represent = lambda opt: \
                                              pr_hair_length_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_baldness", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_baldness_opts)),
                                  label = T("Baldness"),
                                  represent = lambda opt: \
                                              pr_hair_baldness_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_comment"),

                            # Facial hair
                            Field("facial_hair_type", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_type_opts)),
                                  label = T("Facial hair, type"),
                                  represent = lambda opt: \
                                              pr_facial_hair_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                  label = T("Facial hair, color"),
                                  represent = lambda opt: \
                                              pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_length", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_length_opts)),
                                  label = T("Facial hear, length"),
                                  represent = lambda opt: \
                                              pr_facial_hair_length_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_comment"),

                            # Body hair and skin marks
                            Field("body_hair"),
                            Field("skin_marks", "text"),

                            # Medical Details: scars, amputations, implants
                            Field("medical_conditions", "text"),

                            # Other details
                            Field("other_details", "text"),

                            comments(),
                            *s3_meta_fields())


    table.height_cm.comment = DIV(DIV(_class="tooltip",
                                      _title="%s|%s" % (T("Height"),
                                                        T("The body height (crown to heel) in cm."))))
    table.weight_kg.comment = DIV(DIV(_class="tooltip",
                                      _title="%s|%s" % (T("Weight"),
                                                        T("The weight in kg."))))

    table.pe_id.readable = False
    table.pe_id.writable = False

    s3mgr.model.add_component(table,
                              pr_pentity=dict(joinby=super_key(db.pr_pentity),
                                              multiple=False))

# =============================================================================
def pr_rheader(r, tabs=[]):
    """
        Person Registry resource headers
        - used in PR, HRM, DVI, MPR, MSG, VOL
    """

    if "viewing" in r.vars:
        tablename, record_id = r.vars.viewing.rsplit(".", 1)
        record = db[tablename][record_id]
    else:
        tablename = r.tablename
        record = r.record

    if r.representation == "html":
        rheader_tabs = s3_rheader_tabs(r, tabs)

        if tablename == "pr_person":
            person = record
            if person:
                ptable = db.pr_person
                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       s3_fullname(person),
                       TH("%s: " % T("ID Tag Number")),
                       "%(pe_label)s" % person,
                       #TH("%s: " % T("Picture"), _rowspan=3),
                       TD(ptable.picture.represent(person.picture),
                          _rowspan=3)),

                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH("%s: " % T("Gender")),
                       "%s" % pr_gender_opts.get(person.gender, T("unknown"))),

                    TR(TH("%s: " % T("Nationality")),
                       "%s" % (gis.get_country(person.nationality, key_type="code") or T("unknown")),
                       TH("%s: " % T("Age Group")),
                       "%s" % pr_age_group_opts.get(person.age_group, T("unknown"))),

                    ), rheader_tabs)
                return rheader

        elif tablename == "pr_group":
            group = record
            if group:
                table = db.pr_group_membership
                query = (table.group_id == record.id) & \
                        (table.group_head == True)
                leader = db(query).select(table.person_id,
                                          limitby=(0, 1)).first()
                if leader:
                    leader = s3_fullname(leader.person_id)
                else:
                    leader = ""
                rheader = DIV(TABLE(
                                TR(TH("%s: " % T("Name")),
                                   group.name,
                                   TH("%s: " % T("Leader")),
                                   leader),
                                TR(TH("%s: " % T("Description")),
                                   group.description,
                                   TH(""),
                                   "")
                                ), rheader_tabs)
                return rheader

    return None

# =============================================================================
# This requires the pr_person table:
#
# Update the allowed maximum hierarchy label now that we know what fields
# are in gis_config. This allows taking the schema into account when
# validating the site config.
gis.update_gis_config_dependent_options()

# End
# =============================================================================

