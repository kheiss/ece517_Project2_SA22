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

class SimileTimelineTest(unittest.TestCase):

    def setUp(self):
        # Connect to the test database created by createTestDb.py
        self.testDb = DAL('sqlite://simileTimelineTest.db')
        self.testDb.define_table('timeline', Field('title'), Field('description'), Field('start','datetime'), Field('end','datetime'))
        self.timeLineDataProvider = simile.SimileTimeline()        

        # Dump the contents of the test db to verify that it's not empty.
#        print "TESTDB TIMEKINE TABLE CONTENTS -------"
#        print self.testDb.tables
#        print self.testDb(self.testDb.timeline).select()
        

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
        self.description = 'description'
        self.start = None
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoTitle(self):
        
        self.title = None
        self.description = 'description'
        self.start = datetime.datetime.now()
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoStart(self):
        
        self.title = 'title'
        self.description = 'description'
        self.start = None
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    def testAddEvent(self):
        
        # event with only title and start as a datetime
        self.title = 'Event1' # required
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
        self.title = 'Event2' # required
        self.description = 'Description2' # optional
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
        self.title = 'Event3' # required
        self.description = 'Description3' # optional
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
        self.title = 'title' # required
        self.description = 'description' # optional
        self.end = datetime.datetime.now() # optional
        self.start = datetime.datetime.now() # required
        
        with self.assertRaises(ValueError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    # verify that no error is reaised if start == end       
    def testAddEventEndEqualsStart(self):
        self.title = 'title' # required
        self.description = 'description' # optional
        self.start = datetime.datetime.now() # required
        self.end = self.start # optional
        
        self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    @unittest.expectedFailure # remove for production
    # verify that a TypeError is raised because start is neither a date nor a datetime
    def testAddEventStartWrongType(self):
        self.title = 'title' # required
        self.description = 'description' # optional
        self.start = datetime.time.hour # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    @unittest.expectedFailure # remove for production
    # verify that a TypeError is raised because end is neither a date nor a datetime
    def testAddEventEndWrongType(self):
        self.title = 'title' # required
        self.description = 'description' # optional
        self.start = datetime.datetime.now() # required
        self.end = datetime.time.hour # optional
                
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)


    # should raise a TypeError when addEventSource() is called with null table
    # and/or null title and/or null start 
    def testAddEventSourceNoParameters(self):
        # addEventSource() should set None as the default value for all its parameters.
        # Therefore calling addEventSource() with no parameters should be 
        # the same as calling it by passing no table, no title and no start.
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource()


    # should raise a TypeError when addEventSource() is called with no table
    # and no title and no start
    def testAddEventSourceNoTableNoTitleNoStart(self):
        
        self.table= None # required
        self.filter = None # optional
        self.title = None # required
        self.description = 'description' # optional
        self.start = None # required
        self.end = datetime.datetime.now() # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)


    # should raise a TypeError when addEventSource() is called with no table
    def testAddEventSourceNoTable(self):
        
        self.table= None # required
        self.filter = None # optional
        self.title = "title" # required
        self.description = 'description' # optional
        self.start = "start" # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)

    
    # should raise a TypeError when addEventSource() is called with no title
    def testAddEventSourceNoTitle(self):
        
        self.table = self.testDb.timeline
        self.filter = None # optional
        self.title = None # required
        self.description = 'description' # optional
        self.start = "start" # required
        self.end = None # optional
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
            
    
    # should raise a TypeError when addEventSource() is called with no start
    def testAddEventSourceNoStart(self):
        
        self.table = self.testDb.timeline
        self.filter = None # optional
        self.title = "title" # required
        self.description = 'description' # optional
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
        self.table = self.testDb.timeline
        self.filter = None # optional
        self.title = "title" # required
        self.description = 'description' # optional
        self.start = "start" # required
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
        self.table = self.testDb.timeline
        self.filter = None # optional
        self.title = "title" # required
        self.description = None # optional
        self.start = "start" # required
        self.end = "end" # optional
        
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

        # We use the timeline table of the test database as a source of events.
        self.table = self.testDb.timeline
        self.filter = None # optional
        self.title = "title" # required
        self.description = 'description' # optional
        self.start = "start" # required
        self.end = "end" # optional
        
        self.timeLineDataProvider.addEventSource(self.table, self.filter, self.title, self.description, self.start, self.end)
        data = self.timeLineDataProvider._generateData()
        expected = {'dateTimeFormat': 'iso8601', 'events': [{'start': '2008-03-05T00:00:00', 'durationEvent': True, 'end': '2008-04-27T00:00:00', 'description': 'It--a natural reflex actions which formerly had the quality of it. ', 'title': '74 diagram and we will dispute the outline we see a. '}, {'start': '2008-09-21T00:00:00', 'durationEvent': True, 'end': '2008-08-08T00:00:00', 'description': 'Sport for nowhere do not seen an animal play an infinite. ', 'title': 'Insectivorous bats. Girdled about the brain. But we have. '}, {'start': '2008-02-06T00:00:00', 'durationEvent': True, 'end': '2008-09-23T00:00:00', 'description': 'Celandine with or pass through the tse-tse fly spreads out some. ', 'title': 'Marks most important acquisitions of working powerfully along with a smack. '}, {'start': '2008-10-09T00:00:00', 'durationEvent': True, 'end': '2008-10-07T00:00:00', 'description': 'Healthfulness and muscle-cells which just mentioned indicates a plaice and bettered. ', 'title': 'Mostly in this is blown back and the mind at least. '}, {'start': '2008-07-30T00:00:00', 'durationEvent': True, 'end': '2008-06-17T00:00:00', 'description': 'Everyone who found to the monitors are often it had no. ', 'title': 'Transmissible. given the ascent of rose on from roots of detecting. '}, {'start': '2008-02-08T00:00:00', 'durationEvent': True, 'end': '2008-02-16T00:00:00', 'description': 'Stars--or rather with the other medium of backboned animals have found. ', 'title': 'Cocoon flies to create fresh invention of the united states copyright. '}, {'start': '2008-08-14T00:00:00', 'durationEvent': True, 'end': '2008-09-08T00:00:00', 'description': 'Flower-vase well says do not have we saw combine to sneak. ', 'title': 'Twenty-five million million years ago they are in the end were. '}, {'start': '2008-01-04T00:00:00', 'durationEvent': True, 'end': '2008-08-10T00:00:00', 'description': 'Persecuted. Mcgregor from its axis in the okapi and easy. ', 'title': 'Crowning advantage over 800 trillion miles. That 93 000 000. '}, {'start': '2008-05-05T00:00:00', 'durationEvent': True, 'end': '2008-09-13T00:00:00', 'description': 'Apace there is snow. It may be small number develop. ', 'title': 'Solution.... It can be discovered in process of the floor. '}, {'start': '2008-05-11T00:00:00', 'durationEvent': True, 'end': '2008-01-30T00:00:00', 'description': 'Attracted one in the number of many times we know and. ', 'title': 'Elevation of radium. the expression of energy which indicate a skeleton. '}]}
        self.assertEqual(data, expected)


    def testGenerateCode(self):
        pass

# to make the command
# python web2py.py -N -M -S eden -R applications/eden/tests/unit_tests/modules/timeline/simile/simile.py
# execute this unit test test
suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(SimileTimelineTest))
unittest.TextTestRunner(verbosity=2).run(suite) 