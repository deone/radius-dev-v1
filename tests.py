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
            ('Called-Station-Id', '"00-18-0A-F2-DE-10:Radius test"'),
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

        # self.ap = AccessPoint.objects.create(name='My AP', mac_address='00:18:0A:F2:DE:15')

    def test_authorize_user_voucher_None(self):
        result = rules.authorize(self.p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User account or Voucher does not exist.'))

    def test_authorize_voucher_password_incorrect(self):
        p = (
            ('User-Name', '"f@f.com"'),
            ('User-Password', '"00000"'),
            ('Called-Station-Id', '"00-18-0A-F2-DE-10:Radius test"'),
            )

        voucher = Radcheck.objects.create(user=None, username='f@f.com',
            attribute='MD5-Password', op=':=', value=md5_password('12345'))

        result = rules.authorize(p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'Voucher Password Incorrect'))

        voucher.delete()

    def test_authorize_user_password_incorrect(self):
        p = (
            ('User-Name', '"f@f.com"'),
            ('User-Password', '"00000"'),
            ('Called-Station-Id', '"00-18-0A-F2-DE-10:Radius test"'),
            )

        user = User.objects.create_user('f@f.com', 'f@f.com', '12345')

        result = rules.authorize(p)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1][0], ('Reply-Message', 'User Password Incorrect'))

        user.delete()

    def tearDown(self):
        # self.ap.delete()
        pass

class FunctionsTestCase(unittest.TestCase):

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
        
        self.now = timezone.now()
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
        self.ap = AccessPoint.objects.create(name='My AP', mac_address='00:18:0A:F2:DE:11')

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
        gps = GroupPackageSubscription.objects.create(group=group, package=self.package, start=self.now,
            stop=self.now + timedelta(hours=PACKAGE_TYPES_HOURS_MAP[self.package.package_type]))

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

    def test_get_ap(self):
        ap = rules.get_ap('00:18:0A:F2:DE:11')
        self.assertTrue(isinstance(ap, AccessPoint))

    def test_get_ap_None(self):
        self.assertEqual(rules.get_ap('00:18:0A:F2:DE:12'), None)

    def test_check_voucher_password_valid(self):
        self.assertTrue(rules.check_voucher_password(self.voucher, '12345'))

    def test_check_voucher_password_invalid(self):
        self.assertFalse(rules.check_voucher_password(self.voucher, '00000'))

    def test_check_user_password_valid(self):
        self.assertTrue(rules.check_user_password(self.user, '12345'))

    def test_check_user_password_invalid(self):
        self.assertFalse(rules.check_user_password(self.user, '00000'))

    def test_check_user_account_status_valid(self):
        self.assertTrue(rules.check_user_account_status(self.user))

    def test_check_user_account_status_invalid(self):
        self.user.is_active = False
        self.user.save()
        self.assertFalse(rules.check_user_account_status(self.user))

    def test_check_user_eligibility_on_ap_valid(self):
        self.ap.status = 'PUB'
        self.ap.save()
        self.assertTrue(rules.check_user_eligibility_on_ap(self.user, self.ap))

    def test_check_user_eligibility_on_ap_invalid(self):
        self.assertFalse(rules.check_user_eligibility_on_ap(self.user, self.ap))

    def test_check_subscription_validity_valid(self):
        subscription = rules.get_or_create_subscription(self.voucher)
        response = rules.check_subscription_validity(subscription)
        self.assertEqual(len(response), 3)
        self.assertEqual(response[0], 2)
        subscription.delete()

    def test_check_subscription_validity_invalid(self):
        subscription = rules.get_or_create_subscription(self.voucher)
        subscription.stop = self.now - timedelta(hours=PACKAGE_TYPES_HOURS_MAP[subscription.package.package_type])
        subscription.save()
        response = rules.check_subscription_validity(subscription)
        self.assertEqual(len(response), 3)
        self.assertEqual(response[0], 0)
        subscription.delete()

    def tearDown(self):
        self.user.delete() # This also deletes self.subscriber
        self.voucher.delete()
        self.ivoucher.delete()
        self.package.delete()
        self.ap.delete()

# suite = unittest.TestSuite([AuthorizeTestCase('test_success'), AuthorizeTestCase('test_fail')])
# suite.run(unittest.TestResult())

if __name__ == "__main__":
    unittest.main()
