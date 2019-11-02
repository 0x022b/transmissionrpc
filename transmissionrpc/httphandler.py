# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2019 Janne K <0x022b@gmail.com>
# Licensed under the MIT license.

from urllib.request import Request, build_opener, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, HTTPDigestAuthHandler
from urllib.error import HTTPError, URLError
from http.client import BadStatusLine

from transmissionrpc.error import HTTPHandlerError


class HTTPHandler(object):
    """
    Prototype for HTTP handling.
    """

    def set_authentication(self, uri, login, password):
        """
        Transmission use basic authentication in earlier versions and digest
        authentication in later versions.

         * uri, the authentication realm URI.
         * login, the authentication login.
         * password, the authentication password.
        """
        raise NotImplementedError(
            "Bad HTTPHandler, failed to implement set_authentication.")

    def request(self, url, query, headers, timeout):
        """
        Implement a HTTP POST request here.

         * url, The URL to request.
         * query, The query data to send. This is a JSON data string.
         * headers, a dictionary of headers to send.
         * timeout, requested request timeout in seconds.
        """
        raise NotImplementedError(
            "Bad HTTPHandler, failed to implement request.")


class DefaultHTTPHandler(HTTPHandler):
    """
    The default HTTP handler provided with transmissionrpc.
    """

    def __init__(self):
        HTTPHandler.__init__(self)
        self.http_opener = build_opener()

    def set_authentication(self, uri, login, password):
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(
            realm=None, uri=uri, user=login, passwd=password)
        self.http_opener = build_opener(HTTPBasicAuthHandler(
            password_manager), HTTPDigestAuthHandler(password_manager))

    def request(self, url, query, headers, timeout):
        request = Request(url, query.encode('utf-8'), headers)
        try:
            response = self.http_opener.open(request, timeout=timeout)
        except HTTPError as error:
            if error.fp is None:
                raise HTTPHandlerError(
                    error.filename, error.code, error.msg, dict(error.hdrs))
            else:
                raise HTTPHandlerError(
                    error.filename, error.code, error.msg, dict(error.hdrs), error.read())
        except URLError as error:
            # urllib2.URLError documentation is horrendous!
            # Try to get the tuple arguments of URLError
            if hasattr(error.reason, 'args') and isinstance(error.reason.args, tuple) and len(error.reason.args) == 2:
                raise HTTPHandlerError(
                    httpcode=error.reason.args[0], httpmsg=error.reason.args[1])
            else:
                raise HTTPHandlerError(
                    httpmsg='urllib2.URLError: %s' % (error.reason))
        except BadStatusLine as error:
            raise HTTPHandlerError(
                httpmsg='httplib.BadStatusLine: %s' % (error.line))
        return response.read().decode('utf-8')
