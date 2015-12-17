import os
import sys
import time
import urllib2
import urllib
import simplejson
import cStringIO

from pyquery import PyQuery as pq

def fetch_image(searchTerm):
    searchTerm = searchTerm.replace(' ','%20')

    url = ('http://www.bing.com/images/search?q=naked+asian')
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'SRCHHPGUSR=CW=1587&CH=371&DPR=1&ADLT=OFF'))
    page = opener.open(url)
    xhtml = page.read()

    page = pq(xhtml).xhtml_to_html()

    for x in page('.thumb'): 
        print x.attrib['href']

def main():
    fetch_image('cosplay')

if __name__ == '__main__':
    main()
