# -*- coding: utf-8 -*-

"""
    Resource Import Tools

    @author: Graeme Foster <graeme[at]acm.org>
    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2011 (c) Sahana Software Foundation
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

# @todo: remove all interactive error reporting out of the _private methods, and raise exceptions instead.
__all__ = ["S3Importer", "S3ImportJob", "S3ImportItem"]

import os
import sys
import uuid
import cPickle
import tempfile
from datetime import datetime
from copy import deepcopy
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
from lxml import etree

from gluon import *
from gluon.storage import Storage, Messages
from gluon.tools import callback
import gluon.contrib.simplejson as simplejson
from gluon.serializers import json

from s3tools import SQLTABLES3
from s3crud import S3CRUD
from s3xml import S3XML

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3IMPORTER: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
def dataItemElementRepresent(value):
    """
        @todo: docstring?
    """
    
    def convertStrToType(field, value):
        if field.type == "string" or \
               field.type == "string" or  \
               field.type == "password" or \
               field.type == "upload" or \
               field.type == "text":
            return value
        elif field.type == "integer" or field.type == "id":
            return int(value)
        elif field.type == "double" or field.type == "decimal":
            return double(value)
        elif  field.type == 'boolean':
            if value and not str(value)[:1].upper() in ["F", "0"]:
                return "T"
            else:
                return "F"
        elif field.type == "date":
            return value # @todo fix this to get a date
        elif field.type == "time":
            return value # @todo fix this to get a time
        elif field.type == "datetime":
            return value # @todo fix this to get a datetime
        else:
            return value

    def addDataElement(list, table):
        result = ""
        first = ""
        for child in list:
            f = child.get("field", None)
            value = child.get("value", None)
            try:
                field = table[f]
                value = convertStrToType(field, value)
                value = S3XML.xml_encode(value)
            except:
                pass
            if f != None and value != None:
                if first == "":
                    first = "<p><b>%s:</b> %s</p> " % (f, value)
                result += "<tr><th>%s:</th><td>%s</td></tr>\n " % \
                    (f, value)
        return (first, result)

    value = S3XML.xml_decode(value)
    try:
        element = etree.fromstring(value)
    except: # XMLSyntaxError:
        return value
    mainResource = element.get("name")
    mainTable = current.db[mainResource]
    first = ""
    result = "<table class='importItem [id]'> "
    (first,r) = addDataElement(element.findall("data"), mainTable)
    result += r
    resource = element.findall("resource")
    for element in resource:
        reference = element.get("name")
        refTable = current.db[reference]
        (blackHole,r) = addDataElement(element.findall("data"), refTable)
        result += r
    result += "</table>"
    return first + result

# -----------------------------------------------------------------------------
def date_represent(date_obj):
    """
        @todo: docstring?
        @todo: replace by S3DateTime method?
    """
    return date_obj.strftime("%d %B %Y, %I:%M%p")

# =============================================================================

class S3Importer(S3CRUD):
    """
        Transformable formats (XML, JSON, CSV) import handler

        @status: work in progress
    """

    UPLOAD_TABLE_NAME = "s3_import_upload"

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view

            Known means of communicating with this module:

            It expects a URL of the form: /prefix/name/import.xml

            It will interpret the http requests as follows:

            GET     will trigger the upload
            POST    will trigger either commits or display the import details
            DELETE  will trigger deletes

            It will accept one of the following control vars:
            item:   to specify a single item in the import job
            job:    to specify a job
            It should not receive both so job takes precedent over item

            A controller can request extra data to be displayed on the screen
            this data will create an extra column in the data with the same
            value used for every record. The extra data is defined in the
            controller and will be a callback stored in
            response.s3.importerPrep. This callback will return a dict of the
            following format:
               data['Label'] = Value to appear on the upload form
               data['Widget'] = Widget to appear on the upload form
             * data['Lookup'] = The field in the controller table linked to the widget
             * data['Field'] = The field in the controller table that will be inserted into the upload file
             * data['Represent'] = A represent callback to be used to display the data
             * data['Stylesheet'] = The transform stylesheet to be used
               * optional key value pairs

        """

        _debug("S3Importer.apply_method(%s)" % r)

        # @todo: use request extension to determine the file format

        T = current.T
        messages = self.messages = Messages(T)
        messages.download_template = "Download Template"
        messages.invalid_file_format = "Invalid File Format"

        # @ToDo: use messages
        # @todo: use all-uppercase names for constants
        self.ErrorUnsupportedFileType = T("Unsupported file type of %s")
        self.ErrorNoStyleSheetFound = T("No Stylesheet %s could be found to manage the import file.")
        self.ErrorOpenFile = T("Unable to open the file %s")
        self.ErrorUploadFileMissing = T("The file to upload is missing")
        self.WarningNoRecords = T("No records to import")
        self.WarningNoJobToDelete = T("No job to delete, maybe it has already been deleted.")
        try:
            self.uploadTitle = current.response.s3.crud_strings[self.tablename].upload_title
        except:
            self.uploadTitle = T("Upload a %s import file" % r.function)
        self.displayJobTitle = T("Details of the selected import job")
        self.displayJobListTitle = T("List of import items")
        self.fileUploaded = T("Import file uploaded")
        self.uploadSubmitBtn = T("Upload Data File")
        self.UploadDataTableOpen = T("Open")
        self.UploadDataTableView = T("View")
        self.UploadDataTableDelete = T("Delete")
        self.ImportItemDataTableDisplay = T("Display Details")
        self.ImportJobAvailable = T("Total records in the Import Job")
        self.ImportJobSelected = T("Records selected")
        self.JobDeleted = T("Import job deleted")
        self.UploadTableImportFile = T("Import File")
        self.UploadTableImportFileComment = T("Upload a file formatted according to the Template.")
        self.UploadTableUserName = T("User Name")
        self.CompletedMsg = T("Job run on %s. With result of (%s)")
        self.CommitTotalImported = T("%s records imported")
        self.CommitTotalIgnored = T("%s records ignored")
        self.CommitTotalError = T("%s records in error")

        current.session.s3.ocr_enabled = False
        self.error = None
        self.warning = None
        self.importJob = None
        self.controllerTable = self.table
        self.controllerTablename = self.tablename
        self.request = r # used by __define_table()
        self.__define_table()

        # @todo: redirect to a login screen for interactive imports
        _debug("   Check authorisation for %s" % self.s3importTablename)
        _debug("   Check authorisation for %s" % self.controllerTablename)
        authorised = self.permit("create", self.s3importTablename) and \
                     self.permit("create", self.controllerTablename)
        if not authorised:
            if r.method is not None:
                r.unauthorised()
            else:
                return dict(form=None)

        self.settings = self.manager.s3.crud
        self.data = None
        self.controller = r.controller
        self.function = r.function

        source = None
        transform = None
        uploadID = None
        items = None

        # @todo get the data from either get_vars or post_vars appropriately
        #       for post -> commit_items would need to add the uploadID
        if "transform" in r.get_vars:
            transform = r.get_vars["transform"]
        if "filename" in r.get_vars:
            source = r.get_vars["filename"]
        if "job" in r.post_vars:
            uploadID = r.post_vars["job"]
        elif "job" in r.get_vars:
            uploadID = r.get_vars["job"]
        items = self._process_item_list(r.vars, uploadID)
        if "delete" in r.get_vars:
            r.http = "DELETE"

        # Now branch off to the appropriate controller function
        if r.http == "GET":
            if source != None:
                output = self.commit(source, transform)
            if uploadID != None:
                output = self.display_job(uploadID)
            else:
                output = self.upload()
        elif r.http == "POST":
            if items != None:
                output = self.commit_items(uploadID, items)
            else:
                output = self.display()
        elif r.http == "DELETE":
            if uploadID != None:
                output = self.delete_job(uploadID)
        else:
            r.error(501, self.manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def upload(self):
        """
            This will display the upload form
            It will ask for a file to be uploaded or for a job to be selected.

            If a file is uploaded then it will guess at the file type and
            ask for the transform file to be used. The transform files will
            be in a dataTable with the module specific files shown first and
            after those all other known transform files. Once the transform
            file is selected the import process can be started which will
            generate an importJob, and a "POST" method will occur

            If a job is selected it will have two actions, open and delete.
            Open will mean that a "GET" method will occur, with the job details
            passed in.
            Whilst the delete action will trigger a "DELETE" method.
        """

        _debug("S3Importer.upload()")

        response = current.response
        request = self.request

        form = self._create_upload_form()
        output = self._create_upload_dataTable()
        if request.representation == "aadata":
            return output

        output.update(form=form, title=self.uploadTitle)
        return output

    # -------------------------------------------------------------------------
    def display(self):
        """
            This will take an uploaded file and generate an importJob
            Once the importJob has been created it will then take the
            job number and display the job details on the screen
        """

        _debug("S3Importer.display()")

        request = self.request
        response = current.response

        db = current.db
        table = self.s3importTable

        output = dict()

        # the call to sqlform will then update the details on the database.
        form = self._create_upload_form()
        uploadFilename = form.vars.file
        # uploadFilename shouldn't be blank but it can be if the form is resent
        # in which case we'll go back to the start screen
        if form.errors or \
           (uploadFilename == "") or \
           (uploadFilename == None):
            response.flash = "" # clear the success message & just display the error
            if (uploadFilename == "") or (uploadFilename == None):
                response.error = self.ErrorUploadFileMissing
            output = self._create_upload_dataTable()
            output.update(form=form,
                          title=self.uploadTitle,
                          )
        else:
            query = (table.file == uploadFilename)
            result = db(query).update(controller=self.controller,
                                      function=self.function,
                                      filename = request.vars.file.filename,
                                      user_id = current.session.auth.user.id
                                     )
            # Now commit the changes
            db.commit()

            # @todo: use the request extension as file format?
            #uploadFileFormat = request.vars.file.type.split("/")[1]
            uploadFileFormat = uploadFilename.split(".").pop()
            if uploadFileFormat not in ["csv"]:
                response.error = self.messages.invalid_file_format
                return self.upload()
            path = table.file.uploadfolder

            # @todo check that the file is not empty
            uploadFile = os.path.join(request.folder,
                          "uploads",
                          #"imports",
                          uploadFilename
                         )
            openUploadFile = open(uploadFile, "rb")

            query = (table.file == uploadFilename)
            row = db(query).select(table.id,
                                   limitby=(0, 1)).first()
            uploadID = row.id
            result = self._generate_import_job(uploadID,
                                               openUploadFile,
                                               uploadFileFormat
                                              )

            if uploadID == None:
                # redirect to the start page (no vars to remove)
                query = (table.file == uploadFilename)
                row = db(query).update(status = 2) # in error
                if self.error != None:
                    response.error = self.error
                if self.warning != None:
                    response.warning = self.warning
                response.flash = "" # clear the success message & just display the error
                return self.upload()
            # Display the details on the screen
            redirect(URL(r=self.request, f=self.function,
                         args=["import.xml"], vars={"job":uploadID}))
            #output = self.display_job(uploadID)
        return output

    # -------------------------------------------------------------------------
    def display_job(self, uploadID):
        """
            @todo: docstring?
        """

        _debug("S3Importer.display_job()")

        request = self.request
        response = current.response

        db = current.db
        table = self.s3importTable
        job_id = self._get_job_id_from_uploadID(uploadID)
        output = dict()
        if job_id == None:
            # redirect to the start page (removes all vars)
            query = (table.id == uploadID)
            row = db(query).update(status = 2) # in error
            current.session.warning = self.WarningNoRecords
            redirect(URL(r=request, f=self.function, args=["import.xml"]))

        # Get the status of the upload job
        query = (table.id == uploadID)
        row = db(query).select(table.status,
                               table.modified_on,
                               table.summary_added,
                               table.summary_error,
                               table.summary_ignored,
                               limitby=(0, 1)).first()
        status = row.status
        # completed display details
        if status == 3: # Completed
            # @todo currently this is an unnecessary server call,
            #       change for completed records to be a display details
            #       and thus avoid the round trip.
            #       but keep this code to protect against hand-crafted URLs
            #       (and the 'go back' syndrome on the browser)
            result = (row.summary_added,
                      row.summary_error,
                      row.summary_ignored,
                     )
            self._display_completed_job(result, row.modified_on)
            redirect(URL(r=request, f=self.function, args=["import.xml"]))
        # otherwise display import items
        response.view = self._view(request, "list.html")

        output = self._create_import_item_dataTable(uploadID, job_id)
        if request.representation == "aadata":
            return output

        rowcount = len(self._get_all_items_from_uploadID(uploadID))
        rheader = DIV(TABLE(
            TR(
                TH("%s: " % self.ImportJobAvailable),
                TD(rowcount, _id="totalAvaliable"),
                TH("%s: " % self.ImportJobSelected),
                TD(0, _id="totalSelected")
              ),
        ))

        output.update(title=self.displayJobTitle,
                      rheader=rheader,
                      subtitle=self.displayJobListTitle,)

        return output

    # -------------------------------------------------------------------------
    def commit(self, source, transform):
        """
            @todo: docstring?
        """

        _debug("S3Importer.commit(%s, %s)" % (source, transform))

        db = current.db
        session = current.session
        request = self.request

        try:
            openFile = open(source, "r")
        except:
            session.error = self.ErrorOpenFile % source
            redirect(URL(r=request, f=self.function))

        # @todo: manage different file formats
        # @todo: find file format from request.extension
        fileFormat = "csv"

        # insert data in the table and get the ID
        try:
            user = session.auth.user.id
        except:
            user = None

        uploadID = self.s3importTable.insert(controller=self.controller,
                                             function=self.function,
                                             filename = source,
                                             user_id = user,
                                             status = 1)
        db.commit()

        # create the import job
        result = self._generate_import_job(uploadID,
                                           openFile,
                                           fileFormat,
                                           stylesheet=transform
                                          )
        if result == None:
            if self.error != None:
                if session.error == None:
                    session.error = self.error
                else:
                    session.error += self.error
            if self.warning != None:
                if session.warning == None:
                    session.warning = self.warning
                else:
                    session.warning += self.warning
        else:
            items = self._get_all_items_from_uploadID(uploadID, True)
            # commit the import job
            self._commit_import_job(uploadID, items)
            result = self._update_upload_job(uploadID)
            # get the results and display
            msg = (source
                   + " : "
                   + self.CommitTotalImported
                   + " "
                   + self.CommitTotalError
                   + " "
                   + self.CommitTotalIgnored) \
                   % result
            if session.flash == None:
                session.flash = msg
            else:
                session.flash += msg

    # -------------------------------------------------------------------------
    def commit_items(self, uploadID, items):
        """
            @todo: docstring?
        """

        _debug("S3Importer.commit_items(%s, %s)" % (uploadID, items))
        # Save the import items
        self._commit_import_job(uploadID, items)
        # Update the upload table
        # change the status to completed
        # record the summary details
        # delete the upload file
        result = self._update_upload_job(uploadID)
        # redirect to the start page (removes all vars)
        self._display_completed_job(result)
        redirect(URL(r=self.request, f=self.function, args=["import.xml"]))

    # -------------------------------------------------------------------------
    def delete_job(self, uploadID):
        """
            Delete an uploaded file and the corresponding import job

            @param uploadID: the upload ID
        """

        _debug("S3Importer.delete_job(%s)" % (uploadID))

        db = current.db

        request = self.request
        resource = request.resource # use self.resource?
        response = current.response

        # Get the import job ID
        job_id = self._get_job_id_from_uploadID(uploadID)

        # Delete the import job (if any)
        if job_id:
            result = resource.import_xml(None,
                                         id = None,
                                         tree = None,
                                         job_id = job_id,
                                         delete_job = True)
        # @todo: check result

        # now delete the upload entry
        query = (self.s3importTable.id == uploadID)
        count = db(query).delete()
        # @todo: check that the record has been deleted

        # Now commit the changes
        db.commit()

        result = count

        # return to the main import screen
        # @todo: check result properly
        if result == False:
            response.warning = self.WarningNoJobToDelete
        else:
            response.flash = self.JobDeleted

        # redirect to the start page (remove all vars)
        self.next = self.request.url(vars=dict())
        return

    # ========================================================================
    # Utility methods
    # ========================================================================
    def _create_upload_form(self):
        """
            This will create the upload form
        """

        response = current.response
        request = self.request

        response.view = self._view(request, "list_create.html")

        if response.s3.importerPrep:
            table = self.s3importTable
            extraData = response.s3.importerPrep()
            table.extra_data.readable = True
            table.extra_data.writable = True
            if "Represent" in extraData:
                table.extra_data.represent = extraData["Represent"]
            if "Label" in extraData:
                table.extra_data.label = extraData["Label"]
            if "Widget" in extraData:
                table.extra_data.widget = extraData["Widget"]

        # Get the form
        self.settings.submit_button = self.uploadSubmitBtn
        self._use_upload_table()
        form = self.sqlform(message=self.fileUploaded)
        self._use_controller_table()

        # Add a link to download the Template
        if "extra_data" in request.vars and \
           "Stylesheet" in extraData:
            template = "%s.csv" % extraData["Stylesheet"].split(".", 1)[0]
        else:
            template = "%s.csv" % self.function
        form[0][-1].append(TR(TD(A(self.messages.download_template,
                                   _href=URL(r=request,
                                             c="static",
                                             f="formats",
                                             args=["s3csv",
                                                   self.controller,
                                                   template]))),
                           _id="template__row"))

        return form

    # -------------------------------------------------------------------------
    def _create_upload_dataTable(self):
        """
            @todo: docstring?
        """

        response = current.response
        request = self.request
        db = current.db
        controller = self.controller
        function = self.function
        s3 = response.s3

        table = self.s3importTable
        s3.filter = (table.controller == controller) & \
                    (table.function == function)
        fields = ["id",
                  "filename",
                  table.created_on.name,
                  table.user_id.name,
                  table.status.name,
                 ]
        if s3.importerPrep:
            fields.append(table.extra_data.name)

        self._use_upload_table()
        output = self._dataTable(fields, sort_by = [[2,"desc"]])
        self._use_controller_table()

        if request.representation == "aadata":
            return output

        query = (table.status != 3) # Status of Pending or in-Error
        rows = db(query).select(table.id)
        restrictOpen = [str(row.id) for row in rows]
        query = (table.status == 3) # Status of Completed
        rows = db(query).select(table.id)
        restrictView = [str(row.id) for row in rows]

        s3.actions = [
                    dict(label=str(self.UploadDataTableOpen),
                         _class="action-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import.xml"],
                                 vars={"job":"[id]"}),
                         restrict = restrictOpen

                         ),
                    dict(label=str(self.UploadDataTableView),
                         _class="action-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import.xml"],
                                 vars={"job":"[id]"}),
                         restrict = restrictView
                         ),
                    dict(label=str(self.UploadDataTableDelete),
                         _class="delete-btn",
                         url=URL(r=request,
                                 c=controller,
                                 f=function,
                                 args=["import.xml"],
                                 vars={"job":"[id]",
                                       "delete":"True"
                                      }
                                )
                         ),
                  ]
        # Display an Error if no job is attached with this record
        query = (table.status == 1) # Pending
        rows = db(query).select(table.id)
        s3.dataTableStyleAlert = [str(row.id) for row in rows]
        query = (table.status == 2) # in error
        rows = db(query).select(table.id)
        s3.dataTableStyleWarning = [str(row.id) for row in rows]

        return output

    # -------------------------------------------------------------------------
    def _create_import_item_dataTable(self, uploadID, job_id):
        """
            @todo: docstring?
        """

        response = current.response

        represent = {"element" : dataItemElementRepresent}
        self._use_import_item_table(job_id)
        # Add a filter to the dataTable query
        response.s3.filter = (self.table.job_id == job_id) & \
                             (self.table.tablename == self.controllerTablename)

        output = self._dataTable(["id",
                                   "element",
                                   "error",
                                  ],
                                  sort_by = [[1, "asc"]],
                                  represent=represent,
                                 )
        self._use_controller_table()

        if self.request.representation == "aadata":
            return output

        response.s3.dataTableSelectable = True
        response.s3.dataTableSelectAll = True
        response.s3.dataTablePostMethod = True
        table = output["items"]
        job = INPUT(_type="hidden", _id="importUploadID", _name="job",
                    _value="%s" % uploadID)
        mode = INPUT(_type="hidden", _id="importMode", _name="mode",
                     _value="Exclusive")
        selected = INPUT(_type="hidden", _id="importSelected",
                         _name="selected", _value="")
        form = FORM(table, job, mode, selected)
        output["items"] = form
        response.s3.dataTableSelectSubmitURL = "import.xml?job=%s&" % uploadID
        response.s3.actions = [
                                dict(label= str(self.ImportItemDataTableDisplay),
                                     _class="action-btn",
                                     _jqclick="$('.importItem.'+id).toggle();",
                                     ),
                              ]
        return output

    # -------------------------------------------------------------------------
    def _generate_import_job(self,
                             uploadID,
                             openFile,
                             fileFormat,
                             stylesheet=None
                            ):
        """
            This will take a s3_import_upload record and
            generate the importJob

            @param uploadFilename: The name of the uploaded file

            @todo: complete parameter descriptions
        """

        _debug("S3Importer._generate_import_job(%s, %s, %s, %s)" % (uploadID,
                                                                openFile,
                                                                fileFormat,
                                                                stylesheet
                                                               )
              )
        request = self.request
        response = current.response
        resource = request.resource

        db = current.db

        # ---------------------------------------------------------------------
        # CSV
        if fileFormat == "csv" or fileFormat == "comma-separated-values":

            # If it exists then add the extra_data to the import file
            if "extra_data" in request.vars:
                openFile = self._add_extraData_to_CSV(openFile)

            fmt = "csv"
            src = openFile

        # ---------------------------------------------------------------------
        # XML
        # @todo: implement
        #elif fileFormat == "xml":

        # ---------------------------------------------------------------------
        # S3JSON
        # @todo: implement
        #elif fileFormat == "s3json":

        # ---------------------------------------------------------------------
        # PDF
        # @todo: implement
        #elif fileFormat == "pdf":

        # ---------------------------------------------------------------------
        # Unsupported Format
        else:
            msg = self.ErrorUnsupportedFileType % fileFormat
            self.error = msg
            _debug(msg)
            return None

        # Get the stylesheet
        if stylesheet == None:
            stylesheet = self._get_stylesheet()
        if stylesheet == None:
            return None

        # before calling import tree ensure the db.table is the controllerTable
        self.table = self.controllerTable
        self.tablename = self.controllerTablename

        # Generate the import job
        resource.import_xml(src,
                            format=fmt,
                            stylesheet=stylesheet,
                            ignore_errors = True,
                            commit_job = False)

        job = resource.job
        if job is None:
            if resource.error:
                # Error
                self.error = resource.error
                return None
            else:
                # Nothing to import
                self.warning = self.WarningNoRecords
                return None
        else:
            # Job created
            job_id = job.job_id

            query = (self.s3importTable.id == uploadID)
            result = db(query).update(job_id=job_id)
            # @todo: add check that result == 1, if not we are in error
            # Now commit the changes
            db.commit()

        return True

    # -------------------------------------------------------------------------
    def _add_extraData_to_CSV(self, openFile):
        """
            @todo: docstring?
        """

        request = self.request
        response = current.response
        db = current.db

        extraData = response.s3.importerPrep()
        if "extra_data" in request.vars and request.vars.extra_data != "":
            value = request.vars.extra_data
            # If we have a lookup defined change the value to the right one in the table
            if "Lookup" in extraData:
                query = extraData["Lookup"] == value
                row = db(query).select(extraData["Field"]).first()
                if (row != None) and (extraData["Field"].name in row):
                    value = row[extraData["Field"].name]
            # Now add the extra column
            firstLine = True
            newcsv = tempfile.TemporaryFile()
            with openFile as f:
                for line in f:
                    line = line.strip()
                    if line == "":
                        continue
                    if firstLine:
                        line += ',"%s"\n' % extraData["Label"]
                        firstLine = False
                    else:
                        line += ',"%s"\n' % value
                    _debug(line.strip())
                    newcsv.write(line)
            openFile = newcsv
            openFile.flush()
            openFile.seek(0)
        return openFile

    # -------------------------------------------------------------------------
    def _get_stylesheet(self):
        """
            Get the stylesheet for transformation of the import

            @todo: docstring?
        """

        request = self.request
        response = current.response

        # @todo: make a class constant
        templateDir = os.path.join(request.folder, "static", "formats", "s3csv")

        # @todo: use S3Request constant here for the extension
        xslFileName = "%s.xsl" % self.function

        # if stylesheet is defined in extraData then try that one.
        if "extra_data" in request.vars and request.vars.extra_data != "":
            extraData = response.s3.importerPrep()
            _debug("Request.vars: %s" % request.vars)
            _debug("Extra Data: %s" % extraData)
            if "Stylesheet" in extraData:
                stylesheet = os.path.join(request.folder,
                                          "static",
                                          "formats",
                                          "s3csv",
                                          self.controller,
                                          extraData["Stylesheet"])
                if os.path.exists(stylesheet) == False:
                    # No able to access the extraData stylesheet
                    msg = self.ErrorNoStyleSheetFound % stylesheet
                    self.error = msg
                    _debug(msg)
                    return None
                else:
                    return stylesheet

        # try the app directory in the templates directory first
        stylesheet = os.path.join(templateDir, self.controller, xslFileName)
        if os.path.exists(stylesheet) == False:
            # now try the templates directory
            stylesheet = os.path.join(templateDir, xslFileName)
            if os.path.exists(stylesheet) == False:
                # No appropriate stylesheet template could be found
                msg = self.ErrorNoStyleSheetFound % stylesheet
                self.error = msg
                _debug(msg)
                return None

        return stylesheet

    # -------------------------------------------------------------------------
    def _commit_import_job(self, uploadID, items):
        """
            This will save all of the selected import items

            @todo: parameter descriptions?
        """

        _debug("S3Importer._commit_import_job(%s, %s)" % (uploadID, items))

        db = current.db
        request = self.request
        resource = request.resource

        # load the items from the s3_import_item table
        self.importDetails = dict()
        job_id = self._get_job_id_from_uploadID(uploadID)

        itemTable = S3ImportJob.define_item_table()

        if itemTable != None:
            #****************************************************************
            # EXPERIMENTAL
            # This doesn't delete related items
            # but import_tree will tidy it up later
            #****************************************************************
            # get all the items selected for import
            rows = self._get_all_items_from_uploadID(uploadID)

            # loop through each row and delete the items not required
            self._storeImportDetails(job_id, "preDelete")
            for id in rows:
                if str(id) not in items:
                    # @todo: replace with a helper method from the API
                    _debug("Deleting item.id = %s" % id)
                    query = (itemTable.id == id)
                    db(query).delete()

            #****************************************************************
            # EXPERIMENTAL
            #****************************************************************

            # set up the table we will import data into
            self.table = self.controllerTable
            self.tablename = self.controllerTablename

            self._storeImportDetails(job_id, "preImportTree")

            # Now commit the remaining items
            msg = resource.import_xml(None,
                                      job_id = job_id,
                                      ignore_errors = True)
            return resource.error is None

    # -------------------------------------------------------------------------
    def _storeImportDetails(self, job_id, key):
        """
            This will store the details from an importJob

            @todo: parameter descriptions?
        """

        _debug("S3Importer._storeImportDetails(%s, %s)" % (job_id, key))

        db = current.db
        itemTable = S3ImportJob.define_item_table()

        query = (itemTable.job_id == job_id)  & \
                (itemTable.tablename == self.controllerTablename)
        rows = db(query).select(itemTable.data, itemTable.error)
        items = [dict(data=row.data, error=row.error) for row in rows]

        self.importDetails[key] = items

    # -------------------------------------------------------------------------
    def _update_upload_job(self, uploadID):
        """
            This will record the results from the import, and change the
            status of the upload job

            @todo: parameter descriptions?
            @todo: report errors in referenced records, too
        """

        _debug("S3Importer._update_upload_job(%s)" % (uploadID))

        request = self.request
        resource = request.resource
        db = current.db

        totalPreDelete = len(self.importDetails["preDelete"])
        totalPreImport = len(self.importDetails["preImportTree"])
        totalIgnored = totalPreDelete - totalPreImport

        if resource.error_tree is None:
            totalErrors = 0
        else:
            totalErrors = len(resource.error_tree.findall(
                            "resource[@name='%s']" % resource.tablename))

        totalRecords = totalPreImport - totalErrors
        if totalRecords < 0:
            totalRecords = 0

        query = (self.s3importTable.id == uploadID)
        result = db(query).update(summary_added=totalRecords,
                                  summary_error=totalErrors,
                                  summary_ignored = totalIgnored,
                                  status = 3)

        # Now commit the changes
        db.commit()
        return (totalRecords, totalErrors, totalIgnored)

    # -------------------------------------------------------------------------
    def _display_completed_job(self, resultList, completed=None):
        """
            @todo: docstring?
        """

        session = current.session
        msg = (self.CommitTotalImported
               + " "
               + self.CommitTotalError
               + " "
               + self.CommitTotalIgnored) \
               % resultList
        if completed != None:
            session.flash = self.CompletedMsg % (date_represent(completed),
                                                 msg)
        elif resultList[1] is not 0:
            session.error = msg
        elif resultList[2] is not 0:
            session.warning = msg
        else:
            session.flash = msg

    # -------------------------------------------------------------------------
    def _dataTable(self,
                   list_fields = [],
                   sort_by = [[1, "asc"]],
                   represent={},
                  ):
        """
            Method to get the data for the dataTable
            This can be either a raw html representation or
            and ajax call update
            Additional data will be cached to limit calls back to the server

            @param list_fields: list of field names
            @param sort_by: list of sort by columns
            @param represent: a dict of field callback functions used
                              to change how the data will be displayed

            @return: a dict()
               In html representations this will be a table of the data
               plus the sortby instructions
               In ajax this will be a json response

               In addition the following values will be made available:
               totalRecords         Number of records in the filtered data set
               totalDisplayRecords  Number of records to display
               start                Start point in the ordered data set
               limit                Number of records in the ordered set
               NOTE: limit - totalDisplayRecords = total cached
        """

        # ********************************************************************
        # Common tasks
        # ********************************************************************
        session = current.session
        request = self.request
        response = current.response
        resource = self.resource
        representation = request.representation
        db = current.db
        table = self.table
        tablename = self.tablename
        vars = request.get_vars
        output = dict()

        # Check permission to read this table
        authorised = self.permit("read", tablename)
        if not authorised:
            request.unauthorised()

        # List of fields to select from
        # fields is a list of Field objects
        # list_field is a string list of field names
        if list_fields == []:
            fields = resource.readable_fields()
        else:
            fields = [table[f] for f in list_fields if f in table.fields]
        if not fields:
            fields = []

        # attach any represent callbacks
        for f in fields:
            if f.name in represent:
                f.represent = represent[f.name]

        # Make sure that we have the table id as the first column
        if fields[0].name != table.fields[0]:
            fields.insert(0, table[table.fields[0]])

        list_fields = [f.name for f in fields]

        # Filter
        if response.s3.filter is not None:
            self.resource.add_filter(response.s3.filter)

        # ********************************************************************
        # ajax call
        # ********************************************************************
        if representation == "aadata":
            start = vars.get("iDisplayStart", None)
            limit = vars.get("iDisplayLength", None)
            if limit is not None:
                try:
                    start = int(start)
                    limit = int(limit)
                except ValueError:
                    start = None
                    limit = None # use default
            else:
                start = None # use default
            # Using the sort variables sent from dataTables
            if vars.iSortingCols:
                orderby = self.ssp_orderby(table, list_fields)

            # Echo
            sEcho = int(vars.sEcho or 0)

            # Get the list
            items = self.sqltable(fields=list_fields,
                                  start=start,
                                  limit=limit,
                                  orderby=orderby,
                                  download_url=self.download_url,
                                  as_page=True) or []
            # Ugly hack to change any occurrence of [id] with the true id
            # Needed because the represent doesn't know the id
            for i in range(len(items)):
                id = items[i][0]
                for j in range(len(items[i])):
                    new = items[i][j].replace("[id]",id)
                    items[i][j] = new
            totalrows = self.resource.count()
            result = dict(sEcho = sEcho,
                          iTotalRecords = totalrows,
                          iTotalDisplayRecords = totalrows,
                          aaData = items)

            output = json(result)

        # ********************************************************************
        # html 'initial' call
        # ********************************************************************
        else: # catch all
            start = 0
            limit = 1
            # Sort by
            vars["iSortingCols"] = len(sort_by)

            # generate the dataTables.js variables for sorting
            index = 0
            for col in sort_by:
                colName = "iSortCol_%s" % str(index)
                colValue = col[0]
                dirnName = "sSortDir_%s" % str(index)
                if len(col) > 1:
                    dirnValue = col[1]
                else:
                    dirnValue = "asc"
                vars[colName] = colValue
                vars[dirnName] = dirnValue
            # Now using these sort variables generate the order by statement
            orderby = self.ssp_orderby(table, list_fields)

            del vars["iSortingCols"]
            for col in sort_by:
                del vars["iSortCol_%s" % str(index)]
                del vars["sSortDir_%s" % str(index)]

            # Get the first row for a quick up load
            items = self.sqltable(fields=list_fields,
                                  start=start,
                                  limit=1,
                                  orderby=orderby,
                                  download_url=self.download_url,
                                 )
            totalrows = self.resource.count()
            if items:
                if totalrows:
                    if response.s3.dataTable_iDisplayLength:
                        limit = 2 * response.s3.dataTable_iDisplayLength
                    else:
                        limit = 20
                # Add a test on the first call here:
                # Now get the limit rows for ajax style update of table
                aadata = dict(aaData = self.sqltable(
                                fields=list_fields,
                                start=start,
                                limit=limit,
                                orderby=orderby,
                                download_url=self.download_url,
                                as_page=True,
                               ) or [])
                # Ugly hack to change any occurrence of [id] with the true id
                # Needed because the represent doesn't know the id
                for i in range(len(aadata["aaData"])):
                    id = aadata["aaData"][i][0]
                    for j in range(len(aadata["aaData"][i])):
                        new = aadata["aaData"][i][j].replace("[id]",id)
                        aadata["aaData"][i][j] = new

                aadata.update(iTotalRecords=totalrows,
                              iTotalDisplayRecords=totalrows)
                response.aadata = json(aadata)
                response.s3.start = 0
                response.s3.limit = limit
            else: # No items in database
                # s3import tables don't have a delete field but kept for the record
                if "deleted" in table:
                    available_records = db(table.deleted == False)
                else:
                    available_records = db(table.id > 0)
                # check for any records on an unfiltered table
                if available_records.select(table.id,
                                            limitby=(0, 1)).first():
                    items = self.crud_string(tablename, "msg_no_match")
                else:
                    items = self.crud_string(tablename, "msg_list_empty")

            output.update(items=items, sortby = sort_by)
            # Value to be added to the dataTable ajax call
            response.s3.dataTable_Method = "import"

        return output

    # -------------------------------------------------------------------------
    def _process_item_list(self, vars, uploadID):
        """
            get the list of selected items from the mode and selected
            if the mode is Inclusive then the list is given by selected
            else the mode is Exclusive and it will be all the items for the
            given uploadID excluding those in the selected list

            @todo: parameter descriptions?
        """

        _debug("S3Importer._process_item_list(%s, %s)" % (vars, uploadID))
        items = None

        if "mode" in vars:
            mode = vars["mode"]
            if "selected" in vars:
                selected = vars["selected"].split(",")
            else:
                selected = []
            if mode == "Inclusive":
                items = selected
            elif mode == "Exclusive":
                importItems = self._get_all_items_from_uploadID(uploadID)
                for i in range(len(importItems)):
                    importItems[i] = str(importItems[i])
                for item in selected:
                    if item in importItems:
                        del importItems[importItems.index(item)]
                items = importItems
        return items

    # -------------------------------------------------------------------------
    def _get_job_id_from_uploadID(self, uploadID):
        """
            @todo: docstring?
        """

        _debug("S3Importer._get_job_id_from_uploadID(%s)" % (uploadID))
        db = current.db
        table = self.s3importTable
        query = (table.id == uploadID)
        row = db(query).select(table.job_id,
                               limitby=(0, 1)).first()
        if row == None:
            return None
        else:
            return row.job_id

    # -------------------------------------------------------------------------
    def _get_all_items_from_uploadID(self, uploadID, asString=False):
        """
            get all the importItems for the the uploadID
            using the controller tablename from self.controllerTablename
            1) Get the job_id from the s3_import_upload table
            2) Get all items with the matching job_id and tablename

            @todo: parameter descriptions?
        """

        _debug("S3Importer._get_all_items_from_uploadID(%s)" % (uploadID))
        items = []
        db = current.db

        # @todo: put this join into the query
        job_id = self._get_job_id_from_uploadID(uploadID)

        itemTable = S3ImportJob.define_item_table()
        query = (itemTable.job_id == job_id) & \
                (itemTable.tablename == self.controllerTablename)
        rows = db(query).select()
        for row in rows:
            if asString:
                items.append(str(row.id))
            else:
                items.append(row.id)
        return items

    # -------------------------------------------------------------------------
    def _use_upload_table(self):
        """
            @todo: docstring?
        """

        self.resource.table = self.s3importTable
        self.resource.tablename = self.s3importTablename
        self.resource.clear_query()
        self.table = self.s3importTable
        self.tablename = self.s3importTablename

    # -------------------------------------------------------------------------
    def _use_controller_table(self):
        """
            @todo: docstring?
        """

        self.resource.table = self.controllerTable
        self.resource.tablename = self.controllerTablename
        self.resource.clear_query()
        self.table = self.controllerTable
        self.tablename = self.controllerTablename

    # -------------------------------------------------------------------------
    def _use_import_item_table(self, job_id):
        """
            @todo: docstring?
        """

        #self.table = self.__get_import_item_table(job_id)
        self.tablename = S3ImportJob.ITEM_TABLE_NAME
        self.table = S3ImportJob.define_item_table()
        self.resource.table = self.table
        self.resource.tablename = self.tablename
        self.resource.clear_query()

    # -------------------------------------------------------------------------
    def __define_table(self):
        """
            Define the database tables for uploads
        """

        _debug("S3Importer.__define_table()")

        T = current.T
        db = current.db
        r = self.request
        self.s3importTablename = self.UPLOAD_TABLE_NAME

        import_upload_status = {
            1: T("Pending"),
            2: T("In error"),
            3: T("Completed"),
        }

        def user_name_represent(id):
            rep_str = "-"
            table = db.auth_user

            query = (table.id == id)
            row = db(query).select(table.first_name,
                                   table.last_name,
                                   limitby=(0, 1)).first()
            if row:
                rep_str = "%s %s" % (row.first_name, row.last_name)
            return rep_str

        def status_represent(index):
            if index == None:
                return "Unknown"
            else:
                return import_upload_status[index]

        if self.UPLOAD_TABLE_NAME not in db:
            table = self.define_upload_table()
            table.file.upload_folder = os.path.join(r.folder,
                                                    "uploads",
                                                    #"imports"
                                                    )
            table.file.comment = DIV(_class="tooltip",
                                     _title="%s|%s" %
                                        (self.UploadTableImportFile,
                                         self.UploadTableImportFileComment))
            table.file.label = self.UploadTableImportFile
            table.status.requires = IS_IN_SET(import_upload_status,
                                              zero=None)
            table.status.represent = status_represent
            table.user_id.label = self.UploadTableUserName
            table.user_id.represent = user_name_represent
            table.created_on.default = r.utcnow
            table.created_on.represent = date_represent
            table.modified_on.default = r.utcnow
            table.modified_on.update = r.utcnow
            table.modified_on.represent = date_represent

        self.s3importTable = db[self.UPLOAD_TABLE_NAME]

    # -------------------------------------------------------------------------
    @classmethod
    def define_upload_table(cls):
        """
            @todo: docstring?
        """

        db = current.db

        upload_table = db.define_table(cls.UPLOAD_TABLE_NAME,
                Field("controller",
                       readable=False,
                       writable=False),
                 Field("function",
                       readable=False,
                       writable=False),
                 Field("file",
                       "upload",
                       autodelete=True),
                 Field("filename",
                       readable=False,
                       writable=False),
                 Field("status",
                       "integer",
                       default=1,
                       readable=False,
                       writable=False),
                 Field("extra_data",
                       readable=False,
                       writable=False),
                 Field("job_id",
                       length=128,
                       readable=False,
                       writable=False),
                 Field("user_id",
                       "integer",
                       readable=False,
                       writable=False),
                 Field("created_on", "datetime",
                       readable=False,
                       writable=False),
                 Field("modified_on", "datetime",
                       readable=False,
                       writable=False),
                 Field("summary_added",
                       "integer",
                       readable=False,
                       writable=False),
                 Field("summary_error",
                       "integer",
                       readable=False,
                       writable=False),
                 Field("summary_ignored",
                       "integer",
                       readable=False,
                       writable=False),
                 Field("completed_details",
                       "text",
                       readable=False,
                       writable=False))

        return upload_table

# =============================================================================

class S3ImportItem(object):
    """ Class representing an import item (=a single record) """

    METHOD = Storage(
        CREATE="create",
        UPDATE="update",
        DELETE="delete"
    )

    POLICY = Storage(
        THIS="THIS",                # keep local instance
        OTHER="OTHER",              # update unconditionally
        NEWER="NEWER",              # update if import is newer
        MASTER="MASTER"             # update if import is master
    )

    # -------------------------------------------------------------------------
    def __init__(self, job):
        """
            Constructor

            @param job: the import job this item belongs to
        """

        self.job = job
        self.manager = job.manager
        self.ERROR = job.manager.ERROR

        # Locking and error handling
        self.lock = False
        self.error = None

        # Identification
        self.item_id = uuid.uuid4() # unique ID for this item
        self.id = None
        self.uid = None

        # Data elements
        self.table = None
        self.element = None
        self.data = None
        self.original = None
        self.components = []
        self.references = []
        self.load_components = []
        self.load_references = []
        self.parent = None
        self.skip = False

        # Conflict handling
        self.mci = 2
        self.mtime = datetime.utcnow()
        self.modified = True
        self.conflict = False

        # Allowed import methods
        self.strategy = job.strategy
        # Update and conflict resolution policies
        self.update_policy = job.update_policy
        self.conflict_policy = job.conflict_policy

        # Actual import method
        self.method = None

        self.onvalidation = None
        self.onaccept = None

        # Item import status flags
        self.accepted = None
        self.permitted = False
        self.committed = False

        # Writeback hook for circular references:
        # Items which need a second write to update references
        self.update = []

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ Helper method for debugging """

        _str = "<S3ImportItem %s {item_id=%s uid=%s id=%s error=%s data=%s}>" % \
               (self.table, self.item_id, self.uid, self.id, self.error, self.data)
        return _str

    # -------------------------------------------------------------------------
    def parse(self,
              element,
              original=None,
              table=None,
              tree=None,
              files=None):
        """
            Read data from a <resource> element

            @param element: the element
            @param table: the DB table
            @param tree: the import tree
            @param files: uploaded files

            @returns: True if successful, False if not (sets self.error)
        """

        manager = self.manager
        db = current.db
        xml = manager.xml
        model = manager.model
        validate = manager.validate

        self.element = element
        if table is None:
            tablename = element.get(xml.ATTRIBUTE.name, None)
            try:
                model.load(tablename)
                table = db[tablename]
            except:
                self.error = self.ERROR.BAD_RESOURCE
                element.set(xml.ATTRIBUTE.error, self.error)
                return False

        self.table = table
        self.tablename = table._tablename

        if original is None:
            original = manager.original(table, element)
        data = xml.record(table, element,
                          files=files,
                          original=original,
                          validate=validate)

        if data is None:
            self.error = self.ERROR.VALIDATION_ERROR
            self.accepted = False
            if not element.get(xml.ATTRIBUTE.error, False):
                element.set(xml.ATTRIBUTE.error, str(self.error))
            return False

        self.data = data

        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if xml.UID in original:
                self.uid = original[xml.UID]
                self.data.update({xml.UID:self.uid})
        elif xml.UID in data:
            self.uid = data[xml.UID]
        if xml.MTIME in data:
            self.mtime = data[xml.MTIME]
        if xml.MCI in data:
            self.mci = data[xml.MCI]

        _debug("New item: %s" % self)
        return True

    # -------------------------------------------------------------------------
    def deduplicate(self):

        RESOLVER = "resolve"

        if self.id:
            return

        manager = self.manager
        model = manager.model
        xml = manager.xml
        table = self.table

        if self.original is not None:
            original = self.original
        else:
            original = manager.original(table, self.data)

        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if xml.UID in original:
                self.uid = original[xml.UID]
                self.data.update({xml.UID:self.uid})
        else:
            resolve = model.get_config(self.tablename, RESOLVER)
            if self.data and resolve:
                resolve(self)

        return
        
    # -------------------------------------------------------------------------
    def authorize(self):
        """
            Authorize the import of this item, sets self.permitted
        """

        manager = self.manager
        db = current.db
        authorize = manager.permit

        self.permitted = False

        if not self.tablename:
            return False

        prefix = self.tablename.split("_", 1)[0]
        if prefix in manager.PROTECTED:
            return False

        if not authorize:
            self.permitted = True

        self.method = self.METHOD.CREATE
        if self.id:

            if self.data.deleted is True:
                self.method = self.METHOD.DELETE
                self.accepted = True

            else:
                if not self.original:
                    query = (self.table.id == self.id)
                    self.original = db(query).select(limitby=(0, 1)).first()
                if self.original:
                    self.method = self.METHOD.UPDATE

        if self.method == self.METHOD.CREATE:
            self.id = 0

        if authorize:
            self.permitted = authorize(self.method,
                                       self.tablename,
                                       record_id=self.id)

        return self.permitted

    # -------------------------------------------------------------------------
    def validate(self):
        """
            Validate this item (=record onvalidation), sets self.accepted
        """

        manager = self.manager
        model = manager.model
        xml = manager.xml

        if self.accepted is not None:
            return self.accepted
        if self.data is None:
            return False

        form = Storage()
        form.method = self.method
        form.vars = self.data
        if self.id:
            form.vars.id = self.id
        form.errors = Storage()
        tablename = self.tablename
        key = "%s_onvalidation" % self.method
        onvalidation = model.get_config(tablename, key,
                       model.get_config(tablename, "onvalidation"))
        if onvalidation:
            try:
                callback(onvalidation, form, tablename=tablename)
            except:
                pass # @todo need a better handler here.
        self.accepted = True
        if form.errors:
            for k in form.errors:
                e = self.element.findall("data[@field='%s']" % k)
                if not e:
                    e = self.element
                    form.errors[k] = "[%s] %s" % (k, form.errors[k])
                else:
                    e = e[0]
                e.set(xml.ATTRIBUTE.error,
                      str(form.errors[k]).decode("utf-8"))
            self.error = self.ERROR.VALIDATION_ERROR
            self.accepted = False
        return self.accepted

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit this item to the database

            @param ignore_errors: skip invalid components
                                  (still reports errors)
        """

        manager = self.manager
        db = current.db
        xml = manager.xml
        model = manager.model
        table = self.table

        # Check if already committed
        if self.committed:
            # already committed
            return True

        # If the parent item gets skipped, then skip this item as well
        if self.parent is not None and self.parent.skip:
            return True

        _debug("Committing item %s" % self)

        # Resolve references
        self._resolve_references()

        # Validate
        if not self.validate():
            _debug("Validation error: %s (%s)" % (self.error, xml.tostring(self.element, pretty_print=True)))
            self.skip = True
            return ignore_errors

        elif self.components:
            for component in self.components:
                if not component.validate():
                    _debug("Validation error, component=%s" %
                            component.tablename)
                    component.skip = True
                    # Skip this item on any component validation errors
                    # unless ignore_errors is True
                    if ignore_errors:
                        continue
                    else:
                        self.skip = True
                        return False

        # De-duplicate
        self.deduplicate()

        # Log this item
        if manager.log is not None:
            manager.log(self)

        # Authorize item
        if not self.authorize():
            _debug("Not authorized - skip")
            self.error = manager.ERROR.NOT_PERMITTED
            self.skip = True
            return ignore_errors

        _debug("Method: %s" % self.method)

        # Check if import method is allowed in strategy
        if not isinstance(self.strategy, (list, tuple)):
            self.strategy = [self.strategy]
        if self.method not in self.strategy:
            _debug("Method not in strategy - skip")
            self.error = manager.ERROR.NOT_PERMITTED
            self.skip = True
            return True

        this = self.original
        if not this and self.id and \
           self.method in (self.METHOD.UPDATE, self.METHOD.DELETE):
            query = (table.id == self.id)
            this = db(query).select(limitby=(0, 1)).first()
        this_mtime = None
        this_mci = 0
        if this:
            if xml.MTIME in table.fields:
                this_mtime = xml.as_utc(this[xml.MTIME])
            if xml.MCI in table.fields:
                this_mci = this[xml.MCI]
        self.mtime = xml.as_utc(self.mtime)

        # Conflict detection
        this_modified = True
        self.modified = True
        self.conflict = False
        last_sync = xml.as_utc(self.job.last_sync)
        if last_sync:
            if this_mtime and this_mtime < last_sync:
                this_modified = False
            if self.mtime and self.mtime < last_sync:
                self.modified = False
            if self.modified and this_modified:
                self.conflict = True

        if self.conflict and \
           self.method in (self.METHOD.UPDATE, self.METHOD.DELETE):
            _debug("Conflict: %s" % self)
            if self.job.onconflict:
                self.job.onconflict(self)

        if self.data is not None:
            data = Storage(self.data)
        else:
            data = Storage()

        # Update existing record
        if self.method == self.METHOD.UPDATE:

            if this:
                if "deleted" in this and this.deleted:
                    policy = self._get_update_policy(None)
                    if policy == self.POLICY.NEWER and \
                       this_mtime and this_mtime > self.mtime or \
                       policy == self.POLICY.MASTER and \
                       (this_mci == 0 or self.mci != 1):
                        self.skip = True
                        return True
                fields = data.keys()
                for f in fields:
                    if isinstance(this[f], datetime):
                        if xml.as_utc(data[f]) == xml.as_utc(this[f]):
                            del data[f]
                            continue
                    else:
                        if data[f] == this[f]:
                            del data[f]
                            continue
                    remove = False
                    policy = self._get_update_policy(f)
                    if policy == self.POLICY.THIS:
                        remove = True
                    elif policy == self.POLICY.NEWER:
                        if this_mtime and this_mtime > self.mtime:
                            remove = True
                    elif policy == self.POLICY.MASTER:
                        if this_mci == 0 or self.mci != 1:
                            remove = True
                    if remove:
                        del data[f]
                        self.data.update({f:this[f]})

            if not self.skip and not self.conflict and \
               (len(data) or self.components or self.references):
                if self.uid and xml.UID in table:
                    data.update({xml.UID:self.uid})
                if xml.MTIME in table:
                    data.update({xml.MTIME: self.mtime})
                if xml.MCI in data:
                    # retain local MCI on updates
                    del data[xml.MCI]
                if "deleted" in table.fields:
                    # Undelete re-imported records:
                    data.update(deleted=False)
                query = (table._id == self.id)
                try:
                    success = db(query).update(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return False
                if success:
                    self.committed = True
            else:
                # Nothing to update
                self.committed = True

        # Create new record
        elif self.method == self.METHOD.CREATE:

            # Do not apply field policy to UID and MCI
            if xml.UID in data:
                del data[xml.UID]
            if xml.MCI in data:
                del data[xml.MCI]

            for f in data:
                policy = self._get_update_policy(f)
                if policy == self.POLICY.MASTER and self.mci != 1:
                    del data[f]

            if len(data) or self.components or self.references:

                # Restore UID and MCI
                if self.uid and xml.UID in table.fields:
                    data.update({xml.UID:self.uid})
                if xml.MCI in table.fields:
                    data.update({xml.MCI:self.mci})

                # Insert the new record
                try:
                    success = table.insert(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return False
                if success:
                    self.id = success
                    self.committed = True

            else:
                # Nothing to create
                self.skip = True
                return True

        # Delete local record
        elif self.method == self.METHOD.DELETE:

            if this:
                if this.deleted:
                    self.skip = True
                policy = self._get_update_policy(None)
                if policy == self.POLICY.THIS:
                    self.skip = True
                elif policy == self.POLICY.NEWER and \
                     (this_mtime and this_mtime > self.mtime):
                    self.skip = True
                elif policy == self.POLICY.MASTER and \
                     (this_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                prefix, name = self.tablename.split("_", 1)
                resource = manager.define_resource(prefix, name, id=self.id)

                ondelete = model.get_config(self.tablename, "ondelete")
                success = resource.delete(ondelete=ondelete,
                                          cascade=True)
                if resource.error:
                    self.error = resource.error
                    self.skip = True
                    return ignore_errors

            _debug("Success: %s, id=%s %sd" % (self.tablename, self.id,
                                               self.skip and "skippe" or \
                                               self.method))
            return True

        # Audit + onaccept on successful commits
        if self.committed:
            form = Storage()
            form.method = self.method
            form.vars = self.data
            tablename = self.tablename
            prefix, name = tablename.split("_", 1)
            if self.id:
                form.vars.id = self.id
            if manager.audit is not None:
                manager.audit(self.method, prefix, name,
                              form=form,
                              record=self.id,
                              representation="xml")
            model.update_super(table, form.vars)
            if self.method == self.METHOD.CREATE:
                manager.auth.s3_set_record_owner(table, self.id)
            key = "%s_onaccept" % self.method
            onaccept = model.get_config(tablename, key,
                       model.get_config(tablename, "onaccept"))
            if onaccept:
                callback(onaccept, form, tablename=self.tablename)

        # Update referencing items
        if self.update and self.id:
            for u in self.update:
                item = u.get("item", None)
                if not item:
                    continue
                field = u.get("field", None)
                if isinstance(field, (list, tuple)):
                    pkey, fkey = field
                    query = table.id == self.id
                    row = db(query).select(table[pkey],
                                           limitby=(0, 1)).first()
                    if row:
                        item._update_reference(fkey, row[pkey])
                else:
                    item._update_reference(field, self.id)

        _debug("Success: %s, id=%s %sd" % (self.tablename, self.id,
                                           self.skip and "skippe" or \
                                           self.method))
        return True

    # -------------------------------------------------------------------------
    def _get_update_policy(self, field):
        """
            Get the update policy for a field (if the item will
            update an existing record)

            @param field: the name of the field
        """

        if isinstance(self.update_policy, dict):
            r = self.update_policy.get(field,
                self.update_policy.get("__default__", self.POLICY.THIS))
        else:
            r = self.update_policy
        if not r in self.POLICY.values():
            r = self.POLICY.THIS
        return r

    # -------------------------------------------------------------------------
    def _resolve_references(self):
        """
            Resolve the references of this item (=look up all foreign
            keys from other items of the same job). If a foreign key
            is not yet available, it will be scheduled for later update.
        """

        manager = self.manager
        model = manager.model
        db = current.db

        items = self.job.items
        for reference in self.references:

            item = None
            field = reference.field
            entry = reference.entry
            if not entry:
                continue

            # Resolve key tuples
            if isinstance(field, (list,tuple)):
                pkey, fkey = field
            else:
                pkey, fkey = ("id", field)

            # Resolve the key table name
            fieldtype = str(self.table[fkey].type)
            multiple = False
            if fieldtype[:9] == "reference":
                ktablename = fieldtype[10:]
            elif fieldtype[:14] == "list:reference":
                ktablename = fieldtype[15:]
                multiple = True
            else:
                continue
            if entry.tablename:
                ktablename = entry.tablename
            try:
                model.load(ktablename)
                ktable = db[ktablename]
            except:
                continue

            # Resolve the foreign key (value)
            fk = entry.id
            if entry.item_id:
                item = items[entry.item_id]
                if item:
                    fk = item.id
            if fk and pkey != "id":
                row = db(ktable._id == fk).select(ktable[pkey],
                                                  limitby=(0, 1)).first()
                if not row:
                    fk = None
                    continue
                else:
                    fk = row[pkey]

            # Update record data
            if fk:
                if multiple:
                    val = self.data.get(fkey, [])
                    if fk not in val:
                        val.append(fk)
                    self.data[fkey] = val
                else:
                    self.data[fkey] = fk
            else:
                if fkey in self.data and not multiple:
                    del self.data[fkey]
                if item:
                    item.update.append(dict(item=self, field=fkey))

    # -------------------------------------------------------------------------
    def _update_reference(self, field, value):
        """
            Helper method to update a foreign key in an already written
            record. Will be called by the referenced item after (and only
            if) it has been committed. This is only needed if the reference
            could not be resolved before commit due to circular references.

            @param field: the field name of the foreign key
            @param value: the value of the foreign key
        """

        db = current.db
        if not value:
            return
        if self.id and self.permitted:
            fieldtype = str(self.table[field].type)
            if fieldtype.startswith("list:reference"):
                query = (self.table.id == self.id)
                record = db(query).select(self.table[field],
                                          limitby=(0,1)).first()
                if record:
                    values = record[field]
                    if value not in values:
                        values.append(value)
                        db(self.table.id == self.id).update(**{field:values})
            else:
                db(self.table.id == self.id).update(**{field:value})

    # -------------------------------------------------------------------------
    def store(self, item_table=None):
        """
            Store this item in the DB
        """

        manager = self.manager
        db = current.db
        xml = manager.xml

        _debug("Storing item %s" % self)
        if item_table is None:
            return None
        query = item_table.item_id == self.item_id
        row = db(query).select(item_table.id, limitby=(0, 1)).first()
        if row:
            record_id = row.id
        else:
            record_id = None
        record = Storage(job_id = self.job.job_id,
                         item_id = self.item_id,
                         tablename = self.tablename,
                         record_uid = self.uid,
                         error = self.error)
        if self.element is not None:
            element_str = xml.tostring(self.element,
                                       xml_declaration=False)
            record.update(element=element_str)
        if self.data is not None:
            data = Storage()
            for f in self.data.keys():
                table = self.table # Graeme added July 30th
                if f not in table.fields:
                    continue
                fieldtype = str(self.table[f].type)
                if fieldtype == "id" or \
                   fieldtype[:9] == "reference" or \
                   fieldtype[:14] == "list:reference":
                    continue
                data.update({f:self.data[f]})
            data_str = cPickle.dumps(data)
            record.update(data=data_str)
        ritems = []
        for reference in self.references:
            field = reference.field
            entry = reference.entry
            if entry and entry.item_id is not None:
                ritems.append(simplejson.dumps(dict(field=field,
                                              item_id=str(entry.item_id))))
        if ritems:
            record.update(ritems=ritems)
        citems = [c.item_id for c in self.components]
        if citems:
            record.update(citems=citems)
        if self.parent:
            record.update(parent=self.parent.item_id)
        if record_id:
            db(item_table.id == record_id).update(**record)
        else:
            record_id = item_table.insert(**record)
        _debug("Record ID=%s" % record_id)
        return record_id

    # -------------------------------------------------------------------------
    def restore(self, row):
        """
            Restore an item from a item table row. This does not restore
            the references (since this can not be done before all items
            are restored), must call job.restore_references() to do that

            @param row: the item table row
        """

        manager = self.manager
        model = manager.model
        xml = manager.xml
        db = current.db

        self.item_id = row.item_id
        self.accepted = None
        self.permitted = False
        self.committed = False
        tablename = row.tablename
        self.id = None
        self.uid = row.record_uid
        if row.data is not None:
            self.data = cPickle.loads(row.data)
        else:
            self.data = Storage()
        data = self.data
        if xml.MTIME in data:
            self.mtime = data[xml.MTIME]
        if xml.MCI in data:
            self.mci = data[xml.MCI]
        if xml.UID in data:
            self.uid = data[xml.UID]
        self.element = etree.fromstring(row.element)
        if row.citems:
            self.load_components = row.citems
        if row.ritems:
            self.load_references = [simplejson.loads(ritem) for ritem in row.ritems]
        self.load_parent = row.parent
        try:
            model.load(tablename)
            table = db[tablename]
        except:
            self.error = self.ERROR.BAD_RESOURCE
            return False
        else:
            self.table = table
            self.tablename = tablename
        original = manager.original(table, self.data)
        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if xml.UID in original:
                self.uid = original[xml.UID]
                self.data.update({xml.UID:self.uid})
        self.error = row.error
        if self.error and not self.data:
            # Validation error
            return False
        return True

# =============================================================================
class S3ImportJob():
    """
        Class to import an element tree into the database
    """

    JOB_TABLE_NAME = "s3_import_job"
    ITEM_TABLE_NAME = "s3_import_item"

    # -------------------------------------------------------------------------
    def __init__(self, manager, table,
                 tree=None,
                 files=None,
                 job_id=None,
                 strategy=None,
                 update_policy=None,
                 conflict_policy=None,
                 last_sync=None,
                 onconflict=None):
        """
            Constructor

            @param manager: the S3RequestManager instance performing this job
            @param tree: the element tree to import
            @param files: files attached to the import (for upload fields)
            @param job_id: restore job from database (record ID or job_id)
            @param strategy: the import strategy
            @param update_policy: the update policy
            @param conflict_policy: the conflict resolution policy
            @param last_sync: the last synchronization time stamp (datetime)
            @param onconflict: custom conflict resolver function
        """

        self.manager = manager
        db = current.db

        xml = manager.xml

        self.error = None # the last error
        self.error_tree = etree.Element(xml.TAG.root)

        self.table = table
        self.tree = tree
        self.files = files
        self.directory = Storage()

        self.elements = Storage()
        self.items = Storage()
        self.references = []

        self.job_table = None
        self.item_table = None

        # Import strategy
        self.strategy = strategy
        if self.strategy is None:
            self.strategy = [S3ImportItem.METHOD.CREATE,
                             S3ImportItem.METHOD.UPDATE,
                             S3ImportItem.METHOD.DELETE]
        if not isinstance(self.strategy, (tuple, list)):
            self.strategy = [self.strategy]

        # Update policy (default=always update)
        self.update_policy = update_policy
        if not self.update_policy:
            self.update_policy = S3ImportItem.POLICY.OTHER
        # Conflict resolution policy (default=always update)
        self.conflict_policy = conflict_policy
        if not self.conflict_policy:
            self.conflict_policy = S3ImportItem.POLICY.OTHER

        # Synchronization settings
        self.last_sync = last_sync
        self.onconflict = onconflict

        if job_id:
            self.__define_tables()
            jobtable = self.job_table
            if str(job_id).isdigit():
                query = jobtable.id == job_id
            else:
                query = jobtable.job_id == job_id
            row = db(query).select(limitby=(0, 1)).first()
            if not row:
                raise SyntaxError("Job record not found")
            self.job_id = row.job_id
            if not self.table:
                tablename = row.tablename
                try:
                    model.load(tablename)
                    table = db[tablename]
                except:
                    pass
        else:
            self.job_id = uuid.uuid4() # unique ID for this job

    # -------------------------------------------------------------------------
    def add_item(self,
                 element=None,
                 original=None,
                 components=None,
                 parent=None,
                 joinby=None):
        """
            Parse and validate an XML element and add it as new item
            to the job.

            @param element: the element
            @param original: the original DB record (if already available,
                             will otherwise be looked-up by this function)
            @param components: a dictionary of components (as in S3Resource)
                               to include in the job (defaults to all
                               defined components)
            @param parent: the parent item (if this is a component)
            @param joinby: the component join key(s) (if this is a component)

            @returns: a unique identifier for the new item, or None if there
                      was an error. self.error contains the last error, and
                      self.error_tree an element tree with all failing elements
                      including error attributes.
        """

        manager = self.manager
        model = manager.model
        xml = manager.xml
        db = current.db

        if element in self.elements:
            # element has already been added to this job
            return self.elements[element]

        # Parse the main element
        item = S3ImportItem(self)

        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        if element is not None:
            self.elements[element] = item_id

        if not item.parse(element,
                          original=original,
                          files=self.files):
            self.error = item.error
            item.accepted = False
            if parent is None:
                self.error_tree.append(deepcopy(item.element))

        else:
            # Now parse the components
            table = item.table

            components = model.get_components(table, names=components)
            for alias in components:
                component = components[alias]
                pkey = component.pkey
                if component.linktable:
                    ctable = component.linktable
                    ctablename = ctable._tablename
                    fkey = component.lkey
                else:
                    ctable = component.table
                    ctablename = component.tablename
                    fkey = component.fkey
                    
                celements = xml.select_resources(element, ctablename)
                if celements:
                    original = None
                    if not component.multiple:
                        uid = None
                        if item.id:
                            query = (table.id == item.id) & \
                                    (table[pkey] == ctable[fkey])
                            original = db(query).select(ctable.ALL,
                                                        limitby=(0, 1)).first()
                            if original:
                                uid = original.get(xml.UID, None)
                        celements = [celements[0]]
                        if uid:
                            celements[0].set(xml.UID, uid)

                    for celement in celements:
                        item_id = self.add_item(element=celement,
                                                original=original,
                                                parent=item,
                                                joinby=(pkey, fkey))
                        if item_id is None:
                            item.error = self.error
                            self.error_tree.append(deepcopy(item.element))
                        else:
                            citem = self.items[item_id]
                            citem.parent = item
                            item.components.append(citem)

            # Handle references
            table = item.table
            tree = self.tree
            if tree is not None:
                rfields = filter(lambda f:
                                 str(table[f].type)[:9] == "reference" or
                                 str(table[f].type)[:14] == "list:reference",
                                 table.fields)
                item.references = self.lookahead(element,
                                                 table=table,
                                                 fields=rfields,
                                                 tree=tree,
                                                 directory=self.directory)
                for reference in item.references:
                    entry = reference.entry
                    if entry and entry.element is not None:
                        item_id = self.add_item(element=entry.element)
                        if item_id:
                            entry.update(item_id=item_id)

            # Parent reference
            if parent is not None:
                entry = Storage(item_id=parent.item_id,
                                element=parent.element,
                                tablename=parent.tablename)
                item.references.append(Storage(field=joinby,
                                               entry=entry))

        return item.item_id

    # -------------------------------------------------------------------------
    def lookahead(self,
                  element,
                  table=None,
                  fields=None,
                  tree=None,
                  directory=None):
        """
            Find referenced elements in the tree

            @param element: the element
            @param table: the DB table
            @param fields: the FK fields in the table
            @param tree: the import tree
            @param directory: a dictionary to lookup elements in the tree
                              (will be filled in by this function)
        """

        manager = self.manager
        db = current.db
        xml = manager.xml
        model = manager.model
        reference_list = []

        root = None
        if tree is not None:
            if isinstance(tree, etree._Element):
                root = tree
            else:
                root = tree.getroot()
        references = element.findall("reference")
        for reference in references:
            field = reference.get(xml.ATTRIBUTE.field, None)
            # Ignore references without valid field-attribute
            if not field or field not in fields:
                continue
            # Find the key table
            multiple = False
            fieldtype = str(table[field].type)
            if fieldtype.startswith("reference"):
                ktablename = fieldtype[10:]
            elif fieldtype.startswith("list:reference"):
                ktablename = fieldtype[15:]
                multiple = True
            else:
                # ignore if the field is not a reference type
                continue
            try:
                model.load(ktablename)
                ktable = db[ktablename]
            except:
                # Invalid tablename - skip
                continue
            tablename = reference.get(xml.ATTRIBUTE.resource, None)
            # Ignore references to tables without UID field:
            if xml.UID not in ktable.fields:
                continue
            # Fall back to key table name if tablename is not specified:
            if not tablename:
                tablename = ktablename
            # Super-entity references must use the super-key:
            if tablename != ktablename:
                if field != ktable._id.name:
                    continue
                else:
                    field = (field, field)
            # Ignore direct references to super-entities:
            if tablename == ktablename and ktable._id.name != "id":
                continue
            # Get the foreign key
            uids = reference.get(xml.UID, None)
            attr = xml.UID
            if not uids:
                uids = reference.get(xml.ATTRIBUTE.tuid, None)
                attr = xml.ATTRIBUTE.tuid
            if uids and multiple:
                uids = simplejson.loads(uids)
            elif uids:
                uids = [uids]

            # Find the elements and map to DB records
            relements = []

            # Create a UID<->ID map
            id_map = Storage()
            if attr == xml.UID and uids:
                _uids = map(xml.import_uid, uids)
                query = ktable[xml.UID].belongs(_uids)
                records = db(query).select(ktable.id,
                                           ktable[xml.UID])
                id_map = dict([(r[xml.UID], r.id) for r in records])

            if not uids:
                # Anonymous reference: <resource> inside the element
                expr = './/%s[@%s="%s"]' % (xml.TAG.resource,
                                            xml.ATTRIBUTE.name,
                                            tablename)
                relements = reference.xpath(expr)
                if relements and not multiple:
                    relements = [relements[0]]

            elif root is not None:

                for uid in uids:

                    entry = None
                    # Entry already in directory?
                    if directory is not None:
                        entry = directory.get((tablename, attr, uid), None)
                    if not entry:
                        expr = './/%s[@%s="%s" and @%s="%s"]' % (
                                    xml.TAG.resource,
                                    xml.ATTRIBUTE.name,
                                    tablename,
                                    attr,
                                    uid)
                        e = root.xpath(expr)
                        if e:
                            # Element in the source => append to relements
                            relements.append(e[0])
                        else:
                            # No element found, see if original record exists
                            _uid = xml.import_uid(uid)
                            if _uid and _uid in id_map:
                                _id = id_map[_uid]
                                entry = Storage(tablename=tablename,
                                                element=None,
                                                uid=uid,
                                                id=_id,
                                                item_id=None)
                                reference_list.append(Storage(field=field,
                                                              entry=entry))
                            else:
                                continue
                    else:
                        reference_list.append(Storage(field=field,
                                                      entry=entry))

            # Create entries for all newly found elements
            for relement in relements:
                uid = relement.get(attr, None)
                if attr == xml.UID:
                    _uid = xml.import_uid(uid)
                    id = _uid and id_map and id_map.get(_uid, None) or None
                else:
                    _uid = None
                    id = None
                entry = Storage(tablename=tablename,
                                element=relement,
                                uid=uid,
                                id=id,
                                item_id=None)
                # Add entry to directory
                if uid and directory is not None:
                    directory[(tablename, attr, uid)] = entry
                # Append the entry to the reference list
                reference_list.append(Storage(field=field, entry=entry))

        return reference_list

    # -------------------------------------------------------------------------
    def load_item(self, row):
        """
            Load an item from the item table (counterpart to add_item
            when restoring a job from the database)
        """

        item = S3ImportItem(self)
        if not item.restore(row):
            self.error = item.error
            if item.load_parent is None:
                self.error_tree.append(deepcopy(item.element))
        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        return item_id

    # -------------------------------------------------------------------------
    def resolve(self, item_id, import_list):
        """
            Resolve the reference list of an item

            @param item_id: the import item UID
            @param import_list: the ordered list of items (UIDs) to import
        """

        item = self.items[item_id]
        if item.lock or item.accepted is False:
            return False
        references = []
        for reference in item.references:
            entry = reference.entry
            if entry.item_id:
                references.append(entry.item_id)
        for ritem_id in references:
            if ritem_id in import_list:
                continue
            else:
                item.lock = True
                if self.resolve(ritem_id, import_list):
                    import_list.append(ritem_id)
                item.lock = False
        return True

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit the import job to the DB

            @param ignore_errors: skip any items with errors
                                  (does still report the errors)
        """

        manager = self.manager
        model = manager.model
        xml = manager.xml

        # Resolve references
        import_list = []
        for item_id in self.items:
            self.resolve(item_id, import_list)
            if item_id not in import_list:
                import_list.append(item_id)
        imports = [self.items[_id] for _id in import_list]
        # Commit the items
        for item in imports:
            error = None
            success = item.commit(ignore_errors=ignore_errors)
            error = item.error
            if error:
                self.error = error
                element = item.element
                if element is not None:
                    element.set(xml.ATTRIBUTE.error, str(self.error))
                    self.error_tree.append(deepcopy(element))
                if not ignore_errors:
                    return False
        return True

    # -------------------------------------------------------------------------
    def __define_tables(self):
        """
            Define the database tables for jobs and items
        """

        self.job_table = self.define_job_table()
        self.item_table = self.define_item_table()

    # -------------------------------------------------------------------------
    @classmethod
    def define_job_table(cls):

        db = current.db
        if cls.JOB_TABLE_NAME not in db:
            job_table = db.define_table(cls.JOB_TABLE_NAME,
                                        Field("job_id", length=128,
                                              unique=True,
                                              notnull=True),
                                        Field("tablename"),
                                        Field("timestmp", "datetime",
                                              default=datetime.utcnow()))
        else:
            job_table = db[cls.JOB_TABLE_NAME]
        return job_table

    # -------------------------------------------------------------------------
    @classmethod
    def define_item_table(cls):

        db = current.db
        if cls.ITEM_TABLE_NAME not in db:
            item_table = db.define_table(cls.ITEM_TABLE_NAME,
                                        Field("item_id", length=128,
                                              unique=True,
                                              notnull=True),
                                        Field("job_id", length=128),
                                        Field("tablename", length=128),
                                        #Field("record_id", "integer"),
                                        Field("record_uid"),
                                        Field("error", "text"),
                                        Field("data", "text"),
                                        Field("element", "text"),
                                        Field("ritems", "list:string"),
                                        Field("citems", "list:string"),
                                        Field("parent", length=128))
        else:
            item_table = db[cls.ITEM_TABLE_NAME]
        return item_table

    # -------------------------------------------------------------------------
    def store(self):
        """
            Store this job and all its items in the job table
        """

        manager = self.manager
        db = current.db

        _debug("Storing Job ID=%s" % self.job_id)
        self.__define_tables()
        jobtable = self.job_table
        query = jobtable.job_id == self.job_id
        row = db(query).select(jobtable.id, limitby=(0, 1)).first()
        if row:
            record_id = row.id
        else:
            record_id = None
        record = Storage(job_id=self.job_id)
        try:
            tablename = self.table._tablename
        except:
            pass
        else:
            record.update(tablename=tablename)
        for item in self.items.values():
            item.store(item_table=self.item_table)
        if record_id:
            db(jobtable.id == record_id).update(**record)
        else:
            record_id = jobtable.insert(**record)
        _debug("Job record ID=%s" % record_id)
        return record_id

    # -------------------------------------------------------------------------
    def delete(self):
        """
            Delete this job and all its items from the job table
        """

        db = current.db

        _debug("Deleting job ID=%s" % self.job_id)
        self.__define_tables()
        item_table = self.item_table
        query = item_table.job_id == self.job_id
        db(query).delete()
        job_table = self.job_table
        query = job_table.job_id == self.job_id
        db(query).delete()

    # -------------------------------------------------------------------------
    def restore_references(self):
        """
            Restore the job's reference structure after loading items
            from the item table
        """

        for item in self.items.values():
            for citem_id in item.load_components:
                if citem_id in self.items:
                    item.components.append(self.items[citem_id])
            item.load_components = []
            for ritem in item.load_references:
                field = ritem["field"]
                item_id = ritem["item_id"]
                if item_id in self.items:
                    _item = self.items[item_id]
                    entry = Storage(tablename=_item.tablename,
                                    element=_item.element,
                                    uid=_item.uid,
                                    id=_item.id,
                                    item_id=item_id)
                    item.references.append(Storage(field=field,
                                                   entry=entry))
            item.load_references = []
            if item.load_parent is not None:
                item.parent = self.items[item.load_parent]
                item.load_parent = None

# =============================================================================
