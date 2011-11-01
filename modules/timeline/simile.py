import json
import xml
from datetime import datetime, date, time
from gluon import *

from timeline.base import Timeline
from timeline.event import *

class SimileEvent(Event):
    def __init__(self, **kwargs):
        super(SimileEvent, self).__init__(**kwargs)

        self.description = kwargs.get('desc', None)
        self.end = kwargs.get('end', None)

        if self.end != None:
            self.durationEvent = True
        else:
            self.durationEvent = False



class SimileEventSource(EventSource):
    def __init__(self, **kwargs):
        super(SimileEventSource, self).__init__(**kwargs)

        self.description = kwargs.get('desc', None)
        self.end = kwargs.get('end', None)


    # This function is used internally to format date and datetime objects to something
    # we can pass to the timeline
    def _formatTime(self, obj):
        if type(obj) is datetime:
            return obj.isoformat('T')
        elif type(obj) is date:
            return datetime.combine(obj, time()).isoformat('T')
        else:
            return None


    def getEvents(self):
        events = []

        # Get our table entries and filter them if needed
        db = self.table._db
        rows = db(self.table).select()
        if self.filter != None and callable(self.filter):
            rows = rows.find(self.filter) 

        for row in rows:
            event = {}
            
            # Get titles and descriptions
            title = self.getStringRepresentation(self.table, row, self.title)
            if title == None:
                continue

            if self.description != None:
                description = self.getStringRepresentation(self.table, row, self.description)
                if description == None:
                    continue
            else:
                description = None
                
            # When doing these row accesses, we make sure they actually exist
            # and catch any exceptions, skipping that entry
            try:
                start = self._formatTime(row[self.start])

                if self.end != None:
                    end = self._formatTime(row[self.end])
                else:
                    end = None
            except KeyError:
                continue

            event = SimileEvent(title=title, desc=description, start=start, end=end)
            events.append(event)

        return events



class SimileTimeline(Timeline):
    """Timeline using Simile Widgets implementation"""

    # An example of running this might be:
    # From "python web2py.py -S eden -M" console
    #
    # simile = local_import('timeline/simile')
    # tl = simile.SimileTimeline()
    # tl.addEventSource(table=db.irs_ireport, title='name', desc='message', start='datetime')
    # timeline = tl.generateCode()
    # return dict(timeline=timeline)

    # This is the path to the timeline javascript library
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
        source = SimileEventSource(table=table, filter=filter, title=title, desc=desc, start=start, end=end)
        self.sources.append(source)
        return True


    # The dates entered here must either be of type date or datetime
    def addEvent(self, title=None, desc=None, start=None, end=None):
        event = SimileEvent(title=title, desc=desc, start=start, end=end)
        self.events.append(event)
        return True


    # This function generates data structures that will eventually be fed to the timeline
    def _generateData(self):
        data = {}
        data['dateTimeFormat'] = 'iso8601'
        data['events'] = []

        # Add the data provided by the event sources
        for source in self.sources:
            for event in source.getEvents():
                data['events'].append(event.__dict__)

        # Add the static event data
        for event in self.events:
            data['events'].append(event.__dict__)

        return data


    def _data_to_json(self):
        return json.dumps(self._generateData())

    
    # This method is called by the user.  It returns the HTML and Javascript needed
    # to display the timeline.  It also places a reference to the Timeline Javascript
    # in the HEAD so that the Timeline will load correctly.
    def generateCode(self):
        body = []
        code = ""

        # Generate the timeline javascript
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

