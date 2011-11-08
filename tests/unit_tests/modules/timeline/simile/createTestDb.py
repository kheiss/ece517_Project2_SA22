'''
To run this code execute the following command from within the web2py directory

python web2py.py -N -M -S eden -R applications/eden/tests/unit_tests/modules/timeline/simile/createTestDb.py
'''

# Create a test database containing random data for the SimileTimeline module
testDb = DAL('sqlite://simileTimelineTest.db')
testDb.define_table('timeline', Field('title'), Field('description'), Field('start','datetime'), Field('end','datetime'))
testDb(testDb.timeline).delete()
from gluon.contrib.populate import populate
populate(testDb.timeline,10)
testDb.commit()

# Create a test database that contains a copy of the irs_icategory table from the "real" database
#import copy
#test_db = DAL('sqlite://simileTimelineTest.db')  # Name and location of the test DB file
#tablename = "irs_icategory"
#table_copy = copy.copy(db[tablename])
#test_db.define_table(tablename, *table_copy)

# Create a test database that's laid out just like the "real" database
#import copy
#test_db = DAL('sqlite://simileTimelineTest.db')  # Name and location of the test DB file
#for tablename in db.tables:  # Copy tables!
#    for f in db[tablename]:    
#        table_copy = copy.copy(f)
#        test_db.define_table(tablename, *table_copy)