#!/usr/bin/env python3
# vim: set fileencoding=utf-8 fileformat=unix :

"""Post an entry in Dayly repository in Dropbox synced folder.

Usage: {script} [options]

Options:
    -h, --help              show this
    --datetime <timespec>   set timestamp   YYYYmmddTHHMMSS
    --timestamp <timespec>  set timestamp   YYYYmmddTHHMMSS
    --address <text>        set address
    --latitude <n>          set latitude    [+-]NNN.NNNN (degree)
    --longitude <n>         set longitude   [+-]NNN.NNNN (degree)
    --altitude <n>          set altitude    [+-]NNNN (meter)
    --humidity <n>          set humidity    0..100 (percent)
    --temperature <n>       set temperature [+-]NNN (Fahrenheit)
    --skyline <text>        set skyline
    --weather <text>        set weather
    --photo <path>          set photo read from <path>
    --language <lang>       set language for address/weather
    --conf <path>           read settings from <path> [default: ~/.dayly]
    --debug                 don't write actually
    --version               show script version
"""


import sys
import os
import shutil
import time
import random
import json
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError

from pygeocoder import Geocoder, GeocoderError


__version__ = "0.5.0"
__author__ = "HAYASI Hideki"
__copyright__ = "Copyright (C) 2017 HAYASI Hideki"
__license__ = "ZPL 2.1"
__email__ = "linxs@linxs.org"
__status__ = "Development"

DAYLYVERSION = "1.0.3.3"
DAYLYIDBYTES = 20
DAYLYDIR = os.path.expanduser("~/Dropbox/Apps/Dayly")
DAYLYPHOTODIR = DAYLYDIR + "/photos"
DAYLYENTRYDIR = DAYLYDIR + "/entries"

DEFAULT_TIMEZONE = "Asia/Tokyo"

OWM_APIKEY = "ef3b99de363453dc4ac427cc50df28af"
OWM_QUERY = ("http://api.openweathermap.org/data/2.5/weather?"
             "lat={lat}&lon={lon}&appid={apikey}")


def sanitized(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class DaylyEntry:

    def __init__(self, idstring):
        self.version = "1.0.3.3"
        self.generated = time.time()
        self._location = None
        self._weather = None
        self._media = []
        self.id = os.path.splitext(idstring)[0].zfill(DAYLYIDBYTES * 2)

    def filename(self):
        return self.id + ".entry"

    def photofilename(self):
        return "".zfill(DAYLYIDBYTES) + "_" + self.id + ".jpg"

    def set_location(self,
            address=None, latitude=None, longitude=None, altitude=None):
        self._location = dict(
                address=address,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                )

    def set_weather(self,
            humidity=None, temperature=None, skyline=None, weather=None):
        self._weather = dict(
                humidity=humidity,
                temperature=temperature,
                skyline=skyline,
                weather=weather,
                )

    def add_media(self, type="photo", filename=None, description=""):
        self._media.append(dict(
            type=type,
            filename=filename or self.photofilename(),
            description=description,
            ))

    def __str__(self):
        t = ["<entry>"]
        def a(indent, k, v=None):
            v = v or getattr(self, k, "")
            if v is None: v = "nan"
            t.append("{i}<{k}>{v}</{k}>".format(i=" " * indent, k=k, v=v))
        def getattrs(*names):
            for name in names:
                v = getattr(self, name, None)
                if v: return v
            return None
        a(1, "version")
        a(1, "generated", int(getattrs("generated", "datetime")))
        a(1, "id")
        a(1, "content", sanitized(self.content))
        a(1, "datetime", int(getattrs("datetime", "generated")))
        a(1, "timestamp", int(getattrs("timestamp") or -1))
        a(1, "flags", "0")
        a(1, "status", "1")
        if self._location:
            t.append(" <location>")
            a(2, "address", self._location["address"])
            a(2, "latitude", self._location["latitude"])
            a(2, "longitude", self._location["longitude"])
            a(2, "altitude", self._location["altitude"])
            t.append(" </location>")
        if self._media:
            t.append(" <media>")
            for m in self._media:
                t.append("  <item>")
                a(3, "type", m["type"])
                a(3, "file", m["filename"])
                a(3, "description", m["description"])
                t.append("  </item>")
            t.append(" </media>")
        if self._weather:
            t.append(" <weather>")
            a(2, "humidity", self._weather["humidity"])
            a(2, "temperature", self._weather["temperature"])
            a(2, "skyline", self._weather["skyline"])
            a(2, "weather", self._weather["weather"])
            t.append(" </weather>")
        t.append("</entry>")
        return "\n".join(t)


def newid():
    return hex(random.randint(0, 256 ** DAYLYIDBYTES))[2:].zfill(40).upper()


def import_media(entry_id, path, pretend=False):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".jpg": pass
    elif ext == ".jpeg": ext = ".jpg"
    else: raise ValueError("photo must be *.jpg or *.jpeg")
    while True:
        newpath = os.path.join(DAYLYPHOTODIR, "{}_{}{}".format(
                newid(), entry_id, ext))
        if not os.path.exists(newpath): break
    if pretend: print("----- copy {} to {}".format(path, newpath))
    else: shutil.copy(path, newpath)
    return os.path.basename(newpath)


def get_altitude(latitude, longitude, unit=None):
    return None


def get_location(address=None, latitude=None, longitude=None, altitude=None,
        language=None, altitude_unit=None):
    if address:
        try:
            location = Geocoder.geocode(address, language=language)
        except GeocoderError as e:
            if e.args[0] == "ZERO_RESULTS":
                return (address, None, None, None)
            raise
    else:
        if not all([latitude, longitude]):
            return ("unknown place", None, None, None)
        try:
            location = Geocoder.reverse_geocode(latitude, longitude,
                    language=language)
        except GeocoderError as e:
            if e.args[0] == "ZERO_RESULTS":
                return ("unknown place", latitude, longitude, None)
            raise
    address = location[0].formatted_address
    latitude = location[0].latitude
    longitude = location[0].longitude
    altitude = get_altitude(latitude, longitude, unit=altitude_unit)
    return (address, latitude, longitude, altitude)


def get_weather(apikey, coordinates):
    lat, lon = coordinates
    url = OWM_QUERY.format(apikey=apikey, lat=lat, lon=lon)
    try:
        response = urlopen(url)
    except URLError as e:
        eprint("URLError: reason={}, code={}".format(
                getattr(e, "reason", "unknown"),
                getattr(e, "code", "unknown")))
        return None
    return json.loads(response.read().decode("utf-8"))


def build_dayly_entry(unixtime, content,
        timestamp=None,
        address=None, latitude=None, longitude=None, altitude=None,
        weather=None, skyline=None, temperature=None, humidity=None,
        photopath=None,
        owmapikey=None,
        language=None,
        pretend=False):
    entry = DaylyEntry(newid())
    if unixtime is None:
        unixtime = time.time()
    elif isinstance(unixtime, str):
        unixtime = unixtime.translate(str.maketrans("T", " ", ":-"))
        unixtime = time.mktime(time.strptime(unixtime, "%Y%m%d %H%M%S"))
    elif isinstance(unixtime, time.struct_time):
        unixtime = time.mktime(unixtime)
    entry.datetime = unixtime
    entry.content = content
    entry.timestamp = timestamp
    if any([address, latitude, longitude, altitude]):
        address, latitude, longitude, altitude = get_location(
                address, latitude, longitude, altitude, language=language)
        entry.set_location(address, latitude, longitude, altitude)
        if owmapikey:
            owm = get_weather(owmapikey, (latitude, longitude))
            weather = " ".join(word.capitalize() for word
                            in owm["weather"][0]["description"].split())
            skyline = owm["weather"][0]["main"]
            temperature = str(owm["main"]["temp"] - 273.15) + "C"
            humidity = owm["main"]["humidity"] / 100.0
    if any([weather, skyline, temperature, humidity]):
        if temperature:
            temperature = str(temperature)
            if temperature.endswith("C"):
                temperature = round(32 + float(temperature[:-1]) * 9 / 5, 2)
            elif temperature.endswith("F"):
                temperature = float(temperature[:-1])
        if humidity:
            humidity = str(humidity)
            if humidity.endswith("%"):
                humidity = float(humidity.rstrip("%")) / 100
        entry.set_weather(humidity, temperature, skyline, weather)
    if photopath:
        path = import_media(entry.id, photopath, pretend=pretend)
        entry.add_media(filename=path)
    if pretend:
        print(entry.filename())
        for line in str(entry).splitlines():
            print("| " + line)
    else:
        path = os.path.join(DAYLYENTRYDIR, entry.filename())
        with open(path, "w", encoding="utf-8") as out:
            out.write(str(entry))
        print(path)


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
    import configparser
    encoding = (getencoding(path) or "utf-8").replace("_", "-").lower()
    if encoding == "utf-8": encoding = "utf-8-sig"
    conf = configparser.ConfigParser(dict(
            language="en",
            timezone=DEFAULT_TIMEZONE,
            ))
    conf.read(path, encoding=encoding)
    return conf


def main(doc):
    import docopt
    args = docopt.docopt(doc.format(script=__file__), version=__version__)
    try:
        conf = read_config(os.path.expanduser(args["--conf"]))
    except FileNotFoundError:
        conf = None
    build_dayly_entry(args["--datetime"], sys.stdin.read().strip(),
            timestamp=args["--timestamp"],
            address=args["--address"],
            latitude=args["--latitude"],
            longitude=args["--longitude"],
            altitude=args["--altitude"],
            weather=args["--weather"],
            skyline=args["--skyline"],
            temperature=args["--temperature"],
            humidity=args["--humidity"],
            photopath=os.path.expanduser(args["--photo"] or ""),
            owmapikey=conf.get("OpenWeatherMap", "apikey") if conf else None,
            language=args["--language"] or conf.get("dayly", "language"),
            pretend=args["--debug"])


if __name__ == "__main__":
    main(__doc__)
