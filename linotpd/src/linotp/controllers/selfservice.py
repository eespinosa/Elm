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
selfservice controller - This is the controller for the self service interface,
                where users can manage their own tokens

                All functions starting with /selfservice/user...
                are data functions and protected by the session key
                i.e. the session key must be passed as the parameter session=

"""
import os

try:
    import json
except ImportError:
    import simplejson as json

import webob
import time
import base64

from pylons import request, response, config, tmpl_context as c
from pylons.controllers.util import abort
from mako.exceptions import CompileException

from linotp.lib.base import BaseController
from pylons.templating import render_mako as render


from linotp.lib.token import getTokenType

from linotp.lib.token import getTokens4UserOrSerial

from linotp.lib.policy import getSelfserviceActions

from linotp.lib.util import getParam
from linotp.lib.util import check_selfservice_session
from linotp.lib.util import remove_empty_lines

from linotp.lib.reply import sendError

from linotp.lib.util    import get_version
from linotp.lib.util    import get_copyright_info
from linotp.lib.util import get_client

from linotp.model.meta import Session


from linotp.lib.userservice import (add_dynamic_selfservice_enrollment,
                                    add_dynamic_selfservice_policies,
                                    create_auth_cookie
                                    )


from linotp.lib.selfservice import get_imprint
from linotp.lib.user import User, getAllUserRealms


import traceback
# import datetime, random
import copy

from linotp.lib.selftest import isSelfTest
from linotp.controllers.userservice import get_auth_user

from linotp.lib.token import newToken

from pylons.i18n.translation import _


import logging
log = logging.getLogger(__name__)

audit = config.get('audit')

ENCODING = "utf-8"

optional = True
required = False


log = logging.getLogger(__name__)
audit = config.get('audit')


def getTokenForUser(user):
    """
    should be moved to token.py
    """
    tokenArray = []

    log.debug("[getTokenForUser] iterating tokens for user...")
    log.debug("[getTokenForUser] ...user %s in realm %s." %
              (user.login, user.realm))
    tokens = getTokens4UserOrSerial(user=user, serial=None, _class=False)

    for token in tokens:
        tok = token.get_vars()
        if tok.get('LinOtp.TokenInfo', None):
            token_info = json.loads(tok.get('LinOtp.TokenInfo'))
            tok['LinOtp.TokenInfo'] = token_info
        tokenArray.append(tok)

    log.debug("[getTokenForUser] found tokenarray: %r" % tokenArray)
    return tokenArray


class SelfserviceController(BaseController):

    authUser = None

    def __before__(self, action):
        '''
        This is the authentication to self service
        If you want to do ANYTHING with selfservice, you need to be
        authenticated.  The _before_ is executed before any other function
        in this controller.
        '''

        try:

            param = request.params

            audit.initialize()
            c.audit['success'] = False
            c.audit['client'] = get_client()


            c.version = get_version()
            c.licenseinfo = get_copyright_info()
            if isSelfTest():
                log.debug("[__before__] Doing selftest!")
                uuser = getParam(param, "selftest_user", True)
                if uuser is not None:
                    (c.user, _foo, c.realm) = uuser.rpartition('@')
                else:
                    c.realm = ""
                    c.user = "--u--"
                    env = request.environ
                    uuser = env.get('REMOTE_USER')
                    if uuser is not None:
                        (c.user, _foo, c.realm) = uuser.rpartition('@')

                self.authUser = User(c.user, c.realm, '')
                log.debug("[__before__] authenticating as %s in realm %s!" % (c.user, c.realm))
            else:
                # Use WebAuth instead of LinOTP auth.
                identity = request.environ.get('REMOTE_USER')
                if identity is None:
					abort(401, "You are not authenticated")

                # Put their current realm as the first one we find them in.
                # Doesn't really matter since tokens are realm-independent.
                realms = getAllUserRealms(User(identity, "", ""))
                if (realms):
                    c.user = identity
                    c.realm = realms[0]

                self.authUser = User(c.user, c.realm, '')

                # Check token expiry.
            	age = int(request.environ.get('WEBAUTH_TOKEN_EXPIRATION')) - time.time()

                # Set selfservice cookie
            	response.set_cookie('linotp_selfservice', 'REMOTE_USER', max_age = int(age))

                # Set userservice auth cookie
                self.client = get_client()
                authcookie = create_auth_cookie(config, identity, self.client)
                response.set_cookie('userauthcookie', authcookie, max_age=360*24)

                log.debug("[__before__] set the self.authUser to: %s, %s " % (self.authUser.login, self.authUser.realm))
                log.debug('[__before__] param for action %s: %s' % (action, param))

                # checking the session
                if (False == check_selfservice_session(request.url,
                                                       request.path,
                                                       request.cookies,
                                                       request.params)):
                    c.audit['action'] = request.path[1:]
                    c.audit['info'] = "session expired"
                    audit.log(c.audit)
                    abort(401, "No valid session")

            c.imprint = get_imprint(c.realm)

            c.tokenArray = []

            c.user = self.authUser.login
            c.realm = self.authUser.realm
            c.tokenArray = getTokenForUser(self.authUser)

            # only the defined actions should be displayed
            # - remark: the generic actions like enrollTT are allready approved
            #   to have a rendering section and included
            actions = getSelfserviceActions(self.authUser)
            c.actions = actions
            for policy in actions:
                if "=" in policy:
                    (name, val) = policy.split('=')
                    val = val.strip()
                    # try if val is a simple numeric -
                    # w.r.t. javascript evaluation
                    try:
                        nval = int(val)
                    except:
                        nval = val
                    c.__setattr__(name.strip(), nval)

            c.dynamic_actions = add_dynamic_selfservice_enrollment(config,
                                                                   c.actions)

            # we require to establish all token local defined
            # policies to be initialiezd
            additional_policies = add_dynamic_selfservice_policies(config,
                                                                   actions)
            for policy in additional_policies:
                c.__setattr__(policy, -1)

            c.otplen = -1
            c.totp_len = -1

            return response

        except webob.exc.HTTPUnauthorized as acc:
            # the exception, when an abort() is called if forwarded
            log.info("[__before__::%r] webob.exception %r" % (action, acc))
            log.info("[__before__] %s" % traceback.format_exc())
            Session.rollback()
            Session.close()
            raise acc

        except Exception as e:
            log.error("[__before__] failed with error: %r" % e)
            log.error("[__before__] %s" % traceback.format_exc())
            Session.rollback()
            Session.close()
            return sendError(response, e, context='before')

        finally:
            log.debug('[__before__] done')

    def __after__(self, action,):
        '''

        '''
        param = request.params

        try:
            if c.audit['action'] in ['selfservice/index']:
                if isSelfTest():
                    log.debug("[__after__] Doing selftest!")
                    suser = getParam(param, "selftest_user", True)
                    if suser is not None:
                        (c.user, _foo, c.realm) = getParam(param,
                                                           "selftest_user",
                                                           True)\
                                                           .rpartition('@')
                    else:
                        c.realm = ""
                        c.user = "--ua--"
                        env = request.environ
                        uuser = env.get('REMOTE_USER')
                        realms = getAllUserRealms(User(uuser, "", ""))
                        if (realms):
                            c.user = uuser
                            c.realm = realms[0]
    ### This makes no sense...
    #                c.audit['user'] = c.user
    #                c.audit['realm'] =  c.realm
    #            else:
    #                user = getUserFromRequest(request).get("login")
    #                c.audit['user'] ,c.audit['realm'] = user.split('@')
    #                uc = user.split('@')
    #                c.audit['realm'] = uc[-1]
    #                c.audit['user'] = '@'.join(uc[:-1])

                log.debug("[__after__] authenticating as %s in realm %s!" % (c.user, c.realm))

                c.audit['user'] = c.user
                c.audit['realm'] = c.realm
                c.audit['success'] = True

                if 'serial' in param:
                    c.audit['serial'] = param['serial']
                    c.audit['token_type'] = getTokenType(param['serial'])

                audit.log(c.audit)

            return response

        except webob.exc.HTTPUnauthorized as acc:
            # the exception, when an abort() is called if forwarded
            log.error("[__after__::%r] webob.exception %r" % (action, acc))
            log.error("[__after__] %s" % traceback.format_exc())
            Session.rollback()
            Session.close()
            raise acc

        except Exception as e:
            log.error("[__after__] failed with error: %r" % e)
            log.error("[__after__] %s" % traceback.format_exc())
            Session.rollback()
            Session.close()
            return sendError(response, e, context='after')

        finally:
            log.debug('[__after__] done')

    def index(self):
        '''
        This is the redirect to the first template
        '''
        c.title = "LinOTP Self Service"
        ren = render('/selfservice/base.mako')
        return ren

    def load_form(self):
        '''
        This shows the enrollment form for a requested token type.

        implicit parameters are:

        :param type: token type
        :param scope: defines the rendering scope

        :return: rendered html of the requested token
        '''
        res = ''
        param = {}

        try:

            param.update(request.params)

            act = getParam(param, "type", required)
            try:
                (tok, section, scope) = act.split('.')
            except Exception:
                return res

            if section != 'selfservice':
                return res

            g = config['pylons.app_globals']
            tokenclasses = copy.deepcopy(g.tokenclasses)

            if tok in tokenclasses:
                tclass = tokenclasses.get(tok)
                tclt = newToken(tclass)
                if hasattr(tclt, 'getClassInfo'):
                    sections = tclt.getClassInfo(section, {})
                    if scope in sections.keys():
                        section = sections.get(scope)
                        page = section.get('page')
                        c.scope = page.get('scope')
                        c.authUser = self.authUser
                        html = page.get('html')
                        res = render(os.path.sep + html)
                        res = remove_empty_lines(res)

            Session.commit()
            return res

        except CompileException as exx:
            log.error("[load_form] compile error while processing %r.%r:" %
                                                                (tok, scope))
            log.error("[load_form] %r" % exx)
            log.error("[load_form] %s" % traceback.format_exc())
            Session.rollback()
            raise Exception(exx)

        except Exception as exx:
            Session.rollback()
            error = ('error (%r) accessing form data for: tok:%r, scope:%r'
                                ', section:%r' % (exx, tok, scope, section))
            log.error(error)
            log.error("[load_form] %s" % traceback.format_exc())
            return '<pre>%s</pre>' % error

        finally:
            Session.close()
            log.debug('[load_form] done')

    def custom_style(self):
        '''
        In case the user hasn't defined a custom css, Pylons calls this action.
        Return an empty file instead of a 404 (which would mean hitting the
        debug console)
        '''
        response.headers['Content-type'] = 'text/css'
        return ''

    def assign(self):
        '''
        In this form the user may assign an already existing Token to himself.
        For this, the user needs to know the serial number of the Token.
        '''
        return render('/selfservice/assign.mako')

    def resync(self):
        '''
        In this form, the user can resync an HMAC based OTP token
        by providing two OTP values
        '''
        return render('/selfservice/resync.mako')

    def reset(self):
        '''
        In this form the user can reset the Failcounter of the Token.
        '''
        return render('/selfservice/reset.mako')

    def getotp(self):
        '''
        In this form, the user can retrieve OTP values
        '''
        return render('/selfservice/getotp.mako')

    def disable(self):
        '''
        In this form the user may select a token of his own and
        disable this token.
        '''
        return render('/selfservice/disable.mako')

    def enable(self):
        '''
        In this form the user may select a token of his own and
        enable this token.
        '''
        return render('/selfservice/enable.mako')

    def unassign(self):
        '''
        In this form the user may select a token of his own and
        unassign this token.
        '''
        return render('/selfservice/unassign.mako')

    def delete(self):
        '''
        In this form the user may select a token of his own and
        delete this token.
        '''
        return render('/selfservice/delete.mako')


    def setpin(self):
        '''
        In this form the user may set the OTP PIN, which is the static password
        he enters when logging in in front of the otp value.
        '''
        return render('/selfservice/setpin.mako')

    def setmpin(self):
        '''
        In this form the user my set the PIN for his mOTP application soft
        token on his phone. This is the pin, he needs to enter on his phone,
        before a otp value will be generated.
        '''
        return render('/selfservice/setmpin.mako')

    def history(self):
        '''
        This is the form to display the history table for the user
        '''
        return render('/selfservice/history.mako')

    def webprovisionoathtoken(self):
        '''
        This is the form for an oathtoken to do web provisioning.
        '''
        return render('/selfservice/webprovisionoath.mako')

    def activateqrtoken(self):
        '''
        return the form for an qr token activation
        '''
        return render('/selfservice/activateqr.mako')

    def webprovisiongoogletoken(self):
        '''
        This is the form for an google token to do web provisioning.
        '''
        try:
            c.actions = getSelfserviceActions(self.authUser)
            return render('/selfservice/webprovisiongoogle.mako')
        except Exception as exx:
            log.error("[webprovisiongoogletoken] failed with error: %r" % exx)
            log.error("[webprovisiongoogletoken] %s" % traceback.format_exc())
            return sendError(response, exx)

        finally:
            log.debug('[webprovisiongoogletoken] done')

    def webprovisionelm(self):
        '''
        Form for Elm token adding. Basically a merged PIN and Google Authenticator form.
        '''
        return render('/selfservice/webprovisionelm.mako')

    def usertokenlist(self):
        '''
        This returns a tokenlist as html output
        '''
        res = render('/selfservice/tokenlist.mako')
        return res




#eof##########################################################################
