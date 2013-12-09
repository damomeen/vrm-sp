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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USASA

import uuid, httplib, sys, os, thread

sys.path.append(os.getcwd()+"/../") # add directory with corba stub to python modules path
import VRM_AP__POA as VRM_AP
import VRM_AP as VRM
import _GlobalIDL as glob
del sys.path[-1]

from geysers_psnc_utils.corbaUtils import CorbaServant, corbaClient

import logging

logging.basicConfig(filename = "vrmap-stub.log", level = logging.DEBUG, 
                    format = "%(levelname)s - %(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger('vrmap-stub')


class vrm_presence (VRM_AP.Presence):
    
    def __init__(self, dataModel):
        pass
     
    def register(self, spName, maxTimeout, spConfigRef, spCommandsRef):
        print 'Presence.register() called'
        print '--> spName %s, maxTimeout %d' % (spName, maxTimeout)
        print '--> ConfigRef', spConfigRef
        print '--> spCommandsRef', spCommandsRef
        thread.start_new_thread(call_init, (spConfigRef,))

    def unregister(self, spName):
        print 'Presence.unregister() called'
        print '--> spName', spName

def call_init(spConfigRef):
    try:
        spConfigRef.init(10)
    except:
        import traceback
        traceback.print_exc()
  
class vrm_notif (VRM_AP.Notifications):

    def __init__(self, dataModel):
        pass

    def vrResult(self, handle, result, error):
        print 'Notification.vrResult() called', handle, result, error


if __name__ == '__main__':
    # processed when module is started as a standlone application
    for servant in [vrm_presence, vrm_notif]:
        server = CorbaServant(servant, None, '/tmp') #'/opt/vrm/var/gmpls')
        server.start()

