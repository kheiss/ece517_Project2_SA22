# -*- coding: utf-8 -*-

""" Messaging Module - Controllers """

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

s3mgr.load("msg_outbox")

# Options Menu (available in all Functions' Views)
s3_menu(module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# =============================================================================
def compose():

    """ Compose a Message which can be sent to a pentity via a number of different communications channels """

    return response.s3.msg_compose()

# -----------------------------------------------------------------------------
# Send Outbound Messages - to be called via cron
# -----------------------------------------------------------------------------
def process_email():

    """ Controller for Email processing - to be called via cron """

    msg.process_outbox(contact_method = "EMAIL")
    return

# -----------------------------------------------------------------------------
def process_sms():

    """ Controller for SMS processing - to be called via cron """

    msg.process_outbox(contact_method = "SMS")
    return

# -----------------------------------------------------------------------------
def process_twitter():

    """ Controller for Twitter message processing - to be called via cron """

    msg.process_outbox(contact_method = "TWITTER")
    return

# =============================================================================
def outbox():

    """ View the contents of the Outbox """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.message_id.label = T("Message")
    table.message_id.writable = False
    table.pe_id.readable = True
    table.pe_id.label = T("Recipient")

    # Subject works for Email but not SMS
    table.message_id.represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.message, limitby=(0, 1)).first().message
    table.pe_id.represent = lambda id: s3_pentity_represent(id, default_label = "")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_list = T("View Outbox"),
        title_update = T("Edit Message"),
        subtitle_list = T("Available Messages"),
        label_list_button = T("View Outbox"),
        label_delete_button = T("Delete Message"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in Outbox")
    )

    add_btn = A(T("Compose"),
                _class="action-btn",
                _href=URL(f="compose")
                )

    s3mgr.configure(tablename, listadd=False)
    return s3_rest_controller(module, resourcename, add_btn = add_btn)


# =============================================================================
def log():

    """
        RESTful CRUD controller for the Master Message Log
        - all Inbound & Outbound Messages go here

        @ToDo: Field Labels for i18n
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    ADD_MESSAGE = T("Add Message")
    LIST_MESSAGES = T("List Messages")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MESSAGE,
        title_display = T("Message Details"),
        title_list = LIST_MESSAGES,
        title_update = T("Edit message"),
        title_search = T("Search messages"),
        subtitle_create = T("Send new message"),
        subtitle_list = T("Messages"),
        label_list_button = LIST_MESSAGES,
        label_create_button = ADD_MESSAGE,
        msg_record_created = T("Message added"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No messages in the system"))

    s3mgr.configure(tablename, listadd=False)
    return s3_rest_controller(module, resourcename)


# =============================================================================
def tropo():

    """
        Receive a JSON POST from the Tropo WebAPI

        @see: https://www.tropo.com/docs/webapi/newhowitworks.htm
    """

    exec("from applications.%s.modules.tropo import Tropo, Session" % request.application)
    # Faster for Production (where app-name won't change):
    #from applications.eden.modules.tropo import Tropo, Session
    try:
        s = Session(request.body.read())
        t = Tropo()
        # This is their service contacting us, so parse their request
        try:
            row_id = s.parameters["row_id"]
            # This is an Outbound message which we've requested Tropo to send for us
            table = db.msg_tropo_scratch
            query = (table.row_id == row_id)
            row = db(query).select().first()
            # Send the message
            #t.message(say_obj={"say":{"value":row.message}},to=row.recipient,network=row.network)
            t.call(to=row.recipient, network=row.network)
            t.say(row.message)
            # Update status to sent in Outbox
            db(db.msg_outbox.id == row.row_id).update(status=2)
            # Set message log to actioned
            db(db.msg_log.id == row.message_id).update(actioned=True)
            # Clear the Scratchpad
            db(query).delete()
            return t.RenderJson()
        except:
            # This is an Inbound message
            try:
                message = s.initialText
                # This is an SMS/IM
                # Place it in the InBox
                uuid = s.id
                recipient = s.to["id"]
                try:
                    fromaddress = s.fromaddress["id"]
                except:
                    # SyntaxError: s.from => invalid syntax (why!?)
                    fromaddress = ""
                db.msg_log.insert(uuid=uuid, fromaddress=fromaddress,
                                  recipient=recipient, message=message,
                                  inbound=True)
                # Send the message to the parser
                reply = parserdooth(message)
                t.say([reply])
                return t.RenderJson()
            except:
                # This is a Voice call
                # - we can't handle these yet
                raise HTTP(501)
    except:
        # GET request or some random POST
        pass


# -----------------------------------------------------------------------------
# Parser for inbound messages
# -----------------------------------------------------------------------------
def parserdooth(message):

    """
        This function hopes to grow into a full fledged page that offers
        customizable routing with keywords
            - Dooth = Messenger
    """
    import difflib
    import string

    primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
    contact_keywords = ["email", "mobile", "facility", "clinical", "security", "phone", "status", "hospital", "person", "organisation"]
    keywords = string.split(message)
    query = []
    name = ""
    reply = ""
    for word in keywords:
        match = difflib.get_close_matches(word, primary_keywords + contact_keywords)
        if match:
            query.append(match[0])
        else:
            name = word

#   ------------ Person Search [get name person phone email]------------
    if "person" in query:
        result = person_search(name)

        if len(result) > 1:
            return T("Multiple Matches")
        if len(result) == 1:
            if "Person" in result[0]["name"]:
                reply = result[0]["name"]
                table3 = db.pr_contact
                if "email" in query:
                    query = (table3.pe_id == result[0]["id"]) & \
                            (table3.contact_method == "EMAIL")
                    recipient = db(query).select(table3.value,
                                                 orderby = table3.priority,
                                                 limitby=(0, 1)).first()
                    reply = "%s Email->%s" % (reply, recipient.value)
                if "mobile" in query:
                    query = (table3.pe_id == result[0]["id"]) & \
                            (table3.contact_method == "SMS")
                    recipient = db(query).select(table3.value,
                                                 orderby = table3.priority,
                                                 limitby=(0, 1)).first()
                    reply = "%s Mobile->%s" % (reply,
                                               recipient.value)

        if len(reply) == 0:
            return T("No Match")

        return reply

#   -------------Hospital Search [example: get name hospital facility status ] --------------
    if "hospital" in query:
        table = db.hms_hospital
        resource = s3mgr.define_resource("hms", "hospital")
        result = resource.search_simple(fields=["name"],label = str(name))
        if len(result) > 1:
            return T("Multiple Matches")

        if len(result) == 1:
            hospital = db(table.id == result[0]).select().first()
            reply = "%s %s (%s) " % (reply, hospital.name,
                                     T("Hospital"))
            if "phone" in query:
                reply = reply + "Phone->" + str(hospital.phone_emergency)
            if "facility" in query:
                reply = reply + "Facility status " + str(table.facility_status.represent(hospital.facility_status))
            if "clinical" in query:
                reply = reply + "Clinical status " + str(table.facility_status.represent(hospital.clinical_status))
            if "security" in query:
                reply = reply + "Security status " + str(table.facility_status.represent(hospital.security_status))

        if len(reply) == 0:
            return T("No Match")

        return reply

#   -----------------Organization search [example: get name organisation phone]------------------------------
    if "organisation" in query:
        table = db.org_organisation
        resource = s3mgr.define_resource("org", "organisation")
        result = resource.search_simple(fields=["name"], label = str(name))
        if len(result) > 1:
            return T("Multiple Matches")

        if len(result) == 1:
            organisation = db(table.id == result[0]).select().first()
            reply = "%s %s (%s) " % (reply, organisation.name,
                                     T("Organization"))
            if "phone" in query:
                reply = reply + "Phone->" + str(organisation.donation_phone)
            if "office" in query:
                reply = reply + "Address->" + s3_get_db_field_value(tablename = "org_office",
                                                                    fieldname = "address",
                                                                    look_up_value = organisation.id)
        if len(reply) == 0:
            return T("No Match")

        return reply

    return "Please provide one of the keywords - person, hospital, organisation"

# =============================================================================
def twitter_search():
    """ Controller to modify Twitter search queries """

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def twitter_search_results():
    """ Controller to retrieve tweets for user saved search queries - to be called via cron. Currently in real time also. """

    # Update results
    result = msg.receive_subscribed_tweets()

    if not result:
        session.error = T("Need to configure Twitter Authentication")
        redirect(URL(f="twitter_settings", args=[1, "update"]))

    return s3_rest_controller(module, resourcename)

# =============================================================================
@auth.s3_requires_membership(1)
def setting():

    """ SMS settings for the messaging framework """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS handler")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Outgoing SMS Handler"),
                          T("Selects what type of gateway to use for outbound SMS"))))
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit SMS Settings"),
        msg_record_modified = T("SMS settings updated")
    )

    def prep(r):
        if r.http == "POST":
            # Go to the details page for the chosen SMS Gateway
            outgoing_sms_handler = request.post_vars.get("outgoing_sms_handler",
                                                         None)
            if outgoing_sms_handler == "WEB_API":
                s3mgr.configure(tablename,
                                update_next = URL(f="api_settings",
                                                  args=[1, "update"]))
            elif outgoing_sms_handler == "SMTP":
                s3mgr.configure(tablename,
                                update_next = URL(f="smtp_to_sms_settings",
                                                  args=[1, "update"]))
            elif outgoing_sms_handler == "MODEM":
                s3mgr.configure(tablename,
                                update_next = URL(f="modem_settings",
                                                  args=[1, "update"]))
            elif outgoing_sms_handler == "TROPO":
                s3mgr.configure(tablename,
                                update_next = URL(f="tropo_settings",
                                                  args=[1, "update"]))
            else:
                s3mgr.configure(tablename,
                                update_next = URL(args=[1, "update"]))
        return True
    response.s3.prep = prep

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False)
    response.menu_options = admin_menu_options
    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def email_settings():

    """
        RESTful CRUD controller for email settings
            - appears in the administration menu
        Only 1 of these ever in existence
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.inbound_mail_server.label = T("Server")
    table.inbound_mail_type.label = T("Type")
    table.inbound_mail_ssl.label = "SSL"
    table.inbound_mail_port.label = T("Port")
    table.inbound_mail_username.label = T("Username")
    table.inbound_mail_password.label = T("Password")
    table.inbound_mail_delete.label = T("Delete from Server?")
    table.inbound_mail_port.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Port"),
                          T("For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP)."))))
    table.inbound_mail_delete.comment = DIV(DIV(_class="tooltip",
            _title="%s|%s" % (T("Delete"),
                              T("If this is set to True then mails will be deleted from the server after downloading."))))

    if not auth.has_membership(auth.id_group("Administrator")):
        session.error = UNAUTHORISED
        redirect(URL(f="index"))
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit Email Settings"),
        msg_record_modified = T("Email settings updated"),
    )

    response.menu_options = admin_menu_options
    s3mgr.configure(tablename, listadd=False, deletable=False)
    return s3_rest_controller(module, "email_settings")


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def modem_settings():

    """
        RESTful CRUD controller for modem settings
        - appears in the administration menu
        Multiple Modems can be configured to receive Inbound Messages
    """

    try:
        import serial
    except ImportError:
        session.error = T("Python Serial module not available within the running Python - this needs installing to activate the Modem")
        redirect(URL(c="admin", f="index"))

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.modem_port.label = T("Port")
    table.modem_baud.label = T("Baud")
    table.enabled.label = T("Enabled")
    table.modem_port.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Port"),
                          T("The serial port at which the modem is connected - /dev/ttyUSB0, etc on linux and com1, com2, etc on Windows"))))
    table.modem_baud.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Baud"),
                          T("Baud rate to use for your modem - The default is safe for most cases"))))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Enabled"),
                          T("Unselect to disable the modem"))))

    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Modem Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Modem settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    s3mgr.configure(tablename,
                    #deletable=False,
                    #listadd=False,
                    #update_next = URL(args=[1, "update"])
                    )
    response.menu_options = admin_menu_options
    return s3_rest_controller(module, resourcename)


#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def smtp_to_sms_settings():

    """
        RESTful CRUD controller for SMTP to SMS settings
        - appears in the administration menu
        Only 1 of these ever in existence
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.address.label = T("Address")
    table.subject.label = T("Subject")
    table.enabled.label = T("Enabled")
    table.address.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Address"),
                          T("Email Address to which to send SMS messages. Assumes sending to phonenumber@address"))))
    table.subject.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Subject"),
                          T("Optional Subject to put into Email - can be used as a Security Password by the service provider"))))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Enabled"),
                          T("Unselect to disable this SMTP service"))))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit SMTP to SMS Settings"),
        msg_record_modified = T("SMTP to SMS settings updated"),
    )

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False,
                    update_next = URL(args=[1, "update"]))
    response.menu_options = admin_menu_options
    return s3_rest_controller(module, resourcename)


#------------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def api_settings():

    """
        RESTful CRUD controller for Web API settings
        - appears in the administration menu
        Only 1 of these ever in existence
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.url.label = T("URL")
    table.to_variable.label = T("To variable")
    table.message_variable.label = T("Message variable")
    table.enabled.label = T("Enabled")
    table.url.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("URL"),
                          T("The URL of your web gateway without the post parameters"))))
    table.parameters.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Parameters"),
                          T("The post variables other than the ones containing the message and the phone number"))))
    table.message_variable.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Message Variable"),
                          T("The post variable on the URL used for sending messages"))))
    table.to_variable.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("To variable"),
                          T("The post variable containing the phone number"))))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title="%s|%s" % (T("Enabled"),
                          T("Unselect to disable this API service"))))

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit Web API Settings"),
        msg_record_modified = T("Web API settings updated"),
    )

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False,
                    update_next = URL(args=[1, "update"]))
    response.menu_options = admin_menu_options
    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def tropo_settings():

    """
        RESTful CRUD controller for Tropo settings
        - appears in the administration menu
        Only 1 of these ever in existence
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    table.token_messaging.label = T("Tropo Messaging Token")
    table.token_messaging.comment = DIV(DIV(_class="stickytip",
                                            _title="%s|%s" % (T("Tropo Messaging Token"),
                                                              T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>")))
    #table.token_voice.label = T("Tropo Voice Token")
    #table.token_voice.comment = DIV(DIV(_class="stickytip",_title=T("Tropo Voice Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit Tropo Settings"),
        msg_record_modified = T("Tropo settings updated"),
    )

    s3mgr.configure(tablename,
                    deletable=False,
                    listadd=False,
                    update_next = URL(args=[1, "update"]))
    response.menu_options = admin_menu_options
    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def twitter_settings():

    """
        RESTful CRUD controller for Twitter settings
        - appears in the administration menu
        Only 1 of these ever in existence
    """

    try:
        import tweepy
    except:
        session.error =  T("tweepy module not available within the running Python - this needs installing for non-Tropo Twitter support!")
        redirect(URL(c="admin", f="index"))

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_update = T("Authenticate system's Twitter account"),
        msg_record_modified = T("System's Twitter account updated"),
    )

    def prep(r):
        if not (deployment_settings.twitter.oauth_consumer_key and deployment_settings.twitter.oauth_consumer_secret):
            session.error = T("You should edit Twitter settings in models/000_config.py")
            return True
        oauth = tweepy.OAuthHandler(deployment_settings.twitter.oauth_consumer_key,
                                    deployment_settings.twitter.oauth_consumer_secret)

        #tablename = "%s_%s" % (module, resourcename)
        #table = db[tablename]
        table = r.table

        if r.http == "GET" and r.method in ("create", "update"):
            # We're showing the form
            try:
                session.s3.twitter_oauth_url = oauth.get_authorization_url()
                session.s3.twitter_request_key = oauth.request_token.key
                session.s3.twitter_request_secret = oauth.request_token.secret
            except tweepy.TweepError:
                session.error = T("Problem connecting to twitter.com - please refresh")
                return True
            table.pin.readable = True
            table.pin.label = SPAN(T("PIN number "),
                A(T("from Twitter"), _href=T(session.s3.twitter_oauth_url), _target="_blank"),
                " (%s)" % T("leave empty to detach account"))
            table.pin.value = ""
            table.twitter_account.label = T("Current Twitter account")
            return True
        else:
            # Not showing form, no need for pin
            table.pin.readable = False
            table.pin.label = T("PIN") # won't be seen
            table.pin.value = ""       # but let's be on the safe side
        return True
    response.s3.prep = prep

    # Post-processor
    def user_postp(r, output):
        output["list_btn"] = ""
        return output
    response.s3.postp = user_postp

    response.menu_options = admin_menu_options
    s3mgr.configure(tablename, listadd=False, deletable=False)
    return s3_rest_controller(module, "twitter_settings")


# =============================================================================
# The following functions hook into the pr functions:
#
def group():

    """ RESTful CRUD controller """

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(c="default", f="user", args="login",
        vars={"_next":URL(c="msg", f="group")}))

    module = "pr"
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False

    # Do not show system groups
    response.s3.filter = (table.system == False)

    return s3_rest_controller(module, resourcename, rheader=pr_rheader)


# -----------------------------------------------------------------------------
def group_membership():

    """ RESTful CRUD controller """

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(c="default", f="user", args="login",
        vars={"_next":URL(c="msg", f="group_membership")}))

    module = "pr"
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False
    table.comments.readable = table.comments.writable = False
    table.group_head.readable = table.group_head.writable = False

    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
def contact():

    """ Allows the user to add, update and delete their contacts """

    # Load Model
    s3mgr.load("pr_address")

    module = "pr"
    table = db.pr.contact
    ptable = db.pr_person

    if auth.is_logged_in() or auth.basic():
        query = (ptable.uuid == auth.user.person_uuid)
        person = db(query).select(ptable.pe_id,
                                  limitby=(0, 1)).first().pe_id
        response.s3.filter = (table.pe_id == person)
    else:
        redirect(URL(c="default", f="user", args="login",
            vars={"_next":URL(c="msg", f="contact")}))

    # These fields will be populated automatically
    table.name.writable = table.name.readable = False
    table.pe_id.writable = table.pe_id.readable = False
    table.person_name.writable = table.person_name.readable = False
    table.id.writable = False
    #table.id.readable = False

    def msg_contact_onvalidation(form):
        """ This onvalidation method adds the person id to the record """
        ptable = db.pr_person
        query = (ptable.uuid == auth.user.person_uuid)
        person = db(query).select(ptable.pe_id,
                                  limitby=(0, 1)).first().pe_id
        form.vars.pe_id = person

    s3mgr.configure(table._tablename,
                    onvalidation=msg_contact_onvalidation)

    def msg_contact_restrict_access(r):
        """ The following restricts update and delete access to contacts not owned by the user """
        if r.id :
            table = db.pr.contact
            ptable = db.pr_person
            query = (ptable.uuid == auth.user.person_uuid)
            person = db(query).select(ptable.pe_id,
                                      limitby=(0, 1)).first().pe_id
            query = (table.id == r.id)
            if person == db(query).select(table.pe_id,
                                          limitby=(0, 1)).first().pe_id:
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    response.s3.prep = msg_contact_restrict_access

    response.menu_options = []
    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
def search():

    """
        Do a search of groups which match a type
        - used for auto-completion
    """

    if not (auth.is_logged_in() or auth.basic()):
        # Not allowed
        return

    # JQuery UI Autocomplete uses 'term' instead of 'value'
    # (old JQuery Autocomplete uses 'q' instead of 'value')
    value = request.vars.term or request.vars.q
    if value:
        # Call the search function
        items = person_search(value)
        # Encode in JSON
        item = json.dumps(items)
        response.headers["Content-Type"] = "application/json"
        return item
    return


# -----------------------------------------------------------------------------
def person_search(value):

    """ Search for People & Groups which match a search term """

    # Shortcuts
    groups = db.pr_group
    persons = db.pr_person

    items = []

    # We want to do case-insensitive searches
    # (default anyway on MySQL/SQLite, but not PostgreSQL)
    value = value.lower()

    # Check Groups
    query = (groups["name"].lower().like("%" + value + "%")) & (groups.deleted == False)
    rows = db(query).select(groups.pe_id)
    for row in rows:
        items.append({"id":row.pe_id, "name":s3_pentity_represent(row.pe_id, default_label = "")})

    # Check Persons
    deleted = (persons.deleted == False)

    # First name
    query = (persons["first_name"].lower().like("%" + value + "%")) & deleted
    rows = db(query).select(persons.pe_id, cache=(cache.ram, 60))
    for row in rows:
        items.append({"id":row.pe_id, "name":s3_pentity_represent(row.pe_id, default_label = "")})

    # Middle name
    query = (persons["middle_name"].lower().like("%" + value + "%")) & deleted
    rows = db(query).select(persons.pe_id, cache=(cache.ram, 60))
    for row in rows:
        items.append({"id":row.pe_id, "name":s3_pentity_represent(row.pe_id, default_label = "")})

    # Last name
    query = (persons["last_name"].lower().like("%" + value + "%")) & deleted
    rows = db(query).select(persons.pe_id, cache=(cache.ram, 60))
    for row in rows:
        items.append({"id":row.pe_id, "name":s3_pentity_represent(row.pe_id, default_label = "")})

    return items


# -----------------------------------------------------------------------------
def subscription():
    resourcename = "subscription"
    #form for the subscrption preferences of the user
    return s3_rest_controller(module, resourcename)


# -----------------------------------------------------------------------------
def load_search(id):
    var = {}
    var["load"] = id
    s3mgr.load("pr_save_search")
    rows = db(db.pr_save_search.id == id).select(db.pr_save_search.ALL)
    import cPickle
    for row in rows:
        search_vars = cPickle.loads(row.search_vars)
        prefix = str(search_vars["prefix"])
        function = str(search_vars["function"])
        date = str(row.modified_on)
        break
    field = "%s.modified_on__gt" %(function)
    date = date.replace(" ","T")
    date = date + "Z"
    var[field] = date
    #var["transform"] = "eden/static/formats/xml/import.xsl"
    r = current.manager.parse_request(prefix, 
                                      function, 
                                      args=["search"], 
                                      #extension="xml", 
                                      get_vars=Storage(var) 
                                     )
    #redirect(URL(r=request, c=prefix, f=function, args=["search"],vars=var))
    response.s3.no_sspag=True
    output = r()
    #extract the updates
    return output


# -----------------------------------------------------------------------------
def get_criteria(id):
        s = ""
        try:
            id = id.replace("&apos;","'")
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
                            st = st.replace("_search_"," ")
                            st = st.replace("_advanced","")
                            st = st.replace("_simple","")
                            st = st.replace("text","text matching")
                            """st = st.replace(search_vars["function"],"")
                            st = st.replace(search_vars["prefix"],"")"""
                            st = st.replace("_"," ")
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
            return s
        except:
            return s


# -----------------------------------------------------------------------------
def check_updates(user_id):
    #Check Updates for all the Saved Searches Subscribed by the User
    message = "<h2>Saved Searches' Update</h2>"
    flag = 0
    s3mgr.load("pr_save_search")
    rows = db(db.pr_save_search.user_id == user_id).select(db.pr_save_search.ALL)
    for row in rows :
        if row.subscribed:
            records = load_search(row.id)
            #message = message + "<b>" + get_criteria(row.id) + "</b>"
            if str(records["items"]) != "No Matching Records":
                message = message + str(records["items"]) + "<br />" #Include the Saved Search details
                flag = 1                
            db.pr_save_search[row.id] = dict(modified_on = request.utcnow)
    if flag == 0:
        return
    else:
        return XML(message)


# -----------------------------------------------------------------------------
def subscription_messages():
    
    subs = None
    if request.args[0] == "daily":
        subs = db(db.msg_subscription.subscription_frequency == "daily").select(
                                                                                db.msg_subscription.ALL)
    if request.args[0] == "weekly":
        subs = db(db.msg_subscription.subscription_frequency=="weekly").select(
                                                                               db.msg_subscription.ALL)
    if request.args[0] == "monthly":
        subs = db(db.msg_subscription.subscription_frequency=="monthly").select(
                                                                                db.msg_subscription.ALL)
    if subs:    
        for sub in subs:
            #check if the message is not empty
            message = check_updates(sub.user_id)
            if message == None:
                return
            person_id = auth.s3_user_to_person(sub.user_id)
            rows = db(db.pr_person.id == person_id).select(db.pr_person.ALL)
            for row in rows:
                pe_id = row.pe_id
                break
            msg.send_by_pe_id(pe_id,
                              subject="Subscription Updates",
                              message=message,
                              sender_pe_id = None,
                              pr_message_method = "EMAIL",
                              sender="noreply@sahana.com",
                              fromaddress="sahana@sahana.com")
    return


# =============================================================================
# Enabled only for testing:
#
@auth.s3_requires_membership(1)
def tag():

    """ RESTful CRUD controller """

    # Load all models
    s3mgr.model.load_all_models()

    resourcename = "tag"
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]
    table.resource.requires = IS_IN_SET(db.tables)

    s3mgr.configure(tablename, listadd=False)
    return s3_rest_controller(module, resourcename)


# END ================================================================================
