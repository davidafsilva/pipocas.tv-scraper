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
from bs4 import BeautifulSoup

# configuration

configuration = {
    # authentication parameters
    "LOGIN_USER": "xxx",
    "LOGIN_PWD": "xxx",
    # tipically you don't need to change nothing below
    "DEBUG": False,
    "BASE_URL": "http://pipocas.tv/",
    "LOGIN_URL": "http://pipocas.tv/vlogin.php",
    "LOGIN_FAIL_REGEX": "<strong>Login falhado!</strong>",
    "SUBS_LANG": "todas",
    "SUBS_URL": "http://pipocas.tv/subtitles.php?release={0}&grupo=rel&linguagem={1}",
    "SUBS_NO_RESULTS_REGEX": "<b>Nada Encontrado.</b>",
    "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh) AppleWebKit/537 Chrome/26 Safari/537",
}

# /configuration

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

# version
VERSION = "0.10"

# Country class
class PipocasSubtitleCountry:
    def __init__(self, name, flag_url):
        """
        Subtitle country constructor
        """
        self.name = name
        self.flag_url = flag_url

    def get_name(self):
        """
        Gets the name of the country
        """
        return self.name

    def get_flag_url(self):
        """
        Gets the flag URL
        """
        return self.flag_url

    def __str__(self):
        """
        to string method implementation
        """
        attrs = vars(self)
        return "Country[" + ', '.join("%s: %s" % item for item in attrs.items()) + "]"

# Subtitle class
class PipocasSubtitle:
    def __init__(self, release, poster_url, country, hits, rating, votes, download_url):
        """
        Subtitle constructor
        """
        self.release = release
        self.poster_url = poster_url
        self.country = country
        self.hits = hits
        self.rating = rating
        self.votes = votes
        self.download_url = download_url

    def get_release(self):
        """
        Gets the release name of the subtitle
        """
        return self.release

    def get_poster_url(self):
        """
        Gets the poster url for the subtitle
        """
        return self.poster_url

    def get_country(self):
        """
        Gets the country of the subtitle
        """
        return self.country

    def get_hits(self):
        """
        Gets the amount of hits by the subtitle
        """
        return self.hits

    def get_rating(self):
        """
        Gets the subtitle rating
        """
        return self.rating

    def get_votes(self):
        """
        Gets the total amount of votes for the current rating
        """
        return self.votes

    def get_download_url(self):
        """
        Gets the download url for the subtitle
        """
        return self.download_url

    def __str__(self):
        """
        to string method implementation
        """
        attrs = vars(self)
        return "Subtitle[" + ', '.join("%s: %s" % item for item in attrs.items()) + "]"


# the scraper class
class PipocasScraper:
    def __init__(self):
        """
        Scraper constructor
        """
        self.cookies = None
        self.error = None

    def __config(self, key):
        """
        Gets the configuration for the given key
        """
        return configuration[key]

    def __is_debug_enabled(self):
        """
        Checks if is debug enabled
        """
        return self.__config("DEBUG")

    def __debug(self, txt):
        if self.__is_debug_enabled():
            print "[DEBUG]-["+str(datetime.datetime.now())+"] "+txt

    def __handle_http_error(self, exception):
        """
        Handles the HTTP errors catched
        """
        msg = "An error occurred while querying the server: %s - %s"
        if exception.code in http_codes:
            return msg % (str(exception.code), http_codes[exception.code][0])
        else:
            return msg % (str(exception.code), exception.reason)

    def __build_request(self, url, data):
        """
        Builds an HTTP request
        """
        request = urllib2.Request(url, data)
        request.add_header("User-agent", configuration["HTTP_USER_AGENT"])
        if not self.cookies is None:
            request.add_header("Cookie", self.cookies)
        return request

    def __get(self, url):
        """
        Executes an HTTP GET request
        """
        try:
            request = self.__build_request(url, None)
            response = urllib2.urlopen(request)
            return response.read()
        except urllib2.HTTPError, e:
            self.error = self.__handle_http_error(e)
        except urllib2.URLError, e:
            self.error = "Unable to reach the server:", e.reason
        return None

    def __post(self, url, parameters):
        """
        Executes an HTTP POST request
        """
        try:
            data = urllib.urlencode(parameters)
            request = self.__build_request(url, data)
            response = urllib2.urlopen(request)
            return response
        except urllib2.HTTPError, e:
            self.error = self.__handle_http_error(e)
        except urllib2.URLError, e:
            self.error = "Unable to reach the server:", e.reason
        return None

    def __login(self):
        """
        Logs in into the server
        """
        url = self.__config("LOGIN_URL")
        user = self.__config("LOGIN_USER")
        pwd = self.__config("LOGIN_PWD")
        self.__debug("Logging in as " + user + "...")
        response = self.__post(url, {'username': user, 'password': pwd})
        if not self.has_errors():
            html = response.read()
            if not re.search(configuration["LOGIN_FAIL_REGEX"], html):
                self.cookies = response.info()["Set-Cookie"]
                self.__debug("Successfully logged in!")
                return True
            self.__debug("Login failed")
        return False

    def __handle_search_results(self, results):
        """
        Handles the search results
        """
        self.__debug("filtering HTML...")
        container = results.select("div.box.last-box")
        self.__debug("filtered!")
        self.__debug("found " + str(len(container)) + " result(s)")
        response = []
        while len(container) > 0:
            result = container.pop(0)
            elements = {}
            # country
            tmp = result.select("img.title-flag")[0]
            elements['country'] = tmp["alt"]
            elements['country_flag'] = tmp["src"]
            # title
            elements['title'] = tmp.parent.get_text().strip()
            # release
            tmp = result.select("h1.title")[0]
            elements['release'] = tmp.get_text().replace('\n', '').strip()
            if not elements['release'] is None and len(elements['release']) > 8 and elements['release'][:8] == 'Release:':
                elements['release'] = elements['release'][8:].strip()
            # poster
            tmp = result.find_all(attrs={"alt": "Poster"})[0]
            elements['poster'] = tmp["src"]
            # hits
            tmp = result.select("li.sub-box2")[0].ul.li
            elements["hits"] = int(tmp.contents[1].strip())
            # rating
            tmp = results.select("li.sub-box4")[0].div.div
            tmp = tmp.contents
            if not tmp is None and len(tmp) > 0:
                tmp = tmp[len(tmp)-1].split()
                if not tmp is None and len(tmp) == 6:
                    elements["rating"] = float(tmp[0])
                    elements["votes"] = int(tmp[4])
            # download
            tmp = results.select("a.download")[0]
            elements["download"] = configuration["BASE_URL"] + tmp["href"]
            # add the subtitle
            response.append(self.__create_sub(elements))
        return self.__sort(response)

    def __create_sub(self, elements):
        """
        Creates the subtitle class from the elements
        """
        country = PipocasSubtitleCountry(elements['country'], elements['country_flag'])
        return PipocasSubtitle(elements['release'], elements['poster'], country,
                               elements['hits'], elements['rating'], elements['votes'],
                               elements['download'])

    def __sort(self, subtitles):
        """
        Sorts the given list of subtitles by rating/hits
        TODO: implement
        """
        return sorted(subtitles, key=lambda subtitle: (subtitle.get_rating(), subtitle.get_hits()), reverse=True)

    def __generate_search_url(self, release):
        return self.__config("SUBS_URL").format(urllib.quote_plus(release), self.__config("SUBS_LANG"))

    ## public methods ##

    def has_errors(self):
        """
        Checks if any error occured in the last request
        """
        return not self.error is None

    def get_error(self):
        """
        Gets the error message for the last request, if any
        """
        return self.error

    def search(self, release):
        """
        Searches subtitles for the given release
        """
        self.error = None
        if self.__login():
            geturl = self.__generate_search_url(release)
            self.__debug("fetching URL: " + geturl)
            results = self.__get(geturl)
            if not self.has_errors():
                if re.search(self.__config("SUBS_NO_RESULTS_REGEX"), results):
                    self.__debug("No results were found for " + release)
                    return []
                else:
                    soup = BeautifulSoup(results)
                    self.__debug("HTML retrieved")
                    self.__debug(soup)
                    return self.__handle_search_results(soup)
        elif not self.has_errors():
            self.error = "Invalid login credentials specified."
        return None


def main():
    if len(sys.argv) == 1:
        print "Pipocas scraper v%s (c) David Silva" % (VERSION)
        print "Usage: %s (release|movie|tv-show)" % (sys.argv[0])
    else:
        scraper = PipocasScraper()
        results = scraper.search(sys.argv[1])
        if scraper.has_errors():
            print scraper.get_error()
        else:
            for sub in results:
                print sub

# call the main
if __name__ == "__main__":
    main()
