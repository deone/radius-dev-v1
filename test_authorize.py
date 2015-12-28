#! /usr/bin/env python

import unittest

import rules

import django
django.setup()

from django.contrib.auth.models import User

from accounts.helpers import md5_password
from accounts.models import Radcheck, AccessPoint


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

    def test_voucher_password_incorrect(self):
        voucher = Radcheck.objects.create(user=None, username='c@c.com',
            attribute='MD5-Password', op=':=', value=md5_password('00000'))

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'Voucher Password Incorrect'))

        voucher.delete()

    def test_user_password_incorrect(self):
        user = User.objects.create_user('c@c.com', 'c@c.com', '00000')

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User Password Incorrect'))

        user.delete()

    def test_ap_not_found(self):
        p = (
            ('Called-Station-Id', '"00-18-0A-F2-DE-18:Radius test"'),
            )

        result = rules.authorize(p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'AP Not Found. Please call customer care.'))

    def test_user_inactive(self):
        user = User.objects.create_user('c@c.com', 'c@c.com', '12345')
        user.is_active = False
        user.save()

        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User Inactive'))

        user.delete()

    def tearDown(self):
        self.ap.delete()

if __name__ == "__main__":
    unittest.main()
