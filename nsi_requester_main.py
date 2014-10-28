
import sys, os, logging, time
from optparse import OptionParser
from threading import Lock
import json
import cherrypy
from daemon import Daemon
     
from rest_api import  NSI_rest_server
  
##############################################

MODULE_NAME = 'nsi-rest'
__version__ = '0.1'

##############################################

class ModuleDaemon(Daemon):
    def __init__(self, moduleName, options):
        self.moduleName=moduleName
        self.options = options
        self.logger = logging.getLogger(self.__class__.__name__)
        pidFile = "%s/%s.pid" % (self.options.pidDir, self.moduleName)
        self.initializeDataModel()
        Daemon.__init__(self, pidFile)

    #---------------------
    def initializeDataModel(self):
        self.dataModels = {
            'data':{},
            'lock':Lock(),
            'clients':{},
        }     
        with file(MODULE_NAME + ".conf", 'r') as f:
            data = f.read()
            logger.debug("Config is %s", data)
            self.config = json.loads(data)

    #---------------------
    def run(self):
        """
        Method called when starting the daemon. 
        """
        try:
            # starting interfaces threads
            server = NSI_rest_server(config = self.config)
            server.start()
        except:
            import traceback
            self.logger.error("Exception" + traceback.format_exc())

##############################################

if __name__ == "__main__":
    
    # optional command-line arguments processing
    usage="usage: %prog start|stop|restart [options]"
    parser = OptionParser(usage=usage, version="%prog " + __version__)
    parser.add_option("-p", "--pidDir", dest="pidDir", default='/tmp', help="directory for pid file")
    parser.add_option("-l", "--logDir", dest="logDir", default='.', help="directory for log file")
    #parser.add_option("-c", "--confDir", dest="confDir", default='.',    help="directory for config file")
    options, args = parser.parse_args()
    
    # I do a hack if configDir is default - './' could not point to local dir 
    #if options.confDir == '.':
    #    options.confDir = sys.path[0]

    if 'start' in args[0]:
        # clear log file
        try:
            os.remove("%s/%s.log" % (options.logDir, MODULE_NAME))
        except: 
            pass          

    # creation of logging infrastructure
    logging.basicConfig(filename = "%s/%s.log" % (options.logDir, MODULE_NAME),
                        level    = logging.DEBUG,
                        format   = "%(levelname)s - %(asctime)s - %(name)s - %(message)s")
    logger = logging.getLogger(MODULE_NAME)

    # starting module's daemon
    daemon = ModuleDaemon(MODULE_NAME, options)
    
    # mandatory command-line arguments processing
    if len(args) == 0:
        print usage
        sys.exit(2)
    if 'start' == args[0]:
        logger.info('starting the module')
        daemon.start()
    elif 'stop' == args[0]:
        logger.info('stopping the module')
        daemon.stop()
    elif 'restart' == args[0]:
        logger.info('restarting the module')
        daemon.restart()
    else:
        print "Unknown command"
        print usage
        sys.exit(2)
    sys.exit(0)

