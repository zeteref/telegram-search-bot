import os
import sys
import time
import urllib2
import urllib
import simplejson
import cStringIO

from pyquery import PyQuery as pq

def fetch_image(searchTerm, safe=True):
    searchTerm = urllib.quote_plus(searchTerm)

    url = ('http://www.bing.com/images/search?q=%s' % searchTerm)

    opener = urllib2.build_opener()
    if not safe:
        opener.addheaders.append(('Cookie', 'SRCHHPGUSR=CW=1587&CH=371&DPR=1&ADLT=OFF'))

    page = opener.open(url)
    xhtml = page.read()
    page = pq(xhtml).xhtml_to_html()

    links = [x.attrib['href'] for x in page('.thumb')]
    print links

def main():
    fetch_image('kitty')

if __name__ == '__main__':
    main()
