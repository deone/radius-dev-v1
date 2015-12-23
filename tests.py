#! /usr/bin/env python

import unittest

import rules 

class AuthorizeTestCase(unittest.TestCase):

    def setUp(self):
        self.p = (
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

    def test_instantiate(self):
        self.assertTrue(rules.instantiate(self.p))

    def test_authorize(self):
        result = rules.authorize(self.p)
        print result
        self.assertEqual(len(result), 3)

# suite = unittest.TestSuite([AuthorizeTestCase('test_success'), AuthorizeTestCase('test_fail')])
# suite.run(unittest.TestResult())

if __name__ == "__main__":
    unittest.main()
