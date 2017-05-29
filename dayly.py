#!/usr/bin/env python3
# vim: set fileencoding=utf-8 fileformat=unix :

"""{script}: Post an entry in Dayly repository in Dropbox synced folder.

Usage: {script} [options] [LOCATION]

Options:
  -h, --help                show this
  -f, --conf=<path>         read settings from <path> [default: ~/.dayly]
  -d, --date=<timespec>     set date and time for entry; YYYYmmddTHHMMSS
  -p, --photo=<path>        attach JPEG photo
  -l, --language=<lang>     set language for address/weather
  --filename                print filename of entry (virtually) created
  --debug                   don't create entry actually
  --version                 show version

Note:
  Weather information is not given if more than 3 hours have passed since
  the time specified by option --date.  Note that ``--date 20171231`` is
  equivalent to ``--date 20171231T000000``.
"""


import sys
import os
import shutil
import time
import random
import re
import unicodedata
from configparser import ConfigParser, NoOptionError

import geocoder
import pyowm


__version__ = "0.9.0"
__author__ = "HAYASI Hideki"
__copyright__ = "Copyright (C) 2017 HAYASI Hideki"
__license__ = "ZPL 2.1"
__email__ = "linxs@linxs.org"
__status__ = "Beta"
__description__ = "A console version of Dayly diary app"

DAYLYVERSION = "1.0.3.3"
DAYLYIDBYTES = 20
DEFAULT_TIMEZONE = "Asia/Tokyo"
LATLONPAT = r"\((?P<lat>[+\-]?\d*(\.\d*)?), *(?P<lon>[+\-]?\d*(\.\d*)?)\)"
FWHYPHEN = "\u2022"
HWHYPHEN = "\uFF0D"


def sanitized(s):
    """Sanitize HTML/XML text.

    :param str s: source text
    :rtype: str
    :return: sanitized text in which &/</> is replaced with entity refs
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def newid():
    """Create a new random ID.

    :rtype: str
    :return: 40 hexadecimal chars representing a newly created ID
    """
    return hex(random.randint(0, 256 ** DAYLYIDBYTES))[2:].zfill(40).upper()


class DaylyEntry:
    """Dayly entry"""

    syncdir = os.path.expanduser("~/Dropbox/Apps/Dayly")

    def __init__(self, dt, id=None, language=None):
        """Initiator.

        :param str/struct_time dt: entry date and time
        :param str id: entry ID (40 hexadecimal digits)
        :param str language: language for address/weather information
        """
        if isinstance(dt, str):
            dt = dt.translate(str.maketrans("T", " ", ":-"))
            try:
                dt = time.mktime(time.strptime(dt, "%Y%m%d %H%M%S"))
            except ValueError:
                dt = time.mktime(time.strptime(dt, "%Y%m%d"))
        elif isinstance(dt, time.struct_time):
            dt = time.mktime(dt)
        else:
            dt = dt or time.time()
        self.datetime = dt
        self.version = DAYLYVERSION
        self.generated = time.time()
        self._location = None
        self._weather = None
        self._media = []
        self.id = id or os.path.splitext(idstring)[0].zfill(DAYLYIDBYTES * 2)
        self.language = language
        self.debug = False

    def filename(self):
        """Get the filename of entry."""
        return self.id + ".entry"

    def set_location(self, location,
                     language=None, altitude=None, unit="meters"):
        """Set location via Google geocoding service.

        :param tuple/str location:
        :param str language: language for Google geocoding
        :param str language: language e.g. 'en', 'ja'
        :param float altitude: altitude
        :param str unit: altitude unit e.g. 'meters', 'feet'
        """
        language = language or self.language
        unit = dict(m="meters", ft="feet").get(unit, "meters")
        kw = {"language": language}
        if isinstance(location, tuple):
            kw["method"] = "reverse"
        try:
            location = geocoder.google(location, **kw)
        except:
            self._location = dict(
                    address=location,
                    latitude=None, longitude=None, altitude=None)
            return
        if not location.ok:
            raise ValueError("unknown place")
        address = unicodedata.normalize(
                    "NFKC", location.address.replace(FWHYPHEN, HWHYPHEN))
        if not altitude:
            altitude = getattr(geocoder.elevation(location.latlng), unit)
        self._location = dict(
                address=address,
                latitude=location.latlng[0], longitude=location.latlng[1],
                altitude=altitude)

    def set_weather(self, apikey, language=None):
        """Get weather information from OpenWeatherMap.

        :param str apikey: OpenWeatherMap API key
        :param str language: language e.g. 'en', 'ja'
        """
        if not all((self._location["latitude"], self._location["longitude"])):
            return
        language = language or self.language
        try:
            owm = pyowm.OWM(apikey, language=language)
        except:
            if hasattr(self, "_weather"):
                del self._weather
            return
        w = owm.weather_at_coords(
                lat=self._location["latitude"],
                lon=self._location["longitude"])
        ww = w.get_weather()
        self._weather = dict(
                weather=" ".join(word.capitalize() for word
                                 in ww.get_detailed_status().split()),
                skyline=ww.get_status(),
                temperature=ww.get_temperature("fahrenheit")["temp"],
                humidity=ww.get_humidity() / 100.0)

    def add_media(self, path, type="photo", description=""):
        """Attach (add) a file to entry.

        :param str path: pathname of source file
        :param str type: type of attachment; 'photo'
        :param str description:

        Each attachment is copied into Dayly's photo repository dir.
        The source file must be JPEG and has extension '.jpg' or '.jpeg'.
        """
        ext = os.path.splitext(path)[1].lower()
        if ext == ".jpg":
            pass
        elif ext == ".jpeg":
            ext = ".jpg"
        else:
            raise ValueError("photo must be *.jpg or *.jpeg")
        while True:
            newfile = "{}_{}{}".format(newid(), self.id, ext)
            newpath = os.path.join(self.__class__.syncdir, "photos", newfile)
            if not os.path.exists(newpath):
                break
        if self.debug:
            print("----- copy {} to {}".format(path, newpath))
        else:
            shutil.copy(path, newpath)
        self._media.append(dict(
            type=type,
            filename=newfile,
            description=description))

    def __str__(self):
        t = []
        indent_level = 0

        def indent():
            nonlocal indent_level
            indent_level += 1

        def dedent():
            nonlocal indent_level
            indent_level -= 1

        def _(k, v=None):
            v = v or getattr(self, k, "")
            if v is None:
                v = "nan"
            t.append("{i}<{k}>{v}</{k}>".format(
                     i=" " * indent_level,
                     k=k,
                     v=sanitized(str(v))))

        def __(k):
            t.append("{i}<{k}>".format(i=" " * indent_level, k=k))

        def getattrs(*names):
            for name in names:
                v = getattr(self, name, None)
                if v:
                    return v

        __("entry")
        indent()
        _("version")
        _("generated", int(getattrs("generated", "datetime")))
        _("id")
        _("content", self.content)
        _("datetime", int(getattrs("datetime", "generated")))
        _("timestamp", int(getattrs("timestamp") or -1))
        _("flags", "0")
        _("status", "1")
        if self._location:
            __("location")
            indent()
            _("address", self._location["address"])
            _("latitude", self._location["latitude"])
            _("longitude", self._location["longitude"])
            _("altitude", self._location["altitude"])
            dedent()
            __("/location")
        if self._media:
            __("<media>")
            indent()
            for m in self._media:
                __("item")
                indent()
                _("type", m["type"])
                _("file", m["filename"])
                _("description", m["description"])
                dedent()
                __("/item")
            dedent()
            __("/media")
        if self._weather:
            __("weather")
            indent()
            _("humidity", self._weather["humidity"])
            _("temperature", self._weather["temperature"])
            _("skyline", self._weather["skyline"])
            _("weather", self._weather["weather"])
            dedent()
            __("/weather")
        dedent()
        __("/entry")
        return "\n".join(t)

    def save(self):
        """Save i.e. actually write a file of entry."""
        path = os.path.join(self.__class__.syncdir, "entries", self.filename())
        with open(path, "w", encoding="utf-8") as out:
            out.write(str(self))


def build(timespec, content,
          location=None,
          photo=None,
          owmapikey=None,
          language=None,
          syncdir=None,
          debug=False):
    """Build a Dayly entry.

    :param time.time timespec: date and time on which the entry describes
    :param str content: entry text
    :param str/tuple location: address or coordinates
    :param str photo: pathname of the attached file (photo)
    :param str owmapikey: the API key for OpenWeatherMap
    :param str language: languaged used in the response from OpenWeatherMap
    :param str syncdir: Dropbox sync directory
    :param bool debug: True=only report; False=actually create an entry file
    :rtype: str
    :return: filename/pathname of the entry (virtually) created
    """
    if syncdir:
        DaylyEntry.syncdir = os.path.expanduser(syncdir)
    entry = DaylyEntry(timespec, id=newid(), language=language)
    if debug:
        entry.debug = True
    entry.content = content
    entry.timestamp = -1  # ToDo:
    if location:
        entry.set_location(location)
        if owmapikey and (0 <= time.time() - entry.datetime <= 10800):  # in 3H
            entry.set_weather(owmapikey)
    if photo:
        entry.add_media(photo, description=description)
    if debug:
        for line in str(entry).splitlines():
            print("| " + line)
    else:
        entry.save()
    return entry.filename()


def getmetainfo(content):
    """Get meta information from content text.

    :param str content: source text
    :rtype tuple:
    :return: (timespec, location, pure_content)
    """
    timespec = location = None
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if 1 < i:
            break
        if not line:
            continue
        if line.startswith("!"):
            timespec = line[1:].strip()
            lines[i] = None
        elif line.startswith("@"):
            location = line[1:].strip()
            lines[i] = None
    return (timespec, location,
            "\n".join(line for line in lines if line is not None))


def getencoding(path):
    """Detect encoding string from the leading two lines.

    :param str path: pathname of the source file
    :rtype: str or None
    :return: encoding str or None
    """
    import re
    coding = re.compile(r"coding[:=]\s*(\w)+")
    with open(path, encoding="ascii") as in_:
        for _ in (0, 1):
            try:
                mo = coding.search(in_.readline())
            except UnicodeDecodeError:
                continue
            if mo:
                return mo.group(0)
    return None


def read_config(path):
    """Read settings from an INI file.

    :param str path: pathname of the INI file
    :rtype: configparser.ConfigParser
    :return: contents of the INI file
    """
    while os.path.islink(path):
        path = os.readlink(path)
    path = os.path.realpath(path)
    if not os.path.isfile(path):
        return None
    encoding = (getencoding(path) or "utf-8").replace("_", "-").lower()
    if encoding == "utf-8":
        encoding = "utf-8-sig"
    conf = ConfigParser(dict(language="en", timezone=DEFAULT_TIMEZONE))
    conf.read(path, encoding=encoding)
    return conf


def main():
    import docopt
    args = docopt.docopt(__doc__.format(script=os.path.basename(__file__)),
                         version=__version__)
    try:
        conf = read_config(os.path.expanduser(args["--conf"]))
    except FileNotFoundError:
        conf = None
    if not conf:
        raise FileNotFoundError("prepare ~/.dayly before use")
    try:
        syncdir = conf.get("dayly", "syncdir")
    except NoOptionError:
        syncdir = None
    timespec, location, content = getmetainfo(sys.stdin.read().strip())
    timespec = args["--date"] or timespec
    location = args["LOCATION"] or location or "home"
    if location:
        try:
            location = conf.get("locations", location)
        except NoOptionError:
            pass  # raw address
    if location.startswith("("):
        mo = re.match(LATLONPAT, location)
        if not mo:
            raise ValueError("illegal coordinates")
        location = (float(mo.group("lat")), float(mo.group("lon")))
    filename = build(
            timespec, content,
            location=location,
            photo=os.path.expanduser(args["--photo"] or ""),
            owmapikey=conf.get("OpenWeatherMap", "apikey") if conf else None,
            language=args["--language"] or conf.get("dayly", "language"),
            syncdir=syncdir,
            debug=args["--debug"])
    if args["--filename"]:
        print(filename)


if __name__ == "__main__":
    sys.exit(main())
