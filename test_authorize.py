#! /usr/bin/env python

import unittest

import rules

import django
django.setup()

from django.contrib.auth.models import User

from accounts.helpers import md5_password
from accounts.models import Radcheck, AccessPoint
from packages.models import InstantVoucher, Package


class AuthorizeTestCase(unittest.TestCase):

    def setUp(self):
        self.p = (
            ('Acct-Session-Id', '"624874448299458941"'),
            ('Called-Station-Id', '"00-18-0A-F2-DE-15:Radius test"'),
            ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'),
            ('Framed-IP-Address', '172.31.3.142'),
            ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'),
            ('NAS-IP-Address', '108.161.147.120'),
            ('NAS-Port', '0'),
            ('NAS-Port-Id', '"Wireless-802.11"'),
            ('NAS-Port-Type', 'Wireless-802.11'),
            ('Service-Type', 'Login-User'),
            ('User-Name', '"c@c.com"'),
            ('User-Password', '"12345"'),
            ('Attr-26.29671.1', '0x446a756e676c65204851203032')
            )

        self.ap = AccessPoint.objects.create(name='My AP', mac_address='00:18:0A:F2:DE:15')

    def test_user_voucher_None(self):
        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User account or Voucher does not exist.'))

    def test_ap_not_found(self):
        p = (
            ('Called-Station-Id', '"00-18-0A-F2-DE-18:Radius test"'),
            )

        result = rules.authorize(p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'AP Not Found. Please call customer care.'))

    def test_user_has_no_subscription(self):
        self.ap.status = 'PUB'
        self.ap.save()
        username = 'c@c.com'
        password = '12345'
        user = User.objects.create_user(username, username, password)
        voucher = Radcheck.objects.create(user=user, username=username,
            attribute='MD5-Password', op=':=', value=md5_password(password))

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User Has No Subscription.'))

        voucher.delete()
        user.delete()

    # Refactor these
    def test_user_unauthorized(self):
        voucher = Radcheck.objects.create(user=None, username='c@c.com',
            attribute='MD5-Password', op=':=', value=md5_password('12345'))
        package = Package.objects.create(package_type='Daily', volume='3', speed='1.5', price=4)
        iv = InstantVoucher.objects.create(radcheck=voucher, package=package)

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User Unauthorized.'))

        iv.delete()
        package.delete()
        voucher.delete()

    def test_authorize_response(self):
        self.ap.status = 'PUB'
        self.ap.save()
        voucher = Radcheck.objects.create(user=None, username='c@c.com',
            attribute='MD5-Password', op=':=', value=md5_password('12345'))
        package = Package.objects.create(package_type='Daily', volume='3', speed='1.5', price=4)
        iv = InstantVoucher.objects.create(radcheck=voucher, package=package)

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1][0][0], 'Session-Timeout')
        self.assertEqual(result[1][1][0], 'Maximum-Data-Rate-Upstream')
        self.assertEqual(result[1][2][0], 'Maximum-Data-Rate-Downstream')

        iv.delete()
        package.delete()
        voucher.delete()
    #####

    def tearDown(self):
        self.ap.delete()

if __name__ == "__main__":
    unittest.main()
