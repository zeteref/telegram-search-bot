import requests

text = "/card horse"

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
