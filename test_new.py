#! /usr/bin/env python

import unittest
from datetime import timedelta

import rules 

import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from billing.settings import PACKAGE_TYPES_HOURS_MAP
from accounts.helpers import md5_password
from accounts.models import Radcheck, Subscriber, GroupAccount, AccessPoint
from packages.models import (Package, PackageSubscription, GroupPackageSubscription, InstantVoucher)

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

class AuthorizeVoucherTestCase(AuthorizeTestCase):

    def setUp(self, *args, **kwargs):
        super(AuthorizeVoucherTestCase, self).setUp(*args, **kwargs)
        self.voucher = Radcheck.objects.create(user=None, username='c@c.com',
            attribute='MD5-Password', op=':=', value=md5_password('12345'))
        self.package = Package.objects.create(package_type='Daily', volume='3', speed='1.5', price=4)
        self.iv = InstantVoucher.objects.create(radcheck=self.voucher, package=self.package)
        self.ap.status = 'PUB'
        self.ap.save()

    def test_voucher_password_incorrect(self):
        self.voucher.value = md5_password('00000')
        self.voucher.save()

        result = rules.authorize(self.p)
        print result
        """ self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'Voucher Password Incorrect')) """

    def tearDown(self):
        self.voucher.delete()
        self.package.delete()
        self.iv.delete()
        self.ap.delete()

if __name__ == "__main__":
    unittest.main()
