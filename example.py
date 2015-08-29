#! /usr/bin/env python
#
# Python module example file
# Miguel A.L. Paraz <mparaz@mparaz.com>
#
# $Id: dd5b0b88243ea2919634d1ae519f5825f0560c93 $

import os
import sys
import subprocess

import radiusd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")
hostname = subprocess.check_output('hostname')[:-1]

if not hostname.startswith('billing'):
    sys.path.insert(1, "/Users/deone/src/billing/lib/python2.7/site-packages")
    sys.path.insert(1, "/Users/deone/src/billing/billing")
else:
    sys.path.insert(1, "/root/billing/lib/python2.7/site-packages")
    sys.path.insert(1, "/root/billing/billing")

from django.contrib.auth.models import User

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
    params = dict(p)
    username = params['User-Name'][1:-1]
    user = User.objects.get(username__exact=username)

    if user.is_active:
        return radiusd.RLM_MODULE_OK
    else:
        return radiusd.RLM_MODULE_REJECT

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

