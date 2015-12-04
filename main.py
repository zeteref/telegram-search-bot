import StringIO
import json
import logging
import random
import urllib
import urllib2
import cStringIO

from pyquery import PyQuery as pq

# for sending images
from PIL import Image

# standard app engine imports

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

import telegram

f = open('secret.json')
s = json.loads(f.read())
f.close()

TOKEN = s['TOKEN']

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

bot = telegram.Bot(token=TOKEN)


class CardNotFoundError(Exception): pass

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

    def format_first(self, first):
        VALID = ['type', 'rarity', 'set', 'race', 'class']

        url = "http://www.hearthpwn.com%s" % first('.col-name a').attr('href')
        page = pq(url=url, opener=lambda url, **kw: urllib.urlopen(url).read())

        tmp = [pq(x).text() for x in page('.infobox ul li')]
        if not tmp: raise CardNotFoundError()

        attrs = []
        for attr in tmp:
            a = attr.split(':')
            if a[0].lower() not in VALID: continue
            attrs.append('*%s*: %s' % (a[0], a[1]))

            if a[0].lower() == 'type':
                attrs.append('*Cost*:  %s' %first('.col-cost').text())
                if a[1].lower().strip() in ['minion', 'weapon']:
                    attrs.append('*Attack*:  %s' %first('.col-attack').text())
                    attrs.append('*Health*:  %s' %first('.col-health').text())

        if page('.card-info p').text().strip():
            desc = "_%s_" % page('.card-info p').text()
        else:
            desc = ""
 
        return """[%s](%s)
                
%s
                
%s
                
%s
""" %     (
                first('.col-name').text(),
                url,
                "\n".join(attrs),
                desc,
                page('img.hscard-static').attr('src')
            )

    def stat_command(self, params):
        try:
            cost, attack, health = parse_stats(params)
            url = "http://www.hearthpwn.com/cards?display=1&filter-premium=1&filter-attack-val=%s&filter-attack-op=3&filter-cost-val=%s&filter-cost-op=3&filter-health-val=%s&filter-health-op=3" % (attack, cost, health)
            page = pq(url=url, opener=lambda url, **kw: urllib.urlopen(url).read())
            self.show_results(page)
        except:
            self.reply('unable to find cards for %s' % params)
            logging.exception('Exception was thrown')

    def karta_command(self, card_name):
        try:
            url = get_card_url(card_name, 'plPL')
            bot.sendMessage(chat_id=self.chat_id, text=url)
        except:
            self.reply('unable to find image for card %s' % card_name)
            logging.exception("Exception was thrown")

    def card_command(self, params):
        try:
            url = 'http://www.hearthpwn.com/cards?display=1&filter-name=%s&filter-include-card-text=y&filter-premium=1' % urllib.quote_plus(params)
            page = pq(url=url, opener=lambda url, **kw: urllib.urlopen(url).read())
            self.show_results(page)
        except:
            self.reply('Unable to find cards for %s' % params)
            logging.exception('Exception was thrown')

    def show_results(self, page):
        cells = page('.visual-details-cell h3 a')
        trs = [pq(x) for x in page('table.listing tr')[1:]]
        self.msg(self.format_first(trs[0]))

        msg = []
        for tr in trs[1:4]:
            msg.append("[%s](http://www.hearthpwn.com%s) Cost:%s Attack:%s Health:%s" % (tr('.col-name').text(),
                                                                                         tr('.col-name a').attr('href'),
                                                                                         tr('.col-cost').text(),
                                                                                         tr('.col-attack').text(),
                                                                                         tr('.col-health').text())
                )

            self.msg("\n".join(msg))


    def movie_command(self, params):
        try:
            for url in get_movie_ulrs(params)[:3]:
                self.reply('http://www.imdb.com%s' % url, preview='false')
        except:
            self.reply('Unable to find movie for %s' % params)
            logging.exception('Exception was thrown')

    def msg(self, msg=None, img=None, preview='true', reply=False):
        if self.message_id == "-1": # for testing
            self.response.write("\n")
            self.response.write(msg)
        elif msg:
            params = {
                'chat_id': str(self.chat_id),
                'text': msg.encode('utf-8'),
                'enable_web_page_preview': preview,
            }
            if reply:
                params['reply_to_message_id'] = str(self.message_id)

            bot.sendMessage(chat_id=self.chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=False)


    def photo(self, url):
        if self.message_id == "-1":
            self.response.write("\n")
            self.response.write("photo:%s" % url)
        else:
            #bot.sendPhoto(chat_id=self.chat_id, photo=url)
            #bot.sendPhoto(chat_id=self.chat_id, photo='https://telegram.org/img/t_logo.png')
            pass

    def reply(self, msg=None, img=None, preview='true'):
        self.msg(msg,img,preview, reply=True)

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
