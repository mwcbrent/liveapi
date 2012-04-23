
import time,urllib2

CALLBACK_URL   = 'https://liveauth.herokuapp.com/callback'
CALLBACK_STORE = 'https://liveauth.herokuapp.com/get/%s'

class AuthCallbackError(Exception):
    pass

class AuthNotAvailable(Exception):
    pass

class AuthCallback(object):

    """
        Get Live Connect API auth_code from liveauth server
    """

    def __init__(self,state,debug=False):
        self.state = state
        self.opener = urllib2.build_opener(
                            urllib2.HTTPSHandler(debuglevel=debug)
                      )

    def check(self):
        try:
            r = self.opener.open(CALLBACK_STORE % self.state)
            code = r.read()
            if code.startswith('ERROR:'):
                raise AuthCallbackError, code
            else:
                return code
        except urllib2.HTTPError,e:
            if e.code == 404:
                raise AuthNotAvailable
            else:
                raise e

    def poll(self,timeout=30,delay=1.0):
        t = time.time() + timeout
        while time.time() < t:
            try:
                return self.check()
            except AuthNotAvailable:
                time.sleep(delay)
        raise AuthNotAvailable

if __name__ == '__main__':
    
    import sys
    try:
        cb = AuthCallback(sys.argv[1])
        print cb.check()
    except IndexError:
        print "Usage: %s <state>" % sys.argv[0]




