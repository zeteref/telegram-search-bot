import StringIO
import json
import logging
import random
import urllib
import urllib2

from pyquery import PyQuery as pq

# for sending images
from PIL import Image

# standard app engine imports

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

f = open('secret.json')
s = json.loads(f.read())
f.close()

TOKEN = s['TOKEN']

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def parse_stats(text):
    cost = attack = health = None
    for stat in text.split():
        if parse_stat('c', stat):
            cost = parse_stat('c', stat)
        if parse_stat('a', stat):
            attack = parse_stat('a', stat)
        if parse_stat('h', stat):
            health = parse_stat('h', stat)

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


def parse_stat(char, stat):
    if stat.startswith(char) and ':' in stat:
        return stat.split(':')[1]

def parse_command(text):
    if not text.startswith('/'): return

    tmp = text[1:].split()
    return tmp[0] + "_command", ' '.join(tmp[1:])

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
        try:
            urlfetch.set_default_fetch_deadline(60)
            body = json.loads(self.request.body)
            logging.info('request body:')
            logging.info(body)
            self.response.write(json.dumps(body))

            update_id = body['update_id']
            message = body['message']
            self.message_id = message.get('message_id')
            date = message.get('date')
            text = message.get('text')
            fr = message.get('from')
            chat = message['chat']
            self.chat_id = chat['id']

            command, params = parse_command(text)

            if not command: return
            if not hasattr(self, command): return

            func = getattr(self, command)
            func(params)
        except:
            logging.exception('Exception was thrown')

    def card_command(self, card_name):
        try:
            url = get_card_url(card_name)
            self.reply(url)
        except:
            self.reply('unable to find image for card %s' % card_name)
            logging.exception("Exception was thrown")

    def stat_command(self, params):
        try:
            cost, attack, health = parse_stats(params)
            url = "http://www.hearthhead.com/cards=?filter=stat-cost-min=%s;stat-cost-max=%s;stat-attack-min=%s;stat-attack-max=%s;stat-health-min=%s;stat-health-max=%s"
            self.reply(url % (cost, cost, attack, attack, health, health))
        except:
            self.reply('unable to find cards for %s' % params)
            logging.exception('Exception was thrown')

    def karta_command(self, card_name):
        try:
            url = get_card_url(card_name, 'plPL')
            self.reply(url)
        except:
            self.reply('unable to find image for card %s' % card_name)
            logging.exception("Exception was thrown")

    def movie_command(self, params):
        try:
            for url in get_movie_ulrs(params)[:3]:
                self.reply('http://www.imdb.com%s' % url, preview='false')
        except:
            self.reply('Unable to find movie for %s' % params)
            logging.exception('Exception was thrown')

    def desc_command(self, params):
        try:
            url = 'http://www.hearthpwn.com/cards?filter-name=%s&filter-include-card-text=y&filter-premium=1' % urllib.quote_plus(params)
            page = pq(url=url, opener=lambda url, **kw: urllib.urlopen(url).read())
            cells = page('.visual-details-cell h3 a')
            ret = ["%s\nhttp://www.hearthpwn.com%s" % (x.text, x.get('href')) for x in cells]
            if len(ret) == 1:
                self.card_command(params)
                return
            self.reply('\n'.join(ret[:5]))
        except:
            self.reply('Unable to find cards for %s' % params)
            logging.exception('Exception was thrown')

    def reply(self, msg=None, img=None, preview='true'):
        if self.message_id == "-1": # for testing
            self.response.write("\n")
            self.response.write(msg)
        elif msg:
            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                'chat_id': str(self.chat_id),
                'text': msg.encode('utf-8'),
                'enable_web_page_preview': preview,
                'reply_to_message_id': str(self.message_id),
            })).read()

            logging.info(resp)

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
