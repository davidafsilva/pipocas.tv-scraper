"""
Copyright (c) 2013, David Silva
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
        * Redistributions of source code must retain the above copyright
            notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above copyright
            notice, this list of conditions and the following disclaimer in the
            documentation and/or other materials provided with the distribution.
        * Neither the name of the <organization> nor the
            names of its contributors may be used to endorse or promote products
            derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import urllib
import urllib2
import sys
import re
import datetime

# configuration

configuration = {
    "LOGIN_URL": "http://pipocas.tv/vlogin.php",
    "LOGIN_USER": "Badjoras",
    "LOGIN_PWD": "9zvnkyAXuA",
    "LOGIN_FAIL_REGEX": "<strong>Login falhado!</strong>",
    "SUBS_LANG": "todas",
    "SUBS_URL": "http://pipocas.tv/subtitles.php?release={0}&grupo=rel&linguagem={1}",
    "SUBS_NO_RESULTS_REGEX": "<b>Nada Encontrado.</b>",
    "SUBS_RESULTS_REGEX": "<div class=\"box last-box\">.*<span><img alt=\"(.*)\" class=\"title-flag\" src=\"(.*)\"\/>(.*)<\/span>.*<h1 class=\"title\">(.*)<img.*<\/h1>.*<img alt=\"Poster\" src=\"(.*)\"\/>.*<li><span>Hits:<\/span>(.*)<\/li>\n<li><span>Coment\xc3rios:<\/span>(.*)<\/li>.*<li><span>Fonte:<\/span>(.*)<\/li>\n<li><span>CDs:<\/span>(.*)<\/li>\n<li><span>FPS:<\/span>(.*)<\/li>.*<\/li><\/ul>(.*) \/ (.*) de (.*) Voto\(s\)<\/div><\/div><br\/>.*<a href=\"download.php\?id=(.*)\" class=\"download\"><\/a>.*<div class=\"description\-box\">.*<br\/><br\/>",
    "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh) AppleWebKit/537 Chrome/26 Safari/537",
}

# /configuration

# global variables
_cookies = None
_debug = True

# Table mapping response codes to messages;
http_codes = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),
    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),
    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),
    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'No permission -- see authorization schemes'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this server.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),
    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.')
}


def handle_http_error(exception):
    msg = "An error occurred while querying the server: %s - %s"
    if exception.code in http_codes:
            print msg % (str(exception.code), http_codes[exception.code][0])
    else:
        print msg % (str(exception.code), exception.reason)


def build_request(url, data):
    request = urllib2.Request(url, data)
    request.add_header("User-agent", configuration["HTTP_USER_AGENT"])
    if not _cookies is None:
        request.add_header("Cookie", _cookies)
    return request


def get(url):
    try:
        request = build_request(url, None)
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.HTTPError, e:
        handle_http_error(e)
    except urllib2.URLError, e:
        print "Unable to reach the server:", e.reason
    return None


def post(url, parameters):
    try:
        data = urllib.urlencode(parameters)
        request = build_request(url, data)
        response = urllib2.urlopen(request)
        return response
    except urllib2.HTTPError, e:
        handle_http_error(e)
    except urllib2.URLError, e:
        print "Unable to reach the server:", e.reason
    return None


def login():
    global _cookies
    url = configuration["LOGIN_URL"]
    user = configuration["LOGIN_USER"]
    pwd = configuration["LOGIN_PWD"]
    debug("Logging in as " + user + "...")
    response = post(url, {'username': user, 'password': pwd})
    html = response.read()
    if not re.search(configuration["LOGIN_FAIL_REGEX"], html):
        _cookies = response.info()["Set-Cookie"]
        debug("Successfully logged in!")
        debug("Cookies: " + _cookies)
        return True
    debug("Login failed")
    return False


def debug(txt):
    if _debug:
        print "[DEBUG]-["+str(datetime.datetime.now())+"] "+txt


def handle_results(results):
    debug("filtering HTML...")
    subs_html = re.findall(configuration["SUBS_RESULTS_REGEX"], results)
    debug("filtered results:")
    debug(str(subs_html))


def search(release):
    if login():
        lang = configuration["SUBS_LANG"]
        geturl = configuration["SUBS_URL"].format(urllib.quote_plus(release), lang)
        debug("fetching URL: " + geturl)
        results = get(geturl)
        if re.search(configuration["SUBS_NO_RESULTS_REGEX"], results):
            debug("No results were found for " + release)
            print "No results were found for '%s'" % (release)
        else:
            debug("HTML retrieved")
            debug(str(results))
            handle_results(results)
    else:
        print "Invalid login credentials specified."


def main():
    f = open("tmp.results", "r")
    handle_results(f.read())
    # if len(sys.argv) == 1:
    #     print "Usage: %s (release|movie|tv-show)" % (sys.argv[0])
    # else:
    #     search(sys.argv[1])


# call the main
if __name__ == "__main__":
    main()
