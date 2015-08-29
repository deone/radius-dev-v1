#! /usr/bin/env python

import unittest

import rules 

class AuthorizeTestCase(unittest.TestCase):

    def setUp(self):
        self.p = (('User-Name', '"alwaysdeone@gmail.com"'), ('User-Password', '"12345"'), ('NAS-IP-Address', '192.168.8.102'), ('NAS-Port', '0'), ('Message-Authenticator', '0x7edbbcb48daa747ef293a0ba548c1f6c'))
        self.user = rules.get_user(self.p)
        self.user.is_active = True
        self.user.save()

    def test_success(self):
        result = rules.authorize(self.p)
        self.assertEqual(result, 2)

    def test_fail(self):
        self.user.is_active = False
        self.user.save()
        result = rules.authorize(self.p)
        self.assertEqual(result, 0)

suite = unittest.TestSuite([AuthorizeTestCase('test_success'), AuthorizeTestCase('test_fail')])

suite.run(unittest.TestResult())

if __name__ == "__main__":
    unittest.main()
