#! /usr/bin/env python

import os
import radiusd


radiusd.radlog(radiusd.L_INFO, "*** Setting settings module ***")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")
radiusd.radlog(radiusd.L_INFO, "*** - Settings module set successfully ***")


radiusd.radlog(radiusd.L_INFO, "*** Importing and setting up Django elements ***")
import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import AccessPoint
radiusd.radlog(radiusd.L_INFO, "*** - Django elements imported and set up successfully ***")


p = (
    ('Acct-Session-Id', '"624874448299458941"'),
    ('Called-Station-Id', '"00-18-0A-F2-DE-20:Radius test"'),
    ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'),
    ('Framed-IP-Address', '172.31.3.142'),
    ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'),
    ('NAS-IP-Address', '108.161.147.120'),
    ('NAS-Port', '0'),
    ('NAS-Port-Id', '"Wireless-802.11"'),
    ('NAS-Port-Type', 'Wireless-802.11'),
    ('Service-Type', 'Login-User'),
    ('User-Name', '"alwaysdeone@gmail.com"'),
    ('User-Password', '"12345"'),
    ('Attr-26.29671.1', '0x446a756e676c65204851203032')
    )

def get_user(username):
    return User.objects.get(username__exact=username)

def get_ap(mac):
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
    radiusd.radlog(radiusd.L_INFO, '*** Instantiating Python module ***')

def fetch_user(username):
    radiusd.radlog(radiusd.L_INFO, '*** Fetching User... ***')
    try:
        user = get_user(username)
    except User.DoesNotExist:
        radiusd.radlog(radiusd.L_INFO, '*** - User Not Found ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User account does not exist.'),), (('Auth-Type', 'python'),))
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - User fetched successfully: ' + user.username + ' ***')
        return user

def fetch_ap(ap_mac):
    radiusd.radlog(radiusd.L_INFO, '*** Fetching AP... ***')
    try:
        ap = get_ap(ap_mac)
    except AccessPoint.DoesNotExist:
        radiusd.radlog(radiusd.L_INFO, '*** - AP Not Found ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'AP Not Found. Please call customer care.'),), (('Auth-Type', 'python'),))
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - AP fetched successfully: ' + ap.mac_address + ' ***')
        return ap

def check_password(user, password):
    radiusd.radlog(radiusd.L_INFO, '*** Checking Password... ***')
    if user.check_password(password):
        radiusd.radlog(radiusd.L_INFO, '*** - Password Correct! ***')
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - Password Incorrect :-( ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'Password Incorrect'),), (('Auth-Type', 'python'),))

def check_user_account_status(user):
    radiusd.radlog(radiusd.L_INFO, '*** Checking User Account Status... ***')
    if user.is_active:
        radiusd.radlog(radiusd.L_INFO, '*** - User Account Active ***')
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - User Account Inactive ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User Inactive'),), (('Auth-Type', 'python'),))

def check_ap_eligibility(user, ap):
    radiusd.radlog(radiusd.L_INFO, '*** AP Checking User Eligibility... ***')
    if ap.allows(user):
        radiusd.radlog(radiusd.L_INFO, '*** - AP Allowed User ***')
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - AP Disallowed User ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User Unauthorized'),), (('Auth-Type', 'python'),))

def check_subscription_validity(user):
    radiusd.radlog(radiusd.L_INFO, '*** Check User Subscription Validity ... ***')
    subscription = get_subscription(user)
    if subscription.is_valid():
        radiusd.radlog(radiusd.L_INFO, '*** - User Subscription Valid ***')
        now = timezone.now()

        package_period = str((subscription.stop - now).total_seconds())
        package_period = package_period.split(".")[0]

        bandwidth_limit = str(float(subscription.package.speed) * 1000000)
        bandwidth_limit = bandwidth_limit.split('.')[0]

        radiusd.radlog(radiusd.L_INFO, '*** - Sending Access-Accept to Meraki ***')
        return (radiusd.RLM_MODULE_OK,
            (('Session-Timeout', package_period),('Maximum-Data-Rate-Upstream', bandwidth_limit),('Maximum-Data-Rate-Downstream', bandwidth_limit)),
            (('Auth-Type', 'python'),))
    else:
        radiusd.radlog(radiusd.L_INFO, '*** - User Subscription Invalid ***')
        radiusd.radlog(radiusd.L_INFO, '*** - Sending Access-Reject to Meraki ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'Subscription Invalid'),), (('Auth-Type', 'python'),))

def authorize(p):
    radiusd.radlog(radiusd.L_INFO, "*** Request Content: " + str(p) + " ***")

    params = dict(p)

    username = trim_value(params['User-Name'])
    ap_mac = create_mac(params['Called-Station-Id'])
    password = trim_value(params['User-Password'])

    # Fetch User
    user = fetch_user(username)
    # Fetch AP
    ap = fetch_ap(ap_mac)
    # Check Password
    check_password(user, password)
    # Check User Account Status
    check_user_account_status(user)
    # Check whether AP allows user
    check_ap_eligibility(user, ap)
    # Check user subscription validity
    response = check_subscription_validity(user)

    return response

if __name__ == "__main__":
    a = authorize(p)
    print a
