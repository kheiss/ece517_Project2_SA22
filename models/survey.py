# -*- coding: utf-8 -*-

"""
    survey - Assessment Data Analysis Tool

    @author: Graeme Foster <graeme at acm dot org>
    
    For more details see the blueprint at:
    http://eden.sahanafoundation.org/wiki/BluePrint/SurveyTool/ADAT
    
    Brief overview of the data model
    * Template: the main repository for an assessment
    * Series:   specific detail for an instance of template
"""

module = "survey"

if deployment_settings.has_module(module):
    
    s3mgr.model.add_component("survey_complete",
                              survey_series = dict(joinby="series_id",
                                                   multiple=True))

    def survey_tables():

        import sys
        sys.path.append("applications/%s/modules/s3" % request.application)

        from s3codec import S3Codec
        from s3survey import survey_question_type, \
                             survey_analysis_type

        module = "survey"

        survey_template_status = {
            1: T("Pending"),
            2: T("Active"),
            3: T("Closed"),
            4: T("Master")
        }

        # ==========================
        # Data Base Tables
        # ==========================
        # survey_template
        # survey_sections
        # survey_question
        # survey_question_metadata
        # survey_question_list
        # survey_series
        # survey_response
        # survey_answer
        # ==========================

        #**********************************************************************
        # Template
        #**********************************************************************
        """
            The survey_template table
            
            The template is the root table and acts as a container for 
            the questions that will be used in a survey.
        """
        resourcename = "template"
        tablename = "%s_%s" % (module, resourcename)
    
        table = db.define_table(tablename,
                                   Field("name",
                                         "string",
                                         label = T("Template Name"),
                                         default="",
                                         length=120,
                                         notnull=True,
                                         unique=True,
                                         ),
                                   Field("description", "text", default="", length=500),
                                   Field("status",
                                         "integer",
                                         requires = IS_IN_SET(survey_template_status,
                                                              zero=None),
                                         default=1,
                                         represent = lambda index: survey_template_status[index],
                                         readable=True,
                                         writable=False),
                                   # Each of the following are links to questions in the template
                                   # The link is based on the question code a char(16) unique field
                                   Field("competion_qstn",
                                         "string",
                                         length=16,
                                        ),
                                   Field("date_qstn",
                                         "string",
                                         length=16,
                                        ),
                                   Field("time_qstn",
                                         "string",
                                         length=16,
                                        ),
                                   Field("location_qstn",
                                         "string",
                                         length=16,
                                        ),
                                   Field("priority_qstn",
                                         "string",
                                         length=16,
                                        ),
                                   *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Assessment Template"),
            title_display = T("Assessment Template Details"),
            title_list = T("List of Assessment Templates"),
            title_analysis_summary = T("Template Summary"),
            title_update = T("Edit Assessment Template"),
            title_question_details = T("Details of each question in the Template"),
            subtitle_create = T("Add a new Assessment Template"),
            subtitle_list = T("Assessment Templates"),
            subtitle_analysis_summary = T("Summary by Question Type - (The fewer text questions the better the analysis can be)"),
            label_list_button = T("List all Assessment Templates"),
            label_create_button = T("Add a new Assessment Template"),
            label_delete_button = T("Delete this Assessment Template"),
            msg_record_created = T("Assessment Template added"),
            msg_record_modified = T("Assessment Template updated"),
            msg_record_deleted = T("Assessment Template deleted"),
            msg_list_empty = T("No Assessment Template currently registered"))

        def template_represent(id):
            """
                Display the template name rather than the id 
            """
            table = db.survey_template
            query = (table.id == id)
            record = db(query).select(table.name,limitby=(0, 1)).first()
            if record:
                return record.name
            else:
                return None

        template_id = S3ReusableField("template_id",
                                      db.survey_template,
                                      sortby="name",
                                      label=T("Template"),
                                      requires = IS_ONE_OF(db,
                                                           "survey_template.id",
                                                           template_represent,
                                                           ),
                                      represent = template_represent,
                                      ondelete = "RESTRICT")
        s3mgr.model.add_component(table, survey_template="template_id")

        #**********************************************************************
        # Sections
        #**********************************************************************
        """
            The survey_sections table
            
            The questions can be grouped into sections this provides 
            the description of the section and
            the position of the section within the template
        """
        resourcename = "section"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                 Field("name",
                                       "string",
                                       default="",
                                       length=120,
                                       notnull=True,
                                       ),
                                 Field("description",
                                       "text",
                                       default="",
                                       length=500),
                                 Field("posn",
                                       "integer",
                                       ),
                                 Field("cloned_section_id",
                                       "integer",
                                       readable=False,
                                       writable=False,
                                       ),
                                 template_id(),
                                 *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Template Section"),
            title_display = T("Template Section Details"),
            title_list = T("List of Template Sections"),
            title_update = T("Edit Template Section"),
            subtitle_create = T("Add a new Template Section"),
            subtitle_list = T("Template Sections"),
            label_list_button = T("List all Template Sections"),
            label_create_button = T("Add a new Template Section"),
            label_delete_button = T("Delete this Template Section"),
            msg_record_created = T("Template Section added"),
            msg_record_modified = T("Template Section updated"),
            msg_record_deleted = T("Template Section deleted"),
            msg_list_empty = T("No Template Section currently registered"))

        s3mgr.configure(tablename, orderby = tablename+".posn")

        #**********************************************************************
        # Question
        #**********************************************************************
        """ The survey_question table defines a question that will appear
            within a section, and thus belong to the template.

            This holds the actual question and
            a unique string code is used to identify the question.

            It will have a type from the questionType dictionary.
            This type will determine the options that can be associated with it.
            A question can belong to many different sections.
            The notes are to help the enumerator and will typically appear as a
            footnote in the printed form.
        """
        resourcename = "question"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                 Field("name",
                                       "string",
                                       length=200,
                                       notnull=True,
                                       ),
                                 Field("code",
                                       "string",
                                       length=16,
                                       notnull=True,
                                       unique=True,
                                       ),
                                 Field("notes",
                                       "string",
                                       length=400
                                       ),
                                 Field("type",
                                       "string",
                                       length=40,
                                       notnull=True,
                                       ),
                                 Field("metadata",
                                       "text",
                                      ), 
                                 *s3_meta_fields()
                               )

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add an Assessment Question"),
            title_display = T("Assessment Question Details"),
            title_list = T("List of Assessment Questions"),
            title_update = T("Edit Assessment Question"),
            subtitle_create = T("Add a new Assessment Question"),
            subtitle_list = T("Assessment Templates"),
            label_list_button = T("List all Assessment Questions"),
            label_create_button = T("Add a new Assessment Question"),
            label_delete_button = T("Delete this Assessment Question"),
            msg_record_created = T("Assessment Question added"),
            msg_record_modified = T("Assessment Question updated"),
            msg_record_deleted = T("Assessment Question deleted"),
            msg_list_empty = T("No Assessment Question currently registered"))

        def answer_list_represent(value):
            """
                Display the answer list in a formatted table.
                Displaying the full question (rather than the code)
                and the answer.
            """
            qtable = db["survey_question"]
            answer_text = value
            list = answer_text.splitlines()
            result = TABLE()
            questions = {}
            for line in list:
                line = S3Codec.xml_decode(line)
                (question, answer) = line.split(",",1)
                question = question.strip("\" ")
                if question in questions:
                    question = questions[question]
                else:
                    query = (qtable.code == question)
                    qstn = db(query).select(qtable.name, limitby=(0, 1)).first()
                    questions[question] = qstn.name
                    question =  qstn.name
                answer = answer.strip("\" ")
                result.append(TR(TD(B(question)),TD(answer)))
            return result

        def question_onaccept(form):
            """
                All of the question metadata will be stored in the metadata
                field in the format (descriptor, value) list
                They will then be inserted into the survey_question_metadata
                table pair will be a record on that table.
            """
            if form.vars.metadata == None:
                return
            qstntable = db.survey_question
            if form.vars.id:
                record = qstntable[form.vars.id]
            else:
                return
            updateMetaData(record,
                           form.vars.type,
                           form.vars.metadata)

        s3mgr.configure(tablename,
                        onaccept = question_onaccept,
                        )

        def updateMetaData (record, type, metadata):
            metatable = db.survey_question_metadata
            data = Storage()
            metadataList = {}
            id = record.id
            metaList = metadata.split(")")
            for meta in metaList:
                pair = meta.split(",",1)
                if len(pair) == 2:
                    desc = pair[0]
                    value = pair[1]
                    desc = desc.strip("( ")
                    value = value.strip()
                    metatable.insert(question_id = id,
                                     descriptor = desc,
                                     value = value
                                    )
                    metadataList[desc] = value
            if type == "Grid":
                widgetObj = survey_question_type["Grid"]()
                widgetObj.insertChildren(record, metadataList)

        #**********************************************************************
        # Question Meta-data
        #**********************************************************************
        """ 
            The survey_question_metadata table is referenced by 
            the survey_question table and is used to manage 
            the metadata that will be associated with a question type.
            For example: if the question type is option, then valid metadata
            might be:
            count: the number of options that will be presented: 3
            1 : the first option                               : Female
            2 : the second option                              : Male
            3 : the third option                               : Not Specified
            So in the above case a question record will be associated with four
            question_metadata records. 
        """
        resourcename = "question_metadata"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                 Field("question_id",
                                       "reference survey_question",
                                       readable=False,
                                       writable=False
                                       ),
                                 Field("descriptor",
                                       "string",
                                       length=20,
                                       notnull=True,
                                       ),
                                 Field("value",
                                       "string",
                                       length=120,
                                       notnull=True,
                                       ),
                                 *s3_meta_fields()
                               )

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Question Meta-Data"),
            title_display = T("Question Meta-Data Details"),
            title_list = T("List of Question Meta-Data"),
            title_update = T("Edit Question Meta-Data"),
            subtitle_create = T("Add new Question Meta-Data"),
            subtitle_list = T("Question Meta-Data"),
            label_list_button = T("List all Question Meta-Data"),
            label_create_button = T("Add new Question Meta-Data"),
            label_delete_button = T("Delete this Question Meta-Data"),
            msg_record_created = T("Question Meta-Data added"),
            msg_record_modified = T("Question Meta-Data updated"),
            msg_record_deleted = T("Question Meta-Data deleted"),
            msg_list_empty = T("No Question Meta-Data currently registered"),
            upload_title = T("Upload a Question List import file")
            )

        #**********************************************************************
        # Question List
        #**********************************************************************
        """ The survey_question_list table is a resolver between
            the survey_question and the survey_section tables.
        
            Along with ids mapping back to these tables
            it will have a code that can be used to reference the question
            it will have the position that the question will appear in the template
        """
        resourcename = "question_list"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                 Field("posn",
                                       "integer",
                                       notnull=True,
                                       ),
                                 template_id(),
                                 Field("question_id",
                                       "reference survey_question",
                                       readable=False,
                                       writable=False
                                       ),
                                 Field("section_id",
                                       "reference survey_section",
                                       readable=False,
                                       writable=False
                                       ),
                                 *s3_meta_fields()
                               )

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            upload_title = T("Upload a Assessment Template import file")
            )

        def question_list_onaccept(form):
            """
                If a grid question is added to the the list then all of the
                grid children will need to be added as well
            """
            qstntable = db.survey_question
            try:
                question_id = form.vars.question_id
                template_id = form.vars.template_id
                section_id = form.vars.section_id
                posn = form.vars.posn
            except:
                return
            record = qstntable[question_id]
            type = record.type
            if type == "Grid":
                widgetObj = survey_question_type["Grid"]()
                widgetObj.insertChildrenToList(question_id,
                                               template_id,
                                               section_id,
                                               posn,
                                              )

        s3mgr.configure(tablename,
                        onaccept = question_list_onaccept,
                        )

        #**********************************************************************
        # Series
        #**********************************************************************
        """
            The survey_series table is used to hold all uses of a template
            
            When a series is first created the template status will change from
            Pending to Active and at the stage no further changes to the
            template can be made.
            
            Typically a series will be created for an event, which may be a
            response to a natural disaster, an exercise,
            or regular data collection activity.
            
            The series is a container for all the responses for the event
        """
        survey_series_status = {
            1: T("Active"),
            2: T("Closed"),
        }
        
        resourcename = "series"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                 Field("name", "string",
                                       default="",
                                       length=120,
                                       requires = IS_NOT_EMPTY()),
                                 Field("description", "text", default="", length=500),
                                 Field("status",
                                       "integer",
                                       requires = IS_IN_SET(survey_series_status,
                                                            zero=None),
                                       default=1,
                                       represent = lambda index: survey_series_status[index],
                                       readable=True,
                                       writable=False),
                                 template_id(empty=False),
                                 person_id(),
                                 organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                 Field("logo", "string", default="", length=512),
                                 Field("language", "string", default="en", length=8),
                                 Field("start_date", "date", default=None),
                                 Field("end_date", "date", default=None),
                                 *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Assessment Series"),
            title_display = T(" Assessment Series Details"),
            title_list = T("List of Assessment Series"),
            title_update = T("Edit Assessment Series"),
            title_analysis_summary = T("Series Summary"),
            title_analysis_chart = T("Series Graph"),
            title_map = T("Series Map"),
            subtitle_create = T("Add a new Assessment Series"),
            subtitle_list = T("Assessment Series"),
            subtitle_analysis_summary = T("Summary of Responses within Series"),
            subtitle_analysis_chart = T("Select a label question and at least one numeric question to draw the graph."),
            subtitle_map = T("Click on a marker to see the assessment details"),
            label_list_button = T("List all Assessment Series"),
            label_create_button = T("Add a new Assessment Series"),
            label_delete_button = T("Delete this Assessment Series"),
            msg_record_created = T("Assessment Series added"),
            msg_record_modified = T("Assessment Series updated"),
            msg_record_deleted = T("Assessment Series deleted"),
            msg_list_empty = T("No Assessment Series currently registered"))

        def series_represent(value):
            """
                This will display the series name, rather than the id
            """
            table = db["survey_series"]
            query = db((table.id == value))
            row = query.select(table.name, limitby=(0, 1)).first()
            return row.name

        s3mgr.model.add_component(table, survey_template="template_id")

        #**********************************************************************
        # Complete
        #**********************************************************************
        """
            The survey_complete table holds all of the answers for a completed
            response. It has a link back to the series this response belongs to.
            
            Whilst this table holds all of the answers in a text field during
            the onaccept each answer is extracted and then stored in the
            survey_answer table. This process of moving the answers to a 
            separate table makes it easier to analyse the answers
            for a given question across all responses. 
        """
        resourcename = "complete"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("series_id",
                                       "reference survey_series",
                                       represent = series_represent,
                                       label = T("Series"),
                                       readable=False,
                                       writable=False
                                       ),
                                 Field("answer_list",
                                       "text",
                                       represent = answer_list_represent
                                       ),
                                 *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Complete a new Assessment"),
            title_display = T("Completed Assessment Details"),
            title_list = T("List of Completed Assessments"),
            title_update = T("Edit Completed Assessment"),
            title_selected = T("List of Selected Answers"),
            subtitle_create = T("Add a new Completed Assessment"),
            subtitle_list = T("Completed Assessment"),
            subtitle_selected = T("Selected Answers"),
            label_list_button = T("List all Completed Assessment"),
            label_create_button = T("Add a new Completed Assessment"),
            label_delete_button = T("Delete this Completed Assessment"),
            msg_record_created = T("Completed Assessment added"),
            msg_record_modified = T("Completed Assessment updated"),
            msg_record_deleted = T("Completed Assessment deleted"),
            msg_list_empty = T("No Completed Assessments currently registered"),
            upload_title = T("Upload the Completed Assessments import file")
            )

        def complete_onaccept(form):
            """
                All of the answers will be stored in the answer_list in the 
                format "code","answer"
                They will then be inserted into the survey_answer table
                each item will be a record on that table.
            """
            rtable = db.survey_complete
            atable = db.survey_answer
    
            if form.vars.id:
                record = rtable[form.vars.id]
            else:
                return
    
            data = Storage()
            id = record.id
            answerList = record.answer_list
            importAnswers(id, answerList)

        s3mgr.configure(tablename,
                        onaccept = complete_onaccept,
                        )

        #**********************************************************************
        # Answer
        #**********************************************************************
        """
            The survey_answer table holds the answer for a single response
            of a given question.
        """
        resourcename = "answer"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("complete_id",
                                       "reference survey_complete",
                                       readable=False,
                                       writable=False
                                       ),
                                Field("question_id",
                                       "reference survey_question",
                                       readable=True,
                                       writable=False
                                       ),
                                Field("value",
                                       "text",
                                       readable=True,
                                       writable=True
                                       ),
                                *s3_meta_fields())
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Assessment Answer"),
            title_display = T("Assessment Answer Details"),
            title_list = T("List of Assessment Answers"),
            title_update = T("Edit Assessment Answer"),
            subtitle_create = T("Add a new Assessment Answer"),
            subtitle_list = T("Assessment Answer"),
            label_list_button = T("List all Assessment Answer"),
            label_create_button = T("Add a new Assessment Answer"),
            label_delete_button = T("Delete this Assessment Answer"),
            msg_record_created = T("Assessment Answer added"),
            msg_record_modified = T("Assessment Answer updated"),
            msg_record_deleted = T("Assessment Answer deleted"),
            msg_list_empty = T("No Assessment Answers currently registered"))

        #**********************************************************************
        # The bread and butter methods to get data off the database
        #**********************************************************************
        def getTemplate(template_id):
            """
                Return the template data from the template id passed in
            """
            table = db.survey_template
            query = (table.id == template_id)
            return db(query).select(limitby=(0, 1)).first()

        def getTemplateFromSeries(series_id):
            """
                Return the template data from the series_id passed in
            """
            series = getSeries(series_id)
            if series != None:
                template_id = series.template_id
                return getTemplate(template_id)
            else:
                return None

        def getSeries(series_id):
            """
                function to return the series from a series id
            """
            table = db.survey_series
            query = db((table.id == series_id))
            row = query.select(limitby=(0, 1)).first()
            return row


        def getSeriesName(series_id):
            """
                function to return the series from a series id
            """
            record = getSeries(series_id)
            return record.name


        #**********************************************************************
        # Functions to get a list of records from the database
        #**********************************************************************
        def getAllSeries():
            """
                function to return all the series on the database
            """
            table = db.survey_series
            row = db(table).select()
            return row

        def getAllQuestionsForTemplate(template_id):
            """
                function to return the list of questions for the given template
                The questions are returned in to order of their position in the
                template.
                
                The data on a question that is returns is as follows:
                qstn_id, code, name, type, posn, section
            """
            sectable = db.survey_section
            q_ltable = db.survey_question_list
            qsntable = db.survey_question
            query = db((q_ltable.template_id == template_id) & \
                       (q_ltable.section_id == sectable.id) & \
                       (q_ltable.question_id == qsntable.id)
                      )
            rows = query.select(qsntable.id,
                                qsntable.code,
                                qsntable.name,
                                qsntable.type,
                                sectable.name,
                                q_ltable.posn,
                                orderby=(q_ltable.posn))
            questions = []
            for row in rows:
                question = {}
                question["qstn_id"] = row.survey_question.id
                question["code"] = row.survey_question.code
                question["name"] = row.survey_question.name
                question["type"] = row.survey_question.type
                question["posn"] = row.survey_question_list.posn
                question["section"] = row.survey_section.name
                questions.append(question)
            return questions

        def getAllQuestionsForSeries(series_id):
            """
                function to return the list of questions for the given series
                The questions are returned in to order of their position in the
                template.
                
                The data on a question that is returns is as follows:
                qstn_id, code, name, type, posn, section
            """
            sertable = db.survey_series
            query = db((sertable.id == series_id))
            row = query.select(sertable.template_id, limitby=(0, 1)).first()
            template_id = row.template_id
            questions = getAllQuestionsForTemplate(template_id)
            return questions

        def getAllQuestionsForComplete(complete_id):
            """
                function to return a tuple of the list of questions and series_id
                for the given completed_id
                
                The questions are returned in to order of their position in the
                template.
                
                The data on a question that is returns is as follows:
                qstn_id, code, name, type, posn, section
            """
            comtable = db.survey_complete
            query = db((comtable.id == complete_id))
            row = query.select(comtable.series_id, limitby=(0, 1)).first()
            series_id = row.series_id
            questions = getAllQuestionsForSeries(series_id)
            return (questions, series_id)

        def buildQuestionnaire(complete_id):
            """
                build a form displaying all the questions and the responses
                for a given complete_id 
            """
            (questions, series_id) = getAllQuestionsForComplete(complete_id)
            return buildQuestionsForm(questions, complete_id)

        def buildQuestionnaireFromTemplate(template_id):
            """
                build a form displaying all the questions for a given template_id
            """
            questions = getAllQuestionsForTemplate(template_id)
            return buildQuestionsForm(questions,readOnly=True)

        def buildQuestionnaireFromSeries(series_id, complete_id=None):
            """
                build a form displaying all the questions for a given series_id
                If the complete_id is also provided then the responses to each
                completed question will also be displayed
            """
            questions = getAllQuestionsForSeries(series_id)
            return buildQuestionsForm(questions, complete_id)


        #**********************************************************************
        # Functions that generate some HTML from the data model
        #**********************************************************************
        def buildQuestionsForm(questions, complete_id=None, readOnly=False):
            # Create the form, hard-coded table layout :(
            form = FORM()
            table = None
            sectionTitle = ""
            for question in questions:
                if sectionTitle != question["section"]:
                    if table != None:
                        form.append(table)
                        form.append(P())
                        form.append(HR(_width="90%"))
                        form.append(P())
                    table = TABLE()
                    table.append(TR(TH(question["section"],
                                       _colspan="2"),
                                    _class="survey_section"))
                    sectionTitle = question["section"]
                widgetObj = survey_question_type[question["type"]](question_id = question["qstn_id"])
                if readOnly:
                    table.append(TR(TD(question["code"]),
                                    TD(widgetObj.type_represent()),
                                    TD(question["name"])
                                   )
                                )
                else:
                    if complete_id != None:
                        widgetObj.loadAnswer(complete_id, question["qstn_id"])
                    widget = widgetObj.display(question_id = question["qstn_id"])
                    if widget != None:
                        table.append(widget)
            form.append(table)
            if not readOnly:
                button = INPUT(_type="submit", _name="Save", _value="Save")
                form.append(button)
            return form


        def survey_template_rheader(r, tabs=[]):
            if r.representation == "html":
    
                tablename, record = s3_rheader_resource(r)
                if tablename == "survey_template" and record:
    
                    # Tabs
                    tabs = [(T("Basic Details"), "read"),
                            (T("Question Details"),"templateRead/"),
                            (T("Question Summary"),"templateSummary/"),
#                            (T("Sections"), "section"),
                           ]
                    rheader_tabs = s3_rheader_tabs(r, tabs)
    
                    sectionTable = db["survey_section"]
                    qlistTable = db["survey_question_list"]
                    if "vars" in current.request and len(current.request.vars) > 0:
                        dummy, template_id = current.request.vars.viewing.split(".")
                    else:
                        template_id = r.id

                    query = (qlistTable.template_id == template_id) & \
                            (qlistTable.section_id == sectionTable.id)
                    rows = db(query).select(sectionTable.id,
                                            sectionTable.name,
                                            orderby = qlistTable.posn)
                    tsection = TABLE(_class="survey-section-list")
                    lblSection = SPAN(T("Sections that are part of this template"),
                                      _style="font-weight:bold;")
                    if (rows.__len__() == 0):
                        rsection = SPAN(T("As of yet, no sections have been added to this template."))
                    else:
                        rsection = TR()
                        count = 0
                        lastSection = ""
                        for section in rows:
                            if section.name == lastSection:
                                continue
                            rsection.append(TD(section.name))
#                            # Comment out the following until templates can be built online
#                            rsection.append(TD(A(section.name,
#                                                 _href=URL(c="survey",
#                                                           f="section",
#                                                           args="%s" % section.id))))
                            lastSection = section.name
                            count += 1
                            if count % 4 == 0:
                                tsection.append(rsection)
                                rsection=TR()
                    tsection.append(rsection)
                            
    
                    rheader = DIV(TABLE(
                                  TR(
                                     TH("%s: " % T("Name")),
                                     record.name,
                                     TH("%s: " % T("Status")),
                                     survey_template_status[record.status],
                                     ),
                                      ),
                                  lblSection,
                                  tsection,
                                  rheader_tabs)
                    return rheader
            return None
        
        

    
        def survey_build_template_summary(template_id):
            table = TABLE(_id="template_summary",
                          _class="dataTable display")
            hr = TR(TH(T("Position")), TH(T("Section")))
            qstnTypeList = {}
            posn = 1
            for (key, type) in survey_question_type.items():
                hr.append(TH(type().type_represent()))
                qstnTypeList[key] = posn
                posn += 1
            hr.append(TH(T("Total")))
            header = THEAD(hr)

            numOfQstnTypes = len(survey_question_type) + 1
            questions = getAllQuestionsForTemplate(template_id)
            sectionTitle = ""
            line = None
            body = TBODY()
            section = 0
            total = ["", T("Total")] + [0]*numOfQstnTypes
            for question in questions:
                if sectionTitle != question["section"]:
                    if line != None:
                        br = TR()
                        for cell in line:
                            br.append(cell)
                        body.append(br)
                    section += 1
                    sectionTitle = question["section"]
                    line = [section, sectionTitle] + [0]*numOfQstnTypes
                line[qstnTypeList[question["type"]]+1] += 1
                line[numOfQstnTypes+1] += 1
                total[qstnTypeList[question["type"]]+1] += 1
                total[numOfQstnTypes+1] += 1
            # Add the trailing row
            br = TR()
            for cell in line:
                br.append(cell)
            body.append(br)
            # Add the footer to the table
            foot = TFOOT()
            tr = TR()
            for cell in total:
                tr.append(TD(B(cell))) # don't use TH() otherwise dataTables will fail
            foot.append(tr)

                
            table.append(header)
            table.append(body)
            table.append(foot)
            # turn off server side pagination
            response.s3.no_sspag = True
            # send the id of the table
            response.s3.dataTableID = "template_summary"
            return table

        # Section as component of Template


    
        def survey_section_rheader(r, tabs=[]):
            pass



        def survey_getQuestionFromCode(code, series_id):
            """
                function to return the question for the given series 
                with the code that matches the one passed in
            """
            sertable = db.survey_series
            q_ltable = db.survey_question_list
            qsntable = db.survey_question
            query = db((sertable.id == series_id) & \
                       (q_ltable.template_id == sertable.template_id) & \
                       (q_ltable.question_id == qsntable.id) & \
                       (qsntable.code == code)
                      )
            record = query.select(qsntable.id,
                                  qsntable.code,
                                  qsntable.name,
                                  qsntable.type,
                                  q_ltable.posn,
                                  limitby=(0, 1)).first()
            question = {}
            if record != None:
                question["qstn_id"] = record.survey_question.id
                question["code"] = record.survey_question.code
                question["name"] = record.survey_question.name
                question["type"] = record.survey_question.type
                question["posn"] = record.survey_question_list.posn
            return question

        def survey_getQuestionFromName(name, series_id):
            """
                function to return the question for the given series 
                with the name that matches the one passed in
            """
            sertable = db.survey_series
            q_ltable = db.survey_question_list
            qsntable = db.survey_question
            query = db((sertable.id == series_id) & \
                       (q_ltable.template_id == sertable.template_id) & \
                       (q_ltable.question_id == qsntable.id) & \
                       (qsntable.name == name)
                      )
            record = query.select(qsntable.id,
                                  qsntable.code,
                                  qsntable.name,
                                  qsntable.type,
                                  q_ltable.posn,
                                  limitby=(0, 1)).first()
            question = {}
            question["qstn_id"] = record.survey_question.id
            question["code"] = record.survey_question.code
            question["name"] = record.survey_question.name
            question["type"] = record.survey_question.type
            question["posn"] = record.survey_question_list.posn
            return question

        def survey_save_answers_for_complete(complete_id, vars):
            # Get all the questions
            (questions, series_id) = getAllQuestionsForComplete(complete_id)
            return saveAnswers(questions, series_id, complete_id, vars)
            
        def survey_save_answers_for_series(series_id, complete_id, vars):
            """
                function to save the list of answers for a completed series
            """
            questions = getAllQuestionsForSeries(series_id)
            return saveAnswers(questions, series_id, complete_id, vars)
            
        def saveAnswers(questions, series_id, complete_id, vars):
            text = ""
            for question in questions:
                code = question["code"]
                if (code in vars) and vars[code] != "":
                    line = '"%s","%s"\n' % (code, vars[code])
                    text += line
            if complete_id == None:
                # Insert into database
                id = db.survey_complete.insert(series_id = series_id, answer_list = text)
                importAnswers(id, text)
                return id
            else:
                # Update the complete_id record
                table = db.survey_complete
                db(table.id == complete_id).update(answer_list = text)
                importAnswers(complete_id, text)
                return complete_id

        def survey_get_series_questions(series_id):
            return getAllQuestionsForSeries(series_id)

        def survey_get_series_questions_of_type(questionList, type):
            if isinstance(type, (list, tuple)):
                types = type
            else:
                types = (type)
            questions = []
            for question in questionList:
                if question["type"] in types:
                    questions.append(question)
                if question["type"] == "Link":
                    widgetObj = survey_question_type["Link"](question_id = question["qstn_id"])
                    if widgetObj.getParentType() in types:
                        questions.append(question)
            return questions





        def survey_series_rheader(r, tabs=[]):
            if r.representation == "html":
    
                tablename, record = s3_rheader_resource(r)
                if tablename == "survey_series" and record:

                    # Tabs
                    if auth.s3_has_permission("create", "survey_series"):
                        tabs = [(T("New Assessment"), "newAssessment/"),
                                (T("Completed Assessments"), "complete"),
                                (T("Series Details"), "read"),
                                (T("Series Summary"),"series_summary/"),
                                (T("Series Graph"),"series_graph/"),
                                (T("Series Map"),"series_map/"),
                                ]
                    else:
                        tabs = [(T("Series Details"), "read"),
                                (T("Series Summary"),"series_summary/"),
                                (T("Series Graph"),"series_graph/"),
                                (T("Series Map"),"series_map/"),
                               ]
                        
                    rheader_tabs = s3_rheader_tabs(r, tabs)
    
                    completeTable = db["survey_complete"]
                    query = (completeTable.series_id == record.id)
                    row = db(query).count()
                    tsection = TABLE(_class="survey-complete-list")
                    lblSection = T("Completed surveys of this Series:")
                    if (row == 0):
                        rsection = SPAN(T("As of yet, no completed surveys have been added to this series."))
                    else:
                        rsection = TR(TH(lblSection), TD(row))
                    tsection.append(rsection)
                            
    
                    rheader = DIV(TABLE(
                                  TR(
                                     TH("%s: " % T("Name")),
                                     record.name,
                                     TH("%s: " % T("Status")),
                                     survey_series_status[record.status],
                                     ),
                                      ),
                                  tsection,
                                  rheader_tabs)
                    return rheader
            return None


    
        # Response

        def survey_build_series_summary(series_id):
            table = TABLE(_id="series_summary",
                          _class="dataTable display")
            hr = TR(TH(T("Position")),
                    TH(T("Code")),
                    TH(T("Question")),
                    TH(T("Type")),
# removed upon request                    TH(T("Completed")),
                    TH(T("Summary"))
                   )
            header = THEAD(hr)

            questions = getAllQuestionsForSeries(series_id)
            line = []
            body = TBODY()
            for question in questions:
                question_id = question["qstn_id"]
                widget = survey_question_type[question["type"]](question_id)
                br = TR()
                br.append(question["posn"])
                br.append(question["code"])
                br.append(question["name"])
                type = widget.type_represent()
                answers = getAllAnswersForQuestionInSeries(question_id,
                                                           series_id)
                analysisTool = survey_analysis_type[question["type"]](question_id,
                                                                      answers)
                chart = analysisTool.chartButton()
                cell = TD()
                cell.append(type)
                if chart:
                    cell.append(chart)
                br.append(cell)
# removed upon request                br.append(analysisTool.count())
                analysisTool.count()
                br.append(analysisTool.summary())
                
                body.append(br)
                
            table.append(header)
            table.append(body)

            # turn off server side pagination
            response.s3.no_sspag = True
            # send the id of the table
            response.s3.dataTableID = "series_summary"
            # turn multi-select on
            response.s3.dataTableSelectable = True
            response.s3.dataTablePostMethod = True
            response.s3.dataTableSubmitLabel = current.T("Show selected answers")
            series = INPUT(_type="hidden", _id="selectSeriesID", _name="series",
                        _value="%s" % series_id)
            mode = INPUT(_type="hidden", _id="importMode", _name="mode",
                         _value="Inclusive")
            selected = INPUT(_type="hidden", _id="importSelected",
                             _name="selected", _value="")
            form = FORM(table, series, mode, selected)
            return form

        # Section as component of Template

        def getAllAnswersForQuestionInSeries(question_id, series_id):
            """
                function to return all the answers for a given question
                from with a specified series
            """
            ctable = db.survey_complete
            atable = db.survey_answer
            query = db((atable.question_id == question_id) & \
                       (atable.complete_id == ctable.id) & \
                       (ctable.series_id == series_id)
                      )
            rows = query.select(atable.id,
                                atable.value,
                                atable.complete_id,
                               )
            answers = []
            for row in rows:
                answer = {}
                answer["answer_id"] = row.id
                answer["value"] = row.value
                answer["complete_id"] = row.complete_id
                answers.append(answer)
            return answers

        def survey_getLocationQuestionsIDForSeries(series_id):
            templateRec = getTemplateFromSeries(series_id)
            if templateRec != None:
                locationQstnCode = templateRec["location_qstn"]
                question = survey_getQuestionFromCode(locationQstnCode, series_id)
                return question["qstn_id"]
            else:
                return None

        def getPriorityQuestionForSeries(series_id):
            templateRec = getTemplateFromSeries(series_id)
            if templateRec != None:
                priorityQstnCode = templateRec["priority_qstn"]
                question = survey_getQuestionFromCode(priorityQstnCode, series_id)
                return question
            else:
                return None


        def survey_answerlist_dataTable_pre():
            # The answer list has been removed for the moment. Currently it
            # displays all answers for a summary it would be better to 
            # be able to display just a few select answers 
            list_fields = ["created_on", "series_id", ]#"answer_list"]
            s3mgr.configure("survey_complete", list_fields=list_fields)

        def survey_serieslist_dataTable_post(r):
            s3_action_buttons(r)
            if auth.s3_has_permission("create", tablename):
                url = URL(c=module,
                          f="newAssessment",
                          vars={"viewing":"survey_series.[id]"}
                         )
            else:
                url = URL(c=module,
                          f="series",
                          args=["[id]/read"]
                         )
            response.s3.actions = [
                                   dict(label=str(T("Open")),
                                        _class="action-btn",
                                        url=url
                                       ),
# Removed project log 29
#                                   dict(label=str(T("Analysis")),
#                                        _class="action-btn",
#                                        url=URL(c=module,
#                                                f="series_summary",
#                                                args=["[id]"])
#                                       ),
#                                   dict(label=str(T("Excel")),
#                                        _class="action-btn",
#                                        url=URL(c=module,
#                                                f="series_export",
#                                                args=["[id]"])
#                                       ),
                                  ]

        def survey_answerlist_dataTable_post(r):
            s3_action_buttons(r)
            response.s3.actions = [
                                   dict(label=str(T("Open")),
                                        _class="action-btn",
                                        url=URL(c=module,
                                                f="series",
                                                args=[r.id,"complete","[id]","update"])
                                       ),
# Doesn't do anything at the moment so removed
#                                   dict(label=str(T("Analysis")),
#                                        _class="action-btn",
#                                        url=URL(c=module,
#                                                f="analysis",
#                                                args=["[id]"])
#                                       ),
                                  ]


        def survey_build_completed_list(series_id, question_id_list):
            table = TABLE(_id="completed_list",
                          _class="dataTable display")
            hr = TR()
            for question_id in question_id_list:
                qtable = db.survey_question
                query = (qtable.id == question_id)
                question = db(query).select(qtable.name,
                                            limitby=(0, 1)).first()
                hr.append(TH(question.name))
            header = THEAD(hr)

            body = TBODY()
            matrix = {}
            for question_id in question_id_list:
                answers = getAllAnswersForQuestionInSeries(question_id,
                                                           series_id)
                for answer in answers:
                    complete_id = answer["complete_id"]
                    data = {question_id: answer["value"]}
                    if complete_id in matrix:
                        matrix[complete_id].update(data)
                    else:
                        matrix.update({complete_id:data})

            for row in matrix.values():
                br = TR()
                for question_id in question_id_list:
                    if question_id in row:
                        br.append(TD(row[question_id]))
                    else:
                        br.append(TD(""))
                body.append(br)

            table.append(header)
            table.append(body)
            # turn off server side pagination
            response.s3.no_sspag = True
            # send the id of the table
            response.s3.dataTableID = "completed_list"
            return table
        
        def complete_rheader(r, tabs=[]):
            # This doesn't work because it loses the series id details
#            if r.representation == "html":
#                # Tabs
#                if auth.s3_has_permission("create", "survey_series"):
#                    tabs = [(T("New Assessment"), "newAssessment/"),
#                            (T("Completed Assessments"), "complete"),
#                            (T("Series Details"), "read"),
#                            (T("Series Summary"),"series_summary/"),
#                            (T("Series Graph"),"series_analysis/"),
#                            (T("Series Map"),"series_map/"),
#                            ]
#                else:
#                    tabs = [(T("Series Details"), "read"),
#                            (T("Series Summary"),"series_summary/"),
#                            (T("Series Graph"),"series_analysis/"),
#                            (T("Series Map"),"series_map/"),
#                           ]
#                    
#                rheader_tabs = s3_rheader_tabs(r, tabs)
#                rheader = DIV(rheader_tabs)
#                return rheader
            return None

        def importAnswers(id, list):
            """
                private function used to save the answer_list stored in
                survey_complete into answer records held in survey_answer
            """
            answer = []
            lines = list.splitlines(True)
            for line in lines:
                answer.append(u'"%s",%s' % (id,line))
            from tempfile import TemporaryFile
            csv = TemporaryFile()
            csv.write(u'"complete_id","question_code","value"\n')
            csv.writelines(answer)
            csv.seek(0)
            xsl = os.path.join("applications",
                               request.application,
                               "static",
                               "formats",
                               "s3csv",
                               "survey",
                               "answer.xsl")
            resource = s3mgr.define_resource("survey", "answer")
            resource.import_xml(csv, stylesheet = xsl, format="csv",)

        #**********************************************************************
        # Functions not currently used
        #**********************************************************************
        def survey_section_select_widget(template_id):
            """
                This will create two list
                The first consists of sections that have been selected for the template
                The second consists of sections that belong to the master template and can thus be selected 
            """
            templateTable = db.survey_template
            sectionTable = db.survey_section
            selectSections = []
            clonedSection = {}
            masterSections = UL()
            selectMasterSections = UL()
            accordian = False
    
            if template_id == None:
                selectquery = db(sectionTable.template_id > 0)
            else:
                selectquery = db(sectionTable.template_id == template_id)
            selected = selectquery.select(orderby = sectionTable.posn)
            for section in selected:
                selectSections.append([section.id, section.name])
                clonedSection[section.cloned_section_id]=True
            sectionDroppable = addContainerForDroppableElements(selectSections,
                                                                "Selected Sections",
                                                                "template_sections",
                                                                "Drag a section here"
                                                                )
    
            masterquery = db((sectionTable.template_id == templateTable.id) 
                        & (templateTable.name == "Master"))
            master = masterquery.select(orderby = sectionTable.posn)
            for section in master:
                name = section.survey_section.name
                id = section.survey_section.id
                if section.survey_section.id in clonedSection:
                    selectMasterSections.append([id,name])
                else:
                    masterSections.append([id,name])
            dict = {"Available":masterSections,"Selected":selectMasterSections}
            masterDraggable = addContainerForDraggableElements(dict,
                                                               "Master Sections",
                                                               "master_sections",
                                                               accordian)
            
            script = addDragnDropSrcipt("master_sections",
                                        "template_sections",
                                        template_id,
                                        accordian)
            sections = TABLE(TR(TH(T("Existing Sections")),
                                TH(T("Sections that can be selected"))
                               ),
                             TR(TD(sectionDroppable, _style="vertical-align:top;"),
                                TD(masterDraggable, _style="vertical-align:top;")
                               )
                            )
            sections.append(script)
            
            # Test area
            widget = S3QuestionTypeTextWidget()
            #sections.append(widget("display", question_id=2))
            # end of test area
            return sections

        """
            Basic functions to enable drap & drop
            @todo Make generic and move to s3widgets
        """
        def addContainerForDraggableElements(dict, title, id, accordian=False):
            """
                @param dict:a dictionary of lists, the key is the title of the list
                            the value is a list of records, each record consists of 
                            the unique id and the display representation
                @param title: the title that will appear at the top of the widget
                @param id: the html id for this widget  
            """
            container = DIV( _id=id)
            container.append(H1(title, _class="ui-widget-header"))
            temp = container
            if accordian:
                temp = DIV(_id="accordian_%s"%id)
                container.append(temp)
            for (key, list) in dict.items():
                if accordian:
                    temp.append(H3(A(key,_href="#")))
                else:
                    temp.append(H3(key))
                ulist = UL()
                temp.append(DIV(ulist))
                for element in list:
                    id = element[0]
                    name = element[1]
                    ulist.append(LI(name, _var=id))
            return container
    
        def addContainerForDroppableElements(list, title, id, emptyMsg="Drop your item here"):
            """
                @param list:a list of records in the drop zone, each record consists 
                            of the unique id and the display representation
                @param title: the title that will appear at the top of the widget
                @param id: the html id for this widget  
            """
            container = DIV( _id=id)
            container.append(H1(title, _class="ui-widget-header"))
            container.append(H3("Included"))
            contained = DIV(_class="ui-widget-container")
            container.append(contained)
            contained_list = OL() 
            contained.append(contained_list)
            if len(list) == 0:
                contained_list.append(LI(emptyMsg, _class="placeholder"))
            else:
                for element in list:
                    id = element[0]
                    name = element[1]
                    contained_list.append(LI(name, _var=id))
            return container
    
        def addDragnDropSrcipt(dragid,dropid,parent_id, accordian=False):
            """
            @todo: add the code to implement the accordion
                   hard coded url with eden it it eek, where's the cheese
                   $( "#accordian_%s" ).accordion();
            """
            accordianText = ""
            if accordian:
                accordianText = "$( '#accordian_%s' ).accordion();" % dragid
            script = """
        $(function() {
          $(document).ready(function() {
            %s
            $( '#%s li' ).draggable({
                appendTo: 'body',
                helper: 'clone'
            });
            $( '#%s ol' ).droppable({
                activeClass: 'ui-state-default',
                hoverClass: 'ui-state-hover',
                accept: ':not(.ui-sortable-helper)',
                drop: function( event, ui ) {
                    $.post(
                        'eden/survey/template/%s/section',
                        {section_id: ui.draggable.attr('var'),
                         section_text: ui.draggable.text(),
                         parent_id: %s,
                         action: "section"
                        }
                    );
                    $( this ).find( '.placeholder' ).remove();
                    $( '<li></li>' ).text( ui.draggable.text() ).appendTo( this );
                }
            });
          });
        });
        """ % (accordianText, dragid, dropid, parent_id, parent_id)
    
            return SCRIPT(script)

        # Pass variables back to global scope (response.s3.*)

        return_dict = dict(
            survey_updateMetaData = updateMetaData,
            survey_getSeriesName = getSeriesName,
            survey_getAllSeries = getAllSeries,
            survey_getAllQuestionsForSeries = getAllQuestionsForSeries,
            survey_buildQuestionnaireFromTemplate = buildQuestionnaireFromTemplate,
            survey_buildQuestionnaireFromSeries = buildQuestionnaireFromSeries,
            survey_buildQuestionnaire = buildQuestionnaire,

            survey_template_rheader = survey_template_rheader,
            survey_build_template_summary = survey_build_template_summary,
            survey_section_rheader = survey_section_rheader,
            survey_series_rheader = survey_series_rheader,
            survey_build_series_summary = survey_build_series_summary,
            survey_section_select_widget = survey_section_select_widget,
            survey_complete_rheader = complete_rheader,
            survey_answerlist_dataTable_pre = survey_answerlist_dataTable_pre,
            survey_answerlist_dataTable_post = survey_answerlist_dataTable_post,
            survey_serieslist_dataTable_post = survey_serieslist_dataTable_post,
            survey_save_answers_for_series = survey_save_answers_for_series,
            survey_build_completed_list = survey_build_completed_list,
            survey_save_answers_for_complete = survey_save_answers_for_complete,
            survey_getAllAnswersForQuestionInSeries = getAllAnswersForQuestionInSeries,
            survey_getLocationQuestionsIDForSeries = survey_getLocationQuestionsIDForSeries,
            survey_getPriorityQuestionForSeries = getPriorityQuestionForSeries,
            survey_get_series_questions = survey_get_series_questions,
            survey_get_series_questions_of_type = survey_get_series_questions_of_type,
            survey_getQuestionFromCode = survey_getQuestionFromCode,
            survey_getQuestionFromName = survey_getQuestionFromName,
            )

        return return_dict

    # Provide a handle to this load function
    s3mgr.loader(survey_tables,
                 "survey_template",
                 "survey_section",
                 "survey_question_list",
                 "survey_question",
                 "survey_question_metadata",
                 "survey_series",
                 "survey_complete",
                 "survey_answer",
                 )

    def survey_template_duplicate(job):
        """
          This callback will be called when importing series records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_template":
            table = job.table
            name = "name" in job.data and job.data.name

        query =  table.name.lower().like('%%%s%%' % name.lower())
        _duplicate = db(query).select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_section_duplicate(job):
        """
          This callback will be called when importing series records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
           - and the same template
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_section":
            table = job.table
            name = "name" in job.data and job.data.name
            template = "template" in job.data and job.data.template_id

        query =  table.name.lower().like('%%%s%%' % name.lower())
        _duplicate = db(query).select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_question_duplicate(job):
        """
          This callback will be called when importing question records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for the question code
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_question":
            table = job.table
            code = "code" in job.data and job.data.code
        _duplicate = db(table.code == code).select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_question_metadata_duplicate(job):
        """
          This callback will be called when importing question_metadata records
          it will look to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for the question_id and descriptor
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_question_metadata":
            table = job.table
            question = "question_id" in job.data and job.data.question_id
            descriptor  = "descriptor" in job.data and job.data.descriptor
        query =  db((table.descriptor==descriptor) &  (table.question_id==question))
        _duplicate = query.select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_question_list_duplicate(job):
        """
          This callback will be called when importing question_list records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - The template_id, question_id and section_id are the same
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_question_list":
            table = job.table
            tid = "template_id" in job.data and job.data.template_id
            qid = "question_id" in job.data and job.data.question_id
            sid = "section_id" in job.data and job.data.section_id

        query =  db((table.template_id==tid) & (table.question_id==qid) & (table.section_id==sid))
        _duplicate = query.select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_series_duplicate(job):
        """
          This callback will be called when importing series records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_series":
            table = job.table
            name = "name" in job.data and job.data.name

        query =  table.name.lower().like('%%%s%%' % name.lower())
        _duplicate = db(query).select(table.id,
                                      limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_complete_duplicate(job):
        """
          This callback will be called when importing series records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for a record with the same name, answer_list
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_complete":
            table = job.table
            answers = "answer_list" in job.data and job.data.answer_list

        query =  table.answer_list == answers
        try:
            _duplicate = db(query).select(table.id, limitby=(0, 1)).first()
        except:
            # if this is part of an import then the select will throw an error
            # if the question code doesn't exist.
            # This can happen during an import if the wrong file is used.
            return 

        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    def survey_answer_duplicate(job):        
        """
          This callback will be called when importing series records it will look
          to see if the record being imported is a duplicate.
    
          @param job: An S3ImportJob object which includes all the details
                      of the record being imported
    
          If the record is a duplicate then it will set the job method to update
    
          Rules for finding a duplicate:
           - Look for a record with the same complete_id and question_id
        """
        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "survey_answer":
            table = job.table
            qid = "question_id" in job.data and job.data.question_id
            rid = "complete_id" in job.data and job.data.complete_id

        query = db((table.question_id==qid) & (table.complete_id==rid))
        _duplicate = query.select(table.id, limitby=(0, 1)).first()
        if _duplicate:
            job.id = _duplicate.id
            job.data.id = _duplicate.id
            job.method = job.METHOD.UPDATE

    # De-duplicate resolvers
    s3mgr.configure("survey_answer", resolve=survey_answer_duplicate)
    s3mgr.configure("survey_complete", resolve=survey_complete_duplicate)
    s3mgr.configure("survey_question_list", resolve=survey_question_list_duplicate)
    s3mgr.configure("survey_question_metadata", resolve=survey_question_metadata_duplicate)
    s3mgr.configure("survey_question", resolve=survey_question_duplicate)
    s3mgr.configure("survey_template", resolve=survey_template_duplicate)
    s3mgr.configure("survey_section", resolve=survey_section_duplicate)
    s3mgr.configure("survey_series", resolve=survey_series_duplicate)
