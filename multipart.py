# -*- coding: utf-8 -*-

import mimetools,mimetypes

def encode_multipart_formdata(fields,files,mimetype=None):
    """
    Derived from - http://code.activestate.com/recipes/146306/

    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be 
    uploaded as files

    Returns (content_type, body) ready for httplib.HTTP instance
    """

    BOUNDARY = mimetools.choose_boundary()
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (
                        key, filename))
        L.append('Content-Type: %s' % (mimetype or 
                                       mimetypes.guess_type(filename)[0] or 
                                       'application/octet-stream'))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(map(bytes,L))
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

