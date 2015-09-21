#! /usr/bin/env python
#
# Python module example file
# Miguel A.L. Paraz <mparaz@mparaz.com>
#
# $Id: dd5b0b88243ea2919634d1ae519f5825f0560c93 $

"""
00 %3A 18 %3A 0a %3A f2 %3A de %3A 20
48 %3A d2 %3A 24 %3A 43 %3A a6 %3A c1
"""

import os
import sys
import subprocess

import radiusd

p = (('Acct-Session-Id', '"624874448299458941"'), ('Called-Station-Id', '"00-18-0A-F2-DE-20:Radius test"'), ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'), ('Framed-IP-Address', '172.31.3.142'), ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'), ('NAS-IP-Address', '108.161.147.120'), ('NAS-Port', '0'), ('NAS-Port-Id', '"Wireless-802.11"'), ('NAS-Port-Type', 'Wireless-802.11'), ('Service-Type', 'Login-User'), ('User-Name', '"alwaysdeone@gmail.com"'), ('User-Password', '"12345"'), ('Attr-26.29671.1', '0x446a756e676c65204851203032'))

def make_env():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")

    import django
    django.setup()

def get_user(username):
    make_env()
    from django.contrib.auth.models import User
    return User.objects.get(username__exact=username)

def get_ap(mac):
    make_env()
    from accounts.models import AccessPoint
    return AccessPoint.objects.get(mac_address__exact=mac)

def create_mac(param):
    called_station_id = trim_value(param).split(':')[0]
    return called_station_id.replace('-', ':')

def trim_value(val):
    return val[1:-1]

def get_subscription(user):
    if user.subscriber.group is not None:
        # User belongs to a group. Return group package subscription
        subscription = user.subscriber.group.grouppackagesubscription_set.all()[0]
    else:
        subscription = user.subscriber.packagesubscription_set.all()[0]

    return subscription

def instantiate(p):
    print "*** instantiate ***"
    print p

def authorize(p):
    print "*** authorize ***"
    make_env()
    from django.utils import timezone

    params = dict(p)
    username = trim_value(params['User-Name'])
    ap_mac = create_mac(params['Called-Station-Id'])

    user = get_user(username)
    print user
    ap = get_ap(ap_mac)
    print ap

    if user.is_active:
        radiusd.radlog(radiusd.L_INFO, '*** User is active ***')
        if ap.allows(user):
            radiusd.radlog(radiusd.L_INFO, '*** AP allowed user ***')
            subscription = get_subscription(user)
            if subscription.is_valid():
                radiusd.radlog(radiusd.L_INFO, '*** User subscription valid ***')
                now = timezone.now()
                package_period = str((subscription.stop - now).total_seconds())
                package_period = package_period.split(".")[0]
                return (radiusd.RLM_MODULE_OK,
                    (('Session-Timeout', package_period),), (('Maximum-Data-Rate-Upstream', '1000000'),), (('Maximum-Data-Rate-Downstream', '1000000'),))
            else:
                return (radiusd.RLM_MODULE_REJECT,
                    (('Reply-Message', 'Subscription Expired'),), (('Auth-Type', 'python'),))
        else:
            return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', 'User Unauthorized'),), (('Auth-Type', 'python'),))
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
