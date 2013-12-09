from threading import Thread
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import pprint, copy
import logging
logger = logging.getLogger(__name__)

from vrmsp_dm import sendAddLambdaRequest, sendRemoveLambdaRequest

data_models = None
global_clients = None

#----------------------------------------------

class ReplanningHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        logger.info('incoming HTTP GET request %s', self.path)
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            path = self.path.split('/')
            if len(path) < 10:
                 self.wfile.write('Incorrent argument number: %d - should be 9 arguments' % len(path))
            #local_nbpr  = {"nodeId":3, "boardId":2, "portId":8, "resourceId":39}
            #remote_nbpr = {"nodeId":2, "boardId":2, "portId":13, "resourceId":39}
            local_nbpr  = {"nodeId":path[2], "boardId":path[3], "portId":path[4], "resourceId":path[5]}
            remote_nbpr = {"nodeId":path[6], "boardId":path[7], "portId":path[8], "resourceId":path[9]}
            
            if path[1] == 'remove-lambda':
                ret = sendRemoveLambdaRequest(data_models, local_nbpr, remote_nbpr)
            elif path[1] == 'add-lambda':
                ret = sendAddLambdaRequest(data_models, local_nbpr, remote_nbpr)

            self.wfile.write('Requesting of lambda modifcation, local %s.%s.%s.%s and remote %s.%s.%s.%s\n' % tuple(path[2:]))
            logger.info('Result is HTTP code %s' % str(ret.status))
            self.wfile.write('Result is HTTP code %s' % str(ret.status))
        except:
            import traceback
            logger.error(traceback.format_exc())

#===============================================

class ReplanningServer(Thread):  
    def __init__(self, dataModels, config):
        '''contructor method required for access to common data model'''
        Thread.__init__(self)        
        global data_models        
        data_models = dataModels
        global global_clients
        global_clients = dataModels['clients']
        self.config = config
        logger.debug('DataModels are %s', str(data_models))
        
    def run(self):
        """Called when server is starting"""
        server = HTTPServer(('', self.config['port']), ReplanningHandler)
        logger.info('Http server started on port %s', self.config['port'])
        server.serve_forever()
