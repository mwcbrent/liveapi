# -*- coding: utf-8 -*-

import datetime,json

from multipart import encode_multipart_formdata

def convert_iso8601(v):
    if v:
        return datetime.datetime.strptime(v[:19],"%Y-%m-%dT%H:%M:%S")
    else:
        return None

def identity(v):
    return v

def proxy(c,v):
    if v:
        return LiveProxyObject(c,v)
    else:
        return None

class LiveProxyObject(object):

    def __init__(self,connection,id):
        self.id = id
        self.connection = connection

    def fetch(self):
        return self.connection.get_object(self.id)

    def __repr__(self):
        return "<LiveProxyObject: id='%s'>" % self.id

class LiveObject(object):

    PARAMS  = [ u'id', u'name' ]
    KEY_MAP = { 
                u'from' : u'from_object', 
              }
    PARAM_MAP = {
                }

    def __init__(self,connection,params):
        self.connection = connection
        self.params = params
        import pprint
        for p in self.PARAMS:
            try:
                k = self.KEY_MAP.get(p,p)
                f = self.PARAM_MAP.get(p,identity)
                if f == proxy:
                    f = lambda v: proxy(self.connection,v)
                v = f(params[p])
                setattr(self,k,v)
            except KeyError,e:
                print "ERROR",e
    
    def __proxy(self):
        return 

    def __repr__(self):
        return "<%s: id='%s' name='%s'>" % (self.__class__.__name__,self.id,self.name)

class LiveFile(LiveObject):

    PARAMS = [ u'comments_count', u'comments_enabled', u'created_time', u'description', 
               u'from', u'id', u'is_embeddable', u'link', u'name', u'parent_id', 
               u'shared_with', u'size', u'source', u'type', u'updated_time', 
               u'upload_location']

    PARAM_MAP = {
                  u'created_time' : convert_iso8601,
                  u'updated_time' : convert_iso8601,
                  u'parent_id' : proxy,
                }

    def file(self):
        return self.connection.request(self.id + "/content")

    def data(self):
        return self.file().read()

    def delete(self):
        self.connection.request(self.id,method='DELETE')

class LiveNotebook(LiveFile):
    pass

class LiveFolder(LiveObject):

    PARAMS = [ u'count', u'created_time', u'description', u'from', u'id', 
               u'is_embeddable', u'link', u'name', u'parent_id', u'shared_with', 
               u'type', u'updated_time', u'upload_location' ]

    PARAM_MAP = {
                  u'created_time' : convert_iso8601,
                  u'updated_time' : convert_iso8601,
                  u'parent_id' : proxy,
                }

    def contents(self):
        return self.connection.get_container(self.id + "/files")

    def upload(self,filename,data,mimetype=None):
        content_type,data = encode_multipart_formdata([],[('file',filename,data)],mimetype)
        r = self.connection.get_json(path = self.id + "/files",
                                     method = 'POST',
                                     headers = { 'Content-type': content_type,
                                                 'Content-length': str(len(data)) },
                                     data = data)
        return LiveProxyObject(self.connection,r[u'id'])

    def delete(self):
        self.connection.request(self.id,method='DELETE')

    def create_folder(self,name,description=""):
        data = json.dumps(dict(name=name,description=description))
        r = self.connection.get_json(path = self.id,
                                     method = 'POST',
                                     headers = { 'Content-type': 'application/json',
                                                  'Content-length': str(len(data)) },
                                     data = data)
        return LiveFolder(self.connection,r)

class LiveAlbum(LiveFolder):
    pass

class LiveCalendar(LiveObject):

    PARAM_MAP = {
                  u'created_time' : convert_iso8601,
                  u'updated_time' : convert_iso8601,
                }

    PARAMS = [ u'created_time', u'description', u'from', u'id', u'is_default', 
               u'name', u'permissions', u'subscription_location', u'updated_time']

class LiveEvent(LiveObject):

    PARAMS = [ u'availability', u'calendar_id', u'created_time', u'description', 
               u'end_time', u'from', u'id', u'is_all_day_event', u'is_recurrent', 
               u'location', u'name', u'recurrence', u'reminder_time', u'start_time', 
               u'updated_time', u'visibility']


