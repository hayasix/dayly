#!/usr/bin/env python3
# vim: set fileencoding=utf-8 fileformat=unix :

"""{script}: Post an entry in Dayly repository in Dropbox synced folder.

Usage: {script} [options] [LOCATION]

Options:
  -h, --help                show this
  -f, --conf=<path>         read settings from <path> [default: ~/.dayly]
  -d, --date=<timespec>     set date and time for entry; YYYYmmddTHHMMSS
  -p, --photo=<path>        attach photo
  -l, --language=<lang>     set language for address/weather
  --filename                print filename of entry created
  --debug                   don't create entry actually
  --version                 show version

Time Zone:
    <timespec> does NOT have time zone; every <timespec> is deemed to be
    the local time.

Location:
    LOCATION can be defined in the settings file specified with option --conf.

Weather History:
    Weather history (or forecast) is not supported yet even if --date option
    is given.  This problem is expected to be fixed in the near future.
"""


import sys
import os
import shutil
import time
import random
import re
from configparser import ConfigParser, NoOptionError

import geocoder
import pyowm


__version__ = "0.7.3"
__author__ = "HAYASI Hideki"
__copyright__ = "Copyright (C) 2017 HAYASI Hideki"
__license__ = "ZPL 2.1"
__email__ = "linxs@linxs.org"
__status__ = "Beta"
__description__ = "A console version of Dayly diary app"

DAYLYVERSION = "1.0.3.3"
DAYLYIDBYTES = 20
DAYLYDIR = os.path.expanduser("~/Dropbox/Apps/Dayly")
DAYLYPHOTODIR = DAYLYDIR + "/photos"
DAYLYENTRYDIR = DAYLYDIR + "/entries"

DEFAULT_TIMEZONE = "Asia/Tokyo"

LATLONPAT = r"\((?P<lat>[+\-]?\d*(\.\d*)?), *(?P<lon>[+\-]?\d*(\.\d*)?)\)"


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

    def __init__(self, dt, id=None, language=None):
        if isinstance(dt, str):
            dt = dt.translate(str.maketrans("T", " ", ":-"))
            dt = time.mktime(time.strptime(dt, "%Y%m%d %H%M%S"))
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
        return self.id + ".entry"

    def set_location(self, location, language=None,
            altitude=None, unit="meters"):
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
        location = geocoder.google(location, **kw)
        if not location.ok: raise ValueError("unknown place")
        address = location.address
        if not altitude:
            altitude = getattr(geocoder.elevation(location.latlng), unit)
        self._location = dict(
                address=address,
                latitude=location.latlng[0],
                longitude=location.latlng[1],
                altitude=altitude)

    def set_weather(self, apikey, language=None):
        """Get weather information from OpenWeatherMap.

        :param str apikey: OpenWeatherMap API key
        :param str language: language e.g. 'en', 'ja'
        """
        language = language or self.language
        owm = pyowm.OWM(apikey, language=language)
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
        if ext == ".jpg": pass
        elif ext == ".jpeg": ext = ".jpg"
        else: raise ValueError("photo must be *.jpg or *.jpeg")
        while True:
            newfile = "{}_{}{}".format(newid(), self.id, ext)
            newpath = os.path.join(DAYLYPHOTODIR, newfile)
            if not os.path.exists(newpath): break
        if self.debug: print("----- copy {} to {}".format(path, newpath))
        else: shutil.copy(path, newpath)
        self._media.append(dict(
            type=type,
            filename=newfile,
            description=description))

    def __str__(self):
        t = []
        indent = 0
        def _(k, v=None):
            v = v or getattr(self, k, "")
            if v is None: v = "nan"
            t.append("{i}<{k}>{v}</{k}>".format(i=" " * indent, k=k, v=v))
        def __(k):
            t.append("{i}<{k}>".format(i=" " * indent, k=k))
        def getattrs(*names):
            for name in names:
                v = getattr(self, name, None)
                if v: return v
        __("entry")
        indent += 1
        _("version")
        _("generated", int(getattrs("generated", "datetime")))
        _("id")
        _("content", sanitized(self.content))
        _("datetime", int(getattrs("datetime", "generated")))
        _("timestamp", int(getattrs("timestamp") or -1))
        _("flags", "0")
        _("status", "1")
        if self._location:
            __("location")
            indent += 1
            _("address", self._location["address"])
            _("latitude", self._location["latitude"])
            _("longitude", self._location["longitude"])
            _("altitude", self._location["altitude"])
            indent -= 1
            __("/location")
        if self._media:
            __("<media>")
            indent += 1
            for m in self._media:
                __("item")
                indent += 1
                _("type", m["type"])
                _("file", m["filename"])
                _("description", m["description"])
                indent -= 1
                __("/item")
            indent -= 1
            __("/media")
        if self._weather:
            __("weather")
            indent += 1
            _("humidity", self._weather["humidity"])
            _("temperature", self._weather["temperature"])
            _("skyline", self._weather["skyline"])
            _("weather", self._weather["weather"])
            indent -= 1
            __("/weather")
        indent -= 1
        __("/entry")
        return "\n".join(t)


def build(timespec, content,
        location=None,
        photo=None,
        owmapikey=None,
        language=None,
        debug=False):
    """Build a Dayly entry.

    :param time.time timespec: date and time on which the entry describes
    :param str content: entry text
    :param str/tuple location: address or coordinates
    :param str photo: pathname of the attached file (photo)
    :param str owmapikey: the API key for OpenWeatherMap
    :param str language: languaged used in the response from OpenWeatherMap
    :param bool debug: True=only report; False=actually create an entry file
    :rtype: str
    :return: filename/pathname of the entry (virtually) created
    """
    entry = DaylyEntry(timespec, id=newid(), language=language)
    if debug: entry.debug = True
    entry.content = content
    entry.timestamp = -1  # ToDo:
    if location:
        entry.set_location(location)
        if owmapikey: entry.set_weather(owmapikey)
    if photo: entry.add_media(photo, description=description)
    if debug:
        for line in str(entry).splitlines(): print("| " + line)
    else:
        path = os.path.join(DAYLYENTRYDIR, entry.filename())
        with open(path, "w", encoding="utf-8") as out:
            out.write(str(entry))
    return entry.filename()


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
            try: mo = coding.search(in_.readline())
            except UnicodeDecodeError: continue
            if mo: return mo.group(0)
    return None


def read_config(path):
    """Read settings from an INI file.

    :param str path: pathname of the INI file
    :rtype: configparser.ConfigParser
    :return: contents of the INI file
    """
    while os.path.islink(path): path = os.readlink(path)
    path = os.path.realpath(path)
    if not os.path.isfile(path): return None
    encoding = (getencoding(path) or "utf-8").replace("_", "-").lower()
    if encoding == "utf-8": encoding = "utf-8-sig"
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
    location = args["LOCATION"] or "home"
    if location:
        try: location = conf.get("locations", location)
        except NoOptionError: pass  # raw address
    if location.startswith("("):
        mo = re.match(LATLONPAT, location)
        if not mo: raise ValueError("illegal coordinates")
        location = (float(mo.group("lat")), float(mo.group("lon")))
    filename = build(
            args["--date"],
            sys.stdin.read().strip(),
            location=location,
            photo=os.path.expanduser(args["--photo"] or ""),
            owmapikey=conf.get("OpenWeatherMap", "apikey") if conf else None,
            language=args["--language"] or conf.get("dayly", "language"),
            debug=args["--debug"])
    if args["--filename"]: print(filename)


if __name__ == "__main__":
    sys.exit(main())
