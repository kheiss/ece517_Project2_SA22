# -*- coding: utf-8 -*-

""" Utilities """

super_entity = s3mgr.model.super_entity
super_link = s3mgr.model.super_link
super_key = s3mgr.model.super_key
s3_action_buttons = s3base.S3CRUD.action_buttons

# -----------------------------------------------------------------------------

def s3_register_validation():
    """ JavaScript client-side validation """

    # Client-side validation (needed to check for passwords being same)

    if request.cookies.has_key("registered"):
        password_position = "last"
    else:
        password_position = "first"

    if deployment_settings.get_auth_registration_mobile_phone_mandatory():
        mobile = """
mobile: {
    required: true
},
"""
    else:
        mobile = ""

    if deployment_settings.get_auth_registration_organisation_mandatory():
        org1 = """
organisation_id: {
    required: true
},
"""
        org2 = "".join(( """,
organisation_id: '""", str(T("Enter your organization")), """',
""" ))
    else:
        org1 = ""
        org2 = ""

    domains = ""
    if deployment_settings.get_auth_registration_organisation_hidden() and \
       request.controller != "admin":
        table = auth.settings.table_user
        table.organisation_id

        table = db.auth_organisation
        query = (table.organisation_id != None) & \
                (table.domain != None)
        whitelists = db(query).select(table.organisation_id,
                                      table.domain)
        if whitelists:
            domains = """$( '#auth_user_organisation_id__row' ).hide();
S3.whitelists = {
"""
            count = 0
            for whitelist in whitelists:
                count += 1
                domains += "'%s': %s" % (whitelist.domain,
                                         whitelist.organisation_id)
                if count < len(whitelists):
                    domains += ",\n"
                else:
                    domains += "\n"
            domains += """};
$( '#regform #auth_user_email' ).blur( function() {
    var email = $( '#regform #auth_user_email' ).val();
    var domain = email.split('@')[1];
    if (undefined != S3.whitelists[domain]) {
        $( '#auth_user_organisation_id' ).val(S3.whitelists[domain]);
    } else {
        $( '#auth_user_organisation_id__row' ).show();
    }
});
"""

    # validate signup form on keyup and submit
    # @ToDo: //remote: 'emailsurl'
    script = "".join(( domains, """
$('#regform').validate({
    errorClass: 'req',
    rules: {
        first_name: {
            required: true
        },""", mobile, """
        email: {
            required: true,
            email: true
        },""", org1, """
        password: {
            required: true
        },
        password_two: {
            required: true,
            equalTo: '.password:""", password_position, """'
        }
    },
    messages: {
        firstname: '""", str(T("Enter your firstname")), """',
        password: {
            required: '""", str(T("Provide a password")), """'
        },
        password_two: {
            required: '""", str(T("Repeat your password")), """',
            equalTo: '""", str(T("Enter the same password as above")), """'
        },
        email: {
            required: '""", str(T("Please enter a valid email address")), """',
            minlength: '""", str(T("Please enter a valid email address")), """'
        }""", org2, """
    },
    errorPlacement: function(error, element) {
        error.appendTo( element.parent().next() );
    },
    submitHandler: function(form) {
        form.submit();
    }
});""" ))
    response.s3.jquery_ready.append( script )

# -----------------------------------------------------------------------------

def s3_get_utc_offset():
    """ Get the current UTC offset for the client """

    offset = None

    if auth.is_logged_in():
        # 1st choice is the personal preference (useful for GETs if user wishes to see times in their local timezone)
        offset = session.auth.user.utc_offset
        if offset:
            offset = offset.strip()

    if not offset:
        # 2nd choice is what the client provides in the hidden field (for form POSTs)
        offset = request.post_vars.get("_utc_offset", None)
        if offset:
            offset = int(offset)
            utcstr = offset < 0 and "UTC +" or "UTC -"
            hours = abs(int(offset/60))
            minutes = abs(int(offset % 60))
            offset = "%s%02d%02d" % (utcstr, hours, minutes)
            # Make this the preferred value during this session
            if auth.is_logged_in():
                session.auth.user.utc_offset = offset

    if not offset:
        # 3rd choice is the server default (what most clients should see the timezone as)
        offset = deployment_settings.L10n.utc_offset

    return offset

# Store last value in session
session.s3.utc_offset = s3_get_utc_offset()

# -----------------------------------------------------------------------------
# Phone number requires
# (defined in s3validators.py)
s3_single_phone_requires = IS_MATCH(single_phone_number_pattern)
s3_phone_requires = IS_MATCH(multi_phone_number_pattern,
                             error_message=T("Invalid phone number!"))

# -----------------------------------------------------------------------------
# Shorten Names - e.g. when used in Dropdowns
# - unused currently?
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# -----------------------------------------------------------------------------
# Make URLs clickable
s3_url_represent = lambda url: (url and [A(url, _href=url, _target="blank")] or [""])[0]

# -----------------------------------------------------------------------------
# Date/Time representation functions
s3_date_represent = S3DateTime.date_represent
s3_time_represent = S3DateTime.time_represent
s3_datetime_represent = S3DateTime.datetime_represent
s3_utc_represent = lambda dt: s3_datetime_represent(dt, utc=True)
s3_date_represent_utc = lambda date: s3_date_represent(date, utc=True)

# -----------------------------------------------------------------------------

def s3_filename(filename):
    """
        Convert a string into a valid filename on all OS

        http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python/698714#698714
    """
    import string
    import unicodedata

    validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    filename = unicode(filename)
    cleanedFilename = unicodedata.normalize("NFKD",
                                            filename).encode("ASCII", "ignore")

    return "".join(c for c in cleanedFilename if c in validFilenameChars)

# -----------------------------------------------------------------------------

def s3_component_form(r, **attr):
    """ Custom Method to create a PDF for a component form """
    exporter = s3base.S3PDF()
    return exporter(r, **attr)

# -----------------------------------------------------------------------------

def s3_include_debug():
    """
        Generates html to include:
            the js scripts listed in ../static/scripts/tools/sahana.js.cfg
            the css listed in ../static/scripts/tools/sahana.css.cfg
    """

    # Disable printing
    class dummyStream:
        """ dummyStream behaves like a stream but does nothing. """
        def __init__(self): pass
        def write(self,data): pass
        def read(self,data): pass
        def flush(self): pass
        def close(self): pass

    save_stdout = sys.stdout
    # redirect all print deals
    sys.stdout = dummyStream()

    scripts_dir_path = "applications/%s/static/scripts" % request.application

    # Get list of script files
    sys.path.append( "%s/tools" % scripts_dir_path)
    import mergejsmf

    configDictCore = {
        "web2py": scripts_dir_path,
        "T2":     scripts_dir_path,
        "S3":     scripts_dir_path
    }
    configFilename = "%s/tools/sahana.js.cfg"  % scripts_dir_path
    (fs, files) = mergejsmf.getFiles(configDictCore, configFilename)

    # Enable print
    sys.stdout = save_stdout

    include = ""
    for file in files:
        include = '%s\n<script src="/%s/static/scripts/%s" type="text/javascript"></script>' \
            % ( include,
                request.application,
                file)

    include = "%s\n <!-- CSS Syles -->" % include
    f = open("%s/tools/sahana.css.cfg" % scripts_dir_path, "r")
    files = f.readlines()
    for file in files[:-1]:
        include = '%s\n<link href="/%s/static/styles/%s" rel="stylesheet" type="text/css" />' \
            % ( include,
                request.application,
                file[:-1]
               )
    f.close()

    return XML(include)

# -----------------------------------------------------------------------------

def s3_represent_multiref(table, opt, represent=None, separator=", "):
    """ Produce a representation for a list:reference field. """

    if represent is None:
        if "name" in table.fields:
            represent = lambda r: r and r.name or UNKNOWN_OPT

    if isinstance(opt, (int, long, str)):
        query = (table.id == opt)
    else:
        query = (table.id.belongs(opt))
    if "deleted" in table.fields:
        query = query & (table.deleted == False)

    records = db(query).select()

    if records:
        try:
            first = represent(records[0])
            rep_function = represent
        except TypeError:
            first = represent % records[0]
            rep_function = lambda r: represent % r

        # NB join only operates on strings, and some callers provide A().
        results = [first]
        for record in records[1:]:
            results.append(separator)
            results.append(rep_function(record))

        # Wrap in XML to allow showing anchors on read-only pages, else
        # Web2py will escape the angle brackets, etc. The single-record
        # location represent produces A() (unless told not to), and we
        # want to show links if we can.
        return XML(DIV(*results))

    else:
        return UNKNOWN_OPT

# -----------------------------------------------------------------------------

def s3_table_links(reference):
    """
        Return a dict of tables & their fields which have references to the
        specified table

        @deprecated: to be replaced by db[tablename]._referenced_by
        - used by controllers/gis.py & pr.py
    """

    tables = {}
    for table in db.tables:
        count = 0
        for field in db[table].fields:
            if str(db[table][field].type) == "reference %s" % reference:
                if count == 0:
                    tables[table] = {}
                tables[table][count] = field
                count += 1

    return tables

# -----------------------------------------------------------------------------

def s3_rheader_tabs(r, tabs=[], paging=False):
    """
        Constructs a DIV of component links for a S3RESTRequest

        @param tabs: the tabs as list of tuples (title, component_name, vars),
            where vars is optional
        @param paging: add paging buttons previous/next to the tabs

        @todo: move into S3CRUD
    """

    rheader_tabs = []

    tablist = []
    previous = next = None

    # Check for r.method tab
    mtab = r.component is None and \
           [t[1] for t in tabs if t[1] == r.method] and True or False
    for i in xrange(len(tabs)):
        record_id = r.id
        title, component = tabs[i][:2]
        vars_in_request = True
        if len(tabs[i]) > 2:
            _vars = Storage(tabs[i][2])
            for k,v in _vars.iteritems():
                if r.vars.get(k) != v:
                    vars_in_request = False
                    break
            if "viewing" in r.vars:
                _vars.viewing = r.vars.viewing
        else:
            _vars = r.vars

        here = False
        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
            if not component:
                component = None
        else:
            if "viewing" in _vars:
                tablename, record_id = _vars.viewing.split(".", 1)
                function = tablename.split("_", 1)[1]
            else:
                function = r.function
                record_id = r.id
        if function == r.name or \
           (function == r.function and "viewing" in request.vars):
            here = r.method == component or not mtab

        if i == len(tabs)-1:
            tab = Storage(title=title, _class = "tab_last")
        else:
            tab = Storage(title=title, _class = "tab_other")
        if i > 0 and tablist[i-1]._class == "tab_here":
            next = tab

        if component:
            if r.component and r.component.alias == component and vars_in_request or \
               r.custom_action and r.method == component:
                tab.update(_class = "tab_here")
                previous = i and tablist[i-1] or None
            if record_id:
                args = [record_id, component]
            else:
                args = [component]
            vars = Storage(_vars)
            if "viewing" in vars:
                del vars["viewing"]
            tab.update(_href=URL(function, args=args, vars=vars))
        else:
            if not r.component and len(tabs[i]) <= 2 and here:
                tab.update(_class = "tab_here")
                previous = i and tablist[i-1] or None
            vars = Storage(_vars)
            args = []
            if function != r.name:
                if "viewing" not in vars and r.id:
                    vars.update(viewing="%s.%s" % (r.tablename, r.id))
                #elif "viewing" in vars:
                elif not tabs[i][1]:
                    if "viewing" in vars:
                        del vars["viewing"]
                    args = [record_id]
            else:
                if "viewing" not in vars and record_id:
                    args = [record_id]
            tab.update(_href=URL(function, args=args, vars=vars))

        tablist.append(tab)
        rheader_tabs.append(SPAN(A(tab.title, _href=tab._href), _class=tab._class))

    if rheader_tabs:
        if paging:
            if next:
                rheader_tabs.insert(0, SPAN(A(">", _href=next._href), _class="tab_next_active"))
            else:
                rheader_tabs.insert(0, SPAN(">", _class="tab_next_inactive"))
            if previous:
                rheader_tabs.insert(0, SPAN(A("<", _href=previous._href), _class="tab_prev_active"))
            else:
                rheader_tabs.insert(0, SPAN("<", _class="tab_prev_inactive"))
        rheader_tabs = DIV(rheader_tabs, _class="tabs")
    else:
        rheader_tabs = ""

    return rheader_tabs

# -----------------------------------------------------------------------------

def s3_rheader_resource(r):
    """
        Identify the tablename and record ID for the rheader

        @param r: the current S3Request

    """

    _vars = r.vars

    if "viewing" in _vars:
        tablename, record_id = _vars.viewing.rsplit(".", 1)
        record = db[tablename][record_id]
    else:
        tablename = r.tablename
        record = r.record

    return (tablename, record)

# -----------------------------------------------------------------------------

def sort_dict_by_values(adict):
    """
        Sort a dict by value and return an OrderedDict.
        - used by models/05_irs.py
    """

    return OrderedDict(sorted(adict.items(), key = lambda item: item[1]))


# -----------------------------------------------------------------------------
# CRUD functions
# -----------------------------------------------------------------------------

def s3_barchart(r, **attr):
    """
        Provide simple barcharts for resource attributes
        SVG representation uses the SaVaGe library
        Need to request a specific value to graph in request.vars

        used as REST method handler for S3Resources

        @todo: replace by a S3MethodHandler
    """

    # Get all the variables and format them if needed
    valKey = r.vars.get("value")

    nameKey = r.vars.get("name")
    if not nameKey and r.table.get("name"):
        # Try defaulting to the most-commonly used:
        nameKey = "name"

    # The parameter value is required; it must be provided
    # The parameter name is optional; it is useful, but we don't need it
    # Here we check to make sure we can find value in the table,
    # and name (if it was provided)
    if not r.table.get(valKey):
        raise HTTP (400, s3mgr.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, s3mgr.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

    start = request.vars.get("start")
    if start:
        start = int(start)

    limit = r.vars.get("limit")
    if limit:
        limit = int(limit)

    settings = r.vars.get("settings")
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}

    if r.representation.lower() == "svg":
        r.response.headers["Content-Type"] = "image/svg+xml"

        from savage import graph
        bar = graph.BarGraph(settings=settings)

        title = deployment_settings.modules.get(module).name_nice
        bar.setTitle(title)

        if nameKey:
            xlabel = r.table.get(nameKey).label
            if xlabel:
                bar.setXLabel(str(xlabel))
            else:
                bar.setXLabel(nameKey)

        ylabel = r.table.get(valKey).label
        if ylabel:
            bar.setYLabel(str(ylabel))
        else:
            bar.setYLabel(valKey)

        try:
            records = r.resource.load(start, limit)
            for entry in r.resource:
                val = entry[valKey]

                # Can't graph None type
                if not val is None:
                    if nameKey:
                        name = entry[nameKey]
                    else:
                        name = None
                    bar.addBar(name, val)
            return bar.save()
        # If the field that was provided was not numeric, we have problems
        except ValueError:
            raise HTTP(400, "Bad Request")
    else:
        raise HTTP(501, body=BADFORMAT)

# -----------------------------------------------------------------------------

def s3_copy(r, **attr):
    """
        Copy a record

        used as REST method handler for S3Resources

        @todo: move into S3CRUDHandler
    """

    redirect(URL(args="create", vars={"from_record":r.id}))

# -----------------------------------------------------------------------------

def s3_import_prep(import_data):
    """
        Example for an import pre-processor

        @param import_data: a tuple of (resource, tree)
    """

    resource, tree = import_data

    #print "Import to %s" % resource.tablename
    #print s3mgr.xml.tostring(tree, pretty_print=True)

    # Use this to skip the import:
    #resource.skip_import = True

# Import pre-process
# This can also be a Storage of {tablename = function}*
s3mgr.import_prep = s3_import_prep

# -----------------------------------------------------------------------------

def s3_rest_controller(prefix, resourcename, **attr):
    """
        Helper function to apply the S3Resource REST interface

        @param prefix: the application prefix
        @param resourcename: the resource name (without prefix)
        @param attr: additional keyword parameters

        Any keyword parameters will be copied into the output dict (provided
        that the output is a dict). If a keyword parameter is callable, then
        it will be invoked, and its return value will be added to the output
        dict instead. The callable receives the S3Request as its first and
        only parameter.

        CRUD can be configured per table using:

            s3mgr.configure(tablename, **attr)

        *** Redirection:

        create_next             URL to redirect to after a record has been created
        update_next             URL to redirect to after a record has been updated
        delete_next             URL to redirect to after a record has been deleted

        *** Form configuration:

        list_fields             list of names of fields to include into list views
        subheadings             Sub-headings (see separate documentation)
        listadd                 Enable/Disable add-form in list views

        *** CRUD configuration:

        editable                Allow/Deny record updates in this table
        deletable               Allow/Deny record deletions in this table
        insertable              Allow/Deny record insertions into this table
        copyable                Allow/Deny record copying within this table

        *** Callbacks:

        create_onvalidation     Function/Lambda for additional record validation on create
        create_onaccept         Function/Lambda after successful record insertion

        update_onvalidation     Function/Lambda for additional record validation on update
        update_onaccept         Function/Lambda after successful record update

        onvalidation            Fallback for both create_onvalidation and update_onvalidation
        onaccept                Fallback for both create_onaccept and update_onaccept
        ondelete                Function/Lambda after record deletion
    """

    # Parse the request
    r = s3mgr.parse_request(prefix, resourcename)

    # Set REST handlers
    r.set_handler("copy", s3_copy)
    r.set_handler("barchart", s3_barchart)
    r.set_handler("analyze", s3base.S3Cube())

    importer = s3base.S3Importer()
    r.set_handler("import", importer,
                  transform=True)
    r.set_handler("import_tree", importer,
                  http=["POST","DELETE"],
                  representation="xml",
                  transform=True)
    r.set_handler("import", importer,
                  representation="aadata")

    # Execute the request
    output = r(**attr)

    if isinstance(output, dict) and (not r.method or r.method == "search"):
        if response.s3.actions is None:

            # Add default action buttons
            prefix, name, table, tablename = r.target()
            authorised = s3_has_permission("update", tablename)

            # If the component has components itself, then use the
            # component's native controller for CRU(D) => make sure
            # you have one, or override by native=False
            if r.component and s3mgr.model.has_components(table):
                native = output.get("native", True)
            else:
                native = False

            # Get table config
            model = s3mgr.model
            listadd = model.get_config(tablename, "listadd", True)
            editable = model.get_config(tablename, "editable", True) and \
                       not auth.permission.ownership_required(table, "update")
            deletable = model.get_config(tablename, "deletable", True)
            copyable = model.get_config(tablename, "copyable", False)

            # URL to open the resource
            open_url = r.resource.crud._linkto(r,
                                               authorised=authorised,
                                               update=editable,
                                               native=native)("[id]")

            # Add action buttons for Open/Delete/Copy as appropriate
            s3_action_buttons(r,
                              deletable=deletable,
                              copyable=copyable,
                              editable=editable,
                              read_url=open_url,
                              update_url=open_url)

            # Override Add-button, link to native controller and put
            # the primary key into vars for automatic linking
            if native and not listadd and \
               s3_has_permission("create", tablename):
                label = s3base.S3CRUD.crud_string(tablename,
                                                  "label_create_button")
                hook = r.resource.components[name]
                fkey = "%s.%s" % (name, hook.fkey)
                vars = request.vars.copy()
                vars.update({fkey: r.id})
                url = URL(prefix, name, args=["create"], vars=vars)
                add_btn = A(label, _href=url, _class="action-btn")
                output.update(add_btn=add_btn)

    elif r.method != "import":
        response.s3.actions = None

    return output

# END
# =============================================================================

