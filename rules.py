#! /usr/bin/env python

import os
import hashlib
from datetime import timedelta

import radiusd


radiusd.radlog(radiusd.L_INFO, "*** Setting settings module ***")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")
radiusd.radlog(radiusd.L_INFO, "*** - Settings module set successfully ***")


radiusd.radlog(radiusd.L_INFO, "*** Importing and setting up Django elements ***")
import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from billing.settings import PACKAGE_TYPES_HOURS_MAP
from accounts.models import AccessPoint, Radcheck
from accounts.helpers import md5_password
from packages.models import InstantVoucher, PackageSubscription

def print_info(info):
    radiusd.radlog(radiusd.L_INFO, info)

print_info("*** - Django elements imported and set up successfully ***")

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

def create_mac(param):
    called_station_id = trim_value(param).split(':')[0]
    return called_station_id.replace('-', ':')

def trim_value(val):
    return val[1:-1]

def instantiate(p):
    print_info('*** Instantiating Python module ***')
    return True

# For simplicity, make Package Subscription reference Radcheck instead of Subscriber for now.
# - Eventually, move all extra user info into Radcheck and rename it to Subscriber. Password check will then happen in Subscriber (md5).
# Check for package subscription. If subscription exists, skip next step.
# Fetch subscriber - query User with username. If not found, query Radcheck with username. If found in Radcheck, create PackageSubscription.
# For instant users, check password by md5-hashing password and comparing it with password in Radcheck.
# Skip account status check for instant users - log this to avoid confusion.
# To check AP eligibilty for instant users, return False in the 'else' block of AccessPoint.allows() if user is not an instance of User.

def create_subscription(voucher):
    ivoucher = InstantVoucher.objects.get(radcheck__username=voucher.username)
    now = timezone.now()
    ps = PackageSubscription.objects.create(
            radcheck=voucher, package=ivoucher.package, start=now,
            stop=now + timedelta(hours=PACKAGE_TYPES_HOURS_MAP[ivoucher.package.package_type]))

    return ps

def get_or_create_subscription(voucher):
    try:
        subscription = PackageSubscription.objects.get(radcheck__username=voucher.username)
    except PackageSubscription.DoesNotExist:
        subscription = create_subscription(voucher)

    return subscription

def get_user_subscription(user):
    if user.subscriber.group is not None:
        # User belongs to a group. Return group package subscription
        subscription = user.subscriber.group.grouppackagesubscription_set.all()[0]
    else:
        try:
            subscription = user.radcheck.packagesubscription_set.all()[0]
        except IndexError:
            return False
        else:
            pass

    return subscription

def get_user(username):
    print_info('*** Fetching User... ***')
    try:
        user = User.objects.get(username__exact=username)
    except User.DoesNotExist:
        print_info('*** - User Not Found ***')
        return None
    else:
        print_info('*** - User fetched successfully: ' + user.username + ' ***')
        return user

def get_voucher(username):
    print_info("*** Okay. Might be a voucher. Let's try fetching Voucher... ***")
    try:
        voucher_list = Radcheck.objects.filter(user=None).filter(username__exact=username)
    except Radcheck.DoesNotExist:
        print_info('*** - Voucher Not Found ***')
        return None
    else:
        voucher = voucher_list[0]
        print_info('*** - Voucher fetched successfully: ' + voucher.username + ' ***')
        return voucher

def get_ap(ap_mac):
    print_info('*** Fetching AP... ***')
    try:
        ap = AccessPoint.objects.get(mac_address__exact=ap_mac)
    except AccessPoint.DoesNotExist:
        print_info('*** - AP Not Found ***')
        return False
    else:
        print_info('*** - AP fetched successfully: ' + ap.mac_address + ' ***')
        return ap

def check_voucher_password(voucher, password):
    if not md5_password(password) == voucher.value:
        print_info('*** - Password Incorrect! ***')
        return False
    else:
        print_info('*** - Password Correct :-( ***')
        return True

def check_user_password(user, password):
    if not user.check_password(password):
        print_info('*** - Password Incorrect! ***')
        return False
    else:
        print_info('*** - Password Correct :-( ***')
        return True 

def check_user_account_status(user):
    """ if not isinstance(user, User):
        print_info('*** - Instant Voucher - Skipping Account Status Check ***')
    else: """
    if user.is_active:
        print_info('*** - User Account Active ***')
        return True
    else:
        print_info('*** - User Account Inactive ***')
        return False

def check_user_eligibility_on_ap(user, ap):
    print_info('*** AP Checking User Eligibility... ***')
    if ap.allows(user):
        print_info('*** - AP Allowed User ***')
        return True
    else:
        print_info('*** - AP Disallowed User ***')
        return False

def check_subscription_validity(subscription):
    print_info('*** Check User Subscription Validity ... ***')
    if subscription:
        if subscription.is_valid():
            print_info('*** - User Subscription Valid ***')
            now = timezone.now()

            package_period = str((subscription.stop - now).total_seconds())
            package_period = package_period.split(".")[0]

            bandwidth_limit = str(float(subscription.package.speed) * 1000000)
            bandwidth_limit = bandwidth_limit.split('.')[0]

            print_info('*** - Sending Access-Accept to Meraki ***')
            return (radiusd.RLM_MODULE_OK,
                (('Session-Timeout', package_period),('Maximum-Data-Rate-Upstream', bandwidth_limit),('Maximum-Data-Rate-Downstream', bandwidth_limit)),
                (('Auth-Type', 'python'),))
        else:
            print_info('*** - User Subscription Invalid ***')
            print_info('*** - Sending Access-Reject to Meraki ***')
            return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', 'Subscription Invalid'),), (('Auth-Type', 'python'),))
    else:
        return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', 'User Has No Subscription'),), (('Auth-Type', 'python'),))

def authorize(p):
    print_info("*** Request Content: " + str(p) + " ***")

    params = dict(p)

    username = trim_value(params['User-Name'])
    ap_mac = create_mac(params['Called-Station-Id'])
    password = trim_value(params['User-Password'])

    # Fetch user
    user = None
    voucher = None

    user = get_user(username)
    if not user:
        voucher = get_voucher(username)
        if not voucher:
            return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', 'User account or Voucher does not exist.'),), (('Auth-Type', 'python'),)) 

    # Check Password
    print_info('*** Checking Password... ***')
    if not user:
        if not check_voucher_password(voucher, password):
            return (radiusd.RLM_MODULE_REJECT,
                    (('Reply-Message', 'Password Incorrect'),), (('Auth-Type', 'python'),))
    if not voucher:
        if not check_user_password(user, password):
            return (radiusd.RLM_MODULE_REJECT,
                    (('Reply-Message', 'Password Incorrect'),), (('Auth-Type', 'python'),)) 

    # Check User Account Status
    print_info('*** Checking User Account Status... ***')
    if user:
        if not check_user_account_status(user):
            return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', 'User Inactive'),), (('Auth-Type', 'python'),))
    else:
        print_info("*** We're skipping account status check for voucher ***")
        pass

    # Fetch AP
    ap = get_ap(ap_mac)
    if not ap:
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'AP Not Found. Please call customer care.'),), (('Auth-Type', 'python'),))

    # Check whether AP allows user
    if not check_user_eligibility_on_ap(user, ap):
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User Unauthorized'),), (('Auth-Type', 'python'),))

    if not voucher:
        subscription = get_user_subscription(user)
    
    if not user:
        subscription = get_or_create_subscription(voucher)

    response = check_subscription_validity(subscription)

    return response
