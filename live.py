
import pprint
import base64,cookielib,hmac,hashlib,json,time,urllib,urllib2,uuid,webbrowser

API_PATH       = 'https://apis.live.net/v5.0/'
AUTH_URL       = 'https://login.live.com/oauth20_authorize.srf?%s'
TOKEN_URL      = 'https://login.live.com/oauth20_token.srf'

from liveobject import LiveObject, LiveFile, LiveFolder, LiveAlbum, LiveCalendar, LiveEvent

class LiveAPIError(Exception):
    pass

class LiveToken(object):

    @classmethod
    def parse(cls,s):
        d = json.loads(s)
        d['scope'] = d['scope'].split()
        d['expires'] = time.time() + d['expires_in']
        if not d.has_key('refresh_token'):
            d['refresh_token'] = None
        return cls.load(d)

    @classmethod
    def load(cls,d):
        return cls(d['authentication_token'],
                   d['access_token'],
                   d['expires'],
                   d['token_type'],
                   d['scope'],
                   d['refresh_token'])

    def __init__(self,authentication_token,access_token,expires,
                      token_type,scope,refresh_token):
        self.authentication_token = authentication_token
        self.access_token = access_token
        self.expires = expires
        self.token_type = token_type
        self.scope = scope
        self.refresh_token = refresh_token

    def base64url_decode(self,s):
        return base64.urlsafe_b64decode(s + '=' * ((4 - len(s)) % 4))

    def decode_jwt(self,secret=None):
        """
            Decode JWT format authentication_token 

            Unclear how to get local calculation of secret working with 
            Live Connect response (code works against example in RFC)

            MS sample code (http://git.io/MnloIQ) suggests that signature
            is calculated using:

                key = sha256(secret + "JWTSig")
                hash = hmac_sha256(key,"envelope"+"."+"claim)

            ...however this does not match RFC and doesn't actually work

        """
        envelope_j,claim_j,crypto = [ self.base64url_decode(str(x)) for x in 
                                          self.authentication_token.split('.') ]
        envelope = json.loads(envelope_j)
        claim = json.loads(claim_j)
        if secret:
            if envelope[u'alg'] == u'HS256':
                local = hmac.new(secret,claim_j,digestmod=hashlib.sha256).digest()
                print "Crypto: ", map(ord,crypto)
                print "Calc:   ", map(ord,local)
            else:
                print u"Algorithm %s not supported" % envelope[u'alg']
        return envelope,claim

    def expired(self):
        return self.expires - time.time() < 60

    def dump(self):
        return { 'authentication_token' : self.authentication_token,
                 'access_token' : self.access_token,
                 'expires' : self.expires,
                 'token_type' : self.token_type,
                 'scope' : self.scope,
                 'refresh_token' : self.refresh_token }

    def __repr__(self):
        return "<LiveToken: auth=%s access=%s refresh=%s type=%s scope=%s expires=%d secs>" % (
                        self.authentication_token[:4] + ".." + self.authentication_token[-4:], 
                        self.access_token[:4] + ".." + self.access_token[-4:],
                        self.refresh_token and 
                            self.refresh_token[:4] + ".." + self.refresh_token[-4:] or None,
                        self.token_type,
                        ",".join(self.scope),
                        int(self.expires - time.time()))

class LiveConnection(object):

    OBJ_MAP = { 'file'      : LiveFile,
                'folder'    : LiveFolder,
                'album'     : LiveAlbum,
                'calendar'  : LiveCalendar,
                'event'     : LiveEvent
              }

    def __init__(self,client_id,client_secret,redirect_uri,debug=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token = None
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
                            urllib2.HTTPSHandler(debuglevel=debug),
                            urllib2.HTTPCookieProcessor(self.cj)
                      )

    def request_auth(self,scope):
        state = str(uuid.uuid1())
        params = dict(client_id=self.client_id,
                      scope=' '.join(scope),
                      response_type='code',
                      redirect_uri=self.redirect_uri,
                      state=state)
        auth_url = AUTH_URL % urllib.urlencode(params)
        webbrowser.open(auth_url)
        return state

    def get_token(self,auth_code):
        params = dict(client_id=self.client_id,
                      redirect_uri=self.redirect_uri,
                      client_secret=self.client_secret,
                      code=auth_code,
                      grant_type='authorization_code')
        data = urllib.urlencode(params)
        r = self.opener.open(TOKEN_URL,data)
        self.token = LiveToken.parse(r.read())

    def refresh_token(self):
        if self.token.refresh_token:
            params = dict(client_id=self.client_id,
                          redirect_uri=self.redirect_uri,
                          client_secret=self.client_secret,
                          refresh_token=self.token.refresh_token,
                          grant_type='refresh_token')
            data = urllib.urlencode(params)
            r = self.opener.open(TOKEN_URL,data)
            self.token = LiveToken.parse(r.read())
        else:
            raise LiveAPIError, "No refresh_token available"

    def get(self,path,params=None):
        if self.token.expired():
            self.refresh_token()
        if params:
            params['access_token'] = self.token.access_token
        else:
            params = { 'access_token' : self.token.access_token }
        return self.opener.open("%s%s?%s" % (API_PATH,path,urllib.urlencode(params)))

    def get_json(self,path,params=None):
        return json.loads(self.get(path,params).read())

    def get_object(self,id,obj_type=None):
        response = self.get_json(id)
        obj_type = obj_type or response.get('type') or response['id'].split('.')[0]
        obj_class = self.OBJ_MAP.get(obj_type,LiveObject)
        return obj_class(self,response)

    def get_container(self,path):
        response = []
        try:
            for item in self.get_json(path)['data']:
                obj_type = item.get('type') or item['id'].split('.')[0]
                obj_class = self.OBJ_MAP.get(obj_type,LiveObject)
                response.append(obj_class(self,item))
            return response
        except KeyError, e:
            raise LiveAPIError, "Invalid collection"

if __name__ == '__main__':

    from ConfigParser import ConfigParser

    ini = ConfigParser()
    ini.read('client.ini')

    CLIENT_ID     = ini.get('liveapi','client_id')
    CLIENT_SECRET = ini.get('liveapi','client_secret')
    REDIRECT_URI  = ini.get('liveapi','redirect_uri')
    SCOPE         = [ 'wl.signin', 'wl.basic', 'wl.skydrive', 'wl.offline_access', 'wl.calendars' ]

    from authcb import AuthCallback

    l = LiveConnection(CLIENT_ID,CLIENT_SECRET,REDIRECT_URI)
    state = l.request_auth(SCOPE)
    cb = AuthCallback(state)
    auth_code = cb.poll()
    l.get_token(auth_code)

