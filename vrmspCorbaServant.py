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

import uuid, httplib, datetime
import thread

import VRM_SP__POA
import VRM_SP
import VRM
import _GlobalIDL as glob

import vrmsp_dm
from geysers_psnc_utils.wsgiservice.xmlserializer import dumps, xml2obj

import logging
logger = logging.getLogger(__name__)

class vrmsp_commands (VRM_SP__POA.VR_Commands):
    
    def __init__(self, dataModels):
        '''contructor method required for access to common data model'''
        self.dataModels = dataModels
        self.defaultTimeout = 10
  
    @vrmsp_dm.corba_exception_handler
    def upgradeLink(self, handle, localNode, remoteNode, localLinkId, remoteLinkId, lblId):
        """
        From IDL:
        void upgradeLink(inout Types::uint32           handle,
                        in    gmplsTypes::nodeId       localNode,
                        in    gmplsTypes::nodeId       remoteNode,
                        in    gmplsTypes::TELinkId     localLinkId,
                        in    gmplsTypes::TELinkId     remoteLinkId,
                        in    gmplsTypes::labelId      lblId,
                        out   Types::uint32            timeout)
        """
        logger.info('\n\n\t\t\t\t\t\t\t\t\tVR_Commands.upgradeLink() called\n')
        logger.info('--> Handle %d', handle)
        logger.info('--> localNode %s, remoteNode %s', str(localNode), str(remoteNode))
        logger.info('--> localLinkId %s, remoteLinkId %s', str(localLinkId), str(remoteLinkId))
        logger.info('--> lblId %s', str(lblId))
        thread.start_new_thread(makeUpgrade, (self.dataModels, localNode, remoteNode, localLinkId, remoteLinkId, lblId, handle))
        return handle, 10 # handle, timeout

def makeUpgrade(dataModels, localNode, remoteNode, localLinkId, remoteLinkId, lblId, handle):
    try:
        #local_nbpr  = vrmsp_dm.getNodeBoardPortResource(dataModels, localNode, localLinkId, lblId)
        #remote_nbpr = vrmsp_dm.getNodeBoardPortResource(dataModels, remoteNode, remoteLinkId, lblId)
        local_nbpr  = {"nodeId":3, "boardId":2, "portId":8, "resourceId":39}
        remote_nbpr = {"nodeId":2, "boardId":2, "portId":13, "resourceId":39}
        logger.debug("Local is %s", local_nbpr)
        logger.debug("Remote is %s", remote_nbpr)
        response = vrmsp_dm.sendAddLambdaRequest(dataModels, local_nbpr, remote_nbpr)
        logger.debug("Replanning response is %s, %s", response.status, str(response))
        result = True if response.status is httplib.OK else False
        vrmsp_dm.generateNotification(dataModels['clients']['vrmapNotifications'], handle, result)
    except:
        import traceback
        logger.error(traceback.format_exc())


class vrmsp_conf (VRM_SP__POA.Config):
    def __init__(self, dataModels):
        '''contructor method required for access to common data model'''
        self.dataModels = dataModels

    @vrmsp_dm.corba_exception_handler
    def init(self, max_timeout):
        logger.info('\n\n\t\t\t\t\t\t\t\tConfig.init() called\n')
        logger.info('--> max_timeout %d', max_timeout)
        import thread
        thread.start_new_thread(vrmsp_dm.gatherAllCtrlIDs, (self.dataModels,))
        return max_timeout
