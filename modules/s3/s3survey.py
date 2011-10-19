# -*- coding: utf-8 -*-

"""
    Custom UI Widgets used by the survey application

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""
import sys
import math

from gluon.sqlhtml import *
from gluon import *

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Survey: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

try:
    # NOTE matplotlib requires a directory to write temp files to.
    #      If it is unable to create or write to this directory
    #      then it will raise a RunTimeError.
    import matplotlib
    # need to set up the back end before importing pyplot
    try:
        if matplotlib.backends.backend == "agg":
            pass
    except:
        matplotlib.use('Agg')
    import numpy as np
    import matplotlib.pyplot as plt
    from pylab import savefig
except ImportError:
    print >> sys.stderr, "S3 Debug: S3Survey: matplotlib Library not installed"

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

# Used when building the spreadsheet
COL_WIDTH_MULTIPLIER = 240

def splitMetaArray (array, length=None):
    """
        Function that will convert a metadata array from its string
        representation to a valid Python list
        
        If the optional length argument is provided then the list must 
        be of this length otherwise None is returned 
    """
    array = array.strip("| ")
    valueList = array.split("|")
    if length != None and len(valueList) != length:
        return None
    result = []
    for value in valueList:
        result.append(value.strip())
    return result

def splitMetaMatrix (matrix, rows= None, columns=None):
    """
        Function that will convert a metadata matrix from its string
        representation to a valid Python list of list

        If the optional rows argument is provided then the list must 
        have this number of rows otherwise None is returned 

        If the optional columns argument is provided then each row must 
        have this number of columns otherwise that row will be ignored 
    """
    result = []
    rowList = matrix.split("*")
    if rows != None and len(rowList) != rows:
        return None
    for row in rowList:
        row = splitMetaArray(row, columns)
        if row != None:
            result.append(row)
    return result


# Question Types
def survey_stringType(question_id = None):
    return S3QuestionTypeStringWidget(question_id)
def survey_textType(question_id = None):
    return S3QuestionTypeTextWidget(question_id)
def survey_numericType(question_id = None):
    return S3QuestionTypeNumericWidget(question_id)
def survey_dateType(question_id = None):
    return S3QuestionTypeDateWidget(question_id)
def survey_optionType(question_id = None):
    return S3QuestionTypeOptionWidget(question_id)
def survey_ynType(question_id = None):
    return S3QuestionTypeOptionYNWidget(question_id)
def survey_yndType(question_id = None):
    return S3QuestionTypeOptionYNDWidget(question_id)
def survey_optionOtherType(question_id = None):
    return S3QuestionTypeOptionOtherWidget(question_id)
def survey_locationType(question_id = None):
    return S3QuestionTypeLocationWidget(question_id)
def survey_linkType(question_id = None):
    return S3QuestionTypeLinkWidget(question_id)
def survey_ratingType(question_id = None):
    pass
def survey_gridType(question_id = None):
    return S3QuestionTypeGridWidget(question_id)
def survey_gridChildType(question_id = None):
    return S3QuestionTypeGridChildWidget(question_id)

survey_question_type = {
    "String": survey_stringType,
    "Text": survey_textType,
    "Numeric": survey_numericType,
    "Date": survey_dateType,
    "Option": survey_optionType,
    "YesNo": survey_ynType,
    "YesNoDontKnow": survey_yndType,
    "OptionOther": survey_optionOtherType,
    "Location": survey_locationType,
    "Link" : survey_linkType,
#    "Rating": survey_ratingType,
    "Grid" : survey_gridType,
    "GridChild" : survey_gridChildType,
}

##########################################################################
# Class S3QuestionTypeAbstractWidget
##########################################################################
class S3QuestionTypeAbstractWidget(FormWidget):
    """
        Abstract Question Type widget

        A QuestionTypeWidget can have three basic states:

        The first is as a descriptor for the type of question.
        In this state it will hold the information about what this type of
        question may look like.

        The second state is when it is associated with an actual question
        on the database. Then it will additionally hold information about what
        this actual question looks like.

        The third state is when the widget of an actual question is
        associated with a single answer to that question. If that happens then
        the self.question record from the database is extended to hold
        the actual answer and the complete_id of that answer.

        For example: A numeric question type has a metadata value of "Format"
        this can be used to describe how the data could be formatted to
        represent a number. When this question type is associated with an
        actual numeric question then the metadata might be "Format" : n, which
        would mean that it is an integer value.

        The general instance variables:

        @ivar metalist: A list of all the valid metadata descriptors. This would
                        be used by a UI when designing a question
        @ivar attr: Any HTML/CSS attributes passed in by the call to display
        @ivar webwidget: The web2py widget that should be used to display the
                         question type
        @ivar typeDescription: The description of the type when it is displayed
                               on the screen such as in reports 

        The instance variables when the widget is associated with a question:

        @ivar id: The id of the question from the survey_question table
        @ivar question: The question record from the database.
                        Note this variable can be extended to include the
                        answer taken from the complete_id, allowing the
                        question to hold a single answer. This is needed when
                        updating responses.
        @ivar qstn_metadata: The actual metadata for this question taken from
                             the survey_question_metadata table and then
                             stored as a descriptor value pair
        @ivar field: The field object from metadata table, which can be used
                     by the widget to add additional rules (such as a requires)
                     before setting up the UI when inputing data

        @author: Graeme Foster (graeme at acm dot org)

    """

    def __init__(self,
                 question_id
                ):
        self.ANSWER_VALID = 0
        self.ANSWER_MISSING = 1
        self.ANSWER_PARTLY_VALID = 2
        self.ANSWER_INVALID = 3

        T = current.T
        db = current.db
        # The various database tables that the widget may want access to
        self.qtable = db.survey_question
        self.mtable = db.survey_question_metadata
        self.qltable = db.survey_question_list
        self.ctable = db.survey_complete
        self.atable = db.survey_answer
        # the general instance variables
        self.metalist = ["Help message"]
        self.attr = {}
        self.webwidget = StringWidget
        self.typeDescription = None
        # The instance variables when the widget is associated with a question
        self.id = question_id
        self.question = None
        self.qstn_metadata = {}
        # Initialise the metadata from the question_id
        self._store_metadata()
        self.field = self.mtable.value

    def _store_metadata(self, qstn_id=None, update=False):
        """
            This will store the question id in self.id,
            the question data in self.question, and
            the metadata for this specific question in self.qstn_metadata

            It will only get the data from the db if it hasn't already been
            retrieved, or if the update flag is True
        """
        if qstn_id != None:
            if self.id != qstn_id:
                self.id = qstn_id
                # The id has changed so force an update
                update = True
        if self.id == None:
            self.question = None
            self.qstn_metadata = {}
            return
        if self.question == None or update:
            db = current.db
            # Get the question from the database
            query = (self.qtable.id == self.id)
            self.question = db(query).select(limitby=(0, 1)).first()
            if self.question == None:
                raise Exception("no question with id %s in database" % self.id)
            # Get the metadata from the database and store in qstn_metadata
            query = (self.mtable.question_id == self.id)
            self.rows = db(query).select()
            for row in self.rows:
                self.qstn_metadata[row.descriptor] = row.value

    def get(self, value, default=None):
        """
            This will return a metadata value held by the widget
        """
        if value in self.qstn_metadata:
            return self.qstn_metadata[value]
        else:
            return default

    def getAnswer(self):
        """
            Return the value of the answer for this question
        """
        if "answer" in self.question:
            answer = self.question.answer
        else:
            answer = ""
        return answer

    def loadAnswer(self, complete_id, question_id, forceDB=False):
        """
            This will return a value held by the widget
            The value can be held in different locations
            1) In the widget itself:
            2) On the database: table.survey_complete
        """
        value = None
        self._store_metadata(question_id)
        if "answer" in self.question and \
           self.question.complete_id == complete_id and \
           forceDB == False:
            answer = self.question.answer
        else:
            query = (self.atable.complete_id == complete_id) & \
                    (self.atable.question_id == question_id)
            row = current.db(query).select(limitby=(0, 1)).first()
            if row != None:
                value = row.value
                self.question["answer"] = value
                self.question["complete_id"] = complete_id
        return value

    def initDisplay(self, **attr):
        """
            This method set's up the variables that will be used by all
            display methods of fields for the question type.
            It uses the metadata to define the look of the field
        """
        if "question_id" in attr:
            self.id = attr["question_id"]
        if self.id == None:
            raise Exception("Need to specify the question_id for this QuestionType")
        qstn_id = self.id
        self._store_metadata(qstn_id)
        attr["_name"] = self.question.code
        self.attr = attr

    def display(self, **attr):
        """
            This displays the widget on a web form. It uses the layout
            function to control how the widget is displayed
        """
        self.initDisplay(**attr)
        value = self.getAnswer()
        input = self.webwidget.widget(self.field, value, **self.attr)
        return self.layout(self.question.name, input, **attr)

    def layout(self, label, widget, **attr):
        """
            This lays the label widget that is passed in on the screen.

            Currently it has a single default layout mechanism but in the
            future it will be possible to add more which will be controlled
            vis the attr passed into display and stored in self.attr
        """
        if "display" in attr:
            display = attr["display"]
        else:
            display = "Default"
        if display == "Default":
            elements = []
            elements.append(TR(TH(label),TD(widget),_class="survey_question"))
            return TAG[""](elements)
        elif display == "Control Only":
            return TD(widget)

    def type_represent(self):
        """
            Display the type in a DIV for displayiong on the screen
        """
        return DIV(self.typeDescription, _class="surveyWidgetType")

    def wrapText(self, sheet, row, col, text, width, style):
            # Wrap text and calculate the row width and height
            characters_in_cell = float(width)
            twips_per_row = 255 #default row height for 10 point font
            rows = math.ceil(len(unicode(text)) / characters_in_cell)
            new_row_height = int(rows * twips_per_row)
            new_col_width = characters_in_cell * COL_WIDTH_MULTIPLIER
            sheet.write(row, col, unicode(text), style=style)
            sheet.row(row).height = new_row_height 
            sheet.col(col).width = new_col_width

    def writeToSpreadsheet(self, sheet, row, col, styleText, styleHeader, styleInput, styleBox, controlOnly=False):
        """
            Function to write out basic details to a spreadsheet
        """
        self._store_metadata()
        if controlOnly:
            sheet.write(row, col, "", style=styleInput)
            col += 1
        else:
            self.wrapText(sheet, row, col, self.question["name"], 25.0, styleText)
            sheet.write(row, col+1, "", style=styleInput)
            col += 2
        row += 1
        return (row, col)

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget

            NOTE: Not currently used but will be used when the UI supports the
                  validation of data entered in to the web form
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = value(valueList, 0)
        if data == None:
            return self.ANSWER_MISSING
        length = self.get("Length")
        if length != None and length(data) > length:
            return ANSWER_PARTLY_VALID
        return self.ANSWER_VALID

    def metadata(self, **attr):
        """
            Create the input fields for the metadata for the QuestionType

            NOTE: Not currently used but will be used when the UI supports the
                  creation of the template and specifically the questions in
                  the template 
        """
        if "question_id" in attr:
            self._store_metadata(attr["question_id"])
        elements = []
        for fieldname in self.metalist:
            value = self.get(fieldname, "")
            input = StringWidget.widget(self.field, value, **attr)
            elements.append(TR(TD(fieldname), TD(input)))
        return TAG[""](elements)


##########################################################################
# Class S3QuestionTypeTextWidget
##########################################################################
class S3QuestionTypeTextWidget(S3QuestionTypeAbstractWidget):
    """
        Text Question Type widget

        provides a widget for the survey module that will manage plain
        text questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """

    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.webwidget = TextWidget
        self.typeDescription = T("Long Text")

##########################################################################
# Class S3QuestionTypeStringWidget
##########################################################################
class S3QuestionTypeStringWidget(S3QuestionTypeAbstractWidget):
    """
        String Question Type widget

        provides a widget for the survey module that will manage plain
        string questions (text with a limited length).

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of characters

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.typeDescription = T("Short Text")

    def display(self, **attr):
        if "length" in self.qstn_metadata:
            length = self.qstn_metadata["length"]
            attr["_size"] = length
            attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

##########################################################################
# Class S3QuestionTypeNumericWidget
##########################################################################
class S3QuestionTypeNumericWidget(S3QuestionTypeAbstractWidget):
    """
        Numeric Question Type widget

        provides a widget for the survey module that will manage simple
        numerical questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The length if the number, default length of 10 characters
        Format:       Describes the makeup of the number, as follows:
                      n    integer
                      n.   floating point
                      n.n  floating point, the number of decimal places defined
                           by the number of n's that follow the decimal point

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.metalist.append("Format")
        self.typeDescription = T("Numeric") 

    def display(self, **attr):
        length = self.get("length", 10)
        attr["_size"] = length
        attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    def formattedAnswer(self, data, format=None):
        if format == None:
            format = self.get("Format", "n")
        parts = format.partition(".")
        if parts[1] == "": # No decimal point so must be a whole number
            return int(data)
        else:
            result = float(data)
            if parts[2] == "": # No decimal places specified
                return result
            else:
                return round(result, len(parts[2]))


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

##########################################################################
# Class S3QuestionTypeDateWidget
##########################################################################
class S3QuestionTypeDateWidget(S3QuestionTypeAbstractWidget):
    """
        Date Question Type widget

        provides a widget for the survey module that will manage simple
        date questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Date")

    def display(self, **attr):
        length = 30
        attr["_size"] = length
        attr["_maxlength"] = length
        return S3QuestionTypeAbstractWidget.display(self, **attr)

    def formattedAnswer(self, data):
        """
            This will take a string and do it's best to return a Date object
            It will try the following in order
            * Convert using the ISO format:
            * look for a month in words a 4 digit year and a day (1 or 2 digits)
            * a year and month that matches the date now and NOT a future date
            * a year that matches the current date and the previous month
        """
        rawDate = data
        date = None
        try:
            # First convert any none numeric to a hyphen
            isoDate = ""
            addHyphen = False
            for char in rawDate:
                if char.isdigit:
                    if addHyphen == True and isoDate != "":
                        iscDate += "-"
                    isoDate += char
                    addHyphen = False
                else:
                    addHyphen = True
            # @ToDo: Use deployment_settings.get_L10n_date_format()
            date = datetime.strptime(rawDate, "%Y-%m-%d")
            return date
        except ValueError:
            try:
                for month in monthList:
                    if month in rawDate:
                        search = re,search("\D\d\d\D", rawDate)
                        if search:
                            day = search.group()
                        else:
                            search = re,search("^\d\d\D", rawDate)
                            if search:
                                day = search.group()
                            else:
                                search = re,search("\D\d\d$", rawDate)
                                if search:
                                    day = search.group()
                                else:
                                    search = re,search("\D\d\D", rawDate)
                                    if search:
                                        day = "0" + search.group()
                                    else:
                                        search = re,search("^\d\D", rawDate)
                                        if search:
                                            day = "0" + search.group()
                                        else:
                                            search = re,search("\D\d$", rawDate)
                                            if search:
                                                day = "0" + search.group()
                                            else:
                                                raise ValueError
                        search = re,search("\D\d\d\d\d\D", rawDate)
                        if search:
                            year = search.group()
                        else:
                            search = re,search("^\d\d\d\d\D", rawDate)
                            if search:
                                year = search.group()
                            else:
                                search = re,search("\D\d\d\d\d$", rawDate)
                                if search:
                                    year = search.group()
                                else:
                                    raise ValueError
                    # @ToDo: Use deployment_settings.get_L10n_date_format()
                    testDate = "%s-%s-%s" % (day, month, year)
                    if len(month) == 3:
                        format == "%d-%b-%Y"
                    else:
                        format == "%d-%B-%Y"
                    date = datetime.strptime(format, testDate)
                    return date
            except ValueError:
                return date


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

##########################################################################
# Class S3QuestionTypeOptionWidget
##########################################################################
class S3QuestionTypeOptionWidget(S3QuestionTypeAbstractWidget):
    """
        Option Question Type widget

        provides a widget for the survey module that will manage simple
        option questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        T = current.T
        self.metalist.append("Length")
        self.webwidget = RadioWidget
        self.typeDescription = T("Option") 

    def display(self, **attr):
        S3QuestionTypeAbstractWidget.initDisplay(self, **attr)
        self.field.requires = IS_IN_SET(self.getList())
        value = self.getAnswer()
        self.field.name = self.question.code
        input = RadioWidget.widget(self.field, value, **self.attr)
        self.field.name = "value"
        return self.layout(self.question.name, input, **attr)

    def getList(self):
        list = []
        length = self.get("Length")
        if length == None:
            raise Exception("Need to have the options specified")
        for i in range(int(length)):
            list.append(self.get(str(i+1)))
        return list

    def writeToSpreadsheet(self, sheet, row, col, styleText, styleHeader, styleInput, styleBox, controlOnly=False):
        """
            Function to write out basic details to a spreadsheet
        """
        self._store_metadata()
        if controlOnly:
            sheet.write(row, col, "", style=styleInput)
            col += 1
        else:
            self.wrapText(sheet, row, col, self.question["name"], 25.0, style=styleHeader)
            list = self.getList()
            for option in list:
                self.wrapText(sheet, row, col+1, option, 12.5, style=styleText)
                sheet.write(row, col+2, "", style=styleInput)
                row += 1
        return (row, col)

    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        if len(valueList) == 0:
            return self.ANSWER_MISSING
        data = valueList[0]
        if data == None:
            return self.ANSWER_MISSING
        self._store_metadata(qstn_id)
        if data in self.getList():
            return self.ANSWER_VALID
        else:
            return self.ANSWER_VALID
        return self.ANSWER_INVALID

##########################################################################
# Class S3QuestionTypeOptionYNWidget
##########################################################################
class S3QuestionTypeOptionYNWidget(S3QuestionTypeOptionWidget):
    """
        YN Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.typeDescription = T("Yes, No")
        self.qstn_metadata["Length"] = 2

    def getList(self):
        T = current.T
        return [T("Yes"), T("No")]


##########################################################################
# Class S3QuestionTypeOptionYNDWidget
##########################################################################
class S3QuestionTypeOptionYNDWidget(S3QuestionTypeOptionWidget):
    """
        Yes, No, Don't Know: Question Type widget

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.typeDescription = T("Yes, No, Don't Know")
        self.qstn_metadata["Length"] = 3

    def getList(self):
        T = current.T
        return [T("Yes"), T("No"), T("Don't Know")]


##########################################################################
# Class S3QuestionTypeOptionOtherWidget
##########################################################################
class S3QuestionTypeOptionOtherWidget(S3QuestionTypeOptionWidget):
    """
        Option Question Type widget with a final other option attached 

        provides a widget for the survey module that will manage simple
        yes no questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Length:       The number of options
        #:            A number one for each option
        Other:        The question type the other option should be

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeOptionWidget.__init__(self, question_id)
        self.typeDescription = T("Option Other")

    def getList(self):
        T = current.T
        list = []
        length = self.get("Length")
        if length == None:
            raise Exception("Need to have the options specified")
        for i in range(int(length)):
            list.append(self.get(str(i+1)))
        list[i]=T("Other")
        return list




##########################################################################
# Class S3QuestionTypeLocationWidget
##########################################################################
class S3QuestionTypeLocationWidget(S3QuestionTypeAbstractWidget):
    """
        Location widget: Question Type widget

        provides a widget for the survey module that will link to the 
        gis_locaton table, and provide the record if a match exists.

        Available metadata for this class:
        Help message: A message to help with completing the question

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.typeDescription = T("Location")


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        if result != ANSWER_VALID:
            return result
        length = self.get("length", 10)
        format = self.get("format")
        data = value(valueList, 0)
        if format != None:
            try:
                self.formattedValue(data, format)
                return self.ANSWER_VALID
            except exceptions.ValueError:
                return self.ANSWER_INVALID

        return self.ANSWER_VALID

##########################################################################
# Class S3QuestionTypeLinkWidget
##########################################################################
class S3QuestionTypeLinkWidget(S3QuestionTypeAbstractWidget):
    """
        Link widget: Question Type widget

        provides a widget for the survey module that has a link with another
        question.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Parent: The question it links to
        Type: The type of question it really is (another question type)
        Relation: How it relates to the parent question
                  groupby: answers should be grouped by the value of the parent

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Parent")
        self.metalist.append("Type")
        self.metalist.append("Relation")
        try:
            self._store_metadata()
            type = self.get("Type")
            parent = self.get("Parent")
            if type == None or parent == None:
                self.typeDescription = T("Link")
            else:
                self.typeDescription = T("%s linked to %s") % (type, parent)
        except:
            self.typeDescription = T("Link") 

    def display(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        return realWidget.display(**attr)

    def getParentType(self):
        self._store_metadata()
        return self.get("Type")

    def getParentQstnID(self):
        db = current.db
        parent = self.get("Parent")
        query = (self.qtable.code == parent)
        row = db(query).select(limitby=(0, 1)).first()
        return row.id


    ######################################################################
    # Functions not fully implemented or used
    ######################################################################
    def validate(self, valueList, qstn_id):
        """
            This will validate the data passed in to the widget
        """
        result = S3QuestionTypeAbstractWidget.validate(self, valueList)
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        return realWidget.validate(valueList, qstn_id)

##########################################################################
# Class S3QuestionTypeGridWidget
##########################################################################
class S3QuestionTypeGridWidget(S3QuestionTypeAbstractWidget):
    """
        Grid widget: Question Type widget

        provides a widget for the survey module that hold a grid of related 
        questions.

        Available metadata for this class:
        Help message: A message to help with completing the question
        Subtitle: The text for the 1st column and 1st row of the grid
        QuestionNo: The number of the first question, used for the question code
        col-cnt:  The number of data columns in the grid
        row-cnt:  The number of data rows in the grid
        columns:  An array of headings for each data column
        rows:     An array of headings for each data row
        data:     A matrix of widgets for each data cell

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Subtitle")
        self.metalist.append("QuestionNo")
        self.metalist.append("col-cnt")
        self.metalist.append("row-cnt")
        self.metalist.append("columns")
        self.metalist.append("rows")
        self.metalist.append("data")
        self.typeDescription = T("Grid")

    def getMetaData(self, qstn_id=None):
        self._store_metadata(qstn_id=qstn_id)
        self.subtitle = self.get("Subtitle")
        self.qstnNo = int(self.get("QuestionNo",1))
        self.colCnt = self.get("col-cnt")
        self.rowCnt = self.get("row-cnt")
        self.columns = splitMetaArray(self.get("columns"))
        self.rows = splitMetaArray(self.get("rows"))
        self.data = splitMetaMatrix(self.get("data"))


    def display(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        self.getMetaData()
        table = []
        if self.data != None:
            tr = TR(_class="survey_question")
            tr.append(TH(self.subtitle))
            for col in self.columns:
                tr.append(TH(col))
            table.append(tr)
            posn = 0
            codeNum = self.qstnNo
            for row in self.data:
                tr = TR(_class="survey_question")
                tr.append(TH(self.rows[posn]))
                for cell in row:
                    if cell == "Blank":
                        tr.append("")
                    else:
                        code = "%s%s" % (self.question["code"], codeNum)
                        codeNum += 1
                        childWidget = self.getChildWidget(code)
                        tr.append(childWidget.subDisplay())
                table.append(tr)
                posn += 1
        return table

    def writeToSpreadsheet(self, sheet, row, startcol, styleText, styleHeader, styleInput, styleBox, controlOnly=False):
        self._store_metadata()
        self.getMetaData()
        col = startcol
        if self.data != None:
            sheet.write(row, col, self.subtitle, style=styleHeader)
            col = startcol
            for heading in self.columns:
                col += 1
                sheet.write(row, col, heading, style=styleHeader)
            row += 1
            posn = 0
            codeNum = self.qstnNo
            for line in self.data:
                col = startcol
                self.wrapText(sheet, row, col, self.rows[posn], 25.0, styleText)
#                sheet.write(row, col, self.rows[posn])
                col += 1
                for cell in line:
                    if cell == "Blank":
                        col += 1
                    else:
                        code = "%s%s" % (self.question["code"], codeNum)
                        codeNum += 1
                        childWidget = self.getChildWidget(code)
                        type = childWidget.get("Type")
                        realWidget = survey_question_type[type](childWidget.id)
                        (ignore, col) = realWidget.writeToSpreadsheet(sheet, row, col, styleText, styleHeader, styleInput, styleBox, True)

#                        (ignore, col) = childWidget.writeToSpreadsheet(sheet, row, col, styleText, styleHeader, styleInput, styleBox, True)
                row += 1
                posn += 1
        return (row, startcol)

    def insertChildren(self, record, metadata):
        self.id = record.id
        self.question = record
        self.qstn_metadata = metadata
        self.getMetaData()
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        type = cell
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        metadata = "(Type, %s)" % type
                        try:
                            id = self.qtable.insert(name = name,
                                                    code = code,
                                                    type = "GridChild",
                                                    metadata = metadata,
                                                   )
                        except:
                            record = self.qtable(code = code)
                            id = record.id
                            record.update_record(name = name,
                                                 code = code,
                                                 type = "GridChild",
                                                 metadata = metadata,
                                                )
                        record = self.qtable(id)
                        if self.get(code):
                            metadata = metadata + self.get(code)
                        current.manager.s3.survey_updateMetaData(record, "GridChild", metadata)

    def insertChildrenToList(self, question_id, template_id, section_id, qstn_posn):
        self.getMetaData(question_id)
        if self.data != None:
            posn = 0
            qstnNo = self.qstnNo
            qstnPosn = 1
            parent_id = self.id
            parent_code = self.question["code"]
            for row in self.data:
                name = self.rows[posn]
                posn += 1
                for cell in row:
                    if cell == "Blank":
                        continue
                    else:
                        code = "%s%s" % (parent_code, qstnNo)
                        qstnNo += 1
                        record = self.qtable(code = code)
                        id = record.id
                        try:
                            self.qltable.insert(question_id = id,
                                                template_id = template_id,
                                                section_id = section_id,
                                                posn = qstn_posn+qstnPosn,
                                               )
                            qstnPosn += 1
                        except:
                            pass # already on the database no change required
        
    def getChildWidget (self, code):
            # Get the question from the database
            query = (self.qtable.code == code)
            question = current.db(query).select(limitby=(0, 1)).first()
            if question == None:
                raise Exception("no question with code %s in database" % code)
            cellWidget = survey_question_type["GridChild"](question.id)
            return cellWidget

##########################################################################
# Class S3QuestionTypeGridChildWidget
##########################################################################
class S3QuestionTypeGridChildWidget(S3QuestionTypeAbstractWidget):
    """
        GridChild widget: Question Type widget

        provides a widget for the survey module that is held by a grid question
        type an provides a link to the true question type.

        Available metadata for this class:
        Type:     The type of question it really is (another question type)

        @author: Graeme Foster (graeme at acm dot org)
    """
    def __init__(self,
                 question_id = None
                ):
        T = current.T
        S3QuestionTypeAbstractWidget.__init__(self, question_id)
        self.metalist.append("Type")
        self.typeDescription = T("Grid Child")

    def display(self, **attr):
        return None
    
    def subDisplay(self, **attr):
        S3QuestionTypeAbstractWidget.display(self, **attr)
        type = self.get("Type")
        realWidget = survey_question_type[type]()
        return realWidget.display(question_id=self.id, display = "Control Only")

    def writeToSpreadsheet(self, sheet, row, startcol, styleText, styleHeader, styleInput, styleBox, controlOnly=False):
        return (row, startcol)

###############################################################################
###  Classes for analysis
###    will work with a list of answers for the same question
###############################################################################

# Analysis Types
def analysis_stringType(question_id,answerList):
    return S3StringAnalysis(question_id,answerList)
def analysis_textType(question_id,answerList):
    return S3TextAnalysis(question_id,answerList)
def analysis_numericType(question_id,answerList):
    return S3NumericAnalysis(question_id,answerList)
def analysis_dateType(question_id,answerList):
    return S3DateAnalysis(question_id,answerList)
def analysis_optionType(question_id,answerList):
    return S3OptionAnalysis(question_id,answerList)
def analysis_ynType(question_id,answerList):
    return S3OptionYNAnalysis(question_id,answerList)
def analysis_yndType(question_id,answerList):
    return S3OptionYNDAnalysis(question_id,answerList)
def analysis_optionOtherType(question_id,answerList):
    return S3OptionOtherAnalysis(question_id,answerList)
def analysis_locationType(question_id,answerList):
    return S3LocationAnalysis(question_id,answerList)
def analysis_linkType(question_id,answerList):
    return S3LinkAnalysis(question_id,answerList)
def analysis_gridType(question_id,answerList):
    return S3GridAnalysis(question_id,answerList)
def analysis_gridChildType(question_id,answerList):
    return S3GridChildAnalysis(question_id,answerList)
#def analysis_ratingType(answerList):
#    return S3RatingAnalysis(answerList)
#    pass

survey_analysis_type = {
    "String": analysis_stringType,
    "Text": analysis_textType,
    "Numeric": analysis_numericType,
    "Date": analysis_dateType,
    "Option": analysis_optionType,
    "YesNo": analysis_ynType,
    "YesNoDontKnow": analysis_yndType,
    "OptionOther": analysis_optionOtherType,
    "Location": analysis_locationType,
    "Link": analysis_linkType,
    "Grid": analysis_gridType,
    "GridChild" : analysis_gridChildType,
#    "Rating": analysis_ratingType,
}

class S3AbstractAnalysis():
    def __init__(self,
                 question_id,
                 answerList,
                ):
        self.question_id = question_id
        self.answerList = answerList
        self.valueList = []
        self.result = []
        self.type = ""
        self.qstnWidget = None
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    self.valueList.append(self.castRawAnswer(answer["value"]))
                except:
                    pass

    def valid(self, answer):
        # @todo add validation here
        # widget = S3QuestionTypeNumericWidget()
        # widget.validate(answer)
        # if widget.ANSWER_VALID:
        return True

    def castRawAnswer(self, answer):
        return answer

    def chartButton(self):
        if len(self.valueList) == 0:
            return None
        if len(current.request.args) == 1:
            seriesID = current.request.args[0]
        else:
            try:
                vars = current.request.vars["viewing"].split(".")
                seriesID = vars[1]
            except:
                return None
        src = URL(r=current.request,
                  f="completed_chart",
                  vars={"question_id":self.question_id,
                        "series_id" : seriesID,
                        "type" : self.type
                        }
                 )
        link = A(current.T("Chart"), _href=src, _target="blank",  _class="action-btn")
        return DIV(link, _class="surveyChart%sWidget" % self.type)

    def drawChart(self, response, data = None, label = None, xLabel = None, yLabel = None):
        msg = "Programming Error: No chart for %sWidget" % self.type
        output = StringIO()
        output.write(msg)
        response.body = output

    def summary(self):
        self.result = []
        return self.count()

    def count(self):
        self.result.append(([current.T("Replies")], len(self.answerList))) 
        return self.format()
    
    def format(self):
        table = TABLE()
        for (key, value) in self.result:
            table.append(TR(TD(B(key)),TD(value)))
        return table

    def groupData(self, groupAnswer):
        """
            method to group the answers by the categories passed in
            The categories will belong to another question
        """
        grouped = {}
        answers = {}
        for answer in self.answerList:
            answers[answer["complete_id"]] = answer["value"]
        for ganswer in groupAnswer:
            gcode = ganswer["complete_id"]
            greply = ganswer["value"]
            if gcode in answers:
                value = answers[gcode]
            else:
                grouped[greply] = []
                continue
            if greply in grouped:
                grouped[greply].append(value)
            else:
                grouped[greply] = [value]
        return grouped

    def filter(self, filterType, groupedData):
        return groupedData

    def splitGroupedData(self, groupedData):
        keys = []
        values = []
        for (key, value) in groupedData.items():
            keys.append(key)
            values.append(value)
        return (keys, values)

class S3StringAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "String"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)

    def chartButton(self):
        return None

class S3TextAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Text"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)

    def chartButton(self):
        return None

class S3DateAnalysis(S3AbstractAnalysis):
    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Date"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)

    def chartButton(self):
        return None


class S3NumericAnalysis(S3AbstractAnalysis):


    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Numeric"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.histCutoff = 10
        self.basicResults()

    def castRawAnswer(self, answer):
        return float(answer)

    def summary(self):
        T = current.T
        widget = S3QuestionTypeNumericWidget()
        fmt = widget.formattedAnswer
        if self.sum:
            self.result.append(([T("Total")], fmt(self.sum)))
        if self.average:
            self.result.append(([T("Average")], fmt(self.average)))
        if self.max:
            self.result.append(([T("Maximum")], fmt(self.max)))
        if self.min:
            self.result.append(([T("Minimum")], fmt(self.min)))
        return self.format()

    def count(self):
        T = current.T
        self.result.append((T("Replies"), len(self.answerList)))
        self.result.append((T("Valid"), self.cnt))
        return self.format()

    def basicResults(self):
        self.cnt = 0
        if len(self.valueList) == 0:
            self.sum = None
            self.average = None
            self.max = None
            self.min = None
            return
        self.sum = 0
        self.max = self.valueList[0]
        self.min = self.valueList[0]
        for answer in self.valueList:
            self.cnt += 1
            self.sum += answer
            if answer > self.max:
                self.max = answer
            if answer < self.min:
                self.min = answer
        self.average = self.sum / float(self.cnt)

    def advancedResults(self):
        array = np.array(self.valueList)
        self.std = array.std()
        self.mean = array.mean()
        self.zscore = {}
        for answer in self.answerList:
            try:
                value = self.castRawAnswer(answer["value"])
            except:
                continue
            complete_id = answer["complete_id"]
            self.zscore[complete_id] = (value - self.mean)/self.std

    def priority(self, complete_id):
        try:
            zscore = self.zscore[complete_id]
            if zscore < -2:
                return 0
            elif zscore < -1:
                return 1
            elif zscore < 0:
                return 2
            elif zscore < 1:
                return 3
            elif zscore < 2:
                return 4
            else:
                return 5
        except:
            return -1

    def chartButton(self):
        if len(self.valueList) < self.histCutoff:
            return None
        return S3AbstractAnalysis.chartButton(self)

    def drawChart(self, response, data = None, label = None, xLabel = None, yLabel = None):
        chart = S3Chart(response)
        chart.displayAsIntegers()
        if data == None:
            chart.survey_hist("",
                              self.valueList,
                              10,
                              0,
                              self.max,
                              xlabel = self.qstnWidget.question.name,
                              ylabel = current.T("Count")
                             )
        else:
            chart.survey_bar(self.qstnWidget.question.name,
                             data,
                             label
                            )

    def filter(self, filterType, groupedData):
        filteredData = {}
        if filterType == "Sum":
            sum = 0
            for (key, valueList) in groupedData.items():
                for value in valueList:
                    try:
                        sum += self.castRawAnswer(value)
                    except:
                        pass
                filteredData[key] = sum
            return filteredData
        return groupedData


class S3OptionAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Option"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.basicResults()


    def summary(self):
        T = current.T
        for (key, value) in self.listp.items():
            self.result.append((T(key), value))
        return self.format()

    def basicResults(self):
        self.cnt = 0
        self.list = {}
        for answer in self.valueList:
            self.cnt += 1
            if answer in self.list:
                self.list[answer] += 1
            else:
                self.list[answer] = 1
        self.listp = {}
        if self.cnt != 0:
            for (key, value) in self.list.items():
                self.listp[key] = "%s%%" %((100 * value) / self.cnt)

    def drawChart(self, response, data = None, label = None, xLabel = None, yLabel = None):
        chart = S3Chart(response)
        data = []
        label = []
        for (key, value) in self.list.items():
            data.append(value)
            label.append(key)
        chart.survey_pie(self.qstnWidget.question.name,
                         data,
                         label
                        )

class S3OptionYNAnalysis(S3OptionAnalysis):


    def __init__(self,
                 question_id,
                 answerList
                ):
        S3OptionAnalysis.__init__(self, question_id, answerList)
        self.type = "YesNo"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.basicResults()


    def summary(self):
        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        return self.format()


    def basicResults(self):
        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = T("Invalid")
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop = T("Invalid")
            else:
                self.list["No"] = 0
                self.nop = T("0%")

class S3OptionYNDAnalysis(S3OptionAnalysis):


    def __init__(self,
                 question_id,
                 answerList
                ):
        S3OptionAnalysis.__init__(self, question_id, answerList)
        self.type = "YesNoDontKnow"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.basicResults()

    def summary(self):
        T = current.T
        self.result.append((T("Yes"), self.yesp))
        self.result.append((T("No"), self.nop))
        self.result.append((T("Don't Know"), self.dkp))
        return self.format()

    def basicResults(self):
        S3OptionAnalysis.basicResults(self)
        T = current.T
        if "Yes" in self.listp:
            self.yesp = self.listp["Yes"]
        else:
            if self.cnt == 0:
                self.yesp = T("Invalid")
            else:
                self.list["Yes"] = 0
                self.yesp = T("0%")
        if "No" in self.listp:
            self.nop = self.listp["No"]
        else:
            if self.cnt == 0:
                self.nop = T("Invalid")
            else:
                self.list["No"] = 0
                self.nop = T("0%")
        if "Don't Know" in self.listp:
            self.dkp = self.listp["Don't Know"]
        else:
            if self.cnt == 0:
                self.dkp = T("Invalid")
            else:
                self.list["Don't Know"] = 0
                self.dkp = T("0%")

class S3OptionOtherAnalysis(S3OptionAnalysis):
    def __init__(self,
                 question_id,
                 answerList
                ):
        S3OptionAnalysis.__init__(self, question_id, answerList)
        self.type = "OptionOther"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.basicResults()

class S3LocationAnalysis(S3AbstractAnalysis):

    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Location"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        self.basicResults()


    def summary(self):
        T = current.T
        self.result.append((T("Known Locations"), self.kcnt))
        self.result.append((T("Duplicate Locations"), self.dcnt))
        self.result.append((T("Unknown Locations"), self.ucnt))
        return self.format()
    
    def count(self):
        T = current.T
        self.result.append((T("Total Locations"), len(self.valueList)))
        self.result.append((T("Unique Locations"), self.cnt))
        return self.format()

    def basicResults(self):
        self.locationList = {}
        self.duplicates = {}
        self.known = {}
        for answer in self.valueList:
            # See if location is already stored
            if answer in self.locationList:
                self.locationList[answer] += 1
            # Get the location detail from database
            else:
                self.locationList[answer] = 1
                locTable = current.db.gis_location
                query = (locTable.name == answer)
                records = current.db(query).select()
                if len(records) > 1:
                    self.duplicates[answer] = records
                if len(records) == 1:
                    self.known[answer] = records.first()
        self.cnt = len(self.locationList)
        self.dcnt = len(self.duplicates)
        self.kcnt = len(self.known)
        if self.cnt == 0:
            self.dper = "0%%"
            self.kper = "0%%"
        else:
            self.dper = "%s%%" %((100 * self.dcnt) / self.cnt)
            self.kper = "%s%%" %((100 * self.kcnt) / self.cnt)
        self.ucnt = self.cnt - self.kcnt - self.dcnt

    def chartButton(self):
        return None


class S3LinkAnalysis(S3AbstractAnalysis):
    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Link"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        linkWidget = S3QuestionTypeLinkWidget(question_id)
        parent = linkWidget.get("Parent")
        relation = linkWidget.get("Relation")
        type = linkWidget.get("Type")
        parent_qid = linkWidget.getParentQstnID()
        valueMap = {}
        for answer in self.answerList:
            complete_id = answer["complete_id"]
            parent_answer = linkWidget.loadAnswer(complete_id, parent_qid, forceDB=True)
            if relation == "groupby":
                # @todo: check for different values
                valueMap.update({parent_answer:answer})
        valueList = [] 
        for answer in valueMap.values():
            valueList.append(answer)
        self.widget = survey_analysis_type[type](question_id, valueList)

    def summary(self):
        return self.widget.summary()
    
    def count(self):
        return self.widget.count()

    def chartButton(self):
        return self.widget.chartButton()

    def filter(self, filterType, groupedData):
        return self.widget.filter(filterType, groupedData)

    def drawChart(self, response, data = None, label = None, xLabel = None, yLabel = None):
        return self.widget.drawChart(response, data, label, xLabel, yLabel)

class S3GridAnalysis(S3AbstractAnalysis):
    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "Grid"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)

class S3GridChildAnalysis(S3AbstractAnalysis):
    def __init__(self,
                 question_id,
                 answerList
                ):
        S3AbstractAnalysis.__init__(self, question_id, answerList)
        self.type = "GridChild"
        self.qstnWidget = survey_question_type[self.type](question_id = question_id)
        childWidget = S3QuestionTypeLinkWidget(question_id)
        trueType = childWidget.get("Type")
        for answer in self.answerList:
            if self.valid(answer):
                try:
                    self.valueList.append(trueType.castRawAnswer(answer["value"]))
                except:
                    pass
        self.widget = survey_analysis_type[trueType](question_id, self.valueList)

    def drawChart(self, response, data = None, label = None, xLabel = None, yLabel = None):
        return self.widget.drawChart(response, data, label, xLabel, yLabel)

class S3Chart:
    def __init__(self, response):
        self.response = response
        try:
            # Create a figure for the chart to be drawn to
            self.fig = plt.figure()
        except:
            msg = "matplotlib Library not installed"
            output = StringIO()
            output.write(msg)
            self.response.body = output
            return
        self.response.headers['Content-Type']="image/png"

    def displayAsIntegers(self):
        self.asInt = True

    def survey_hist(self, title, data, bins, min, max, xlabel=None, ylabel=None):
        # draw the histogram
        self.ax = self.fig.add_subplot(111)
        self.ax.hist(data, bins=bins, range=(min,max))
        left = np.arange(0,bins+1)
        if self.asInt:
            label = left * int(max / bins)
        else:
            label = left * max / bins
        plt.xticks(label, label, rotation=30)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        savefig(self.response.body)
    
    def survey_pie(self, title, data, label):
        # draw a pie chart
        self.ax = self.fig.add_subplot(111)
        self.ax.pie(data, labels=label)
        self.ax.legend()
        plt.title(title)
        savefig(self.response.body)
    
    def survey_bar(self, title, data, label, legendLabels):
        # draw a bar chart
        if not isinstance(data[0],list):
            dataList = [data]
        else:
            dataList = data
        cnt = len(label)
        dcnt = len(dataList)
        lcnt = (len(legendLabels)+1)/2
        width = 0.9 / dcnt
        offset = 0
        gap = 0.1 / dcnt
        bcnt = 1
        bars = []
        height = max(0.2, 0.90 - (0.05 * lcnt))
        rect = [0.08, 0.05, 0.9, height]
        axes = self.fig.add_axes(rect)
        for data in dataList:
            left = np.arange(offset,cnt+offset)    # the x locations for the bars
            colour = (0.2/bcnt,0.5/bcnt,1.0/bcnt)
            plot = axes.bar(left, data, width=width, color=colour)
            bars.append(plot[0])
            bcnt += 1
            offset += width + gap
        left = np.arange(cnt)
        lblAdjust = (1.0-gap)*0.5
        plt.xticks(left+lblAdjust, label)
        plt.tick_params(labelsize=9)
        plt.title(title)
        self.fig.legend(bars,
                       legendLabels,
#                       bbox_to_anchor=(1.05, 1),
#                       loc=2,
#                       borderaxespad=0.
                       bbox_to_anchor=(0.01, height+0.085, 0.98, 0.98 - height),
                       ncol=2,
                       loc=3,
                       prop={"size":10},
                      )
        savefig(self.response.body)

