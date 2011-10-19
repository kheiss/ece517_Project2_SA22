# -*- coding: utf-8 -*-

"""
    S3 Contingency Table Toolkit

    @author: Dominic König <dominic[at]aidiq[dot]com>

    @copyright: 2011 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{Python 2.7}} <http://www.python.org>}
    @requires: U{B{I{SciPy}} <http://www.scipy.org>}
    @requires: U{B{I{NumPy}} <http://www.numpy.org>}
    @requires: U{B{I{MatPlotLib}} <http://matplotlib.sourceforge.net>}
    @requires: U{B{I{PyvtTbl}} <http://code.google.com/p/pyvttbl>}
    @requires: U{B{I{SQLite3}} <http://www.sqlite.org>}

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

__all__ = ["S3Cube"]

import sys

from gluon import current
from gluon.storage import Storage
from gluon.html import *
try:
    from pyvttbl import DataFrame
    PYVTTBL = True
except ImportError:
    print >> sys.stderr, "WARNING: S3Cube unresolved dependencies: scipy, numpy and matplotlib required for analyses"
    PYVTTBL = False
if sys.version_info[0] != 2 or \
   sys.version_info[1] != 7:
    print >> sys.stderr, "WARNING: S3Cube unresolved dependencies: Python 2.7 required for analyses"
    PYVTTBL = False

from s3crud import S3CRUD

# =============================================================================

class S3Cube(S3CRUD):
    """ RESTful method handler to generate contingency tables """

    def __init__(self):

        pass

    def apply_method(self, r, **attr):

        db = current.db

        response = current.response

        if not PYVTTBL:
            r.error(501, "Function not available on this server")

        if r.interactive:

            # Get rows, cols, fact and aggregate from URL
            if "row" in r.get_vars:
                rowname = r.get_vars["row"]
                self.rows = [rowname]
            else:
                r.error(400, "Missing row parameter")
            if "col" in r.get_vars:
                colname = r.get_vars["col"]
                self.cols = [colname]
            else:
                r.error(400, "Missing col parameter")
            if "fact" in r.get_vars:
                self.fact = r.get_vars["fact"]
            else:
                r.error(400, "Missing fact parameter")
            if "aggregate" in r.get_vars:
                self.aggregate = r.get_vars["aggregate"]
            else:
                self.aggregate = "group_concat"

            # Get the fields
            fields = []
            if self.rows:
                fields.extend([f for f in self.rows if f not in fields])
            if self.cols:
                fields.extend([f for f in self.cols if f not in fields])
            if self.fact and self.fact not in fields:
                fields.append(self.fact)
            list_fields = list(fields)
            lfields, join = self.get_list_fields(self.resource.table, list_fields)
            lfields = Storage([(f.fieldname, f) for f in lfields])

            # Get the items
            items = self.sqltable(list_fields, as_list=True)

            # Map the items into a data frame
            df = DataFrame()
            for row in items:
                frow = Storage()
                for field in fields:
                    lfield = lfields[field]
                    tname = lfield.tname
                    fname = lfield.fname
                    if fname in row:
                        value = row[fname]
                    elif tname in row and fname in row[tname]:
                        value = row[tname][fname]
                    else:
                        value = None
                    frow[field] = value
                df.insert(frow)

            # Pivot table
            try:
                pt = df.pivot(self.fact, self.rows, self.cols, aggregate=self.aggregate)
            except:
                r.error(400, "Could not generate contingency table", next=r.url(method=""))

            items = S3ContingencyTable(pt,
                                       rows=self.rows,
                                       cols=self.cols,
                                       fact=self.fact,
                                       lfields=lfields,
                                       _id="list",
                                       _class="dataTable display")

            output = dict(items=items)

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        response.s3.no_sspag = True
        response.view = self._view(r, "list.html")

        return output

# =============================================================================

class S3ContingencyTable(TABLE):

    def __init__(self,
                 ptable,
                 rows=[],
                 cols=[],
                 fact=None,
                 lfields=None,
                 **attributes):

        manager = current.manager

        TABLE.__init__(self, **attributes)
        self.components = []

        rnames = ptable.rnames
        cnames = ptable.cnames
        components = self.components

        headers = TR([TH(lfields[f].label) for f in rows])
        for cn in cnames:
            header = ""
            for colname, value in cn:
                lf = lfields[colname]
                if lf.field:
                    v = manager.represent(lf.field, value, strip_markup=True)
                else:
                    v = value
                label = lf.label
                h = "%s: %s" % (label, v)
                if header:
                    header = "%s, %s" % (header, h)
                else:
                    header = h
            headers.append(TH(header))
        components.append(THEAD(headers))

        ff = lfields[fact]

        i = 0
        tbody = TBODY()
        for item in ptable:
            rheaders = rnames[i]
            if i % 2:
                _class = "odd"
            else:
                _class = "even"
            tr = TR(_class=_class)
            for colname, value in rheaders:
                lf = lfields[colname]
                if lf.field:
                    v = manager.represent(lf.field, value, strip_markup=True)
                else:
                    v = value
                tr.append(TD(v))
            for value in item:
                if value is None:
                    v = "-"
                elif ff.field:
                    v = manager.represent(ff.field, value, strip_markup=True)
                else:
                    v = value
                tr.append(TD(v))
            tbody.append(tr)
            i += 1
        components.append(tbody)

# =============================================================================
