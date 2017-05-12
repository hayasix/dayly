#/usr/bin/env python3.5
# vim: set fileencoding=utf-8 fileformat=unix :

from setuptools import setup
from os.path import join, dirname, exists

with open("dayly.py", "r") as in_:
    for line in in_:
        if line.startswith("def ") or line.startswith("class "): break
        if line.startswith("__"): exec(line)

def read_readme(readme):
    return open(join(dirname(__file__), readme), encoding="utf-8").read()


setup(
    name = "dayly",
    version = __version__,
    author = __author__,
    author_email = __email__,
    url = "https://github.com/linxsorg/dayly",
    license = __license__,
    description = __description__,
    long_description = read_readme("README.rst"),
    platforms = ["generic"],
    py_modules = ["dayly"],
    install_requires = ["docopt>=0.6.2", "geocoder>=1.22.4", "pyowm>=2.6.1"],
    entry_points = {"console_scripts": ["dayly=dayly:main"]},
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: Zope Public License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: Japanese",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
