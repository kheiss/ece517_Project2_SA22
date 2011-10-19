# -*- coding: utf-8 -*-

""" Incident Reporting System - Model

    @author: Sahana Taiwan Team
    @author: Fran Boon
"""

module = "irs"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # List of Incident Categories
    # NB It is important that the meaning of these entries is not changed as otherwise this hurts our ability to do synchronisation
    # The keys are based on the Canadian ems.incident hierarchy, with a few extra general versions added
    # The 2nd is meant for end-users
    # Entries can be hidden from user view in the controller.
    # Additional sets of 'translations' can be added to the tuples.
    irs_incident_type_opts = {
        "animalHealth.animalDieOff": T("Animal Die Off"),
        "animalHealth.animalFeed": T("Animal Feed"),
        "aviation.aircraftCrash": T("Aircraft Crash"),
        "aviation.aircraftHijacking": T("Aircraft Hijacking"),
        "aviation.airportClosure": T("Airport Closure"),
        "aviation.airspaceClosure": T("Airspace Closure"),
        "aviation.noticeToAirmen": T("Notice to Airmen"),
        "aviation.spaceDebris": T("Space Debris"),
        "civil.demonstrations": T("Demonstrations"),
        "civil.dignitaryVisit": T("Dignitary Visit"),
        "civil.displacedPopulations": T("Displaced Populations"),
        "civil.emergency": T("Civil Emergency"),
        "civil.looting": T("Looting"),
        "civil.publicEvent": T("Public Event"),
        "civil.riot": T("Riot"),
        "civil.volunteerRequest": T("Volunteer Request"),
        "crime": T("Crime"),
        "crime.bomb": T("Bomb"),
        "crime.bombExplosion": T("Bomb Explosion"),
        "crime.bombThreat": T("Bomb Threat"),
        "crime.dangerousPerson": T("Dangerous Person"),
        "crime.drugs": T("Drugs"),
        "crime.homeCrime": T("Home Crime"),
        "crime.illegalImmigrant": T("Illegal Immigrant"),
        "crime.industrialCrime": T("Industrial Crime"),
        "crime.poisoning": T("Poisoning"),
        "crime.retailCrime": T("Retail Crime"),
        "crime.shooting": T("Shooting"),
        "crime.stowaway": T("Stowaway"),
        "crime.terrorism": T("Terrorism"),
        "crime.vehicleCrime": T("Vehicle Crime"),
        "fire": T("Fire"),
        "fire.forestFire": T("Forest Fire"),
        "fire.hotSpot": T("Hot Spot"),
        "fire.industryFire": T("Industry Fire"),
        "fire.smoke": T("Smoke"),
        "fire.urbanFire": T("Urban Fire"),
        "fire.wildFire": T("Wild Fire"),
        "flood": T("Flood"),
        "flood.damOverflow": T("Dam Overflow"),
        "flood.flashFlood": T("Flash Flood"),
        "flood.highWater": T("High Water"),
        "flood.overlandFlowFlood": T("Overland Flow Flood"),
        "flood.tsunami": T("Tsunami"),
        "geophysical.avalanche": T("Avalanche"),
        "geophysical.earthquake": T("Earthquake"),
        "geophysical.lahar": T("Lahar"),
        "geophysical.landslide": T("Landslide"),
        "geophysical.magneticStorm": T("Magnetic Storm"),
        "geophysical.meteorite": T("Meteorite"),
        "geophysical.pyroclasticFlow": T("Pyroclastic Flow"),
        "geophysical.pyroclasticSurge": T("Pyroclastic Surge"),
        "geophysical.volcanicAshCloud": T("Volcanic Ash Cloud"),
        "geophysical.volcanicEvent": T("Volcanic Event"),
        "hazardousMaterial": T("Hazardous Material"),
        "hazardousMaterial.biologicalHazard": T("Biological Hazard"),
        "hazardousMaterial.chemicalHazard": T("Chemical Hazard"),
        "hazardousMaterial.explosiveHazard": T("Explosive Hazard"),
        "hazardousMaterial.fallingObjectHazard": T("Falling Object Hazard"),
        "hazardousMaterial.infectiousDisease": T("Infectious Disease (Hazardous Material)"),
        "hazardousMaterial.poisonousGas": T("Poisonous Gas"),
        "hazardousMaterial.radiologicalHazard": T("Radiological Hazard"),
        "health.infectiousDisease": T("Infectious Disease"),
        "health.infestation": T("Infestation"),
        "ice.iceberg": T("Iceberg"),
        "ice.icePressure": T("Ice Pressure"),
        "ice.rapidCloseLead": T("Rapid Close Lead"),
        "ice.specialIce": T("Special Ice"),
        "marine.marineSecurity": T("Marine Security"),
        "marine.nauticalAccident": T("Nautical Accident"),
        "marine.nauticalHijacking": T("Nautical Hijacking"),
        "marine.portClosure": T("Port Closure"),
        "marine.specialMarine": T("Special Marine"),
        "meteorological.blizzard": T("Blizzard"),
        "meteorological.blowingSnow": T("Blowing Snow"),
        "meteorological.drought": T("Drought"),
        "meteorological.dustStorm": T("Dust Storm"),
        "meteorological.fog": T("Fog"),
        "meteorological.freezingDrizzle": T("Freezing Drizzle"),
        "meteorological.freezingRain": T("Freezing Rain"),
        "meteorological.freezingSpray": T("Freezing Spray"),
        "meteorological.hail": T("Hail"),
        "meteorological.hurricane": T("Hurricane"),
        "meteorological.rainFall": T("Rain Fall"),
        "meteorological.snowFall": T("Snow Fall"),
        "meteorological.snowSquall": T("Snow Squall"),
        "meteorological.squall": T("Squall"),
        "meteorological.stormSurge": T("Storm Surge"),
        "meteorological.thunderstorm": T("Thunderstorm"),
        "meteorological.tornado": T("Tornado"),
        "meteorological.tropicalStorm": T("Tropical Storm"),
        "meteorological.waterspout": T("Waterspout"),
        "meteorological.winterStorm": T("Winter Storm"),
        "missingPerson": T("Missing Person"),
        "missingPerson.amberAlert": T("Child Abduction Emergency"),   # http://en.wikipedia.org/wiki/Amber_Alert
        "missingPerson.missingVulnerablePerson": T("Missing Vulnerable Person"),
        "missingPerson.silver": T("Missing Senior Citizen"),          # http://en.wikipedia.org/wiki/Silver_Alert
        "publicService.emergencySupportFacility": T("Emergency Support Facility"),
        "publicService.emergencySupportService": T("Emergency Support Service"),
        "publicService.schoolClosure": T("School Closure"),
        "publicService.schoolLockdown": T("School Lockdown"),
        "publicService.serviceOrFacility": T("Service or Facility"),
        "publicService.transit": T("Transit"),
        "railway.railwayAccident": T("Railway Accident"),
        "railway.railwayHijacking": T("Railway Hijacking"),
        "roadway.bridgeClosure": T("Bridge Closed"),
        "roadway.hazardousRoadConditions": T("Hazardous Road Conditions"),
        "roadway.roadwayAccident": T("Road Accident"),
        "roadway.roadwayClosure": T("Road Closed"),
        "roadway.roadwayDelay": T("Road Delay"),
        "roadway.roadwayHijacking": T("Road Hijacking"),
        "roadway.roadwayUsageCondition": T("Road Usage Condition"),
        "roadway.trafficReport": T("Traffic Report"),
        "temperature.arcticOutflow": T("Arctic Outflow"),
        "temperature.coldWave": T("Cold Wave"),
        "temperature.flashFreeze": T("Flash Freeze"),
        "temperature.frost": T("Frost"),
        "temperature.heatAndHumidity": T("Heat and Humidity"),
        "temperature.heatWave": T("Heat Wave"),
        "temperature.windChill": T("Wind Chill"),
        "wind.galeWind": T("Gale Wind"),
        "wind.hurricaneForceWind": T("Hurricane Force Wind"),
        "wind.stormForceWind": T("Storm Force Wind"),
        "wind.strongWind": T("Strong Wind"),
        "other.buildingCollapsed": T("Building Collapsed"),
        "other.peopleTrapped": T("People Trapped"),
        "other.powerFailure": T("Power Failure"),
    }

    # This Table defines which Categories are visible to end-users
    tablename = "irs_icategory"
    table = db.define_table(tablename,
                            Field("code", label = T("Category"),
                                  requires = IS_IN_SET_LAZY(lambda: \
                                    sort_dict_by_values(irs_incident_type_opts)),
                                  represent = lambda opt: \
                                    irs_incident_type_opts.get(opt, opt)),
                             *s3_timestamp())

    def irs_icategory_onvalidation(form):
        """
            Incident Category Validation:
                Prevent Duplicates

            Done here rather than in .requires to maintain the dropdown.
        """

        table = db.irs_icategory
        category, error = IS_NOT_ONE_OF(db, "irs_icategory.code")(form.vars.code)
        if error:
            form.errors.code = error

        return False
    s3mgr.configure(tablename,
                    onvalidation=irs_icategory_onvalidation,
                    list_fields=[ "code" ])

    # -------------------------------------------------------------------------
    # Reports
    # This is a report of an Incident
    # @ToDo: A single incident may generate many reports, so we should have a 'lead incident'

    resourcename = "ireport"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.sit_situation),
                            Field("name", label = T("Short Description"),
                                  requires = IS_NOT_EMPTY()),
                            Field("message", "text", label = T("Message"),
                                  represent = lambda message: s3_truncate(message, text, length=48, nice=True)),
                            Field("category", label = T("Category"),
                                  # The full set available to Admins & Imports/Exports
                                  # (users use the subset by over-riding this in the Controller)
                                  requires = IS_NULL_OR(IS_IN_SET_LAZY(lambda: \
                                     sort_dict_by_values(irs_incident_type_opts))),
                                  represent = lambda opt: \
                                        irs_incident_type_opts.get(opt, opt)),
                            person_id(label = T("Reporter Name"),
                                      comment = (T("At/Visited Location (not virtual)"),
                                                 s3_person_comment(T("Reporter Name"),
                                                                   T("The person at the location who is reporting this incident (optional)")))),
                            Field("contact", label = T("Contact Details")),
                            #organisation_id(label = T("Assign to Org.")),
                            Field("datetime", "datetime",
                                  label = T("Date/Time"),
                                  widget = S3DateTimeWidget(future=0),
                                  requires = [IS_NOT_EMPTY(),
                                              IS_UTC_DATETIME(allow_future=False)]),
                            location_id(),
                            #document_id(),  # Better to have multiple Documents on a Tab
                            Field("verified", "boolean",
                                  # We don't want these visible in Create forms
                                  # (we override in Update forms in controller)
                                  writable = False, readable = False,
                                  label = T("Verified?"),
                                  represent = lambda verified: \
                                        (T("No"),
                                         T("Yes"))[verified == True]),
                            Field("actioned", "boolean",
                                  label = T("Actioned?"),
                                  represent = lambda actioned: \
                                        (T("No"),
                                         T("Yes"))[actioned == True]),
                            comments(),
                            *s3_meta_fields())

    # CRUD strings
    ADD_INC_REPORT = T("Add Incident Report")
    LIST_INC_REPORTS = T("List Incident Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INC_REPORT,
        title_display = T("Incident Report Details"),
        title_list = LIST_INC_REPORTS,
        title_update = T("Edit Incident Report"),
        title_search = T("Search Incident Reports"),
        subtitle_create = T("Add New Incident Report"),
        subtitle_list = T("Incident Reports"),
        label_list_button = LIST_INC_REPORTS,
        label_create_button = ADD_INC_REPORT,
        label_delete_button = T("Delete Incident Report"),
        msg_record_created = T("Incident Report added"),
        msg_record_modified = T("Incident Report updated"),
        msg_record_deleted = T("Incident Report deleted"),
        msg_list_empty = T("No Incident Reports currently registered"))

    s3mgr.configure(tablename,
                    super_entity = db.sit_situation,
                    list_fields = ["id",
                                   "name",
                                   "category",
                                   "location_id",
                                   #"organisation_id",
                                   "verified",
                                   "actioned",
                                   "message",
                                ])

    ireport_id = S3ReusableField("ireport_id", table,
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "irs_ireport.id", "%(name)s")),
                                  represent = lambda id: id,
                                  label = T("Incident"),
                                  ondelete = "RESTRICT")
    response.s3.ireport_id = ireport_id

    # -------------------------------------------------------------------------
    @auth.s3_requires_membership(1) # must be Administrator
    def irs_ushahidi_import(r, **attr):

        if r.representation == "html" and \
           r.name == "ireport" and not r.component and not r.id:

            url = r.get_vars.get("url", "http://")

            title = T("Incident Reports")
            subtitle = T("Import from Ushahidi Instance")

            form = FORM(TABLE(TR(
                        TH("URL: "),
                        INPUT(_type="text", _name="url", _size="100", _value=url,
                              requires=[IS_URL(), IS_NOT_EMPTY()]),
                        TH(DIV(SPAN("*", _class="req", _style="padding-right: 5px;")))),
                        TR(TD("Ignore Errors?: "),
                        TD(INPUT(_type="checkbox", _name="ignore_errors", _id="ignore_errors"))),
                        TR("", INPUT(_type="submit", _value=T("Import")))))

            label_list_btn = s3base.S3CRUD.crud_string(r.tablename, "title_list")
            list_btn = A(label_list_btn,
                         _href=r.url(method="", vars=None),
                         _class="action-btn")

            rheader = DIV(P("%s: http://wiki.ushahidi.com/doku.php?id=ushahidi_api" % T("API is documented here")),
                          P("%s URL: http://ushahidi.my.domain/api?task=incidents&by=all&resp=xml&limit=1000" % T("Example")))

            output = dict(title=title, form=form, subtitle=subtitle, list_btn=list_btn, rheader=rheader)

            if form.accepts(request.vars, session):

                import_count = [0]
                def sync(job, import_count = import_count):
                    if job.tablename == "irs_ireport":
                        import_count[0] += 1
                s3mgr.configure("irs_report", resolve=sync)

                ireports = r.resource
                ushahidi = form.vars.url

                ignore_errors = form.vars.get("ignore_errors", None)

                stylesheet = os.path.join(request.folder, "static", "formats", "ushahidi", "import.xsl")

                if os.path.exists(stylesheet) and ushahidi:
                    try:
                        success = ireports.import_xml(ushahidi,
                                                      stylesheet=stylesheet,
                                                      ignore_errors=ignore_errors)
                    except:
                        import sys
                        e = sys.exc_info()[1]
                        response.error = e
                    else:
                        if success:
                            count = import_count[0]
                            if count:
                                response.flash = "%s %s" % (import_count[0],
                                                            T("reports successfully imported."))
                            else:
                                response.flash = T("No reports available.")
                        else:
                            response.error = s3mgr.error


            response.view = "create.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

    s3mgr.model.set_method(module, "ireport",
                           method="ushahidi",
                           action=irs_ushahidi_import)

    # -------------------------------------------------------------------------
    def irs_rheader(r, tabs=[]):

        """ Resource Headers for IRS """

        if r.representation == "html":
            if r.record is None:
                # List or Create form: rheader makes no sense here
                return None

            rheader_tabs = s3_rheader_tabs(r, tabs)

            if r.name == "ireport":
                report = r.record
                reporter = report.person_id
                if reporter:
                    reporter = person_represent(reporter)
                location = report.location_id
                if location:
                    location = gis_location_represent(location)
                create_request = A(T("Create Request"),
                                   _class="action-btn colorbox",
                                   _href=URL(c="req", f="req",
                                             args="create",
                                             vars={"format":"popup",
                                                   "caller":"irs_ireport"}),
                                  _title=T("Add Request"))
                create_task = A(T("Create Task"),
                                _class="action-btn colorbox",
                                _href=URL(c="project", f="task",
                                          args="create",
                                          vars={"format":"popup",
                                                "caller":"irs_ireport"}),
                                _title=T("Add Task"))
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Short Description")), report.name,
                                    TH("%s: " % T("Reporter")), reporter),
                                TR(
                                    TH("%s: " % T("Contacts")), report.contact,
                                    TH("%s: " % T("Location")), location)
                                ),
                              #DIV(P(), create_request, " ", create_task, P()),
                              rheader_tabs)

            return rheader

        else:
            return None
else:
    def ireport_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("ireport_id", "integer", readable=False, writable=False)
    response.s3.ireport_id = ireport_id

# END =========================================================================
