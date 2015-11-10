import StringIO
import json
import logging
import random
import urllib
import urllib2

from pyquery import PyQuery as pq

# for sending images
from PIL import Image
import multipart

# standard app engine imports
try:
    from google.appengine.api import urlfetch
    from google.appengine.ext import ndb
    import webapp2
except:
    pass

TOKEN = '139293654:AAExsR0S-0ezGxJwPLgqO4cKld_JDA9tQBk'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False


# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            logging.info('no text')
            return

        def reply(msg=None, img=None, preview='true'):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'enable_web_page_preview': preview,
                    'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        def parse_stats(text):
            cost = attack = health = None
            for stat in text.split():
                if parse_stat('c', stat):
                    cost = parse_stat('c', stat)
                if parse_stat('a', stat):
                    attack = parse_stat('a', stat)
                if parse_stat('h', stat):
                    health = parse_stat('h', stat)

            print cost, attack, health
            return cost, attack, health

        def get_card_url(card_name, locale='enUS'):

            url = "https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/%s?locale=%s" % (urllib.quote(card_name), locale)
            req = urllib2.Request(url)
            req.add_header('X-Mashape-Key','LvOkkIwnJgmshtqGCASAel2whpIFp1xPQkijsnvgf6AWDixiRh')
            resp = urllib2.urlopen(req)

            content = resp.read()

            for tmp in json.loads(content):
                if 'img' in tmp and 'collectible' in tmp:
                    if 'flavor' in tmp:
                        return '%s\n\n%s' % (tmp['flavor'], tmp['img'])
                    else:
                        return tmp['img']

        def get_movie_ulrs(name):
            url = 'http://www.imdb.com/find?q=%s&s=tt&ref_=fn_tt_pop' % urllib.quote_plus(name)
            page = pq(url=url, opener=lambda url, **kw: urllib.urlopen(url).read())
            return [x.get('href') for x in page('td[class="result_text"] a')]


        known = False
        commands = [
                '/card ',
                '/karta ',
                '/desc ',
                '/stat ',
                '/opis ',
                '/movie'
        ]

        for x in commands:
            if text.startswith(x):
                known = True
                break
            
        if known:
            if text.startswith('/stat '):
                cost, attack, health = parse_stats(text)
                url = "http://www.hearthhead.com/cards=?filter=stat-cost-min=%s;stat-cost-max=%s;stat-attack-min=%s;stat-attack-max=%s;stat-health-min=%s;stat-health-max=%s"
                reply(url % (cost, cost, attack, attack, health, health))
            elif text.startswith('/card '):
                card_name = text[6:]
                try:
                    url = get_card_url(card_name)
                    reply(url)
                except:
                    reply('unable to find image for card %s' % card_name)
                    logging.exception("Exception was thrown")
            elif text.startswith('/karta '):
                card_name = text[7:]
                try:
                    url = get_card_url(card_name, 'plPL')
                    reply(url)
                except:
                    reply('unable to find image for card %s' % card_name)
                    logging.exception("Exception was thrown")
            elif text.startswith('/desc '):
                reply('http://www.hearthhead.com/cards=?filter=na=%s;ex=on' % urllib.quote_plus(text[6:]))
            elif text.startswith('/opis '):
                reply('http://www.hearthhead.com/cards=?filter=na=%s;ex=on' % urllib.quote_plus(text[6:]))
            elif text.startswith('/movie '):
                query = text[7:]
                for url in get_movie_ulrs(query)[:3]:
                    reply('http://www.imdb.com%s' % url, preview='false')
            else:
                reply('What command?')

def parse_stat(char, stat):
    if stat.startswith(char) and ':' in stat:
        return stat.split(':')[1]

# $('a[href^="/card"] img')

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
