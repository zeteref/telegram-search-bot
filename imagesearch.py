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
    request = urllib2.Request(url, None, {'Referer': 'testing'})
    request.add_header('Cookie', 'SRCHHPGUSR=CW=1587&CH=371&DPR=1&ADLT=OFF')

    response = urllib2.urlopen(url)
    cookie = response.info()['set-cookie']
    cookie += ', SRCHHPGUSR=CW=1587&CH=371&DPR=1&ADLT=OFF; domain=.bing.com; path=/; expires=Sat, 16-Dec-2017 09:49:05 GMT'

    print cookie

    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
    req.add_header('Cookie',cookie)

    page = urllib2.urlopen(req)
    xhtml = page.read()

    page = pq(xhtml).xhtml_to_html()

    for x in page('.thumb'): 
        print x.attrib['href']

def main():
    fetch_image('cosplay')

if __name__ == '__main__':
    main()
