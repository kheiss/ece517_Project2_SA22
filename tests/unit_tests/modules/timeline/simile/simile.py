'''
Created on Oct 29, 2011

@author:
'''
import unittest
import datetime

import applications.eden.modules.timeline.simile as simile

class Test(unittest.TestCase):


    def setUp(self):
        self.timeLineDataProvider = simile.SimileTimeline()


    def tearDown(self):
        self.timeLineDataProvider = None


    def testConstructor(self):
        # verify that the sources and events lists are initially empty
        self.assertTrue( len(self.timeLineDataProvider.sources) == 0 ) 
        self.assertTrue( len(self.timeLineDataProvider.events) == 0 ) 
        

    @unittest.expectedFailure # remove for production
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoParameters(self):
        self.title = None
        self.description = "Just for fun"
        self.start = datetime.datetime.today()
        self.end = None
        
        # addEvent() should set None as the default value for the title and start parameters.
        # Therefore calling addEvent() with no parameters should be 
        # the same as calling it by passing null title and null start.
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent()
        
    
    @unittest.expectedFailure # remove for production
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoTitleNoStart(self):
        
        self.title = None
        self.description = "Just for fun"
        self.start = None
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    @unittest.expectedFailure # remove for production
    # should raise a TypeError when addEvent() is called with null title
    # and/or null start
    def testAddEventNoTitle(self):
        
        self.title = None
        self.description = "Just for fun"
        self.start = datetime.datetime.now()
        self.end = None
        
        with self.assertRaises(TypeError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    
    @unittest.expectedFailure # remove for production
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
        self.assertEqual(self.event['title'], self.title)
        self.assertEqual(self.event['description'], self.description)
        self.assertFalse(self.event['durationEvent'])
        self.assertEqual(self.event['start'], self.timeLineDataProvider.formatTime(self.start))
        self.assertFalse(self.event.has_key('end'))

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
        self.assertEqual(self.event['title'], self.title)
        self.assertEqual(self.event['description'], self.description)
        self.assertTrue(self.event['durationEvent'])
        self.assertEqual(self.event['start'], self.timeLineDataProvider.formatTime(self.start))
        self.assertEqual(self.event['end'], self.timeLineDataProvider.formatTime(self.end))

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
        self.assertEqual(self.event['title'], self.title)
        self.assertEqual(self.event['description'], self.description)
        self.assertTrue(self.event['durationEvent'])
        self.assertEqual(self.event['start'], self.timeLineDataProvider.formatTime(self.start))
        self.assertEqual(self.event['end'], self.timeLineDataProvider.formatTime(self.end))


    @unittest.expectedFailure # remove for production
    # verify that a ValueError is raised because start > end
    def testAddEventEndBeforeStart(self):
        self.title = 'My Title'
        self.description = "Just for fun"
        self.end = datetime.datetime.now() # optional
        self.start = datetime.datetime.now() # required
        
        with self.assertRaises(ValueError):
            self.timeLineDataProvider.addEvent(self.title, self.description, self.start, self.end)

    def testAddEventSource(self):
        pass


    def testGenerateData(self):
        pass


    def testGenerateCode(self):
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()