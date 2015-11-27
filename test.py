import requests

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


    print r.text

def main():
    #print_response('/card death')
    #print_response('/movie the host 2013')
    #print_response('/karta psy')
    print_response('/card spider')
    print_response('bot test')
    #print_response('/stat c:5 a:5')


if __name__ == '__main__':
    main()

