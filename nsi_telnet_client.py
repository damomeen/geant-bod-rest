import socket

import logging
logger = logging.getLogger(__name__)

NSI = "/home/mininet/nsi-v3"
NSI_ETC = NSI + "/etc"
    
def reserve_service(properties):
    logger.debug("Calling NSI telnet reserve_service function")
    if properties != "":
        _generate_file(NSI_ETC + "/request.properties", properties)
    uid = _send_nsi_command('req rescomprov')
    logger.debug("uid is %s", uid)
    if "urn:uuid:" not in uid:
        logger.error("reservation failed %s", uid)
        return uid, False
    return uid, True
    
def delete_service(uid):
    logger.debug("Calling NSI telnet delete_service function with uid %s", uid)
    _send_nsi_command('req new')
    _send_nsi_command('req release %s' % uid)
    logger.debug("Reservation removed")
    
def get_nrm_topo():
    logger.debug("Calling NSI telnet get_nrm_topo function")
    response = _send_nsi_command('nrm topo')
    topo_name = response.replace("nrm topology exported as ", "").strip()
    logger.debug("Generated nrm topo is %s", topo_name)
    with file(NSI+"/%s.xml" % topo_name, 'r') as f:
        data = f.read()
        add_topo(topo_name, data)
        #logger.debug("NRM topo is: %s", data)
        return data
        
def add_topo(name, data):
    logger.debug("Calling NSI telnet add_topo function with name %s", name)
    filename = "%s/%s.xml" % (NSI_ETC, name)
    _generate_file(filename, data)
    _send_nsi_command('topo add %s' %filename)
  
  
######## UTIL FUNCTIONS #####################

def _send_nsi_command(command):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)
        s.connect(("localhost", 2200))
        logger.debug("NSI telnet connected")
        _read_until(s, "nsi>")
        logger.debug("Sending command: %s ", command)
        s.send(command+"\n")
        response = s.recv(4089)
        logger.debug(" --> Response received: %s", response)
        s.send("quit\n")
        return response
    except:
        logger.exception("Unsuccesful NSI telnet operation")
        return ""

def _read_until(sock, text):
    data = ""
    while True:
        data += sock.recv(4089)
        if text in data:
            print text,
            break
    return data
    
def _parse_connection_status(status):
    status = status.split(',')
    parsed_status = {}
    for s in status[1:]:
        name, value = s.split(":")
        parsed_status[name.strip()] = value.strip()
    return parsed_status
    
def _generate_file(location, content):
    try:
        f = file(location, "w")
        f.write(content)
        f.close
    except:
        logger.exception("File creation unsucessful")




if __name__ == "__main__":
    nsi_reserve_service({})
