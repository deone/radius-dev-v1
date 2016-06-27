#! /usr/bin/env python

from decimal import Decimal

from radlib import *

def instantiate(p):
    print_info('*** Instantiating Python module ***')
    return True

def authorize(p):
    print_info("*** Request Content: " + str(p) + " ***")
    params = dict(p)
    ap_mac = create_mac(params['Called-Station-Id'])

    # Fetch AP
    print_info('*** Fetching AP... ***')
    ap = get_ap(ap_mac)

    if not ap:
        print_info('*** - AP Not Found ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'AP Not Found. Please call customer care.'),), (('Auth-Type', 'python'),))
    else:
        print_info('*** - AP fetched successfully: ' + ap.mac_address + ' ***')

    username = trim_value(params['User-Name'])
    password = trim_value(params['User-Password'])

    # Fetch user/voucher
    user = None
    voucher = None

    print_info('*** Fetching User... ***')
    user = get_user(username)

    if not user:
        print_info('*** - User Not Found ***')
        print_info("*** Okay. Might be a voucher. Let's try fetching Voucher... ***")
        voucher = get_voucher(username)

    if voucher is None and user is None:
        print_info('*** - User Or Voucher Not Found ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User account or Voucher does not exist.'),), (('Auth-Type', 'python'),)) 

    # Check whether AP allows user.
    print_info('*** AP Checking User Eligibility... ***')
    if not check_user_eligibility_on_ap(user, ap):
        print_info('*** - AP Disallowed User ***')
        return (radiusd.RLM_MODULE_REJECT,
            (('Reply-Message', 'User Unauthorized.'),), (('Auth-Type', 'python'),))
    else:
        print_info('*** - AP Allowed User ***')

    if user:
        print_info('*** - User fetched successfully: ' + user.username + ' ***')

        # Check Password
        print_info('*** Checking Password... ***')
        code = check_user_password(user, password)
        if code in REPLY_CODES_MESSAGES:
            print_info('*** - ' + REPLY_CODES_MESSAGES[code] + ' ***')
            return display_reply_message(code)
        else:
            print_info('*** - User Password Correct :-) ***')

        # Check User Account Status
        print_info('*** Checking User Account Status... ***')
        code = check_user_account_status(user)
        if code in REPLY_CODES_MESSAGES:
            print_info('*** - ' + REPLY_CODES_MESSAGES[code] + ' ***')
            return display_reply_message(code)
        else:
            print_info('*** - User Account Active ***')

        subscription = get_user_subscription(user)

    elif voucher:
        print_info('*** - Voucher fetched successfully: ' + voucher.username + ' ***')

        # Check Password
        print_info('*** Checking Password... ***')
        code = check_voucher_password(str(voucher.value), password)
        if code in REPLY_CODES_MESSAGES:
            print_info('*** - ' + REPLY_CODES_MESSAGES[code] + ' ***')
            return display_reply_message(code)
        else:
            print_info('*** - Voucher Password Correct :-) ***')
            

        print_info('*** Checking User Account Status... ***')
        print_info("*** We're skipping account status check for voucher ***")

        subscription = get_or_create_subscription(voucher)

    if not subscription:
        print_info('*** User Has No Subscription... ***')
        return (radiusd.RLM_MODULE_REJECT,
                (('Reply-Message', "You have no subscription. Click 'Manage Account' below to recharge your account and purchase a package."),), (('Auth-Type', 'python'),))
    else:
        # Check subscription validity
        print_info('*** Check User Subscription Validity ... ***')
        response = check_subscription_validity(subscription, user)

        if response[0] == 2:
            print_info('*** - User Subscription Valid ***')
            print_info('*** - Sending Access-Accept to Meraki ***')
        else:
            print_info('*** - User Subscription Invalid ***')
            print_info('*** - Sending Access-Reject to Meraki ***')

        return response

def accounting(p):
    print_info("*** Request Content: " + str(p) + " ***")
    params = dict(p)

    username = trim_value(params['User-Name'])
    acct_status_type = params['Acct-Status-Type']
    data_usage = (int(params['Acct-Input-Octets']) + int(params['Acct-Output-Octets'])) / 1000000000.0

    if acct_status_type == 'Stop':
        radcheck = Radcheck.objects.get(username__exact=username)
        radcheck.data_usage += Decimal(data_usage)
	radcheck.is_logged_in = False
	radcheck.save()

data = (
            ('User-Name', '"dayo@thecodeschool.net"'),
            ('Acct-Status-Type', 'Stop'),
            ('NAS-IP-Address', '108.161.147.120'),
            ('Event-Timestamp', '"Jun 24 2016 16:03:38 GMT"'),
            ('Acct-Input-Packets', '283160'),
            ('Acct-Output-Packets', '338826'),
            ('Acct-Input-Octets', '255909888'),
            ('NAS-Port-Type', 'Wireless-802.11'),
            ('Acct-Session-Id', '"624874448301086964"'),
            ('Acct-Terminate-Cause', 'Admin-Reset'),
            ('Attr-26.29671.1', '0x47482d4b504f4c592d4353422d30312d3032'),
            ('Calling-Station-Id', '"88-25-2C-E3-EF-E5"'),
            ('NAS-Port-Id', '"Wireless-802.11"'),
            ('NAS-Identifier', '"Meraki Cloud Controller RADIUS client"'),
            ('Framed-IP-Address', '10.8.59.86'),
            ('Called-Station-Id', '"00-18-0A-F2-E2-70:Spectra"'),
            ('Acct-Input-Gigawords', '0'),
            ('Service-Type', 'Login-User'),
            ('Acct-Output-Octets', '19741696'),
            ('NAS-Port', '0'),
            ('Acct-Session-Time', '94463'),
            ('Acct-Output-Gigawords', '0'),
            ('Acct-Delay-Time', '133'),
            ('Acct-Unique-Session-Id', '"9bdad742d9ec6fd7773efe9ce8f898ae"')
            )

if __name__ == '__main__':
    accounting(data)
