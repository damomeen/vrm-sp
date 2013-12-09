#
# The Geysers project (work funded by European Commission).
#
# Copyright (C) 2012  Poznan Supercomputing and Network Center
# Authors:
#   Damian Parniewicz (PSNC) <damianp_at_man.poznan.pl>
# 
# This software is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import httplib
import struct
from functools import wraps
import pprint

import _GlobalIDL as glob
import CORBA
import VRM_SP
import VRM_AP
import VRM
import SecGateway
from geysers_psnc_utils.wsgiservice.xmlserializer import dumps, xml2obj
from geysers_psnc_utils.corbaUtils import corbaClient
from geysers_psnc_utils.restUtils import encode_multipart_mime

import logging
logger = logging.getLogger(__name__)


####################################
### Utils

def corba_exception_handler(f):
    'intercepting all corba calls and checking for exceptions'
    wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (VRM_SP.TELNotFound, VRM_SP.ParamError, VRM_SP.InternalError, VRM_SP.GenericError) as e:
            logger.error("Exception:" + str(e))
            raise
        except:
            import traceback
            logger.error("Exception" + traceback.format_exc())
            raise VRM_SP.InternalError("Exception in VRM-SP:" + str(traceback.format_exc()))
    return wrapper


def exception_handler(f):
    'intercepting all calls and checking for exceptions'
    wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            import traceback
            logger.error("Exception" + traceback.format_exc())
    return wrapper

####################################
### Rest messages

def send_rest_req(method, uri, body1, body2, config):
    configMLI = config.get('rest-MLI')
    configAAI = config.get('AaiAuthentication')
    authNToken = ''
    if configMLI == None:
        raise Exception('Could not find information about LICL-MLI server in configuration file')
    if configAAI:
        authNToken = authenticate(configAAI)

    remote_sock = '%(address)s:%(port)i' % configMLI
    if body1:
        body1 = dumps(body1)
    else:
        body1 = ''
    if body2:
        body2 = dumps(body2)
    else:
        body2 = ''
    logger.info('\n\n\n Sending HTTP %s request through MLI interface to %s%s\n', method, remote_sock, uri)
    try:
        if configMLI.get('ssl') is True:
            httpObj = httplib.HTTPSConnection
        else:
            httpObj = httplib.HTTPConnection
        conn = httpObj(remote_sock, timeout=configMLI.get('timeout'))
        content_type, body = encode_multipart_mime([('token', 'text/plain', authNToken), 
                                                    ('endpoint-one', 'application/xml', body1),
                                                    ('endpoint-two', 'application/xml', body2)], 
                                                   'boundary')
        conn.request(method, uri, body, {'Content-type':content_type, 'Accept':'application/xml'})
        logger.info('HTTP request send with body:\n %s \n', body)
    except:
        logger.error('Could not connect to LICL MLI interface server %s', str(configMLI))
        #raise VRM_SP.EqptLinkDown('Could not connect to LICL CCI interface server %s' % str(configMLI))
    res = conn.getresponse()
    xml = res.read()
    logger.info('Response received in CCI interface: HTTP %s %s with headers %s', res.status, res.reason, res.msg, str(res.getheaders()))
    if len(xml) > 0:
        #logger.info('Response XML is %s', xml)
        res.body = xml2obj(xml)
        logger.info('Response (obj) is:\n %s \n', pprint.pformat(res.body))
    else:
        res.body = {}
    return res 


BASE_SCHEMA = '/cxf/mli'


####################################
### Corba Presence client

def XsdPeriod2Seconds(periodXsd):
    import re
    regex = re.compile('PT(?:(?P<hours>\d+)S)?(?:(?P<minutes>\d+)S)?(?:(?P<seconds>\d+)S)')
    period = regex.match(periodXsd).groupdict(0)
    return ((int(period['hours'])*60)+int(period['minutes']))*60+int(period['seconds'])

def registerInVrmAP(dataModels, vrmspConfigServer, vrmspCommandsServer):
    maxConfigTime = 0
    logger.info("Registering to VRM-AP")
    presenceRef = corbaClient(VRM_AP.Presence, iorFile=dataModels['clients']['vrmapPresence']['iorName'])
    logger.debug('vrmspConfigServer %s', vrmspConfigServer)
    presenceRef.register('VRM-LICL-Adapter', maxConfigTime,
                         vrmspConfigServer, vrmspCommandsServer)
    logger.info("Registered in VRM-AP succesfully")

def unregisterInVrmAP(dataModels):
    logger.info("Unregistering from VRM-AP")
    presenceRef = corbaClient(VRM_AP.Presence, iorFile=dataModels['clients']['vrmapPresence']['iorName'])
    presenceRef.unregister('VRM-LICL-Adapter')
    logger.info("Unregistered in VRM-AP succesfully")

####################################
### Corba Resource configuration clients

def str2ieee754(floatString):
    packed = struct.pack('f', float(floatString))
    return struct.unpack('I', packed)[0]

def atoi(aa):
    "convert dotted IPv4 string into long int"
    aa = aa.split('.')
    ia = int(aa[0])<<24 | int(aa[1])<<16 | int(aa[2])<<8 | int(aa[3])
    logger.debug('convetint %s into %s', aa, str(ia))
    return ia

def itoa(ia):
    "convert long int to dotted IPv4 string"
    r = ia>>24, ((ia&0xFF0000)>>16), ((ia&0xFF00)>>8), ia&0xFF
    return '.'.join([str(s) for s in r])

def parse_corba_direction(direction):
    if direction == glob.gmplsTypes.XCDIR_BIDIRECTIONAL:
        return 'Bidirectional'
    elif direction == glob.gmplsTypes.XCDIR_UNIDIRECTIONAL:
        return 'Unidirectional'
    else:
        return 'XCDIR_BCAST'

def operStatus_str2corba(operStatus):
    if operStatus == 'up':
        return glob.gmplsTypes.OPERSTATE_UP
    else:
        return glob.gmplsTypes.OPERSTATE_DOWN

def adminStatus_str2corba(adminStatus):
    if adminStatus == 'enabled':
        return glob.gmplsTypes.ADMINSTATE_ENABLED
    else:
        return glob.gmplsTypes.ADMINSTATE_DISABLED

def switchCap_str2corba(switchCap):
    switchCaps = {
        'PSC':        glob.gmplsTypes.SWITCHINGCAP_PSC_1,
        'PSC-1':      glob.gmplsTypes.SWITCHINGCAP_PSC_1,
        'PSC-2':      glob.gmplsTypes.SWITCHINGCAP_PSC_2,
        'PSC-3':      glob.gmplsTypes.SWITCHINGCAP_PSC_3,
        'PSC-4':      glob.gmplsTypes.SWITCHINGCAP_PSC_4,
        'EVPL' :      glob.gmplsTypes.SWITCHINGCAP_EVPL,
        '802.1 PBBTE':glob.gmplsTypes.SWITCHINGCAP_8021_PBBTE,
        'L2SC':       glob.gmplsTypes.SWITCHINGCAP_L2SC,
        'TDM':        glob.gmplsTypes.SWITCHINGCAP_TDM,
        'DCSC':       glob.gmplsTypes.SWITCHINGCAP_DCSC,
        'OBSC':       glob.gmplsTypes.SWITCHINGCAP_OBSC,
        'LSC':        glob.gmplsTypes.SWITCHINGCAP_LSC,
        'FSC':        glob.gmplsTypes.SWITCHINGCAP_FSC,
    }
    return switchCaps.get(switchCap, glob.gmplsTypes.SWITCHINGCAP_UNKNOWN)

def encType_str2corba(encType):
    encTypes = {
         'Packet':           glob.gmplsTypes.ENCODINGTYPE_PACKET,
         'Ethernet':         glob.gmplsTypes.ENCODINGTYPE_ETHERNET,
         'ANSI ETSI PDH':    glob.gmplsTypes.ENCODINGTYPE_ANSI_ETSI_PDH,
         'Reserved 1':       glob.gmplsTypes.ENCODINGTYPE_RESERVED_1,
         'SDH/SONET':        glob.gmplsTypes.ENCODINGTYPE_SDH_SONET,
         'Reserved 2':       glob.gmplsTypes.ENCODINGTYPE_RESERVED_2,
         'Digital wrapper':  glob.gmplsTypes.ENCODINGTYPE_DIGITAL_WRAPPER,
         'Lambda':           glob.gmplsTypes.ENCODINGTYPE_LAMBDA,
         'Fiber':            glob.gmplsTypes.ENCODINGTYPE_FIBER,
         'Reserved 3':       glob.gmplsTypes.ENCODINGTYPE_RESERVED_3,
         'Fiber channel':    glob.gmplsTypes.ENCODINGTYPE_FIBERCHANNEL,
         'G.709 ODU':        glob.gmplsTypes.ENCODINGTYPE_G709_ODU,
         'G.709 OC':         glob.gmplsTypes.ENCODINGTYPE_G709_OC,
         'Line 8B10B':       glob.gmplsTypes.ENCODINGTYPE_LINE_8B10B,
         'TSON fixed':       glob.gmplsTypes.ENCODINGTYPE_TSON_FIXED,
    }
    return encTypes.get(encType, glob.gmplsTypes.ENCODINGTYPE_UNKNOWN)

def protectionType_str2corba(protectionType):
    protectionTypes = {
        'None':           glob.gmplsTypes.PROTTYPE_NONE,
        'Extra Traffic':  glob.gmplsTypes.PROTTYPE_EXTRA,
        'Unprotected':    glob.gmplsTypes.PROTTYPE_UNPROTECTED,
        'Shared':         glob.gmplsTypes.PROTTYPE_SHARED, 
        'Dedicated 1:1':  glob.gmplsTypes.PROTTYPE_DEDICATED_1TO1, 
        'Dedicated 1+1':  glob.gmplsTypes.PROTTYPE_DEDICATED_1PLUS1,
        'enhanced':       glob.gmplsTypes.PROTTYPE_ENHANCED,
    }
    return protectionTypes.get(protectionType, glob.gmplsTypes.PROTTYPE_NONE)

def usageStatus_str2corba(usageState):
    usageStatus = {
        'Undefined':     glob.gmplsTypes.LABELSTATE_FREE,
        'Free':          glob.gmplsTypes.LABELSTATE_FREE,
        'Booked':        glob.gmplsTypes.LABELSTATE_BOOKED,
        'XConnected':    glob.gmplsTypes.LABELSTATE_XCONNECTED,
        'Busy':          glob.gmplsTypes.LABELSTATE_BUSY,
    }
    return usageStatus.get(usageState, glob.gmplsTypes.LABELSTATE_BUSY)

def otaniLabel(grid, channelSpacing, channelID):
    'coding channel basing on otani-draft'
    def two_comp16(val):
        return struct.unpack('H', struct.pack('h', val))[0]
    if grid in ('1', '2'):
        firstByte = (int(grid)<<5) | (int(channelSpacing)<<1)
        value = firstByte<<24 | two_comp16(int(channelID))
    else:
        value = 0
    logger.debug("Otani label is %s (grid:%s, channelSpacing:%s, channelId:%s)", hex(value), grid, channelSpacing, channelID)
    return value

def label2channel(label):
    def two_comp16(val):
        return struct.unpack('h', struct.pack('H', val))[0]
    return two_comp16(label & 0xFFFF)


def portIdentifier(nodeId, boardId, portId):
    return (int(nodeId)<<26) + (int(boardId)<<16) + int(portId)
 
def boardPortResourceIdentifier(datalinkId, lblId):
    return {
            'boardId':    str((datalinkId & 0x03FF0000) >> 16),
            'portId':     str( datalinkId & 0x0000FFFF),
            'resourceId': str(label2channel(lblId.label32)),
            }

####################################
### Corba security

def authenticate(config):
    logger.info('Authenticate in AAI')
    try:
        aaiRef = corbaClient(SecGateway.AaiServer, iorFile=config['iorName'])
        authNtoken = aaiRef.authenticate(config['user'], config['passwd'])
        logger.debug('AAI authentication authNtoken is', authNtoken)
        return authNtoken
    except CORBA.TRANSIENT:          
        logger.error('Could not connect to AAI server %s', str(config))


###################################

def gatherAllCtrlIDs(dataModel):
    #/info/ctrl, /info/te-link/{id}
    import time
    t = 4.0
    while True:
        dataModel['data']['ctrlId'] = {}
        for ip in dataModel['clients']['gmplsCtrlInfo']['IPs']:
            address = '%s:%s' % (ip, dataModel['clients']['gmplsCtrlInfo']['port'])
            ctrlId = sendGetRequest(address, '/info/ctrl')
            if ctrlId is None:
                continue
            with dataModel['lock']:
                dataModel['data']['ctrlId'][ctrlId] = ip
        time.sleep(t)
        if t < 60*60*24: # query no less that every 24h
            t *= 2
        return

@corba_exception_handler
def getNodeBoardPortResource(dataModel, localNode, localLinkId, lblId):
    ip = dataModel['data']['ctrlId'].get(itoa(localNode))
    if ip is None:
        raise VRM_SP.GenericError("Local node %s not found" % itoa(localNode))
        return

    address = '%s:%s' % (ip, dataModel['clients']['gmplsCtrlInfo']['port'])
    datalink = sendGetRequest(address, "/info/te-link/%s" % itoa(localLinkId.ipv4))
    if datalink is None:
        raise VRM_SP.TELNotFound("Local link %s not found" % itoa(localLinkId.ipv4))
        return

    nbpr = boardPortResourceIdentifier(int(datalink), lblId)

    nodeId = sendGetRequest(address, "/info/node")
    nbpr['nodeId'] = nodeId
    return nbpr
    

def sendGetRequest(ip, uri):
    try:
        conn = httplib.HTTPConnection(ip)
        logger.debug('Sending query: %s%s', ip, uri)
        conn.request('GET', uri, '', {})
        response = conn.getresponse()
        data = response.read()
        data = xml2obj(data)
        logger.debug(" --> response is %s", data)
        if data['info'] == 'None': # response could be 'None' 
            return None
        return data['info']
    except:
        import traceback
        logger.error(traceback.format_exc())
        raise VRM_SP.GenericError("Could not query from %s" % ip)


def sendAddLambdaRequest(dataModel, source, target):
    logger.info('Adding lambda source=%s and destination=%s', source, target)
    uri = BASE_SCHEMA + '/mli/vi/%s/re-planning/modifyLink' % dataModel['clients']['rest-MLI']['vi_id']
    return send_rest_req("POST", uri, body1={'node':source}, body2={'node':target}, config=dataModel['clients'])

def sendRemoveLambdaRequest(dataModel, source, target):
    logger.info('Removing lambda source=%s and destination=%s', source, target)
    uri = BASE_SCHEMA + '/mli/vi/%s/re-planning/modifyLink' % dataModel['clients']['rest-MLI']['vi_id']
    return send_rest_req("PUT", uri, body1={'node':source}, body2={'node':target}, config=dataModel['clients'])


def generateNotification(config, handle, result=True):
    logger.debug('Generate notification towards VRM-AP')
    try:
        notifyRef = corbaClient(VRM_AP.Notifications, iorFile=config['iorName'])
        result = VRM.VR_RESULT_SUCCESS if result == True else VRM.VR_RESULT_FAILURE
        notifyRef.vrResult(handle, result, VRM.VR_ERROR_NONE)
    except CORBA.TRANSIENT:          
        logger.error('Could not connect to VRM-AP %s', str(config))
    
