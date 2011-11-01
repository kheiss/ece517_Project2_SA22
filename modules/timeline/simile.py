import logging
import json
import xml

from datetime import datetime, date, time

from gluon import *

class SimileTimeline(object):
    """Timeline using Simile Widgets implementation"""

    # An example of running this might be:
    # From "python web2py.py -S eden -M" console
    #
    # simile = local_import('timeline/simile')
    # tl = simile.SimileTimeline()
    # tl.addEventSource(table=db.irs_ireport, title='name', desc='message', start='datetime')
    # timeline = tl.generateCode()
    # return dict(timeline=timeline)

    # Notes:
    #
    # The addEventSource() and addEvent() methods could probably be moved into their
    # own class for generating and checking events.  This would allow this class to be reusable
    # across different timeline implementations potentially.

    # This is the path to the timeline javascript library
    # Should this be local instead?
    _SRC_URL = 'http://api.simile-widgets.org/timeline/2.3.1/timeline-api.js?bundle=true'

    # This maps the default timeline intervals
    _INTERVAL_MAP = {
        'SEC' : 'Timeline.DateTime.SECOND',
        'MIN' : 'Timeline.DateTime.MINUTE',
        'HOUR' : 'Timeline.DateTime.HOUR',
        'DAY' : 'Timeline.DateTime.DAY',
        'WEEK' : 'Timeline.DateTime.WEEK',
        'MONTH' : 'Timeline.DateTime.MONTH',
        'YEAR' : 'Timeline.DateTime.YEAR',
    }

    def __init__(self):
        # Sources point to a database table and map the rows to timeline parameters.  Every
        # time the data is generated, this information is pulled from the database.
        self.sources = []

        # Events are manually entered and allow for events not originating from the database.
        # Because they do not point to the database, these entries do not get updated unless
        # done so manually.
        self.events = []

        # Default timeline scales
        self.mainTimelineScale = 'WEEK'
        self.overviewTimelineScale = 'MONTH'

    
    # Need to define this to actually log to web2py
    def _log(self, msg):
        print msg


    # Accessor methods for mainTimelineScale
    def setMainTimelineScale(self, scale):
        if scale in self._INTERVAL_MAP:
            self.mainTimelineScale = scale
            return True
        else:
            return False


    # Accessor methods for mainTimelineScale
    def getMainTimelineScale(self):
        return self.mainTimelineScale


    # Accessor methods for overviewTimelineScale
    def setOverviewTimelineScale(self, scale):
        if scale in self._INTERVAL_MAP:
            self.overviewTimelineScale = scale
            return True
        else:
            return False


    # Accessor methods for overviewTimelineScale
    def getOverviewTimelineScale(self):
        return self.overviewTimelineScale


    # This function doesn't take actual data as parameters but rather information that it
    # uses to query the database. This information is then used to convert the database
    # query into data that the timeline can read.
    def addEventSource(self, table=None, filter=None, title=None, desc=None, start=None, end=None):
        if table == None:
            self._log("A database table must be provided!")
            return False
        if title == None:
            self._log("A title mapping must be provided!")
            return False
        if start == None:
            self._log("A start mapping must be provided!")
            return False

        # We could probably put this in a new class called EventSource
        source = {}
        source['table'] = table
        source['filter'] = filter
        source['title'] = title
        source['desc'] = desc
        source['start'] = start
        source['end'] = end
        self.sources.append(source)
        return True


    # The dates entered here must either be of type date or datetime
    def addEvent(self, title=None, desc=None, start=None, end=None):
        if title == None:
            self._log("A title must be provided!")
            return False
        elif start == None:
            self._log("A start date must be provided!")
            return False

        event = {}
        event['title'] = title
        event['description'] = desc
        event['start'] = self._formatTime(start)
        if end != None:
            event['end'] = self._formatTime(end)
            event['durationEvent'] = True
        else:
            event['durationEvent'] = False

        self.events.append(event)
        return True


    # This function generates data structures that will eventually be fed to the timeline
    def _generateData(self):
        data = {}
        data['dateTimeFormat'] = 'iso8601'
        data['events'] = []

        # Add the data provided by the event sources
        for source in self.sources:
            # Define these for convenience
            table = source['table']
            filter = source['filter']
            title = source['title']
            desc = source['desc']
            start = source['start']
            end = source['end']

            # Get our table entries and filter them if needed
            db = table._db
            rows = db(table).select()
            if filter != None and callable(filter):
                rows = rows.find(filter) 

            for row in rows:
                event = {}
                
                # Get titles and descriptions
                event['title'] = self._getStringRepresentation(table, row, title)
                if event['title'] == None:
                    continue

                if desc != None:
                    event['description'] = self._getStringRepresentation(table, row, desc)
                    if event['description'] == None:
                        continue
                    
                # When doing these row accesses, we make sure they actually exist
                # and catch any exceptions, skipping that entry
                try:
                    event['start'] = self._formatTime(row[start])

                    if end != None:
                        event['end'] = self._formatTime(row[end])
                        event['durationEvent'] = True
                    else:
                        event['durationEvent'] = False
                except KeyError as detail:
                    self._log("Caught error: %s\n Skipping..." % detail)
                    continue

                data['events'].append(event)

        # Add the static event data
        for event in self.events:
            data['events'].append(event)

        return data


    # Attempts to use the represent lambda attribute to transform an otherwise
    # incoherent piece of data
    # Also has the ability to interpret lambda functions and use them to generate a 
    # string.
    def _getStringRepresentation(self, table, row, attr):
        # We do a lot of accesses with potential exceptions here, so lets just
        # wrap the whole thing in a try block
        try:
            # Check to see if the mapping is a lambda. If so, lets use it to get
            # the string
            if attr != None and callable(attr):
                return attr(row)
            
            # Simple sanity check for empty values
            if table == None or row[attr] == None:
                return row[attr]

            # Check to see if we got a represent lambda and run it, otherwise return the 
            # string value of the Field
            repLambda = eval("table.%s.represent" % attr)
            if repLambda != None and callable(repLambda):
                return str(repLambda(row[attr]))
            else:
                return row[attr]
        except KeyError as detail:  # Does this catch all of the possible exceptions?
            self._log("Caught error: %s\n Skipping..." % detail)
            return None


    # Maybe this needs to be updated to allow parsing text in case the user wishes
    # to add times as a string
    def _formatTime(self, obj):
        if type(obj) is datetime:
            return obj.isoformat('T')
        elif type(obj) is date:
            return datetime.combine(obj, time()).isoformat('T')
        else:
            self._log("Unable to convert from type %s" % type(obj))
            return None


    def _data_to_xml(self):
        return self._generateData().xml()


    def _data_to_json(self):
       return json.dumps(self._generateData())


    # This method is called by the user.  It returns the HTML and Javascript needed
    # to display the timeline.  It also places a reference to the Timeline Javascript
    # in the HEAD so that the Timeline will load correctly.
    def generateCode(self):
        body = []
        code = ""

        # Generate the timeline javascript
        # We should probably have a way for the user to specify the time intervalUnit
        body.append(SCRIPT('''
            var tl;
            function onLoad() {
                var tl_el = document.getElementById("my-timeline");
                var eventSource = new Timeline.DefaultEventSource();
                var theme = Timeline.ClassicTheme.create();

                var event_data = %(event_var)s;

                var bandInfos = [
                    Timeline.createBandInfo({
                        eventSource:    eventSource,
                        date:           "%(date_now)s",
                        width:          "70%%", 
                        intervalUnit:   %(main_scale)s, 
                        intervalPixels: 100
                    }),
                    Timeline.createBandInfo({
                        overview:       true,
                        eventSource:    eventSource,
                        date:           "%(date_now)s",
                        width:          "30%%", 
                        intervalUnit:   %(overview_scale)s, 
                        intervalPixels: 200
                    })
                ];
                bandInfos[1].syncWith = 0;
                bandInfos[1].highlight = true;

                tl = Timeline.create(tl_el, bandInfos);
                tl.showLoadingMessage();
                eventSource.loadJSON(event_data, document.location.href);
                tl.hideLoadingMessage();
            }

            var resizeTimerID = null;
            function onResize() {
                if (resizeTimerID == null) {
                    resizeTimerID = window.setTimeout(function() {
                        resizeTimerID = null;
                        tl.layout();
                    }, 500);
                }
            }
            
            window.onload = onLoad;
            window.onresize = onResize;
        ''' % {
            'event_var': self._data_to_json(), 
            'date_now': datetime.now().isoformat('T'), 
            'main_scale': self._INTERVAL_MAP[self.mainTimelineScale], 
            'overview_scale': self._INTERVAL_MAP[self.overviewTimelineScale]
            } ))
        
        # Generate the body code
        body.append(DIV(_id="my-timeline", _style="height: 300px; border: 1px solid #aaa"))
        body.append(TAG['noscript']("This page uses Javascript to show you a Timeline. Please enable Javascript in your browser to see the full page. Thank you."))

        # Add the timeline library to the HEAD.  While we would generally like to 
        # put it in the body with the rest of the code, there is a bug in the timeline
        # that prevents this from working.
        current.response.s3.scripts_head.append(self._SRC_URL)

        # How should we write this code to the view?  response.write? does s3 have a variant?
        # For now we just convert to a string and return it
        for i in body:
            code += i.xml()

        return code

