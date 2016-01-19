import requests
import sys

def print_response(text):
    r = requests.post('http://localhost:8080/webhook', json={
                                                             "update_id": "1",
                                                             "message" : {
                                                                             "message_id" : "-1",
                                                                             "date": "",
                                                                             "text" : text,
                                                                             "from" : "test",
                                                                             "chat" : {"id":1}
                                                                         }
                                                            })

def print_inline(text):
    r = requests.post('http://localhost:8080/webhook', json={
    u'inline_query': {u'query': text, u'from': {u'username': u'zeteref', u'first_name': u'Zet', u'last_name': u'Eref', u'id': 104050882}, u'id': '-1', u'offset': u''}, u'update_id': "-1"
    })


    print '---'
    print r.text
    print '---'

def main():
    print_inline('fire')
    #print_response(' '.join(sys.argv[1:]))
    #print_response('/find spider %s' % sys.argv[1])
    #print_response('/movie the host 2013')
    #print_response('/karta psy')
    #print_response('/card alarm')
    #print_response('/c szukamy #alarm-o- czy #deathwing?')
    #print_response('bot test')
    #print_response('/stat c:5 a:5')


if __name__ == '__main__':
    main()

