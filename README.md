<h3>Pipocas Scraper v0.3</h3>

This project aims to provide a python API/CLI tool for the pipocas.tv subtitle web site.

<pre>
<b>usage:</b> pipocas.py [-h] [-d] [-o filename] [-u <user>] [-p <password>] [-v]
                  [-V]
                  release|movie|tv-show

Pipocas scraper v0.3 (c) David Silva 2013

positional arguments:
  release|movie|tv-show
                        release/movie/tv-show to be searched for

optional arguments:
  -h, --help            show this help message and exit
  -d, --download        specifies that the top rated subtitle found shoud be
                        automatically downloaded
  -o filename, --output filename
                        specifies that path/filename for the downloaded
                        subtitle. The default name is the subtitle id plus ZIP
                        extension
  -l language, --language language
                        specifies the language for the subtitle lookup. Valid
                        choices are: pt, br, es, en. The default behavior
                        doesn't filter for any kind of language
  -u <user>, --user <user>
                        specifies the user for the authentication
  -p <password>, --password <password>
                        specifies the password for the authentication
  -v, --verbose         turns on the debug/verbose output
  -V, --version         show program's version number and exit
</pre>

<h3>Soon:</h3>
- Automatically unpack zip file and rename subtitle (if and only if the zip file contains one entry)
- JSON output
- XML output 

