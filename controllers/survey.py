# -*- coding: utf-8 -*-

"""
    survey - Assessment Data Analysis Tool

    @author: Graeme Foster <graeme at acm dot org>
    
    For more details see the blueprint at:
    http://eden.sahanafoundation.org/wiki/BluePrint/SurveyTool/ADAT    
"""

""" 
    @todo: open template from the dataTables into the section tab not update
    @todo: in the pages that add a link to a template make the combobox display the label not the numbers
    @todo: restrict the deletion of a template to only those with status Pending
    
"""

import sys
sys.path.append("applications/%s/modules/s3" % request.application)
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

import base64

from gluon.contenttype import contenttype
from s3survey import survey_question_type, \
                     survey_analysis_type, \
                     S3Chart

module = request.controller
prefix = request.controller
resourcename = request.function

if not deployment_settings.has_module(prefix):
    raise HTTP(404, body="Module disabled: %s" % prefix)

s3_menu(module)

def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)

def template():

    """ RESTful CRUD controller """

    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    
    def prep(r):
        s3_action_buttons(r)
        query = (r.table.status == 1) # Status of Pending
        rows = db(query).select(r.table.id)
        try:
            response.s3.actions[1]["restrict"].extend(str(row.id) for row in rows)
        except KeyError: # the restrict key doesn't exist
            response.s3.actions[1]["restrict"] = [str(row.id) for row in rows]
        except IndexError: # the delete buttons doesn't exist
            pass
        s3mgr.configure(r.tablename,
                        orderby = "%s.status" % r.tablename,
                        create_next = URL(c="survey", f="template"),
                        update_next = URL(c="survey", f="template"),
                        )
        return True
    
     # Post-processor
    def postp(r, output):
        if r.component:
            if r.component_name == "section":
                template_id = request.args[0]
                # Add the section select widget to the form
                sectionSelect = response.s3.survey_section_select_widget(template_id)
                output.update(form = sectionSelect)
                return output

        # Add a button to show what the questionnaire looks like
#        s3_action_buttons(r)
#        response.s3.actions = \
#        response.s3.actions + [
#                               dict(label=str(T("Display")),
#                                    _class="action-btn",
#                                    url=URL(c=module,
#                                            f="templateRead",
#                                            args=["[id]"])
#                                   ),
#                              ]

        # Add some highlighting to the rows
        query = (r.table.status == 3) # Status of closed
        rows = db(query).select(r.table.id)
        response.s3.dataTableStyleDisabled = [str(row.id) for row in rows]
        response.s3.dataTableStyleWarning = [str(row.id) for row in rows]
        query = (r.table.status == 1) # Status of Pending
        rows = db(query).select(r.table.id)
        response.s3.dataTableStyleAlert = [str(row.id) for row in rows]
        query = (r.table.status == 4) # Status of Master
        rows = db(query).select(r.table.id)
        response.s3.dataTableStyleWarning.extend(str(row.id) for row in rows)
        return output

    if request.ajax:
        post = request.post_vars
        action = post.get("action")
        template_id = post.get("parent_id")
        section_id = post.get("section_id")
        section_text = post.get("section_text")
        if action == "section" and template_id != None:
            id = db.survey_section.insert(name=section_text,
                                          template_id=template_id,
                                          cloned_section_id=section_id)
            if id == None:
                print "Failed to insert record"
            return

    response.s3.prep = prep

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )
    
    response.s3.postp = postp
    rheader = response.s3.survey_template_rheader
    output = s3_rest_controller(prefix, resourcename, rheader=rheader)
            
    return output

def templateRead():
    # Load Model
    prefix = "survey"
    resourcename = "template"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]
    if "vars" in current.request and len(current.request.vars) > 0:
        dummy, template_id = current.request.vars.viewing.split(".")
    else:
        template_id = request.args[0]

    def postp(r, output):
        if r.interactive:
            template_id = r.id
            form = response.s3.survey_buildQuestionnaireFromTemplate(template_id)
            output["items"] = None
            output["form"] = None
            output["item"] = form
            output["title"] = crud_strings.title_question_details
            return output

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    editable=False,
                    deletable=False,
                   )

    response.s3.postp = postp
    r = s3mgr.parse_request(prefix, resourcename, args=[template_id])
    output  = r(method = "read", rheader=response.s3.survey_template_rheader)
    del output["list_btn"] # Remove the list button
    return output

def templateSummary():
    # Load Model
    prefix = "survey"
    resourcename = "template"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            if "vars" in current.request and len(current.request.vars) > 0:
                dummy, template_id = current.request.vars.viewing.split(".")
            else:
                template_id = r.id
            form = response.s3.survey_build_template_summary(template_id)
            output["items"] = form
            output["sortby"] = [[0,"asc"]]
            output["title"] = crud_strings.title_analysis_summary
            output["subtitle"] = crud_strings.subtitle_analysis_summary
            return output

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )

    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename, 
                                method = "list",
                                rheader=response.s3.survey_template_rheader
                               )
    response.s3.actions = None
    return output

def series():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]
    response.s3.survey_answerlist_dataTable_pre()

    def prep(r):
        if r.interactive:
            if r.id and (r.method == "update"):
                if "post_vars" in current.request and len(current.request.post_vars) > 0:
                    series_id = r.id
                    complete_id = r.component_id
                    id = response.s3.survey_save_answers_for_series(series_id,
                                                                    complete_id, # Update
                                                                    current.request.post_vars)
                    session.flash = T("Record updated")
                    redirect(URL(c="survey",
                                 f="series",
                                 args=[r.id,"update"],
                                 vars = {}))


        return True

    def postp(r, output):
        if r.component_name == None:
            response.s3.survey_serieslist_dataTable_post(r)
        elif r.component_name == "complete":
            response.s3.survey_answerlist_dataTable_post(r)
        if r.id and (r.method == "update"):
            series_id = r.id
            complete_id = r.component_id
            form = response.s3.survey_buildQuestionnaireFromSeries(series_id, complete_id)
            output["form"] = form
        if current.request.ajax == True:
            return output["item"]
        return output

    # remove CRUD generate buttons in the tabs
    s3mgr.configure("survey_series",
                    deletable = False,)
    s3mgr.configure("survey_complete",
                    listadd=False,
                    deletable=False)
    response.s3.prep = prep
    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename,
                                rheader=response.s3.survey_series_rheader)
    return output

def series_export_formatted():
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]
    
    if len(request.args) == 1:
        series_id = request.args[0]
        questions = response.s3.survey_getAllQuestionsForSeries(series_id)
        try:
            import xlwt
        except ImportError:
            output = s3_rest_controller(prefix,
                                    resourcename,
                                    rheader=response.s3.survey_series_rheader)
            return output
        
        COL_WIDTH_MULTIPLIER = 864
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet(T("Assignment"))
        output = StringIO()

        protection = xlwt.Protection()
        protection.cell_locked = 1
        noProtection = xlwt.Protection()
        noProtection.cell_locked = 0

        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN

        alignBase = xlwt.Alignment()
        alignBase.horz = xlwt.Alignment.HORZ_LEFT 
        alignBase.vert = xlwt.Alignment.VERT_TOP

        alignWrap = xlwt.Alignment()
        alignWrap.horz = xlwt.Alignment.HORZ_LEFT 
        alignWrap.vert = xlwt.Alignment.VERT_TOP 
        alignWrap.wrap = xlwt.Alignment.WRAP_AT_RIGHT
        
        shadedFill = xlwt.Pattern()
        shadedFill.pattern = xlwt.Pattern.SOLID_PATTERN
        shadedFill.pattern_fore_colour = 0x16 # 25% Grey
        shadedFill.pattern_back_colour = 0x08 # Black
        
        styleHeader = xlwt.XFStyle()
        styleHeader.font.bold = True
        styleHeader.alignment = alignBase
        styleText = xlwt.XFStyle()
        styleText.protection = protection
        styleText.alignment = alignWrap
        styleBox = xlwt.XFStyle()
        styleBox.borders = borders
        styleBox.protection = noProtection
        styleInput = xlwt.XFStyle()
        styleInput.borders = borders
        styleInput.protection = noProtection
        styleInput.pattern = shadedFill
        

        row = 0
        col = 0
        section = ""
        for question in questions:
            widgetObj = survey_question_type[question["type"]](question_id = question["qstn_id"])
            if question["section"] != section:
                if section != "":
                    row += 1
                section = question["section"]
                sheet1.write(row, 0, section, style=styleHeader)
                row += 1
            (row, ignore) = widgetObj.writeToSpreadsheet(sheet1, row, col, styleText, styleHeader, styleInput, styleBox)
        sheet1.protect = True
        book.save(output)
        output.seek(0)
        response.headers["Content-Type"] = contenttype(".xls")
        seriesName = response.s3.survey_getSeriesName(series_id)
        filename = "%s.xls" % seriesName
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
        return output.read()
    else:
        output = s3_rest_controller(prefix,
                                    resourcename,
                                    rheader=response.s3.survey_series_rheader)
        return output

def series_export_basic():
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]
    
    if len(request.args) == 1:
        series_id = request.args[0]
        questions = response.s3.survey_getAllQuestionsForSeries(series_id)
        try:
            import xlwt
        except ImportError:
            output = s3_rest_controller(prefix,
                                    resourcename,
                                    rheader=response.s3.survey_series_rheader)
            return output
        
        COL_WIDTH_MULTIPLIER = 864
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet(T("Assignment"))
        output = StringIO()

        styleHeader = xlwt.XFStyle()
        styleHeader.font.bold = True

        row = 1
        sheet1.write(0, 0, unicode(T("Code")), style=styleHeader)
        sheet1.write(0, 1, unicode(T("Question")), style=styleHeader)
        sheet1.write(0, 2, unicode(T("Answer")), style=styleHeader)
        sheet1.write(0, 3, unicode(T("Notes")), style=styleHeader)
        section = ""
        for question in questions:
            if question["section"] != section:
                section = question["section"]
                sheet1.write_merge(row, row, 0, 3, section, style=styleHeader)
                row += 1
            sheet1.write(row, 0, question["code"])
            sheet1.write(row, 1, question["name"])
            sheet1.write(row, 3, question["type"])
            width=len(unicode(question["name"]))*COL_WIDTH_MULTIPLIER
            sheet1.col(1).width = width
            row += 1
        book.save(output)
        output.seek(0)
        response.headers["Content-Type"] = contenttype(".xls")
        seriesName = response.s3.survey_getSeriesName(series_id)
        filename = "%s.xls" % seriesName
        response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
        return output.read()
    else:
        output = s3_rest_controller(prefix,
                                    resourcename,
                                    rheader=response.s3.survey_series_rheader)
        return output
    
def series_summary():
    # Load Model
    if request.env.request_method == "POST":
        redirect(URL(r=request,
                     f="complete_summary",
                     vars=request.post_vars))
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            if "vars" in current.request and len(current.request.vars) > 0:
                dummy, series_id = current.request.vars.viewing.split(".")
            else:
                series_id = r.id
            form = response.s3.survey_build_series_summary(series_id)
            output["items"] = form
            output["sortby"] = [[0,"asc"]]
            output["title"] = crud_strings.title_analysis_summary
            output["subtitle"] = crud_strings.subtitle_analysis_summary
            return output

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )

    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename, 
                                method = "list",
                                rheader=response.s3.survey_series_rheader
                               )
    response.s3.actions = None
    return output

def series_graph():
    # Load Model
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            # Draw the chart
            if "vars" in current.request and len(current.request.vars) > 0:
                dummy, series_id = current.request.vars.viewing.split(".")
            else:
                series_id = r.id
            debug = "Series ID %s<br />" % series_id
            numQstnList = None
            labelQuestion = None
            if "post_vars" in current.request and len(current.request.post_vars) > 0:
                if "labelQuestion" in current.request.post_vars:
                    labelQuestion = current.request.post_vars.labelQuestion
                if "numericQuestion" in current.request.post_vars:
                    numQstnList = current.request.post_vars.numericQuestion
                    if not isinstance(numQstnList,(list,tuple)):
                        numQstnList = [numQstnList]
                debug += "Label: %s<br />Numeric: %s<br />" % (labelQuestion, numQstnList)
                if (numQstnList != None) and (labelQuestion != None):
                    getAnswers = response.s3.survey_getAllAnswersForQuestionInSeries
                    gqstn = response.s3.survey_getQuestionFromName(labelQuestion, series_id)
                    gqstn_id = gqstn["qstn_id"] 
                    ganswers = getAnswers(gqstn_id, series_id)
                    dataList = []
                    legendLabels = []
                    for numericQuestion in numQstnList:
                        qstn = response.s3.survey_getQuestionFromCode(numericQuestion, series_id)
                        qstn_id = qstn["qstn_id"]
                        qstn_type = qstn["type"]
                        answers = getAnswers(qstn_id, series_id)
                        analysisTool = survey_analysis_type[qstn_type](qstn_id, answers)
                        legendLabels.append(analysisTool.qstnWidget.question.name)
                        grouped = analysisTool.groupData(ganswers)
                        aggregate = "Sum"
                        filtered = analysisTool.filter(aggregate, grouped)
                        (label, data) = analysisTool.splitGroupedData(filtered)
                        debug += "Type: %s<br />Grouped: %s<br />Filtered: %s<br />" % (qstn_type, grouped, filtered)
                        if data != []:
                            dataList.append(data)

                    if dataList == []:
                        output["chart"] = H4(T("Their is insufficient data to draw a chart from the questions selected"))
                    else:
                        chart = Storage()
                        chart["body"] = StringIO()
                        chart["headers"] = Storage()
                        chart["headers"]['Content-Type']="image/png"
                        chartObj = S3Chart(chart)
                        chartObj.displayAsIntegers()
                        chartObj.survey_bar(labelQuestion,
                                            dataList,
                                            label,
                                            legendLabels,
                                           )
                        base64Img = base64.b64encode(chart.body.getvalue())
                        image = IMG(_src="data:image/png;base64,%s" % base64Img)
                        output["chart"] = image
                        debug += "base64Img  Size: %s<br />Image: %s<br />base64Img %s" % (len(base64Img), image, base64Img)
            #output["debug"] = debug

            # Build the form
            if series_id == None:
                return output
            allQuestions = response.s3.survey_get_series_questions(series_id)
            labelTypeList = ("String",
                             "Option",
                             "YesNo", 
                             "YesNoDontKnow",
                             "Location",
                             )
            labelQuestions = response.s3.survey_get_series_questions_of_type (allQuestions, labelTypeList)
            lblQstns = []
            for question in labelQuestions:
                lblQstns.append(question["name"])
            numericTypeList = ("Numeric")
            numericQuestions = response.s3.survey_get_series_questions_of_type (allQuestions, numericTypeList)

            form = FORM()
            table = TABLE()

            labelQstn = SELECT(lblQstns, _name="labelQuestion", value=labelQuestion)
            table.append(TR(TH(T("Label Question:")), _class="survey_question"))
            table.append(labelQstn)

            table.append(TR(TH(T("Numeric Question:")), _class="survey_question"))
            for qstn in numericQuestions:
                innerTable = TABLE()
                tr = TR()
                if numQstnList != None and qstn["code"] in numQstnList:
                    tr.append(INPUT(_type='checkbox',
                                    _name='numericQuestion',
                                    _value=qstn["code"],
                                    value=True,
                                   )
                              )
                else:
                    tr.append(INPUT(_type='checkbox',
                                    _name='numericQuestion',
                                    _value=qstn["code"],
                                   )
                              )
                tr.append(LABEL(qstn["name"]))
                innerTable.append(tr)
                table.append(innerTable)
            form.append(table)

            button = INPUT(_type="submit", _name="Chart", _value=T("Draw Chart"))
            form.append(button)

            output["form"] = form
            output["title"] = crud_strings.title_analysis_chart
            output["subtitle"] = crud_strings.subtitle_analysis_chart
            # if the user is logged in then CRUD will set up a next
            # Unfortunately this kills the display of the chart so...
            r.next = None 
            return output

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )

    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename, 
                                method = "create",
                                rheader=response.s3.survey_series_rheader
                               )
    response.s3.has_required = False
    response.view = "survey/series_analysis.html"
    return output

def series_map():
    def merge_bounds(boundsList):
        min_lon = 180
        min_lat = 90
        max_lon = -180
        max_lat = -90
        if not isinstance(boundsList,(list,tuple)):
             boundsList = [boundsList]
        for bounds in boundsList:
            if "min_lon" in bounds:
                min_lon = min(bounds["min_lon"], min_lon)
            if "min_lat" in bounds:
                min_lat = min(bounds["min_lat"], min_lat)
            if "max_lon" in bounds:
                max_lon = max(bounds["max_lon"], max_lon)
            if "max_lat" in bounds:
                max_lat = max(bounds["max_lat"], max_lat)
        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    # Load Model
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    crud_strings = response.s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            if "vars" in current.request and len(current.request.vars) > 0:
                dummy, series_id = current.request.vars.viewing.split(".")
            else:
                series_id = r.id
            if series_id == None:
                seriesList = []
                records = response.s3.survey_getAllSeries()
                for row in records:
                     seriesList.append(row.id)
            else:
                seriesList = [series_id]
            pqstn_name = None
            if "post_vars" in current.request and len(current.request.post_vars) > 0:
                if "pqstn_name" in current.request.post_vars:
                    pqstn_name = current.request.post_vars.pqstn_name
            feature_queries = []
            bounds = {}
            # NB Currently the colour-coding isn't used (all needs are red)
            response_colour_code = {-1:"#888888", # grey
                                    0:"#000080", # blue
                                    1:"#008000", # green
                                    2:"#FFFF00", # yellow
                                    3:"#FFA500", # orange
                                    4:"#FF0000", # red
                                    5:"#880088", # purple
                                   }
            ctable = db.survey_complete
            atable = db.survey_answer
            gtable = db.gis_location

            for series_id in seriesList:
                series_name = response.s3.survey_getSeriesName(series_id)
    
                question_id = response.s3.survey_getLocationQuestionsIDForSeries(series_id)
                query = (atable.question_id == question_id) & \
                        (ctable.series_id == series_id) & \
                        (atable.complete_id == ctable.id ) & \
                        (atable.value == gtable.name)
                response_locations =  db(query).select(atable.complete_id,
                                                       gtable.uuid,
                                                       gtable.id,
                                                       gtable.name,
                                                       gtable.lat,
                                                       gtable.lon,
                                                      )
                if pqstn_name == None:
                    pqstn = response.s3.survey_getPriorityQuestionForSeries(series_id)
                else:
                    pqstn = response.s3.survey_getQuestionFromName(pqstn_name, series_id)
                if pqstn != {}:
                    pqstn_name = pqstn["name"]
                    pqstn_id = pqstn["qstn_id"]
                    answers = response.s3.survey_getAllAnswersForQuestionInSeries(pqstn_id,
                                                                                  series_id)
                    analysisTool = survey_analysis_type["Numeric"](pqstn_id,
                                                                   answers)
                    analysisTool.advancedResults()
                else:
                    analysisTool = None
                if len(response_locations) > 0:
                    for i in range( 0 , len( response_locations) ):
                        complete_id = response_locations[i].survey_answer.complete_id
                        # Insert how we want this to appear on the map
                        url = URL(c="survey",
                                  f="series",
                                  args=[series_id,
                                        "complete",
                                        complete_id,
                                        "read"
                                        ]
                                  )
                        response_locations[i].shape = "circle"
                        response_locations[i].size = 5
                        if analysisTool == None:
                            priority = -1
                        else:
                            priority = analysisTool.priority(complete_id)
                        response_locations[i].colour = response_colour_code[priority]
                        response_locations[i].popup_url = url
                        response_locations[i].popup_label = response_locations[i].gis_location.name
                    feature_queries.append({ "name": "%s: Assessments" % series_name,
                                             "query": response_locations,
                                             "active": True })
                    if bounds == {}:
                        bounds = (gis.get_bounds(response_locations.records))
                    else:
                        new_bounds = gis.get_bounds(response_locations.records)
                        bounds = merge_bounds([bounds, new_bounds])
            if bounds == {}:
                bounds = gis.get_bounds()
            map = gis.show_map(feature_queries = feature_queries,
                               bbox = bounds,
                              )
            legend = TABLE(
                       TR (TH(T("Marker Priority Levels"),_colspan=2)),
                       TR (TD(T("Grey")),TD(T("No Data"))),
                       TR (TD(T("Blue")),TD(T("Very Low"))),
                       TR (TD(T("Green")),TD(T("Low"))),
                       TR (TD(T("Yellow")),TD(T("Medium Low"))),
                       TR (TD(T("Orange")),TD(T("Medium High"))),
                       TR (TD(T("Red")),TD(T("High"))),
                       TR (TD(T("Purple")),TD(T("Very High"))),
                       _border=1)

            allQuestions = response.s3.survey_get_series_questions(series_id)
            numericTypeList = ("Numeric")
            numericQuestions = response.s3.survey_get_series_questions_of_type (allQuestions, numericTypeList)
            numQstns = []
            for question in numericQuestions:
                numQstns.append(question["name"])

            form = FORM()
            table = TABLE()

            priorityQstn = SELECT(numQstns, _name="pqstn_name", value=pqstn_name)
            table.append(TR(TH(T("Priority Question:")), _class="survey_question"))
            table.append(priorityQstn)
            form.append(table)

            button = INPUT(_type="submit", _name="Chart", _value=T("Select the Priority Question"))
            form.append(button)

            output["title"] = crud_strings.title_map
            output["subtitle"] = crud_strings.subtitle_map
            output["legend"] = legend
            output["form"] = form
            output["map"] = map
            # if the user is logged in then CRUD will set up a next
            # As well as a waste this breaks the map display
            r.next = None 
            return output

    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename, 
                                method = "create",
                                rheader=response.s3.survey_series_rheader
                               )

    response.view = "survey/series_map.html"
    return output

def completed_chart():
    """ RESTful CRUD controller """
    # Load Model
    prefix = "survey"
    resourcename = "series"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    if "series_id" in current.request.vars:
        seriesID = current.request.vars.series_id
    else:
        return "Programming Error: Series ID missing"
    if "question_id" in current.request.vars:
        qstnID = current.request.vars.question_id
    else:
        return "Programming Error: Question ID missing"
    if "type" in current.request.vars:
        type = current.request.vars.type
    else:
        return "Programming Error: Question Type missing"
    getAnswers = response.s3.survey_getAllAnswersForQuestionInSeries 
    answers = getAnswers(qstnID, seriesID)
    analysisTool = survey_analysis_type[type](qstnID, answers)
    qstnName = analysisTool.qstnWidget.question.name
    analysisTool.drawChart(response)
    return response.body.getvalue()

def section():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    def prep(r):
        s3mgr.configure(r.tablename,
                        deletable = False,
                        orderby = r.tablename+".posn",
                        )
        return True

     # Post-processor
    def postp(r, output):
        """ Add the section select widget to the form """
        try:
            template_id = int(request.args[0])
        except:
            template_id = None
        sectionSelect = response.s3.survey_section_select_widget(template_id)
        output["sectionSelect"] = sectionSelect
        return output


    response.s3.prep = prep
    response.s3.postp = postp
    
    rheader = response.s3.survey_section_rheader
    output = s3_rest_controller(prefix, resourcename, rheader=rheader)
    return output



def question():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    def prep(r):
        s3mgr.configure(r.tablename,
                        orderby = r.tablename+".posn",
                        )
        return True

     # Post-processor
    def postp(r, output):
        return output


    response.s3.prep = prep
    response.s3.postp = postp
    
    rheader = response.s3.survey_section_rheader
    output = s3_rest_controller(prefix, resourcename, rheader=rheader)
    return output

def question_list():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    output = s3_rest_controller(prefix, resourcename)
    return output

def question_metadata():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    output = s3_rest_controller(prefix, resourcename)
    return output

def newAssessment():
    # Load Model
    prefix = "survey"
    resourcename = "complete"
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    def prep(r):
        if r.interactive:
            if "vars" in current.request and len(current.request.vars) > 0:
                dummy, series_id = current.request.vars.viewing.split(".")
            if "post_vars" in current.request and len(current.request.post_vars) > 0:
                id = response.s3.survey_save_answers_for_series(series_id,
                                                                None, # Insert
                                                                current.request.post_vars)
                response.flash = response.s3.crud_strings["survey_complete"].msg_record_created
        return True

    def postp(r, output):
        T = current.T
        response.s3.survey_answerlist_dataTable_post(r)
        tablename, series_id = current.request.vars.viewing.split(".")
        form = response.s3.survey_buildQuestionnaireFromSeries(series_id, None)
        urlform=URL(c=module,
                     f="series_export_formatted",
                     args=[series_id])
        urlbasic=URL(c=module,
                     f="series_export_basic",
                     args=[series_id])
        buttons = DIV (A(T("Export Assessment as a Formatted Spreadsheet"), _href=urlform, _id="Excel-export", _class="action-btn"),
                       A(T("Export Assessment as a Spreadsheet"), _href=urlbasic, _id="Excel-export", _class="action-btn")
                      )
        output["subtitle"] = buttons
        output["form"] = form
        return output

    response.s3.prep = prep
    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                resourcename, 
                                method = "create",
                                rheader=response.s3.survey_series_rheader
                               )
    return output

def complete():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]
    response.s3.survey_answerlist_dataTable_pre()

    def prep(r):
        if r.method == "create" or r.method == "update":
            if "post_vars" in current.request and len(current.request.post_vars) > 0:
                complete_id = r.component_id
                id = response.s3.survey_save_answers_for_complete(r.id,
                                                                  current.request.post_vars)
                session.flash = T("Record created")
                redirect(URL(c="survey",
                             f="complete",
                             args=[r.id,"create"],
                             vars = {}))
        return True

    def postp(r, output):
        if r.method == "create" or r.method == "update":
            form = response.s3.survey_buildQuestionnaire(r.id)
            output["form"] = form
        elif r.method == "import":
            pass # don't want the import dataTable to be modified
        else:
            response.s3.survey_answerlist_dataTable_post(r)
        return output

    s3mgr.configure("survey_complete",
                    listadd=False,
                    deletable=False)
    response.s3.prep = prep
    response.s3.postp = postp
    output = s3_rest_controller(prefix, resourcename)
    return output

def complete_summary():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, "complete")
    s3mgr.load(tablename)
    table = db[tablename]
    crud_strings = response.s3.crud_strings[tablename]

    def postp(r, output):
        if r.interactive:
            question_ids = []
            vars = current.request.vars

            if "mode" in vars:
                mode = vars["mode"]
                series_id = vars["series"]
                if "selected" in vars:
                    selected = vars["selected"].split(",")
                else:
                    selected = []
                q_ltable = db.survey_question_list
                sertable = db.survey_series
                query = (sertable.id == series_id) & \
                        (sertable.template_id == q_ltable.template_id)
                questions = db(query).select(q_ltable.posn,
                                              q_ltable.question_id,
                                              orderby = q_ltable.posn)
                for question in questions:
                    if mode == "Inclusive":
                        if str(question.posn) in selected:
                            question_ids.append(str(question.question_id))
                    elif mode == "Exclusive":
                        if str(question.posn) not in selected:
                            question_ids.append(str(question.question_id))
                form = response.s3.survey_build_completed_list(series_id, question_ids)
                output["items"] = form
                output["sortby"] = [[0,"asc"]]
            output["title"] = crud_strings.title_selected
            output["subtitle"] = crud_strings.subtitle_selected
            return output

    # remove CRUD generated buttons in the tabs
    s3mgr.configure(tablename,
                    listadd=False,
                    deletable=False,
                   )

    response.s3.postp = postp
    output = s3_rest_controller(prefix,
                                "complete", 
                                method = "list",
                                rheader=response.s3.survey_complete_rheader
                               )
    response.s3.actions = None
    return output

def answer():
    """ RESTful CRUD controller """
    # Load Model
    tablename = "%s_%s" % (prefix, resourcename)
    s3mgr.load(tablename)
    table = db[tablename]

    output = s3_rest_controller(prefix, resourcename)
    return output

def analysis():
    """ Bespoke controller """
    # Load Model
#    tablename = "%s_%s" % (prefix, resourcename)
#    s3mgr.load(tablename)
#    table = db[tablename]
    try:
        template_id = request.args[0]
    except:
        pass
    s3mgr.configure("survey_complete",
                    listadd=False,
                    deletable=False)
    output = s3_rest_controller(prefix, "complete")
    return output
