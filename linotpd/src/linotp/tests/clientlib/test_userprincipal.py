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

"""
Verify LinOTP for UserPrincipal (user@domain) authentication

the test will create a static-password token, and
will try to verify the user in different situations.
"""


import __builtin__
__builtin__.use_standalone_advanced_controller = True
from linotp.tests.advanced_controller import TestAdvancedController
from linotp.tests.tools.json_utils    import JsonUtils


import logging
log = logging.getLogger(__name__)


class TestUserPrincipalController(TestAdvancedController):
    def __init__(self, *args, **kwargs):
        super(TestUserPrincipalController, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestUserPrincipalController, self).setUp()

        self.setAuthorization(self.getDefaultAuthorization())
        self.createDefaultResolvers()
        self.createDefaultRealms()

        self.splitVal = self.getConfiguration(key='splitAtSign')
        self.setConfiguration('splitAtSign', False)
        self.setAuthorization(None)

    def tearDown(self):
        self.setAuthorization(self.getDefaultAuthorization())

        # The new setConfiguration will remove setting if Value is "None" or "Empty"
        self.setConfiguration('splitAtSign', self.splitVal)

        self.deleteAllTokens()
        self.deleteAllRealms()
        self.deleteAllResolvers()

        self.setAuthorization(None)
        super(TestUserPrincipalController, self).tearDown()

    def test_userprincipal(self):
        """
        Verify LinOTP for UserPrincipal (user@domain) authentication

        the test will create a static-password token, and
        will try to verify the user in different situations.

        2015.07.10: due to lack of information about what is
                    the purpose of this test, only one case
                    is implemented (with user@domain + realm
                    specified)

        """
        user = "pass@user"
        pin = "1234"
        realm = 'myDefRealm'

        # Initialize authorization (we need authorization in
        # token creation/deletion)...
        self.setAuthorization(self.getDefaultAuthorization())
        # Create test token...
        res = self.createToken(user=user,
                               realm=realm,
                               serial="F722362",
                               pin=pin,
                               otpkey="AD8EABE235FC57C815B26CEF37090755",
                               type='spass')
        serial = JsonUtils.getJson(res, ['detail', 'serial'])

        # although not needed, we assign token...
        self.assignToken(serial=serial, user=user, realm=realm)
        self.enableToken(serial=serial)

        # Revoke authorization...
        self.setAuthorization(None)

        # test user-principal authentication
        self.validateCheck(user=user, password=pin, realm=realm)

        # Reactivate authentication
        self.setAuthorization(self.getDefaultAuthorization())
        self.removeTokenBySerial(serial)
