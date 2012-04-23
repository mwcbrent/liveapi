



class LiveObject(object):

    PARAMS = [ u'id', u'name' ]
    MAP =    { 
                u'from' : u'from_object', 
             }

    def __init__(self,connection,params):
        self.connection = connection
        self.params = params
        for p in self.PARAMS:
            try:
                setattr(self,self.MAP.get(p,p),params[p])
            except KeyError,e:
                print "ERROR",e
    
    def __repr__(self):
        return "<%s: id='%s' name='%s'>" % (self.__class__.__name__,self.id,self.name)

class LiveFile(LiveObject):

    PARAMS = [ u'comments_count', u'comments_enabled', u'created_time', u'description', 
               u'from', u'id', u'is_embeddable', u'link', u'name', u'parent_id', 
               u'shared_with', u'size', u'source', u'type', u'updated_time', 
               u'upload_location']

    def file(self):
        return self.connection.get(self.id + "/content")

    def data(self):
        return self.file().read()

class LiveFolder(LiveObject):

    PARAMS = [ u'count', u'created_time', u'description', u'from', u'id', 
               u'is_embeddable', u'link', u'name', u'parent_id', u'shared_with', 
               u'type', u'updated_time', u'upload_location' ]

    def contents(self):
        return self.connection.get_container(self.id + "/files")

class LiveAlbum(LiveFolder):
    pass

class LiveCalendar(LiveObject):

    PARAMS = [ u'created_time', u'description', u'from', u'id', u'is_default', 
               u'name', u'permissions', u'subscription_location', u'updated_time']

class LiveEvent(LiveObject):

    PARAMS = [ u'availability', u'calendar_id', u'created_time', u'description', 
               u'end_time', u'from', u'id', u'is_all_day_event', u'is_recurrent', 
               u'location', u'name', u'recurrence', u'reminder_time', u'start_time', 
               u'updated_time', u'visibility']


