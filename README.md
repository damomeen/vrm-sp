vrm-sp 
=======

Module description
--------------------
The VRM-SP (VI-N Re-planning Manager -Specific Adaptor) is the component that allows the translation between the generalized re-planning actions decided at the VRM level 
and the RESTful requests to the LICL over the MLI. The interaction between the VRM and the VRM-SP is managed through a CORBA interface, where 
both the components implements the servant and client roles to allow requests and asynchronous notifications. The prototype is implemented from scratch in Python v2.6 language.


Files in the module
--------------------
* vrmsp_main.py
    - main file of the module
* vrmsp.conf.sample
    - sample configuration for the module
* http_server.py
    - HTTP REST implementation of MLI interface towards LICL
* tnrcspCorbaServant.py
    - corba interface servant towards vrm-ap
    - require omniorbpy (requires http://omniorb.sourceforge.net/)
* vrmsp_dm.py
    - internal methods of the module
* configure
    - creates python Corba servant stubs and a configuration file
    
* idls/*
    - IDL files used to interact with VRM-AP
    
* testing/corbaInterfaceTest.py
    - simple client generating Corba requests towards vrmsp
    - require omniorb (requires http://omniorb.sourceforge.net/)
* testing/restInterfaceMLI.py
    - HTTP REST MLI implementation
* testing/vrmap-stup.py
    - simulator of VRM-AP module


Most important requirements
------------------------------
1) Python libraries:
 - python-webob
 - python-decorator
 
2) Supporting library 'geysers_psnc_utils' from GEYSERS repository already installed


Basic installation
------------------
1) Please use:
  ./configure
  which is compiling python corba stub modules and create config file for 'vrmsp' module
  
2) Edit module configuration in vrmsp.conf file (Follow 'VRM-SP module configuration').


Advance installation
---------------------
1) In order to use SSL connection please use:
  ./ssl/create_ssl_certificate.sh
 which is creating SSL certificate and private key.
  

VRM-SP module configuration
-------------------------------
For VRM-SP all configuration is related to communication interfaces used by the module.
Commenting or deleting some part of configuration means that part of VRM-SP functinality will be disabled.
The explanation of configuration parameters is presented in form of comments ('#') within a configuration file.

The content of 'vrmsp.conf' is the following:

<pre>
INTERFACES = {
    'clients':
    {
        'rest-MLI':
        {
            'address':'localhost',
            'port': 8011,
            'ssl': False,
            'timeout': 10,
            'vi_id': '1',
        },
        'vrmapPresence':
        {
            'iorName': '/opt/vrm/var/gmpls/vrm_presence.ior',
        },
        'vrmapNotifications':
        {
            'iorName': '/opt/vrm/var/gmpls/vrm_notif.ior',
        },
        'gmplsCtrlInfo':
        {
            'IPs': ['150.254.160.135', '150.254.160.136', '150.254.160.137', '150.254.160.138'],
            'port': 7010,
        },
        #'AaiAuthentication':
        #{
        #    'iorName': '/tmp/AaiServer.ior',
        #    'user': 'Canh',
        #    'passwd': '123456',
        #},
    },
}
</pre>

Basic usage
-------------
  python vrmsp_main.py start
  python vrmsp_main.py stop
  python vrmsp_main.py restop
  python vrmsp_main.py --help

For basic usage files:
 - vrmsp.log and vrmsp.conf are located in vrmsp module directory
 - pid files and ior files are stored in '/tmp


Advance usage example
-------------------------
Directory location of pidfile, logfile, iorfiles, configfile can be declared by attributes:

  python vrmsp_main.py start --iorDir=/tmp --confDir=./ --logDir=/tmp --pidDir=/tmp
  python vrmsp_main.py stop --iorDir=/tmp --confDir=./ --logDir=/tmp --pidDir=/tmp
   
   
Additional info
---------------
Implementation created in FP7-Geysers project.
