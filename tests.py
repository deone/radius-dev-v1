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
from accounts.models import Radcheck, Subscriber, GroupAccount
from packages.models import (Package, PackageSubscription, GroupPackageSubscription, InstantVoucher)

class AuthorizeTestCase(unittest.TestCase):

    def setUp(self):
        self.p = (
            ('Acct-Session-Id', '"624874448299458941"'),
            ('Called-Station-Id', '"00-18-0A-F2-DE-10:Radius test"'),
            ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'),
            ('Framed-IP-Address', '172.31.3.142'),
            ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'),
            ('NAS-IP-Address', '108.161.147.120'),
            ('NAS-Port', '0'),
            ('NAS-Port-Id', '"Wireless-802.11"'),
            ('NAS-Port-Type', 'Wireless-802.11'),
            ('Service-Type', 'Login-User'),
            ('User-Name', '"a@a.com"'),
            ('User-Password', '"12345"'),
            # ('User-Name', '"dayo@thecodeschool.net"'),
            # ('User-Password', '"12345"'),
            # ('User-Name', '"ulyh@spectrawireless.com"'),
            # ('User-Password', '"EYQL9B"'),
            ('Attr-26.29671.1', '0x446a756e676c65204851203032')
            )
        
        self.params = dict(self.p)
        self.username = rules.trim_value(self.params['User-Name'])
        self.password = rules.trim_value(self.params['User-Password'])

        self.user = User.objects.create_user(self.username, self.username, self.password)
        self.subscriber = Subscriber.objects.create(user=self.user, country='NGA', phone_number='+2348029299274')
        self.voucher = Radcheck.objects.create(user=self.user, username=self.username,
            attribute='MD5-Password', op=':=', value=md5_password(self.password))
        self.package = Package.objects.create(package_type='Daily',
            volume='3', speed='1.5', price=4)
        self.ivoucher = InstantVoucher.objects.create(radcheck=self.voucher, package=self.package)

    def test_instantiate(self):
        self.assertTrue(rules.instantiate(self.p))

    def test_create_mac(self):
        mac = rules.create_mac(self.params['Called-Station-Id'])
        self.assertEqual(mac, '00:18:0A:F2:DE:10')

    def test_get_or_create_subscription(self):
        subscription = rules.get_or_create_subscription(self.voucher)
        self.assertTrue(isinstance(subscription, PackageSubscription))
        subscription.delete()

    def test_get_user_subscription_None(self):
        subscription = rules.get_user_subscription(self.user)
        self.assertEqual(subscription, None)

    def test_get_user_group_subscription(self):
        group = GroupAccount.objects.create(name='CUG', max_no_of_users=10)
        self.subscriber.group = group
        self.subscriber.save()
        now = timezone.now()
        gps = GroupPackageSubscription.objects.create(group=group, package=self.package, start=now,
            stop=now + timedelta(hours=PACKAGE_TYPES_HOURS_MAP[self.package.package_type]))

        subscription = rules.get_user_subscription(self.user)
        self.assertTrue(isinstance(subscription, GroupPackageSubscription))
        group.delete()
        gps.delete()

    def test_get_user(self):
        user = rules.get_user(self.username)
        self.assertTrue(isinstance(user, User))

    def test_get_user_None(self):
        self.assertEqual(rules.get_user('hhhh'), None)

    def test_get_voucher(self):
        username = 'aaaa'
        voucher = Radcheck.objects.create(user=None, username=username,
            attribute='MD5-Password', op=':=', value=md5_password('12345'))
        self.assertTrue(isinstance(rules.get_voucher(username), Radcheck))
        voucher.delete()

    def test_get_voucher_None(self):
        self.assertEqual(rules.get_voucher('bbbb'), None)

    """ def test_authorize(self):
        result = rules.authorize(self.p)
        print result
        self.assertEqual(len(result), 3) """

    def tearDown(self):
        self.user.delete() # This also deletes self.subscriber
        self.voucher.delete()
        self.ivoucher.delete()
        self.package.delete()

# suite = unittest.TestSuite([AuthorizeTestCase('test_success'), AuthorizeTestCase('test_fail')])
# suite.run(unittest.TestResult())

if __name__ == "__main__":
    unittest.main()
