import json
import httplib

request_config = {  'endpoint' : 'http://localhost:9090/nsicontest/ConnectionProvider',
                            'provider_nsa' : 'urn:ogf:network:psnc:2013:nsa',
                            'reply_to' : 'http://localhost:9090/nsicontest/ConnectionRequester',
                            'requester_nsa' : 'urn:ogf:network:psnc:2013:nsa',
                            'reservation_id' : 'grid1',
                            'description' : 'default reservation',
                            'start_time' : '60',
                            'end_time' : '120',
                            'version' : '0',
                            'service_type' : 'http://services.ogf.org/nsi/2013/07/descriptions/EVTS.A-GOLE',
                            'source_stp' : 'urn:ogf:network:psnc:2013:mx2.12',
                            'dest_stp' : 'urn:ogf:network:psnc:2013:mx1.18',
                            'ero' : '',
                            'capacity' : '100',
                            'bidirectional' : 'true',
                            'symmetric_path' : 'true',
}
                            
conn = httplib.HTTPConnection('150.254.185.235:8989')
conn.request(method  = 'POST',
                  url         = "/nsi/service", 
                  headers  = {"Content-Type": "application/json"},
                  body      = json.dumps(request_config)
)
                  
response = conn.getresponse()
print "Response received %s, %s" % (response.status, response.reason)

"""
Possible responses:
  * HTTP response code - 201  (Meaning: service is successfully reserved in NSI)
  * HTTP response code - 400  (Meaning: wrong Content-Type in the request)
  * HTTP response code - 500  (Meaning: service reservation is unsucessful)
"""