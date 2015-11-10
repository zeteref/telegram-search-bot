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
    print_response('/card horse')
    print_response('/movie the host 2013')
    print_response('/karta psy')
    print_response('/desc freeze')
    print_response('/stat c:3 a:3 h:3')


if __name__ == '__main__':
    main()

