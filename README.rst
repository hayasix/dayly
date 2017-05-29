=====
dayly
=====

A Dayly client in Python 3.

Dayly is a DayOne-like diary app compatible with iOS, Android, BlackBerry
and Windows Phone.  It syncs via Dropbox, so we can post entries with this
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

``dayly`` assumes that you are running Dayly with sync via Dropbox.
By default the sync directory is ``~/Dropbox/Apps/Dayly``.  You can
change it in the setting file ``.dayly`` described below.

API Key
=======

dayly uses OpenWeatherMap to get weather information, so a API key of
OWM is required.  Both free and paid (pro) subscription plans work.
If you are new to OpenWeatherMap, get your own account at:
https://home.openweathermap.org/users/sign_up

Settings
========

Create a text file named ``.dayly`` in your home directory.  This file
should be comply with ordinary ``.ini`` format.  You can change the
location and the name of ``.dayly`` later by option.

In ``.dayly``, prepare ``[OpenWeatherMap]`` section and store your OWM
API key as follows::

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

Command
=======

Now you can issue ``dayly`` command.  To get help, ``dayly -h``.

For now, ``dayly`` can only post new entries.


-------------
Customization
-------------

Dropbox sync folder
===================

Dropbox sync folder for Dayly can be assigned as follows::

    [dayly]
    syncdir=/your/favorite/directory

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

Language
========

Set your favorite language in ``.dayly`` as follows::

    [dayly]
    syncdir=/your/favorite/directory
    language=ja  ; zh, en, hi, es, ar, ...

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

The language set above will be applied during geocoding and getting
weather information.  You can change your language later by option.

Locations
=========

Your favorite locations can be defined in ``.dayly`` as follows::

    [dayly]
    syncdir=/your/favorite/directory
    language=ja  ; zh, en, hi, es, ar, ...

    [OpenWeatherMap]
    apikey=0123456789abcdef0123456789abcdef

    [locations]
    home=The Great Pyramid at Giza
    office=1600 Pennsylvania Avenue NW Washington, D.C. 20500 U.S.
    villa=(-14.692110, -75.148877)  ; (latitude, longitude)

So ``echo Hi! | dayly --debug home`` gives a virtual entry like this::

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

-------------------------
Embedded Meta Information
-------------------------

The date, time and/or location of an entry can be specified in the first or
second line of the content text as follows::

    !2017-12-31 23:59:59
    @home
    This is the content body.  This entry has its locatin 'home' (defined in
    the setting file described above) and its date/time 2017-12-31 23:59:59
    in YYYY-MM-DD HH:MM:SS format.

-----------
Limitations
-----------

Actions
=======

This program only posts a new entry; browse, search or any other actions
are not supported.

Time zone
=========

Time zone is not supported for option ``--date``.

Weather Information
===================

Historical weather information is not supported.

Weather information is not given if more than 3 hours have passed since
the time specified by option ``--date``.  Note that ``--date 20171231`` is
equivalent to ``--date 20171231T000000``.


-------
License
-------

Copyright (C) 2017 HAYASI Hideki <linxs@linxs.org>.

This program is licensed under Zope Public License (ZPL) Version 2.1.
See ``LICENSE`` for details.
