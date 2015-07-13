# -*- coding: utf-8 -*-
#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2010 - 2015 LSE Leading Security Experts GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: linotp@lsexperts.de
#    Contact: www.linotp.org
#    Support: www.lsexperts.de
#


import time

from linotp_selenium_helper import TestCase, PasswdUserIdResolver, Realm
from linotp_selenium_helper.hotp_token import HotpToken
from linotp_selenium_helper.user_view import UserView


class TestAuth(TestCase):
    """
    TestCase class that tests the auth/index forms
    """

    def test_auth_index(self):
        """
        Test /auth/index form by authenticating susi with a HMAC/HOTP Token
        """
        driver = self.driver

        # Create Passwd UserIdResolver
        #
        # Expected content of /etc/se_mypasswd is:
        #
        # hans:x:42:0:Hans Müller,Room 22,+49(0)1234-22,+49(0)5678-22,hans@example.com:x:x
        # susi:x:1336:0:Susanne Bauer,Room 23,+49(0)1234-24,+49(0)5678-23,susanne@example.com:x:x
        # rollo:x:21:0:Rollobert Fischer,Room 24,+49(0)1234-24,+49(0)5678-24,rollo@example.com:x:x
        #
        passwd_name = "SE_myPasswd"
        passwd_id_resolver = PasswdUserIdResolver(passwd_name, driver,
                                                  self.base_url, filename="/etc/se_mypasswd")
        time.sleep(1)

        # Create realm for all resolvers
        resolvers_realm = [passwd_id_resolver]
        realm_name = "se_test_auth"
        realm = Realm(realm_name, resolvers_realm)
        realm.create(driver, self.base_url)
        time.sleep(1)

        # Enroll HOTP token
        # Seed and OTP values: https://tools.ietf.org/html/rfc4226#appendix-D
        driver.get(self.base_url + "/manage")
        time.sleep(2)
        user_view = UserView(driver, self.base_url, realm_name)
        username = "susi"
        user_view.select_user(username)
        pin = "myauthpin"
        HotpToken(driver,
                  self.base_url,
                  pin=pin,
                  hmac_key="3132333435363738393031323334353637383930")
        time.sleep(1)

        otp_list = ["755224",
                    "287082",
                    "359152",
                    "969429",
                    "338314",
                    "254676"]

        driver.get(self.base_url + "/auth/index")
        for otp in otp_list:
            driver.find_element_by_id("user").clear()
            driver.find_element_by_id("user").send_keys("susi@se_test_auth")
            driver.find_element_by_id("pass").clear()
            driver.find_element_by_id("pass").send_keys(pin + otp)
            driver.find_element_by_css_selector("input[type=\"submit\"]").click()
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            alert.accept()
            self.assertEqual("User successfully authenticated!", alert_text)

        # wrong otp
        driver.find_element_by_id("user").clear()
        driver.find_element_by_id("user").send_keys("susi@se_test_auth")
        driver.find_element_by_id("pass").clear()
        driver.find_element_by_id("pass").send_keys("bla!")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        alert = self.driver.switch_to_alert()
        alert_text = alert.text
        alert.accept()
        self.assertEqual("User failed to authenticate!", alert_text)

        # test auth/index3
        otp_list = ["287922",
                    "162583",
                    "399871",
                    "520489"]

        driver.get(self.base_url + "/auth/index3")
        for otp in otp_list:
            driver.find_element_by_id("user3").clear()
            driver.find_element_by_id("user3").send_keys("susi@se_test_auth")
            driver.find_element_by_id("pass3").clear()
            driver.find_element_by_id("pass3").send_keys(pin)
            driver.find_element_by_id("otp3").clear()
            driver.find_element_by_id("otp3").send_keys(otp)
            driver.find_element_by_css_selector("input[type=\"submit\"]").click()
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            alert.accept()
            self.assertEqual("User successfully authenticated!", alert_text)

        # wrong otp
        driver.find_element_by_id("user3").clear()
        driver.find_element_by_id("user3").send_keys("susi@se_test_auth")
        driver.find_element_by_id("pass3").clear()
        driver.find_element_by_id("pass3").send_keys(pin)
        driver.find_element_by_id("otp3").clear()
        driver.find_element_by_id("otp3").send_keys("some invalid otp")
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        alert = self.driver.switch_to_alert()
        alert_text = alert.text
        alert.accept()
        self.assertEqual("User failed to authenticate!", alert_text)

