import sys, os, time
sys.path.append(os.getcwd()+"/../") # add directory with corba stub to python modules path
#import VRM
import VRM_SP
import _GlobalIDL as glob
from vrmsp_dm import atoi
del sys.path[-1]

from geysers_psnc_utils.corbaUtils import corbaClient as corbaClient

vrmspCommandsRef = corbaClient(VRM_SP.VR_Commands, iorFile='/tmp/vrmsp_commands.ior')

handle       = 0   #Types::uint32
localNode    = atoi("192.168.40.4")   #gmplsTypes::nodeId
remoteNode   = atoi("192.168.40.4")   #gmplsTypes::nodeId
localLinkId  = glob.gmplsTypes.linkId(ipv4 = atoi("3.4.1.2"))   #gmplsTypes::TELinkId
remoteLinkId = glob.gmplsTypes.linkId(ipv4 = atoi("3.4.1.2"))   #gmplsTypes::TELinkId
lblId        = glob.gmplsTypes.labelId(label32 = 1)   #gmplsTypes::labelId2

print "upgradeLink result:", vrmspCommandsRef.upgradeLink(handle, localNode, remoteNode, localLinkId, remoteLinkId, lblId)

