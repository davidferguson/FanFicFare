# -*- coding: utf-8 -*-

# Copyright 2011 Fanficdownloader team, 2015 FanFicFare team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import string
from textwrap import wrap

from base_writer import *

from xhtml2pdf import pisa

## In BaseStoryWriter, we define _write to encode <unicode> objects
## back into <string> for true output.  But txt needs to write the
## title page and TOC to a buffer first to wordwrap.  And StringIO
## gets pissy about unicode bytes in its buflist.  This decodes the
## unicode containing <string> object passed in back to a <unicode>
## object so they join up properly.  Could override _write to not
## encode and do out.write(whatever.encode('utf8') instead.  Honestly
## not sure which is uglier.
class KludgeStringIO():
    def __init__(self, buf = ''):
        self.buflist=[]
    def write(self,s):
        try:
            s=s.decode('utf-8')
        except:
            pass
        self.buflist.append(s)
    def getvalue(self):
        return u''.join(self.buflist)
    def close(self):
        pass

class PdfWriter(BaseStoryWriter):

    @staticmethod
    def getFormatName():
        return 'pdf'

    @staticmethod
    def getFormatExt():
        return '.pdf'

    def __init__(self, config, story):
        
        BaseStoryWriter.__init__(self, config, story)
        
        self.TEXT_FILE_START = string.Template(u'''


${title}

by ${author}


''')

        self.TEXT_TITLE_PAGE_START = string.Template(u'''
''')

        self.TEXT_TITLE_ENTRY = string.Template(u'''${label}: ${value}
''')

        self.TEXT_TITLE_PAGE_END = string.Template(u'''


''')

        self.TEXT_TOC_PAGE_START = string.Template(u'''

TABLE OF CONTENTS

''')

        self.TEXT_TOC_ENTRY = string.Template(u'''
${chapter}
''')
                          
        self.TEXT_TOC_PAGE_END = string.Template(u'''
''')

        self.TEXT_CHAPTER_START = string.Template(u'''

\t${chapter}

''')
        self.TEXT_CHAPTER_END = string.Template(u'')

        self.TEXT_FILE_END = string.Template(u'''

End file.
''')

    def writeStoryImpl(self, out):

        self.wrap_width = self.getConfig('wrap_width')
        if self.wrap_width == '' or self.wrap_width == '0':
            self.wrap_width = 0
        else:
            self.wrap_width = int(self.wrap_width)
        
        wrapout = KludgeStringIO()
        
        if self.hasConfig("file_start"):
            FILE_START = string.Template(self.getConfig("file_start"))
        else:
            FILE_START = self.TEXT_FILE_START
            
        if self.hasConfig("file_end"):
            FILE_END = string.Template(self.getConfig("file_end"))
        else:
            FILE_END = self.TEXT_FILE_END
            
        wrapout.write(FILE_START.substitute(self.story.getAllMetadata()))

        self.writeTitlePage(wrapout,
                            self.TEXT_TITLE_PAGE_START,
                            self.TEXT_TITLE_ENTRY,
                            self.TEXT_TITLE_PAGE_END)
        towrap = wrapout.getvalue()
        
        self.writeTOCPage(wrapout,
                          self.TEXT_TOC_PAGE_START,
                          self.TEXT_TOC_ENTRY,
                          self.TEXT_TOC_PAGE_END)

        towrap = wrapout.getvalue()
        wrapout.close()
        towrap = removeAllEntities(towrap)
        
        self._write(out,self.lineends(self.wraplines(towrap)))

        if self.hasConfig('chapter_start'):
            CHAPTER_START = string.Template(self.getConfig("chapter_start"))
        else:
            CHAPTER_START = self.TEXT_CHAPTER_START
        
        if self.hasConfig('chapter_end'):
            CHAPTER_END = string.Template(self.getConfig("chapter_end"))
        else:
            CHAPTER_END = self.TEXT_CHAPTER_END
        
        storyHTML = ""

        for index, chap in enumerate(self.story.getChapters()):
            if chap.html:
                logging.debug('Writing chapter text for: %s' % chap.title)
                vals={'url':chap.url, 'chapter':chap.title, 'index':"%04d"%(index+1), 'number':index+1}

                storyHTML = storyHTML + "<code><pre>" + removeAllEntities(CHAPTER_START.substitute(vals)) + "</pre></code>"
                storyHTML = storyHTML + chap.html
                storyHTML = storyHTML + removeAllEntities(CHAPTER_END.substitute(vals))

        storyHTML = storyHTML + FILE_END.substitute(self.story.getAllMetadata())

        header = '<meta charset="utf-8"><style>@page {size: a5;top: 1cm;left: 1cm;right: 1cm;bottom: 1cm;}*{font-size:20px;font-family: "Verdana";}pre{text-align:center;font-weight:bold;page-break-before:always;margin-top:30px;}code{font-size:36px;font-family: "Verdana";}blockquote{margin:0px;}.h1{text-align:center;font-size:48px;margin-top:70px;margin-bottom:20px;padding-top:40px}.h3{margin-top:40px;font-size:24px;text-align:center;}p:nth-of-type(1),p:nth-of-type(2),p:nth-of-type(3){display:none;}</style><p class="h1">' + self.story.getAllMetadata()['title'] + '</p><p class="h3">' + self.story.getAllMetadata()['author'] + '</p><p class="h3">' + self.story.getAllMetadata()['description'] + '</h3>'
        html = header + storyHTML

        with open("my.html","w") as f:
            f.write(html)

        pisa.showLogging()
        pisa.CreatePDF(StringIO.StringIO(html), out)

    def wraplines(self, text):
        
        if not self.wrap_width:
            return text
        
        result=''
        for para in text.split("\n"):
            first=True
            for line in wrap(para, self.wrap_width):
                if first:
                    first=False
                else:
                    result += u"\n"
                result += line
            result += u"\n"
        return result 

    ## The appengine will return unix line endings.
    def lineends(self, txt):
        txt = txt.replace('\r','')
        if self.getConfig("windows_eol"):
            txt = txt.replace('\n',u'\r\n')
        return txt
                       
