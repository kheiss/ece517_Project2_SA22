import logging
import json
import xml

from datetime import datetime, date, time

class SimileTimeline(object):
    """Timeline using Simile Widgets implementation"""

    # An example of running this might be:
    #
    # import applications.eden.modules.timeline.simile as simile
    # tl = simile.SimileTimeline()
    # tl.addEventSource(db=db, query=db.irs_ireport, title='name', desc='message', start='datetime')
    # data = tl.generateData()
    #
    # or if we want the output to be a javascript variable 
    # js_var = tl.events_to_js() 

    # Notes:
    #
    # The addEventSource() and addEvent() methods could probably be moved into their
    # own class for generating and checking events.  This would allow this class to be reusable
    # across different timeline implementations potentially.

    SRC_URL = 'http://api.simile-widgets.org/timeline/2.3.1/timeline-api.js?bundle=true'

    def __init__(self):
        # Sources point to a database query and map the rows to timeline parameters.  Every
        # time the data is generated, this information is pulled from the database.
        self.sources = []

        # Events are manually entered and allow for events not originating from the database.
        # Because they do not point to the database, these entries do not get updated unless
        # done so manually.
        self.events = []

    def log(self, msg):
        print msg

    # This function doesn't take actual data as parameters but rather information that it
    # uses to query the database. This information is then used to convert the database
    # query into data that the timeline can read.
    def addEventSource(self, db=None, query=None, title=None, desc=None, start=None, end=None):
        if db == None:
            self.log("A database connection must be provided!")
            return False
        elif query == None:
            self.log("A query must be provided!")
            return False
        elif title == None:
            self.log("A title mapping must be provided!")
            return False
        elif start == None:
            self.log("A start mapping must be provided!")
            return False

        # We could probably put this in a new class called EventSource
        source = {}
        source['db'] = db
        source['query'] = query
        source['title'] = title
        source['desc'] = desc
        source['start'] = start
        source['end'] = end
        self.sources.append(source)
        return True

    # The dates entered here must either be of type date or datetime
    def addEvent(self, title=None, desc=None, start=None, end=None):
        if title == None:
            self.log("A title must be provided!")
            return False
        elif start == None:
            self.log("A start date must be provided!")
            return False

        event = {}
        event['title'] = title
        event['description'] = desc
        event['start'] = self.formatTime(start)
        if end != None:
            event['end'] = self.formatTime(end)
            event['durationEvent'] = True
        else:
            event['durationEvent'] = False

        self.events.append(event)
        return True

    def generateData(self):
        data = {}
        data['dateTimeFormat'] = 'iso8601'
        data['events'] = []

        # Add the data provided by the event sources
        for source in self.sources:
            db = source['db']
            query = source['query']
            title = source['title']
            desc = source['desc']
            start = source['start']
            end = source['end']
            #for row in db().select(db.irs_ireport.ALL):
            for row in db(query).select():
                event = {}

                # When doing these row accesses, we should make sure they actually exist
                # and catch any exceptions
                event['title'] = row[title]
                event['start'] = self.formatTime(row[start])

                if desc != None and row[desc] != None:
                    event['description'] = row[desc]

                if end != None and row[end] != None:
                    event['end'] = self.formatTime(row[end])
                    event['durationEvent'] = True
                else:
                    event['durationEvent'] = False

                data['events'].append(event)

        # Add the static event data
        for event in self.events:
            data['events'].append(event)

        return data

    # Maybe this needs to be updated to allow parsing text in case the user wishes
    # to add times as a string
    def formatTime(self, obj):
        if type(obj) is datetime:
            return obj.isoformat(' ')
        elif type(obj) is date:
            return datetime.combine(date, time()).isoformat(' ')
        else:
            self.log("Unable to convert from type %s" % type(obj))
            return None

    def data_to_xml(self):
        return self.generateData().xml()

    def data_to_json(self):
       return json.dumps(self.generateData())

    # Not sure if we really need this anymore
    def data_to_js(self):
       return "var event_data = %s;" % self.data_to_json()
    
    def generateCode(self):
        code = '''
    <script src="%(src_url)s" type="text/javascript"></script>
    
    <script>
        function onLoad() {
            var event_data = %(event_var)s;
            var date_now = %(date_now)s;
            var eventSource = new Timeline.DefaultEventSource();
            var bandInfos = [
                Timeline.createBandInfo({
                    eventSource:    eventSource,
                    date:           %(date_now)s,
                    width:          "70%%", 
                    intervalUnit:   Timeline.DateTime.MONTH, 
                    intervalPixels: 100
                }),
                Timeline.createBandInfo({
                    overview:       true,
                    eventSource:    eventSource,
                    date:           %(date_now)s,
                    width:          "30%%", 
                    intervalUnit:   Timeline.DateTime.YEAR, 
                    intervalPixels: 200
                })
            ];
            bandInfos[1].syncWith = 0;
            bandInfos[1].highlight = true;
   
            tl = Timeline.create(document.getElementById("my-timeline"), bandInfos);
            eventSource.loadJSON(event_data, document.location.href);
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
    </script>
        
    <body onload="onLoad();" onresize="onResize();">
        Timeline here
        <div id="my-timeline" style="height: 150px; border: 1px solid #aaa"></div>
        <noscript>
            This page uses Javascript to show you a Timeline. Please enable Javascript in your browser to see the full page. Thank you.
        </noscript>
    </body>
        ''' % {'src_url': self.SRC_URL, 'event_var': self.data_to_json(), 'date_now': datetime.now().isoformat(' ')}

        return code
