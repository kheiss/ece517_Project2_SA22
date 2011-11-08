class Event(object):
    def __init__(self, title=None, start=None, **kwargs):
        if title == None or start == None:
            raise TypeError

        self.title = title
        self.start = start


class EventSource(object):
    def __init__(self, table=None, filter=None, title=None, start=None, **kwargs):
        if table == None or title == None or start == None:
            raise TypeError

        self.table = table
        self.filter = filter
        self.title = title
        self.start = start


    # This is a helper function that is designed to get the string equvalent of a field
    # to be used in the timeline.  The primary reason for this is because it is often
    # the case that the data stored in the db table has a string representation differing
    # from that of what is humanly readable.  In these cases, when the table is created
    # a 'represent' attribute can be specified which is typically a lambda function for
    # transforming the field into a humanly readable format.  This method also has the 
    # ability to apply a user generated lambda to the field instead.  In the event that
    # a user lambda nor represent attribute exists, the pure string representation of 
    # the field is returned.
    def getStringRepresentation(self, table, row, attr):
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
        except KeyError as detail:
            self._log("Caught error: %s\n Skipping..." % detail)
            return None

    def getEvents(self):
        raise NotImplementedError

