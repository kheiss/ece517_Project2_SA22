'''
Created on Oct 29, 2011

To run this test case execute the following command from within the web2py directory:

python web2py.py -N -M -S eden -R applications/eden/tests/unit_tests/modules/timeline/simile/simile.py

The db variable used in this test case is initialized by web2py.
It's a connection to the Eden database. 

@author:
'''
import unittest
import datetime

import applications.eden.modules.timeline.simile as simile

#testDb = DAL('sqlite://simileTimelineTest.db')
#from gluon.globals import Request
## Rename the test database so that functions will use it instead of the real database
#db = testDb  

# create a new test db with fake data
#testDb = DAL('sqlite://simileTimelineTest.db')
#testDb.define_table('timeline', Field('title'), Field('description'), Field('start','datetime'), Field('end','datetime'))
#testDb(testDb.timeline).delete()
#from gluon.contrib.populate import populate
#populate(testDb.timeline,10)
#testDb.commit()

#print "CONTENTS -------"
#print testDb.tables
#print testDb(testDb.timeline).select()

class SimileTimelineTest(unittest.TestCase):


    def setUp(self):
        self.timeLineDataProvider = simile.SimileTimeline()        
        

    def tearDown(self):
        self.timeLineDataProvider = None


    def testConstructor(self):
        # verify that the sources and events lists are initially empty
        self.assertTrue( len(self.timeLineDataProvider.sources) == 0 ) 
        self.assertTrue( len(self.timeLineDataProvider.events) == 0 ) 
        self.assertEquals('WEEK', self.timeLineDataProvider.mainTimelineScale)
        self.assertEquals('MONTH', self.timeLineDataProvider.overviewTimelineScale)
        

    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoParameters(self):
        # addEvent() should set None as the default value for all its parameters.
        # Therefore calling addEvent() with no parameters should be 
        # the same as calling it by passing null title and null start.
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent()
        
    
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoTitleNoStart(self):
        
        self.title = None
        self.description = "Just for fun"
        self.start = None
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoTitle(self):
        
        self.title = None
        self.description = "Just for fun"
        self.start = datetime.datetime.now()
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoStart(self):
        
        self.title = 'My Title'
        self.description = "Just for fun"
        self.start = None
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    def testAddEvent(self):
        
        # event with only title and start as a datetime
        self.title = 'Event 1' # required
        self.description = None # optional
        self.start = datetime.datetime.now() # required
        self.end = None # optional
        
        self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)
        
        # verify that the events list has 1 event
        self.assertTrue( len(self.timeLineDataProvider.events) == 1 )
        # verify that the event contains the info that were passed in
        self.event =  self.timeLineDataProvider.events[0]
        self.assertEqual(self.event.title, self.title)
        self.assertEqual(self.event.description, self.description)
        self.assertFalse(self.event.durationEvent)
        self.assertEqual(self.event.start, self.start)
        self.assertEqual(self.event.end, self.end)

        # event with start and end as datetimes
        self.title = 'Event 2' # required
        self.description = 'Description 2' # optional
        self.start = datetime.datetime.now() # required
        self.end = datetime.datetime.now() # optional
        
        self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

        # verify that the events list has 2 events
        self.assertTrue( len(self.timeLineDataProvider.events) == 2 )
        # verify that the event contains the info that were passed in
        self.event =  self.timeLineDataProvider.events[1]
        self.assertEqual(self.event.title, self.title)
        self.assertEqual(self.event.description, self.description)
        self.assertTrue(self.event.durationEvent)
        self.assertEqual(self.event.start, self.start)
        self.assertEqual(self.event.end, self.end)

        # event with start and end as dates
        self.title = 'Event 3' # required
        self.description = 'Description 3' # optional
        self.start = datetime.date.today() # required
        self.end = datetime.date.today() # optional
        
        self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

        # verify that the events list has 3 events
        self.assertTrue( len(self.timeLineDataProvider.events) == 3 )
        # verify that the event contains the info that were passed in
        self.event =  self.timeLineDataProvider.events[2]
        self.assertEqual(self.event.title, self.title)
        self.assertEqual(self.event.description, self.description)
        self.assertTrue(self.event.durationEvent)
        self.assertEqual(self.event.start, self.start)
        self.assertEqual(self.event.end, self.end)


    @unittest.expectedFailure # remove for production
    # verify that a ValueError is raised because start > end
    def testAddEventEndBeforeStart(self):
        self.title = 'My Title' # required
        self.description = "Just for fun" # optional
        self.end = datetime.datetime.now() # optional
        self.start = datetime.datetime.now() # required
        
        with self.assertRaises(ValueError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    # verify that no error is reaised if start == end       
    def testAddEventEndEqualsStart(self):
        self.title = 'My Title' # required
        self.description = "Just for fun" # optional
        self.start = datetime.datetime.now() # required
        self.end = self.start # optional
        
        self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    @unittest.expectedFailure # remove for production
    # verify that a TypeError is raised because start is neither a date nor a datetime
    def testAddEventStartWrongType(self):
        self.title = 'My Title' # required
        self.description = "Just for fun" # optional
        self.start = datetime.time.hour # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    @unittest.expectedFailure # remove for production
    # verify that a TypeError is raised because end is neither a date nor a datetime
    def testAddEventEndWrongType(self):
        self.title = 'My Title' # required
        self.description = "Just for fun" # optional
        self.start = datetime.datetime.now() # required
        self.end = datetime.time.hour # optional
                
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    # should raise a TypeError when addEventSource() is called with null table
    # and/or null title and/or null start 
    def testAddEventSourceNoParameters(self):
        # addEventSource() should set None as the default value for all its parameters.
        # Therefore calling addEventSource() with no parameters should be 
        # the same as calling it by passing null table, a null title and null start.
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource()


    # should raise a TypeError when addEventSource() is called with null table
    # and null title and null start
    def testAddEventSourceNoTableNoTitleNoStart(self):
        
        self.table= None # required
        self.filter = None # optional
        self.title = None # required
        self.description = "Just for fun" # optional
        self.start = None # required
        self.end = datetime.datetime.now() # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)


    # should raise a TypeError when addEventSource() is called with null table
    def testAddEventSourceNoTable(self):
        
        self.table= None # required
        self.filter = None # optional
        self.title = "name" # required
        self.description = "message" # optional
        self.start = "datetime" # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEventSource() is called with null title
    def testAddEventSourceNoTitle(self):
        
        self.table= db.irs_ireport
        self.filter = None # optional
        self.title = None # required
        self.description = "message" # optional
        self.start = "datetime" # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
            
    
    # should raise a TypeError when addEventSource() is called with null start
    def testAddEventSourceNoStart(self):
        
        self.table= db.irs_ireport
        self.filter = None # optional
        self.title = "name" # required
        self.description = "message" # optional
        self.start = None # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)

    
    def testAddEventSource(self):
        # We use the irs_ireport table of the Eden database as a source of events.
        # The irs_ireport table contains the following fields:
        # id, sit_id, name, message, category, person_id, contact, datetime, 
        # location_id, verified, actioned, comments, uuid, mci, deleted, deleted_fk,
        # created_on, modified_on, created_by, modified_by, owned_by_user, owned_by_role,
        # owned_by_organization, owned_by_facility
        self.table = db.irs_ireport 
        self.filter = None # optional
        self.title = "name" # required
        self.description = "message" # optional
        self.start = "datetime" # required
        self.end = None # optional
        
        self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
        
        # verify that the sources list has 1 event
        self.assertTrue( len(self.timeLineDataProvider.sources) == 1 )
        # verify that the event contains the info that were passed in
        self.source =  self.timeLineDataProvider.sources[0]
        self.assertEqual(self.source.table, self.table)
        self.assertEqual(self.source.title, self.title)
        self.assertEqual(self.source.description, self.description)
        self.assertEqual(self.source.start, self.start)
        self.assertEqual(self.source.end, self.end)

        # We use the irs_icategory table of the Eden database as a source of events.
        # The irs_icategory table contains the following fields:
        # id, code, created_on, modified_on
        self.table = db.irs_icategory
        self.filter = None # optional
        self.title = "code" # required
        self.description = None # optional
        self.start = "created_on" # required
        self.end = "modified_on" # optional
        
        self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
        
        # verify that the sources list has 1 event
        self.assertTrue( len(self.timeLineDataProvider.sources) == 2 )
        # verify that the event contains the info that were passed in
        self.source =  self.timeLineDataProvider.sources[1]
        self.assertEqual(self.source.table, self.table)
        self.assertEqual(self.source.title, self.title)
        self.assertEqual(self.source.description, self.description)
        self.assertEqual(self.source.start, self.start)
        self.assertEqual(self.source.end, self.end)
        
        
    def testGenerateData(self):
        # verify what data are returned when no events have been added
        data = self.timeLineDataProvider._generateData()
        self.assertEquals({'dateTimeFormat': 'iso8601', 'events': []}, data)

        # We use the irs_icategory table of the Eden database as a source of events.
        # The irs_icategory table contains the following fields:
        # id, code, created_on, modified_on
        self.table = db.irs_icategory
        self.filter = None # optional
        self.title = "code" # required
        self.description = None # optional
        self.start = "created_on" # required
        self.end = "modified_on" # optional
        
        self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
        data = self.timeLineDataProvider._generateData()
        print data


    def testGenerateCode(self):
        pass

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(SimileTimelineTest))
unittest.TextTestRunner(verbosity=2).run(suite) 