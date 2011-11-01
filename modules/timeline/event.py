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


    # Attempts to use the represent lambda attribute to transform an otherwise
    # incoherent piece of data
    # Also has the ability to interpret lambda functions and use them to generate a 
    # string.
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

