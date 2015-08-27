#! /usr/bin/env python
#
# Python module example file
# Miguel A.L. Paraz <mparaz@mparaz.com>
#
# $Id: dd5b0b88243ea2919634d1ae519f5825f0560c93 $

"""
Meraki Params example
(('Acct-Session-Id', '"624874448299247292"'), ('Called-Station-Id', '"00-18-0A-F2-DE-20:Radius test"'), ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'), ('Framed-IP-Address', '172.31.3.83'), ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'), ('NAS-IP-Address', '108.161.147.120'), ('NAS-Port', '0'), ('NAS-Port-Id', '"Wireless-802.11"'), ('NAS-Port-Type', 'Wireless-802.11'), ('Service-Type', 'Login-User'), ('User-Name', '"hyellis@gmail.com"'), ('User-Password', '"12345"'), ('Attr-26', '0x000073e7010f446a756e676c65204851203032'))
"""

"""
Radtest Params example
(('User-Name', '"alwaysdeone@gmail.com"'), ('User-Password', '"12345"'), ('NAS-IP-Address', '192.168.8.103'), ('NAS-Port', '0'), ('Message-Authenticator', '0xbf2c016d5bc52c8fde08cd5c5a650e54'))
"""

import os
import sys
import subprocess

hostname = subprocess.check_output('hostname')[:-1] 

if hostname != "Oladayos-MacBook-Pro.local":
    sys.path.insert(1, "/Users/deone/src/billing/lib/python2.7/site-packages")
    sys.path.insert(1, "/Users/deone/src/billing/billing")
else:
    sys.path.insert(1, "/root/billing/lib/python2.7/site-packages")
    sys.path.insert(1, "/root/billing/billing")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")

import radiusd
import django

from django.contrib.auth.models import User

p = (('User-Name', '"alwaysdeone@gmail.com"'), ('User-Password', '"12345"'), ('NAS-IP-Address', '192.168.8.103'), ('NAS-Port', '0'), ('Message-Authenticator', '0xbf2c016d5bc52c8fde08cd5c5a650e54'))

def instantiate(p):
    print "*** instantiate ***"
    # print p

def authorize(p):
    print "*** authorize ***"
    # radiusd.radlog(radiusd.L_INFO, '*** radlog call in authorize ***')
    params = dict(p)
    username = params['User-Name'][1:-1]
    user = User.objects.get(username__exact=username)

    if user.is_active:
        return radiusd.RLM_MODULE_OK
    else:
        return radiusd.RLM_MODULE_REJECT

def authenticate(p):
    print "*** authenticate ***"
    print p
    return radiusd.RLM_MODULE_OK

def preacct(p):
    print "*** preacct ***"
    # print p
    return radiusd.RLM_MODULE_OK

def accounting(p):
    print "*** accounting ***"
    # radiusd.radlog(radiusd.L_INFO, '*** radlog call in accounting (0) ***')
    # print
    # print p
    return radiusd.RLM_MODULE_OK

def checksimul(p):
    print "*** checksimul ***"
    # print p
    return radiusd.RLM_MODULE_OK

def pre_proxy(p):
    print "*** pre_proxy ***"
    # print p
    return radiusd.RLM_MODULE_OK

def post_proxy(p):
    print "*** post_proxy ***"
    # print p
    return radiusd.RLM_MODULE_OK

def post_auth(p):
    print "*** post_auth ***"
    # print p
    return radiusd.RLM_MODULE_OK

def recv_coa(p):
    print "*** recv_coa ***"
    # print p
    return radiusd.RLM_MODULE_OK

def send_coa(p):
    print "*** send_coa ***"
    # print p
    return radiusd.RLM_MODULE_OK

def detach():
    print "*** goodbye from example.py ***"
    return radiusd.RLM_MODULE_OK

if __name__ ==  "__main__":
    authorize(p)
