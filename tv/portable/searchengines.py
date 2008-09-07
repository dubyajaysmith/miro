# Miro - an RSS based video player application
# Copyright (C) 2005-2008 Participatory Culture Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# In addition, as a special exception, the copyright holders give
# permission to link the code of portions of this program with the OpenSSL
# library.
#
# You must obey the GNU General Public License in all respects for all of
# the code used other than OpenSSL. If you modify file(s) with this
# exception, you may extend this exception to your version of the file(s),
# but you are not obligated to do so. If you do not wish to do so, delete
# this exception statement from your version. If you delete this exception
# statement from all source files in the program, then also delete it here.

from miro.util import checkU, returnsUnicode
from miro.xhtmltools import urlencode
from xml.dom.minidom import parse
from miro.plat import resources
import os
from miro import config
from miro import prefs
import logging

class SearchEngineInfo:
    def __init__(self, name, title, url, sort_order=0):
        checkU(name)
        checkU(title)
        checkU(url)
        self.name = name
        self.title = title
        self.url = url
        self.sort_order = sort_order

    def get_request_url(self, query, filterAdultContents, limit):
        requestURL = self.url.replace(u"%s", urlencode(query))
        requestURL = requestURL.replace(u"%a", unicode(int(not filterAdultContents)))
        requestURL = requestURL.replace(u"%l", unicode(int(limit)))
        return requestURL

    def __repr__(self):
        return "<SearchEngineInfo %s %s" % (self.name, self.title)

_engines = []

def delete_engines():
    global _engines
    _engines = []

def search_for_search_engines(dir_):
    engines = {}
    try:
        for f in os.listdir(dir_):
            if f.endswith(".xml"):
                engines[os.path.normcase(f)] = os.path.normcase(os.path.join(dir_, f))
    except OSError:
        pass
    return engines

def warn(filename, message):
    logging.warn("Error parsing searchengine: %s: %s", filename, message)

def load_search_engine(filename):
    try:
        dom = parse(filename)
        id_ = displayname = url = sort = None
        root = dom.documentElement
        for child in root.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                tag = child.tagName
                text = child.childNodes[0].data
                if tag == "id":
                    if id_ != None:
                        warn(filename, "Duplicated id tag")
                        return
                    id_ = text
                elif tag == "displayname":
                    if displayname != None:
                        warn(filename, "Duplicated displayname tag")
                        return
                    displayname = text
                elif tag == "url":
                    if url != None:
                        warn(filename, "Duplicated url tag")
                        return
                    url = text
                elif tag == "sort":
                    if sort != None:
                        warn(filename, "Duplicated sort tag")
                        return
                    sort = float(text)
                else:
                    warn(filename, "Unrecognized tag %s" % tag)
                    return
        dom.unlink()
        if id_ == None:
            warn(filename, "Missing id tag")
            return
        if displayname == None:
            warn(filename, "Missing displayname tag")
            return
        if url == None:
            warn(filename, "Missing url tag")
            return
        if sort == None:
            sort = 0

        _engines.append(SearchEngineInfo(id_, displayname, url))

    except:
        warn(filename, "Exception parsing file")

def create_engines():
    delete_engines()
    engines = search_for_search_engines(resources.path("searchengines"))
    engines_dir = os.path.join(config.get(prefs.SUPPORT_DIRECTORY), "searchengines")
    engines.update(search_for_search_engines(engines_dir))
    for fn in engines.itervalues():
        load_search_engine(fn)

    _engines.append(SearchEngineInfo(u"all", u"Search All", u"", -1))
    _engines.sort(lambda a, b: cmp((a.sort_order, a.name, a.title), 
                                   (b.sort_order, b.name, b.title)))

@returnsUnicode
def get_request_url(engine_name, query, filter_adult_contents=True, limit=50):
    if query == "LET'S TEST DTV'S CRASH REPORTER TODAY":
        someVariable = intentionallyUndefinedVariableToTestCrashReporter

    if query == "LET'S DEBUG DTV: DUMP DATABASE":
        from miro import database
        database.defaultDatabase.liveStorage.dumpDatabase(database.defaultDatabase)
        return u""

    if engine_name == u'all':
        all_urls = [urlencode(engine.get_request_url(query, filter_adult_contents, limit)) 
                    for engine in _engines if engine.name != u'all']
        return "dtv:multi:" + ','.join(all_urls)

    for engine in _engines:
        if engine.name == engine_name:
            return engine.get_request_url(query, filter_adult_contents, limit)
    return u""

def get_search_engines():
    return list(_engines)

def get_last_engine_title():
    return get_engine_title(get_last_engine())

def get_engine_title(name):
    for engine in _engines:
        if engine.name == name:
            return engine.title
    return u''

def get_last_engine():
    # FIXME - this needs to be re-written
    return u"youtube"
