
import uuid, copy
import bottle
import thread
from threading import Thread
import httplib
import json
import time

import nsi_telnet_client

import logging
logger = logging.getLogger(__name__)

###################################################################

GLOBAL_CONFIG = {}

BASE_SCHEMA = '/nsi'
PORT = 8989

###################################################################

@bottle.post(BASE_SCHEMA+"/service")
def service_reserve():
    logger.info('\n\n\t\tService reservation request received\n')
    
    content_type = bottle.request.headers.get("Content-Type")
    if content_type != "application/json":
        logger.warning("Unexpected HTTP Content-Type: %s - should be application/json", content_type)
        bottle.abort("400", 'Content-Type should be application/json instead of %s', content_type)
        
    body = bottle.request.body.read()
    parameters = json.loads(body)
    parameters = _fill_missing_nsi_request(parameters)
    properties = _generate_nsi_request_properties(parameters)
    uid, status = nsi_telnet_client.reserve_service(properties)
    
    uid = uid.replace('urn:uuid:', 'urn-uuid-')
    if status == False:
        bottle.abort(500, 'Error during the service reseravation')
        
    bottle.response.headers['Location'] = BASE_SCHEMA + "/service/reserve/" + uid
    bottle.response.status = 201
    logger.debug("HTTP response 201 send, uid is %s", uid)
    
#@bottle.get(BASE_SCHEMA+"/service")
def service_reserve_simple():
    logger.info('\n\n\t\tService reservation request received\n')
    uid, status = nsi_telnet_client.reserve_service("")
    
    uid = uid.replace('urn:uuid:', 'urn-uuid-')
    if status == False:
        bottle.abort(500, 'Error during the service reservation')
        
    bottle.response.headers['Location'] = BASE_SCHEMA + "/service/reserve/" + uid
    bottle.response.status = 201
    logger.debug("HTTP response 201 send, uid is %s", uid)
    return "Service reservation accepted"
    
@bottle.delete(BASE_SCHEMA+"/service/<uid>")
def service_unreserve(uid):
    logger.info('\n\n\t\tService removal request received for %s\n', uid)
    uid = uid.replace('urn-uuid-', 'urn:uuid:')
    nsi_telnet_client.delete_service(uid)

@bottle.get(BASE_SCHEMA+"/register/<name>")
def register(name):
    logger.info("\n\n\t\tRegistration from %s island received\n", name)
    if name not in GLOBAL_CONFIG["nsi-peers"]:
        bottle.abort("404", 'Not found')
        logger.error("Island %s is not configured", name)
    thread.start_new_thread(_get_topology, (name,))
    return "Registration accepted"
    
@bottle.get(BASE_SCHEMA+"/topology")
def topology():
    logger.info('\n\n\t\tTopology request received\n')
    bottle.response.headers['Content-Type'] =  'application/xml'
    return nsi_telnet_client.get_nrm_topo()

##################### UTIL FUNCTIONS ########################################

def _fill_missing_nsi_request(conf):
    default_conf = {  'endpoint' : 'http://localhost:9090/nsicontest/ConnectionProvider',
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
    default_conf.update(conf)
    return default_conf
    
    
def _generate_nsi_request_properties(conf):
    properties = ""
    for item in conf.items():
        properties += "%s = %s\n" % item
    return properties

def _register_all():
    time.sleep(5)
    try:
        logger.debug("Starting registration process for peers: %s", GLOBAL_CONFIG["nsi-peers"])
        for name in GLOBAL_CONFIG["nsi-peers"]:
            thread.start_new_thread(_send_register, (name,))
    except:
        logged.exception("Register all failed")

def _send_register(name):
    logger.debug('Sending registration to %s island', name)
    if name not in GLOBAL_CONFIG["nsi-peers"]:
        logger.error("Island %s is not configured", name)
        return 
    try:
        ip = GLOBAL_CONFIG["nsi-peers"][name]
        endpoint = '%s:%s' % (ip, PORT)
        conn = httplib.HTTPConnection(endpoint, timeout=10)
        uri = BASE_SCHEMA + '/register/%s' % GLOBAL_CONFIG["nsi-name"]
        logger.debug("Sending HTTP GET %s%s", endpoint, uri)
        conn.request('GET', uri)
        response = conn.getresponse()
        if response.status != 200:
            logger.warning("Unsuccesful response received %s, %s", response.status, response.reason)
            return
        logger.debug("Registration to %s successful", name)
        thread.start_new_thread(_get_topology, (name))
    except:
        logged.exception("Sending registration failed")
    
def _get_topology(name):
    logger.debug('Sending topology request to %s island', name)
    if name not in GLOBAL_CONFIG["nsi-peers"]:
        logger.error("Island %s is not configured", name)
        return
    try:
        ip = GLOBAL_CONFIG["nsi-peers"][name]
        endpoint = '%s:%s' % (ip, PORT)
        conn = httplib.HTTPConnection(endpoint, timeout=10)
        uri = BASE_SCHEMA + '/topology'
        logger.debug("Sending HTTP GET %s%s", endpoint, uri)
        conn.request('GET', uri)
        response = conn.getresponse()
        if response.status != 200:
            logger.warning("Unsuccesful response received %s, %s", response.status, response.reason)
            return
        data = response.read()
        nsi_telnet_client.add_topo(name, data)
    except:
        logged.exception("Get toplogy from % island failed", name)

#===============================================

class NSI_rest_server(Thread):  
    def __init__(self, config):
        Thread.__init__(self)     
        global GLOBAL_CONFIG       
        GLOBAL_CONFIG = config
        nsi_telnet_client.get_nrm_topo()
        thread.start_new_thread(_register_all, ())
        
    def run(self):
        """Called when server is starting"""
        logger.info('Running CherryPy HTTP server on port %s', PORT)
        bottle.run(host='0.0.0.0', port=PORT, debug=True, server='cherrypy')


if __name__ == '__main__':
    # processed when module is started as a standlone application
    server = NSI_rest_server(config = None)
    server.start()

