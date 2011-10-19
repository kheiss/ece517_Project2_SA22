# -*- coding: utf-8 -*-

"""
    Project Tracking & Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon
    @date-created: 2010-08-25 (moved from org)
"""

if deployment_settings.has_module("project"):

    def project_tables():
        """ Load the Project tables as-needed """

        # Load the models we depend on
        if deployment_settings.has_module("assess"):
            s3mgr.load("assess_assess")
        assess_id = response.s3.assess_id

        module = "project"

        # =====================================================================
        # Need Type
        # Component of assses_assess too
        #
        resourcename = "need_type"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                sector_id(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_BASELINE_TYPE = T("Add Need Type")
        LIST_BASELINE_TYPE = T("List Need Types")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_BASELINE_TYPE,
            title_display = T("Need Type Details"),
            title_list = LIST_BASELINE_TYPE,
            title_update = T("Edit Need Type"),
            title_search = T("Search Need Type"),
            subtitle_create = T("Add New Need Type"),
            subtitle_list = T("Need Types"),
            label_list_button = LIST_BASELINE_TYPE,
            label_create_button = ADD_BASELINE_TYPE,
            label_delete_button = T("Delete Need Type"),
            msg_record_created = T("Need Type added"),
            msg_record_modified = T("Need Type updated"),
            msg_record_deleted = T("Need Type deleted"),
            msg_list_empty = T("No Need Types currently registered"))

        def need_type_comment():
            if auth.has_membership(auth.id_group("'Administrator'")):
                return DIV(A(ADD_BASELINE_TYPE,
                             _class="colorbox",
                             _href=URL(c="project", f="need_type", args="create",
                                       vars=dict(format="popup")),
                             _target="top",
                             _title=ADD_BASELINE_TYPE
                             )
                           )
            else:
                return None

        need_type_id = S3ReusableField("need_type_id", db.project_need_type,
                                       sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "project_need_type.id",
                                                                       "%(name)s", sort=True)),
                                       represent = lambda id: s3_get_db_field_value(tablename = "project_need_type",
                                                                                    fieldname = "name",
                                                                                    look_up_value = id),
                                       label = T("Need Type"),
                                       comment = need_type_comment(),
                                       ondelete = "RESTRICT")

        def need_type_represent(id):
            return s3_get_db_field_value(tablename = "project_need_type",
                                         fieldname = "name",
                                         look_up_value = id)

        # =====================================================================
        # Need
        #
        resourcename = "need"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                assess_id(),
                                need_type_id(),
                                Field("value", "double"),
                                comments(),
                                *s3_meta_fields())

        # Hide FK fields in forms
        table.assess_id.readable = table.assess_id.writable = False

        table.value.label = "#"
        table.value.represent = lambda value: value is not None and "%d" % value or NONE

        # CRUD strings
        ADD_BASELINE = T("Add Need")
        LIST_BASELINE = T("List Needs")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_BASELINE,
            title_display = T("Needs Details"),
            title_list = LIST_BASELINE,
            title_update = T("Edit Need"),
            title_search = T("Search Needs"),
            subtitle_create = T("Add New Need"),
            subtitle_list = T("Needs"),
            label_list_button = LIST_BASELINE,
            label_create_button = ADD_BASELINE,
            label_delete_button = T("Delete Need"),
            msg_record_created = T("Need added"),
            msg_record_modified = T("Need updated"),
            msg_record_deleted = T("Need deleted"),
            msg_list_empty = T("No Needs currently registered"))

        if deployment_settings.has_module("assess"):
            # Need as component of assessments
            s3mgr.model.add_component(table, assess_assess="assess_id")

        # =====================================================================
        # Projects:
        #   the projects which each organization is engaged in
        #
        project_status_opts = {
            1: T("active"),
            2: T("completed"),
            99: T("inactive")
            }
        resourcename = "project"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("code", label = T("Code")),
                                Field("name", label = T("Title")),
                                sector_id(),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                Field("description", "text",
                                      label = T("Description")),
                                location_id(widget = S3LocationAutocompleteWidget(),
                                            requires = IS_NULL_OR(IS_LOCATION())),
                                Field("status", "integer",
                                        requires = IS_IN_SET(project_status_opts, zero=None),
                                        # default = 99,
                                        label = T("Project Status"),
                                        represent = lambda opt: project_status_opts.get(opt, UNKNOWN_OPT)),
                                Field("beneficiaries", "integer",           # @ToDo: change this field name to total_bnf
                                      label = T("Total Beneficiaries")),
                                Field("start_date", "date",
                                      label = T("Start date")),
                                Field("end_date", "date",
                                      label = T("End date")),
                                Field("funded", "boolean"),
                                donor_id(),
                                Field("budgeted_cost", "double"),
                                *s3_meta_fields())

        # @ToDo: Fix the widget for this before displaying - should donor  be component?
        table.donor_id.readable = table.donor_id.writable = False

        # Field settings
        table.code.requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                               IS_NOT_ONE_OF(db, "project_project.code")]
        table.start_date.requires = IS_NULL_OR(IS_DATE(format = s3_date_format))
        table.end_date.requires = IS_NULL_OR(IS_DATE(format = s3_date_format))
        table.budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))

        # CRUD strings
        ADD_PROJECT = T("Add Project")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT,
            title_display = T("Project Details"),
            title_list = T("List Projects"),
            title_update = T("Edit Project"),
            title_search = T("Search Projects"),
            subtitle_create = T("Add New Project"),
            subtitle_list = T("Projects"),
            label_list_button = T("List Projects"),
            label_create_button = ADD_PROJECT,
            label_delete_button = T("Delete Project"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered"))

        # Reusable field
        project_id = S3ReusableField("project_id", db.project_project,
            sortby="name",
            requires = IS_NULL_OR(IS_ONE_OF(db, "project_project.id", "%(code)s")),
            represent = lambda id: (id and [db.project_project[id].code] or [NONE])[0],
            comment = DIV(A(ADD_PROJECT,
                            _class="colorbox",
                            _href=URL(c="project", f="project", args="create",
                                      vars=dict(format="popup")),
                            _target="top",
                            _title=ADD_PROJECT),
                      DIV( _class="tooltip",
                           _title="%s|%s" % (ADD_PROJECT,
                                             T("Add new project.")))),
            label = T("Project"),
            ondelete = "RESTRICT"
            )

        # Projects as component of Orgs
        s3mgr.model.add_component(table, org_organisation="organisation_id")

        s3mgr.configure(tablename,
                        main="code",
                        list_fields=["id",
                                     "organisation_id",
                                     "location_id",
                                     "sector_id",
                                     "code",
                                     "name",
                                     "status",
                                     "start_date",
                                     "end_date",
                                     "budgeted_cost"])

        # ---------------------------------------------------------------------
        def project_search_location(r, **attr):
            """ form function to search projects by location """

            if attr is None:
                attr = {}

            if not s3_has_permission("read", db.project_project):
                session.error = UNAUTHORISED
                redirect(URL(c="default", f="user", args="login",
                             vars={"_next":URL(args="search_location",
                                               vars=request.vars)}))

            if r.representation == "html":
                # Check for redirection
                if request.vars._next:
                    next = str.lower(request.vars._next)
                else:
                    next = URL(c="org", f="project", args="[id]")

                # Custom view
                response.view = "%s/project_search.html" % r.prefix

                # Title and subtitle
                title = T("Search for a Project")
                subtitle = T("Matching Records")

                # Select form:
                l_opts = [OPTION(_value="")]
                l_opts += [OPTION(location.name, _value=location.id)
                        for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL,
                                                                                    cache=(cache.ram, 3600))]
                form = FORM(TABLE(
                        TR(T("Location: "),
                        SELECT(_name="location", *l_opts, **dict(name="location",
                                                                 requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                        TR("", INPUT(_type="submit", _value=T("Search")))
                        ))

                output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

                # Accept action
                items = None
                if form.accepts(request.vars, session):

                    table = db.project_project
                    query = (table.deleted == False)

                    if form.vars.location is None:
                        results = db(query).select(table.ALL)
                    else:
                        query = query & (table.location_id == form.vars.location)
                        results = db(query).select(table.ALL)

                    if results and len(results):
                        records = []
                        for result in results:
                            href = next.replace("%5bid%5d", result.id)
                            records.append(TR(
                                A(result.name, _href=href),
                                result.start_date or NONE,
                                result.end_date or NONE,
                                result.description or NONE,
                                result.status and project_status_opts[result.status] or "unknown",
                                ))
                        items=DIV(TABLE(THEAD(TR(
                            TH("ID"),
                            TH("Organization"),
                            TH("Location"),
                            TH("Sector(s)"),
                            TH("Code"),
                            TH("Name"),
                            TH("Status"),
                            TH("Start date"),
                            TH("End date"),
                            TH("Budgeted Cost"))),
                            TBODY(records), _id="list", _class="dataTable display"))
                    else:
                            items = T(NONE)

                try:
                    label_create_button = s3.crud_strings["project_project"].label_create_button
                except:
                    label_create_button = s3.crud_strings.label_create_button

                add_btn = A(label_create_button,
                            _href=URL(f="project", args="create"),
                            _class="action-btn")

                output.update(dict(items=items, add_btn=add_btn))

                return output

            else:
                session.error = BADFORMAT
                redirect(URL(r=request))

        # Plug into REST controller
        s3mgr.model.set_method(module, "project",
                               method="search_location",
                               action=project_search_location )

        # ---------------------------------------------------------------------
        def project_rheader(r, tabs=[]):
            """ Project Resource Header - used in Project & Budget modules """

            if r.representation == "html":

                rheader_tabs = s3_rheader_tabs(r, tabs)

                if r.name == "project":

                    table = db.project_project

                    project = r.record

                    if project:
                        sectors = TABLE()
                        if project.sector_id:
                            # @ToDo: Fix for list: type
                            _sectors = re.split("\|", project.sector_id)[1:-1]
                            for sector in _sectors:
                                query = (db.org_sector.id == sector)
                                sectors.append(TR(db(query).select(db.org_sector.name,
                                                                   limitby=(0, 1)).first().name))

                        if deployment_settings.get_ui_cluster():
                            sector_label = T("Cluster(s)")
                        else:
                            sector_label = T("Sector(s)")

                        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % T("Code")),
                                project.code,
                                TH(""),
                                ),
                            TR(
                                TH("%s: " % T("Name")),
                                project.name,
                                TH("%s: " % T("Location")),
                                table.location_id.represent(project.location_id),
                                ),
                            TR(
                                TH("%s: " % T("Status")),
                                project_status_opts.get(project.status, UNKNOWN_OPT),
                                TH("%s: " % sector_label),
                                sectors,
                                )
                        ), rheader_tabs)
                        return rheader

            return None

        # =====================================================================
        # Activity Type
        # @deprecated
        #resourcename = "activity_type"
        #tablename = "%s_%s" % (module, resourcename)
        #table = db.define_table(tablename,
        #                        Field("name", length=128, notnull=True, unique=True),
        #                        *s3_meta_fields())


        #ADD_ACTIVITY_TYPE = T("Add Activity Type")

        #def activity_type_comment():
        #    if auth.has_membership(auth.id_group(1)):
        #        return DIV(A(ADD_ACTIVITY_TYPE,
        #                     _class="colorbox",
        #                     _href=URL(c="project", f="activity_type", args="create", vars=dict(format="popup")),
        #                     _target="top",
        #                     _title=ADD_ACTIVITY_TYPE
        #                     )
        #                   )
        #    else:
        #        return None

        #activity_type_id = S3ReusableField("activity_type_id", db.project_activity_type, sortby="name",
        #                                   requires = IS_NULL_OR(IS_ONE_OF(db, "project_activity_type.id","%(name)s", sort=True)),
        #                                   represent = lambda id: s3_get_db_field_value(tablename = "project_activity_type",
        #                                                                                fieldname = "name",
        #                                                                                look_up_value = id),
        #                                   label = T("Activity Type"),
        #                                   comment = activity_type_comment(),
        #                                   ondelete = "RESTRICT"
        #                                   )

        # =====================================================================
        # Activities
        #
        opt_bnf_type = { 1: T("Individuals"),
                         2: T("Families/HH")
                       }

        resourcename = "activity"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", label = T("Short Description"),
                                      requires=IS_NOT_EMPTY()),
                                donor_id(),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                sector_id(),
                                need_type_id(),
                                #subsector_id(),
                                #Field("quantity"),
                                #Field("unit"), # Change to link to supply
                                Field("start_date","date"),
                                Field("end_date","date"),
                                location_id(),
                                #site_id(),
                                Field("total_bnf", "integer",
                                      label = T("Total Beneficiaries")),
                                #Field("bnf_type","integer"),
                                #Field("bnf_date","date"),
                                #Field("total_bnf_target","integer"),
                                #Field("male","integer"),
                                #Field("female","integer"),
                                #Field("child_2","integer"),
                                #Field("child_5","integer"),
                                #Field("child_15","integer"),
                                #Field("cba_women","integer"),
                                #Field("pl_women","integer"),
                                person_id(label = T("Contact Person")),
                                comments(),
                                *s3_meta_fields())

        #table.bnf_type.label = T("Beneficiary Type")
        #table.bnf_date.label = T("Date of Latest Information on Beneficiaries Reached")
        #table.total_bnf_target.label = T("Total # of Target Beneficiaries")
        #table.child_2.label = T("Children (< 2 years)")
        #table.child_5.label = T("Children (2-5 years)")
        #table.child_15.label = T("Children (5-15 years)")
        #table.cba_women.label = T("CBA Women")
        #table.cba_women.comment = DIV( _class="tooltip", _title= T("Women of Child Bearing Age"))
        #table.pl_women.label = T("PL Women")
        #table.pl_women.comment = DIV( _class="tooltip", _title= T("Women who are Pregnant or in Labour"))
        #table.comments.comment = "(%s)" % T("Constraints Only")

        for field in table:
            if field.type == "integer":
                field.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )

        #table.bnf_type.requires = IS_NULL_OR(IS_IN_SET(opt_bnf_type))
        #table.bnf_type.represent = lambda opt: opt_bnf_type.get(opt, NONE)

        # CRUD Strings
        ADD_ACTIVITY = T("Add Activity")
        LIST_ACTIVITIES = T("List Activities")
        s3.crud_strings[tablename] = Storage(title_create = ADD_ACTIVITY,
                                             title_display = T("Activity Details"),
                                             title_list = LIST_ACTIVITIES,
                                             title_update = T("Edit Activity"),
                                             title_search = T("Search Activities"),
                                             subtitle_create = T("Add New Activity"),
                                             subtitle_list = T("Activities"),
                                             label_list_button = LIST_ACTIVITIES,
                                             label_create_button = ADD_ACTIVITY,
                                             msg_record_created = T("Activity Added"),
                                             msg_record_modified = T("Activity Updated"),
                                             msg_record_deleted = T("Activity Deleted"),
                                             msg_list_empty = T("No Activities Found")
                                             )

        activity_id = S3ReusableField( "activity_id", db.project_activity,
                                       sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                       "project_activity.id",
                                                                       "%(name)s",
                                                                       sort=True)),
                                       represent = lambda id: s3_get_db_field_value(tablename = "project_activity",
                                                                                    fieldname = "name",
                                                                                    look_up_value = id),
                                       label = T("Activity"),
                                       comment = DIV(A(ADD_ACTIVITY,
                                                       _class="colorbox",
                                                       _href=URL(c="project", f="activity",
                                                                 args="create",
                                                                 vars=dict(format="popup")),
                                                       _target="top",
                                                       _title=ADD_ACTIVITY
                                                       )
                                                     ),
                                       ondelete = "RESTRICT")

        # Activities as component of Orgs
        s3mgr.model.add_component(table, org_organisation="organisation_id")

        # =====================================================================
        # Tasks:
        #   a task within a project/activity/event
        #
        project_task_status_opts = {
            1: T("new"),
            2: T("assigned"),
            3: T("completed"),
            4: T("postponed"),
            5: T("feedback"),
            6: T("cancelled"),
            99: T("unspecified")
        }

        project_task_priority_opts = {
            3:T("High"),
            2:T("Medium"),
            1:T("Low")
        }

        tablename = "project_task"
        table = db.define_table(tablename,
                                Field("name", length=80, notnull=True,
                                      requires = IS_NOT_EMPTY(),
                                      label = T("Subject")),
                                Field("description", "text"),
                                #Field("urgent", "boolean", label=T("Urgent")),
                                Field("priority", "integer",
                                      requires = IS_IN_SET(project_task_priority_opts,
                                                           zero=None),
                                      default = 2,
                                      label = T("Priority"),
                                      represent = lambda opt: \
                                        project_task_priority_opts.get(opt,
                                                                       UNKNOWN_OPT)),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True),
                                                readable=False, writable=False),# So that we can add Tasks as Components of Organisations
                                site_id,
                                # @ToDo: Move to HRM?
                                person_id(label=T("Manager")),
                                location_id(label=T("Deployment Location")),
                                Field("status", "integer",
                                      requires = IS_IN_SET(project_task_status_opts,
                                                           zero=None),
                                      default = 1,
                                      label = T("Status"),
                                      represent = lambda opt: \
                                        project_task_status_opts.get(opt,
                                                                     UNKNOWN_OPT)),
                                # @ToDo: Replace these with link tables
                                project_id(readable=False, writable=False),     # So that we can add Tasks as Components of Projects
                                ireport_id(readable=False, writable=False),    # So that we can add Tasks as Components of Incidents
                                *s3_meta_fields())

        table.site_id.readable = table.site_id.writable = True
        table.site_id.label = T("Check-in at Facility")

        # CRUD Strings
        ADD_TASK = T("Add Task")
        LIST_TASKS = T("List Tasks")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_TASK,
            title_display = T("Task Details"),
            title_list = LIST_TASKS,
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            subtitle_create = T("Add New Task"),
            subtitle_list = T("Tasks"),
            label_list_button = LIST_TASKS,
            label_create_button = ADD_TASK,
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No tasks currently registered"))

        # Reusable field
        task_id = S3ReusableField("task_id", db.project_task,
            sortby="name",
            requires = IS_NULL_OR(IS_ONE_OF(db, "project_task.id", "%(name)s")),
            represent = lambda id: \
                (id and [db.project_task[id].name] or [NONE])[0],
            comment = DIV(A(ADD_TASK,
                            _class="colorbox",
                            _href=URL(c="project", f="task",
                                      args="create",
                                      vars=dict(format="popup")),
                            _target="top",
                            _title=ADD_TASK),
                      DIV( _class="tooltip",
                           _title="%s|%s" % (ADD_TASK,
                                             T("A task is a piece of work that an individual or team can do in 1-2 days")))),
            label = T("Task"),
            ondelete = "RESTRICT"
            )

        # Task as Components of Organisations, Projects & Incidents
        joinby = dict(org_organisation="organisation_id",
                      project_project="project_id")
        if deployment_settings.has_module("irs"):
           joinby["irs_ireport"] = "ireport_id"
        s3mgr.model.add_component(table, **joinby)

        def task_onvalidation(form):
            """ Task form validation """

            if str(form.vars.status) == "2" and not form.vars.person_id:
                form.errors.person_id = T("Select a manager for status 'assigned'")

            return True

        def task_create_onaccept(form):
            """ When a Task is created, also create associated Link Tables """

            if session.s3.event:
                # Create a link between this Task & the active Event
                s3mgr.load("event_task")
                db.event_task.insert(event_id=session.s3.event,
                                     task_id=form.vars.id)

            return True

        s3mgr.configure(tablename,
                        onvalidation = task_onvalidation,
                        create_onaccept = task_create_onaccept,
                        list_fields=["id",
                                     #"urgent",
                                     "priority",
                                     "name",
                                     "organisation_id",
                                     "site_id",
                                     "person_id",
                                     "status"],
                        extra="description")

        if deployment_settings.has_module("hrm"):
            tablename = "project_task_job_role"
            table = db.define_table(tablename,
                                    task_id(),
                                    job_role_id(),
                                    *s3_meta_fields())
            # Roles as component of Tasks
            s3mgr.model.add_component(table,
                                      project_task="task_id")

            tablename = "project_task_human_resource"
            table = db.define_table(tablename,
                                    task_id(),
                                    human_resource_id(),
                                    *s3_meta_fields())
            # Human Resources as component of Tasks
            s3mgr.model.add_component(table,
                                      project_task="task_id")

        # Pass variables back to global scope (response.s3.*)
        return dict(
            project_id = project_id,
            project_rheader = project_rheader,
            activity_id = activity_id,
            task_id = task_id,
            need_type_represent = need_type_represent
            )

    # Provide a handle to this load function
    s3mgr.loader(project_tables,
                 "project_project",
                 "project_activity",
                 "project_task")

else:
    def project_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("project_id", "integer", readable=False, writable=False)
    response.s3.project_id = project_id
    def activity_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("activity_id", "integer", readable=False, writable=False)
    response.s3.activity_id = activity_id
    def task_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("task_id", "integer", readable=False, writable=False)
    response.s3.task_id = task_id

# END =========================================================================

