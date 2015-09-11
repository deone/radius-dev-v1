#! /usr/bin/env python

import unittest
from datetime import timedelta

import rules 

class AuthorizeTestCase(unittest.TestCase):

    def setUp(self):
        self.p = (('Acct-Session-Id', '"624874448299458941"'), ('Called-Station-Id', '"00-19-0A-F2-DE-20:Radius test"'), ('Calling-Station-Id', '"48-D2-24-43-A6-C1"'), ('Framed-IP-Address', '172.31.3.142'), ('NAS-Identifier', '"Cisco Meraki cloud RADIUS client"'), ('NAS-IP-Address', '108.161.147.120'), ('NAS-Port', '0'), ('NAS-Port-Id', '"Wireless-802.11"'), ('NAS-Port-Type', 'Wireless-802.11'), ('Service-Type', 'Login-User'), ('User-Name', '"test@example.com"'), ('User-Password', '"12345"'), ('Attr-26.29671.1', '0x446a756e676c65204851203032'))
        params = dict(self.p)

        username = rules.trim_value(params['User-Name'])
        password = rules.trim_value(params['User-Password'])
        ap_mac = rules.create_mac(params['Called-Station-Id'])

        rules.make_env()

        from django.utils import timezone
        from django.contrib.auth.models import User
        from django.conf import settings
        from accounts.models import Subscriber, AccessPoint, GroupAccount
        from packages.models import Package, GroupPackageSubscription

        self.group1 = GroupAccount.objects.create(name='CUG', max_no_of_users=10)
        self.group2 = GroupAccount.objects.create(name='LUG', max_no_of_users=10)
        self.ap = AccessPoint.objects.create(name='Djungle HQ 02', mac_address=ap_mac)
        self.user = User.objects.create_user(username, username, password)

        Subscriber.objects.create(user=self.user, country='NGA', phone_number='+233542751610')

        now = timezone.now()
        p = Package.objects.all()[0]
        self.gps = GroupPackageSubscription.objects.create(group=self.group1, package=p, start=now,
            stop=now + timedelta(hours=settings.PACKAGE_TYPES_HOURS_MAP[p.package_type]))

    """ AP Status/Subscriber Type/Subscription Status Tests """

    # 1. Private AP no group - default

    # - Individual subscriber.
    def test_private_ap_no_group_individual_subscriber(self):
        pass

    # - Group subscriber.
    def test_private_ap_no_group_group_subscriber(self):
        result = rules.authorize(self.p)
        self.assertEqual(result, (0, (('Reply-Message', 'User Unauthorized'),), (('Auth-Type', 'python'),)))


    # 2. Private AP belonging to group

    # - Individual subscriber

    # - Group subscriber. Same group as AP. Valid group subscription.
    def test_private_ap_subscriber_same_group_and_group_subscription_valid(self):
        self.ap.group = self.user.subscriber.group = self.group1
        self.ap.save()
        self.user.subscriber.save()

        result = rules.authorize(self.p)
        self.assertEqual(result, (2, (('Session-Timeout', '7200'),), (('Auth-Type', 'python'),)))

    # - Group subscriber. Same group as AP. Invalid group subscription.
    def test_private_ap_subscriber_same_group_and_group_subscription_invalid(self):
        pass

    # - Group subscriber. Different group.
    def test_private_ap_subscriber_different_groups(self):
        self.ap.group = self.group1
        self.user.subscriber.group = self.group2
        result = rules.authorize(self.p)
        self.assertEqual(result, (0, (('Reply-Message', 'User Unauthorized'),), (('Auth-Type', 'python'),)))


    # 3. Public AP

    # - Individual subscriber. Valid subscription.
    """ def test_public_ap_individual_subscriber_subscription_valid(self):
        self.ap.status = 'PUB'
        self.ap.save()
        result = rules.authorize(self.p)
        self.assertEqual(result, (2, (('Session-Timeout', '7200'),), (('Auth-Type', 'python'),))) """

    # - Individual subscriber. Invalid subscription.
    def test_public_ap_individual_subscriber_subscription_invalid(self):
        pass

    # - Group subscriber. Valid group subscription.
    def test_public_ap_group_subscriber_group_subscription_valid(self):
        self.ap.status = 'PUB'
        self.ap.save()
        self.user.subscriber.group = self.group1
        self.user.subscriber.save()
        
        result = rules.authorize(self.p)
        self.assertEqual(result, (2, (('Session-Timeout', '7200'),), (('Auth-Type', 'python'),)))

    # - Group subscriber. Invalid group subscription.
    def test_public_ap_group_subscriber_group_subscription_invalid(self):
        pass

    """ End AP Status/Subscriber Type/Subscription Status Tests """

    def test_user_is_inactive(self):
        self.user.is_active = False
        self.user.save()
        result = rules.authorize(self.p)
        self.assertEqual(result, (0, (('Reply-Message', 'User De-activated'),), (('Auth-Type', 'python'),)))

    def tearDown(self):
        self.ap.delete()
        self.group1.delete()
        self.group2.delete()
        self.user.delete()
        self.gps.delete()

# suite = unittest.TestSuite([AuthorizeTestCase('test_success'), AuthorizeTestCase('test_fail')])

# suite.run(unittest.TestResult())

if __name__ == "__main__":
    unittest.main()
