=====
dayly
=====

A Dayly client in Python 3.

Dayly is a DayOne-like diary app compatible with iOS, Android and
BlackBerry.  It syncs with Dropbox, so we can post an entry via this
program.  For more information, visit: http://miciniti.com/blog/

------------
Installation
------------

``pip install dayly``

-----
Usage
-----

Dropbox Folder
==============

``dayly`` assumes that you runs Dayly with sync via Dropbox.  The sync
directory must be ``~/Dropbox/Apps/Dayly``.  Otherwise, you have to
modify the source code, ``dayly.py``.  This limitation will be removed
in the near future.

API Key
=======

dayly uses OpenWeatherMap to get weather information, so a API key of
OWM is required.  Both free and paid (pro) subscription plans work.
If you are new to OpenWeatherMap, get your own account at:
https://home.openweathermap.org/users/sign_up

Settings
========

Place a text file named ``.dayly`` in your home directory.  This file
should be comply with ordinary ``.ini`` format.  You can change the
location and the name of ``.dayly`` later by option.

In ``.dayly``, prepare ``[OpenWeatherMap]`` section and store your OWM
API key as following::

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

Command
=======

Now you can issue ``dayly`` command.  To get help, ``dayly -h``.

For now, ``dayly`` can only post a new entry.

-------------
Customization
-------------

Language
========

Set your favorite language in ``.dayly`` like this::

    [dayly]
    language=ja  ; zh, en, hi, es, ar, ...

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

The language set above will be applied during geocoding and getting
weather information.  You can change your favorite language later by
option.

Locations
=========

Your favorite locations can be registered in ``.dayly`` like this::

    [dayly]
    language=ja  ; zh, en, hi, es, ar, ...

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

    [locations]
    home=The Great Pyramid at Giza
    office=1600 Pennsylvania Avenue NW Washington, D.C. 20500 U.S.
    villa=(-14.692110, -75.148877)  ; (latitude, longitude)

So ``echo Hi! | dayly --debug en home`` gives a virtual entry like this::

    | <entry>
    |  <version>1.0.3.3</version>
    |  <generated>1494587511</generated>
    |  <id>1A97BBAD58A13E5968F96D7FB7011D343EC7957D</id>
    |  <content>Hi!</content>
    |  <datetime>1494587511</datetime>
    |  <timestamp>-1</timestamp>
    |  <flags>0</flags>
    |  <status>1</status>
    |  <location>
    |   <address>Al Haram, Nazlet El-Semman, Al Haram, Giza Governorate, Egypt</address>
    |   <latitude>29.9792345</latitude>
    |   <longitude>31.1342019</longitude>
    |   <altitude>63.8</altitude>
    |  </location>
    |  <weather>
    |   <humidity>0.32</humidity>
    |   <temperature>88.05</temperature>
    |   <skyline>Clear</skyline>
    |   <weather>Clear Sky</weather>
    |  </weather>
    | </entry>

--------------
Known Problems
--------------

-   ``dayly`` can only post a new entry.  This is the specification.

-   Location of Dropbox sync folder is hard-coded and cannot be replaced
    by option.  This problem will be fixed in the near future.

-   The date and time specified by option --date are ignored to in
    accessing OpenWeatherMap.  Only the current weather information
    is provided.  This problem will be fixed in the near future.

-----------
Legal Stuff
-----------

(C) 2017 HAYASI Hideki <linxs@linxs.org>.

This program is licensed under ZPL 2.1.  See ``LICENSE``.
