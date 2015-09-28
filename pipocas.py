#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
import re
import datetime
import argparse
import tempfile
import os
import shutil
from bs4 import BeautifulSoup

# configuration

configuration = {
    # authentication parameters
    "LOGIN_USER": "xxx",
    "LOGIN_PWD": "xxx",
    # tipically you don't need to change nothing below
    "DEBUG": False,
    "BASE_URL": "http://pipocas.tv/",
    "DL_ID_URL": "http://pipocas.tv/download.php?id=",
    "LOGIN_URL": "http://pipocas.tv/vlogin.php",
    "LOGIN_FAIL_REGEX": "<strong>Login falhado!</strong>",
    "SUBS_LANG": "todas",
    "SUBS_LANG_MAP": {"pt": "portugues", "br": "brasileiro", "es": "espanhol", "en": "ingles", "todas": "todas"},
    "SUBS_URL": "http://pipocas.tv/subtitles.php?release={0}&grupo=rel&linguagem={1}",
    "SUBS_NO_RESULTS_REGEX": "<b>Nada Encontrado.</b>",
    "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36",
    "SUBS_COOKIE_WHITELIST": ["PHPSESSID", "__cfduid", "pipocas"]
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
VERSION = "0.3"


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
        return u"Country" + str(attrs)


# Subtitle class
class PipocasSubtitle:
    def __init__(self, id, release, poster_url, country, hits, rating, votes, download_url):
        """
        Subtitle constructor
        """
        self.id = id
        self.release = release
        self.poster_url = poster_url
        self.country = country
        self.hits = hits
        self.rating = rating
        self.votes = votes
        self.download_url = download_url

    def get_id(self):
        """
        Gets the subtitle id
        """
        return self.id

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
        return u"Subtitle" + str(attrs)


# Pipocas custom HTTP redirect handler
class PipocasRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        """
        Handles the 301 redirects
        """
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.headers = headers
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        """
        Handles the 302 redirects
        """
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.headers = headers
        result.status = code
        return result


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
            print "[DEBUG]-[" + str(datetime.datetime.now()) + "] " + str(txt)

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
        request.add_header("DNT", "1")
        request.add_header("User-agent", self.__config("HTTP_USER_AGENT"))
        request.add_header("Referer", self.__config("BASE_URL"))
        request.add_header("Origin", self.__config("BASE_URL"))
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
            return response
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
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
            request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
            request.add_header("Accept-Encoding", "Accept-Encoding: gzip,deflate")
            request.add_header("Accept-Language", "pt-PT,pt;q=0.8,en-US;q=0.6,en;q=0.4")
            request.add_header("Cookie", "pipocasv3_c_pipo_uid=NDA4NzU%3D; pipocasv3_c_pipo_pass=e899334fcb9a95666a5ad987a62df805e5973e60; pipocasv3_hashv=c1b22a5870430d5e848e370d76b0fa73; popup_user_login=yes")
            opener = urllib2.build_opener(PipocasRedirectHandler())
            response = opener.open(request)
            return response
        except urllib2.HTTPError, e:
            self.error = self.__handle_http_error(e)
        except urllib2.URLError, e:
            self.error = "Unable to reach the server:", e.reason
        return None

    def __cleanCookies(self, cookies):
        """
        Cleans the received coookies
        """
        ret = ""
        cookies = cookies.replace("httponly, ", "").replace(" path=/,", "")
        for cookie_str in cookies.split("; "):
            key_value = cookie_str.split("=")
            if len(key_value) == 2:
                for whitelist_str in self.__config("SUBS_COOKIE_WHITELIST"):
                    if key_value[0].startswith(whitelist_str):
                        c = key_value[0] + "=" + key_value[1] + "; "
                        ret = c if len(ret) == 0 else ret + c
                        break
        return ret

    def login(self, user, pwd):
        """
        Logs in into the server
        """
        url = self.__config("LOGIN_URL")
        self.__debug("Logging in as " + user + "...")
        response = self.__post(url, {'username': user, 'password': pwd})
        if not self.has_errors():
            html = response.read()
            if not re.search(self.__config("LOGIN_FAIL_REGEX"), html):
                self.cookies = self.__cleanCookies(response.info()["Set-Cookie"])
                self.__debug("Successfully logged in: %s" % (self.cookies))
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
            tmp = result.select("li.sub-box4")[0].div.div.contents
            if not tmp is None and len(tmp) > 0:
                tmp = tmp[len(tmp)-1].split()
                if not tmp is None and len(tmp) == 6:
                    elements["rating"] = float(tmp[0])
                    elements["votes"] = int(tmp[4])
            # download
            tmp = result.select("a.download")[0]
            elements["download"] = configuration["BASE_URL"] + tmp["href"]
            # id
            elements["id"] = tmp["href"].replace("download.php?id=", "")
            # add the subtitle
            response.append(self.__create_sub(elements))
        return self.__sort(response)

    def __create_sub(self, elements):
        """
        Creates the subtitle class from the elements
        """
        country = PipocasSubtitleCountry(elements['country'], elements['country_flag'])
        return PipocasSubtitle(elements['id'], elements['release'], elements['poster'],
                               country, elements['hits'], elements['rating'],
                               elements['votes'], elements['download'])

    def __sort(self, subtitles):
        """
        Sorts the given list of subtitles by rating/hits
        """
        return sorted(subtitles, key=lambda subtitle: (subtitle.get_rating(), subtitle.get_hits()), reverse=True)

    def __generate_search_url(self, release, language):
        return self.__config("SUBS_URL").format(urllib.quote_plus(release), self.__config("SUBS_LANG_MAP")[language])

    def __check_zip_for_single_sub(self, zip_file, rename_subtitle):
        """
        Checks the given zip file contains only a subtitle
        """
        # opens the zip file
        res = zip_file
        """
        TODO: implement
        try:
            zf = zipfile.ZipFile(zip_file)
            self.__debug("ZIP file found.")
            for member in zf.infolist():
                print member
            zf.close()
        except zipfile.BadZipfile:
            # rar file found
            self.__debug("Invalid zip file found")
        """
        return res

    def __create_tmp_directory(self):
        """
        Creates a temporary directory
        """
        return tempfile.mkdtemp(suffix='.tmp', prefix='pipocas', dir=tempfile.gettempdir())

    def __get_file_extension(self, meta):
        """
        Gets the file extension from the given headers
        from an arbitrary request
        """
        if "Content-Disposition" in meta:
            content = meta["Content-Disposition"]
            for disp in content.split():
                disp = disp.strip()
                if disp.startswith("filename="):
                    filename = disp.replace("filename=", "").replace('"', '')
                    return filename[len(filename)-4:]
        return ".rar"

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

    def download_subtitle(self, subtitles, filename):
        """
        Downloads the given subtitle
        """
        sub = subtitles[0]
        self.download_subtitle_by_id(sub.get_id(), sub.get_download_url(), filename)

    def download_subtitle_by_id(self, identifier, url, filename):
        """
        Downloads the given subtitle by his identifier
        """
        working_dir = os.getcwd()
        is_tmp = False
        result_filename = None
        is_auto_filenamed = False
        # request the file
        self.__debug("downloading subtitle form %s" % (url))
        request = self.__get(url)
        if not self.has_errors():
            meta = request.info()
            # construct the filename
            extension = self.__get_file_extension(meta)
            extension_len = len(extension)
            if filename is None or len(filename) == 0:
                filename = identifier + extension
                is_auto_filenamed = True
            elif os.path.isdir(filename):
                    filename = os.path.join(filename, identifier) + extension
            elif len(filename) < extension_len or not filename[len(filename)-extension_len:] == extension:
                filename += extension
            self.__debug("compressed filename: %s" % (filename))
            # creates a temporary directory for the zip file
            if not os.sep in filename:
                is_tmp = True
                tmp_dir = self.__create_tmp_directory()
                self.__debug("created temporary directory %s" % (tmp_dir))
                filename = os.path.join(tmp_dir, filename)
            else:
                working_dir = os.path.dirname(filename)
            file_size = int(meta.getheaders("Content-Length")[0])
            self.__debug(u"%s bytes to be retrieved" % (file_size))
            # open the file (write)
            fp = open(filename, 'wb')
            file_size_dl = 0
            block_sz = 8192
            while True:
                # read a 8k block
                _buffer = request.read(block_sz)
                if not _buffer:
                    break
                # status
                file_size_dl += len(_buffer)
                fp.write(_buffer)
                status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                status = status + chr(8)*(len(status)+1)
                self.__debug(status)
            # close the file
            fp.close()
            # try to extract the subtitle
            if extension == ".zip":
                result_filename = self.__check_zip_for_single_sub(filename, not is_auto_filenamed)
            else:
                result_filename = filename
            # move the file if in a temporary directory
            if is_tmp:
                dest_file = os.path.join(working_dir, os.path.basename(filename))
                self.__debug("moving file %s to %s" % (result_filename, dest_file))
                os.rename(result_filename, dest_file)
                self.__debug("removing temporary directory..")
                shutil.rmtree(tmp_dir)
                result_filename = dest_file
        return result_filename

    def search(self, user, pwd, release, language):
        """
        Searches subtitles for the given release
        """
        self.error = None
        if self.login(user, pwd):
            geturl = self.__generate_search_url(release, language)
            self.__debug("fetching URL: " + geturl)
            results = self.__get(geturl).read()
            if not self.has_errors():
                if re.search(self.__config("SUBS_NO_RESULTS_REGEX"), results):
                    self.__debug("No results were found for " + release)
                    return []
                else:
                    soup = BeautifulSoup(results, "html.parser")
                    self.__debug("HTML retrieved")
                    return self.__handle_search_results(soup)
        elif not self.has_errors():
            self.error = "Invalid login credentials specified."
        return None


# arg parser
parser = argparse.ArgumentParser(description='Pipocas scraper v%s (c) David Silva 2013' % (VERSION))
parser.add_argument('release', metavar='release|movie|tv-show', default=None, help='release/movie/tv-show to be searched for')
parser.add_argument('-i', '--identifier', action='store_true', help='marks the release as an identifier rather than plaintext (forces -d option as well)')
parser.add_argument('-d', '--download', action='store_true', help='specifies that the top rated subtitle found shoud be automatically downloaded')
parser.add_argument('-o', '--output', metavar="filename", default=None, help='specifies that path/filename for the downloaded subtitle. The default name is the subtitle id plus ZIP/SRT extension')
parser.add_argument('-l', '--language', metavar="language", default=configuration["SUBS_LANG"], choices=["pt", "br", "es", "en"], help='specifies the language for the subtitle lookup. \
    Valid choices are: pt, br, es, en. \
    The default behavior doesn\'t filter for any kind of language')
parser.add_argument('-u', '--user', metavar='<user>', default=configuration["LOGIN_USER"], help='specifies the user for the authentication')
parser.add_argument('-p', '--password', metavar='<password>', default=configuration["LOGIN_PWD"], help='specifies the password for the authentication')
parser.add_argument('-v', '--verbose', action='store_true', help='turns on the debug/verbose output')
parser.add_argument('-V', '--version', action='version', version='Pipocas scraper v%s' % (VERSION))
args = parser.parse_args()

# setup debug
configuration["DEBUG"] = args.verbose

# validate -o option (sub_parsers are a bit overkill for this)
#if not args.output is None and not args.download:
#    parser.error("-o/--output must be used with -d/--download switch.")

# execute the scraper
scraper = PipocasScraper()
if args.identifier:
    if scraper.login(args.user, args.password):
        subfile = scraper.download_subtitle_by_id(args.release, configuration["DL_ID_URL"] + args.release, args.output)
        if scraper.has_errors():
            print scraper.get_error()
        else:
            print "zip file downloaded to %s" % (subfile)
    elif not scraper.has_errors():
        print "Invalid login credentials specified."
    else:
        print scraper.get_error()
else:
    subtitles = scraper.search(args.user, args.password, args.release, args.language)
    if scraper.has_errors():
        print scraper.get_error()
    elif not subtitles is None and len(subtitles) > 0:
        if args.download:
            subfile = scraper.download_subtitle(subtitles, args.output)
            if scraper.has_errors():
                print scraper.get_error()
            else:
                print "zip file downloaded to %s" % (subfile)
        else:
            print "   Country\t| Release/Movie/Tv-show\t\t\t\t| Rating\t| Hits\t| Download\t"
            print "-" * 90
            for subtitle in subtitles:
                sub_str = "  " + subtitle.get_country().get_name() + "\t| "
                sub_str += subtitle.get_release() + "\t| "
                sub_str += str(subtitle.get_rating()) + "\t| "
                sub_str += str(subtitle.get_hits()) + "\t| "
                sub_str += subtitle.get_download_url()
                print sub_str
    elif not subtitles is None:
        print "No subtitles were found"
