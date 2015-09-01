#! /usr/bin/env python
#
# Python module example file
# Miguel A.L. Paraz <mparaz@mparaz.com>
#
# $Id: dd5b0b88243ea2919634d1ae519f5825f0560c93 $

"""
(('Acct-Session-Id', '"624874448299458941"'), ('Called-Station-Id', '"00-18-0A-F2-DE-20:Radius test"'), ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'), ('Framed-IP-Address', '172.31.3.142'), ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'), ('NAS-IP-Address', '108.161.147.120'), ('NAS-Port', '0'), ('NAS-Port-Id', '"Wireless-802.11"'), ('NAS-Port-Type', 'Wireless-802.11'), ('Service-Type', 'Login-User'), ('User-Name', '"herbertellisspectradjungle@spectrawireless.com"'), ('User-Password', '"123456"'), ('Attr-26.29671.1', '0x446a756e676c65204851203032'))
00 %3A 18 %3A 0a %3A f2 %3A de %3A 20
48 %3A d2 %3A 24 %3A 43 %3A a6 %3A c1
"""

import os
import sys
import subprocess

import radiusd

p = (('User-Name', '"alwaysdeone@gmail.com"'), ('User-Password', '"12345"'), ('NAS-IP-Address', '192.168.8.102'), ('NAS-Port', '0'), ('Message-Authenticator', '0x7edbbcb48daa747ef293a0ba548c1f6c'))

def make_env():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")
    hostname = subprocess.check_output('hostname')[:-1]

    if not hostname.startswith('billing'):
        sys.path.insert(1, "/Users/deone/src/billing/lib/python2.7/site-packages")
        sys.path.insert(1, "/Users/deone/src/billing/billing")
    else:
        sys.path.insert(1, "/root/billing/lib/python2.7/site-packages")
        sys.path.insert(1, "/root/billing/billing")

def get_user(p):
    make_env()
    from django.contrib.auth.models import User
    params = dict(p)
    username = params['User-Name'][1:-1]
    return User.objects.get(username__exact=username)

def instantiate(p):
    print "*** instantiate ***"
    print p

def authorize(p):
    print "*** authorize ***"
    # print
    # radiusd.radlog(radiusd.L_INFO, '*** radlog call in authorize ***')
    # print
    # print p
    # return radiusd.RLM_MODULE_OK
    user = get_user(p)

    if user.is_active:
        return (radiusd.RLM_MODULE_OK,
            (('Session-Timeout', '120'),), (('Auth-Type', 'python'),))
    else:
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User De-activated'),), (('Auth-Type', 'python'),))

def preacct(p):
  print "*** preacct ***"
  print p
  return radiusd.RLM_MODULE_OK

def accounting(p):
  print "*** accounting ***"
  radiusd.radlog(radiusd.L_INFO, '*** radlog call in accounting (0) ***')
  print
  print p
  return radiusd.RLM_MODULE_OK

def pre_proxy(p):
  print "*** pre_proxy ***"
  print p
  return radiusd.RLM_MODULE_OK

def post_proxy(p):
  print "*** post_proxy ***"
  print p
  return radiusd.RLM_MODULE_OK

def post_auth(p):
  print "*** post_auth ***"
  print p
  return radiusd.RLM_MODULE_OK

def recv_coa(p):
  print "*** recv_coa ***"
  print p
  return radiusd.RLM_MODULE_OK

def authenticate(p):
  print "*** recv_coa ***"
  print p
  return radiusd.RLM_MODULE_OK

def checksimul(p):
  print "*** recv_coa ***"
  print p
  return radiusd.RLM_MODULE_OK

def send_coa(p):
  print "*** send_coa ***"
  print p
  return radiusd.RLM_MODULE_OK


def detach():
  print "*** goodbye from example.py ***"
  return radiusd.RLM_MODULE_OK


if __name__ == "__main__":
    a = authorize(p)
    print a
