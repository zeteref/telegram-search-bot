import json
import base64
import sys
from cards import db

def format_card_reply(card):
    VALID = ['type', 'cost', 'attack', 'health', 'rarity', 'set', 'race', 'class']

    attrs = []
    for attr in VALID:
        if attr not in card: continue
        attrs.append('*%s*: %s' % (attr.capitalize(), card[attr]))

    ret = "[%s](http://wow.zamimg.com/images/hearthstone/cards/enus/medium/%s.png)\n\n%s" % (card["name"], card["id"], "\n".join(attrs))
    if 'text' in card:
        ret += '\n\n_%s_' % card['text']

    return ret


def format_more_cards(cards):   
    cards = cards[:3]

    return "\n".join([ '[%s](http://wow.zamimg.com/images/hearthstone/cards/enus/medium/%s.png)' % (c['name'], c['id']) for c in cards ])


def matches(card, desc='', **kwds):
    if 'text' not in card: card['text'] = ''

    if desc:
        if desc not in card['name'].lower() and desc not in card['text'].lower(): return False

    for k, v in kwds.iteritems():
        if k in card and v.lower() not in str(card[k]).lower(): return False

    return True

def parse_args(args):
    if ':' in args[0]: desc=''
    else: desc = args[0]

    kwds = {}
    for x in args[1:]:
        if ':' in x:
            kv = x.split(':')
            kwds[kv[0]] = kv[1]

    
    return desc, kwds

def find_cards(desc='', **kwds):
    if 'a' in kwds: kwds['attack'] = kwds['a']
    if 'h' in kwds: kwds['health'] = kwds['h']
    if 'c' in kwds: kwds['cost'] = kwds['c']

    cards = json.loads(base64.b64decode(db))
    collectibles = [ x for x in reduce(lambda a,b: a+b, cards.values()) if 'collectible' in x and  x['collectible'] ]
    return [ x for x in collectibles if matches(x, desc.lower(), **kwds) ]


def main():
    desc, kwds = parse_args(sys.argv[1:])
    results = find_cards(desc, **kwds)
    print format_card_reply(results[0])
    print format_more_cards(results[1:])

if __name__ == '__main__':
    main()
