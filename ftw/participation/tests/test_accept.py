from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests import layer
from ftw.testing.mailing import Mailing
from plone.app.testing import login
from plone.registry.interfaces import IRegistry
from unittest2 import TestCase
from zope.component import getUtility
from zope.interface import alsoProvides
import email


class TestAcceptInvitation(TestCase):

    layer = layer.FTW_PARTICIPATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.folder = create(Builder('folder'))
        alsoProvides(self.folder, IParticipationSupport)

        create(Builder('user').named('Felix', 'Leiter'))
        create(Builder('user').named('James', 'Bond'))

        Mailing(self.layer['portal']).set_up()
        
        self.portal.manage_changeProperties(
            {'email_from_name': 'Plone Admin',
             'email_from_address': 'plone@plone.local'})
             

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    def test_accept_confirmation_mail_encodings(self):
        invitation = Invitation(target=self.folder,
                                email='felix@leiter.com',
                                inviter='james.bond',
                                roles=['Reader'])

        login(self.portal, 'felix.leiter')
        view = self.portal.restrictedTraverse('accept_invitation')
        view(iid=invitation.iid)
        message = email.message_from_string(Mailing(self.portal).pop())

        self.assertItemsEqual(['text/plain; charset="utf-8"',
                               'text/html; charset="utf-8"'],
                              [payload.get('Content-Type')
                               for payload in message.get_payload()])

        self.assertEquals('=?utf-8?q?Bond_James?= <james@bond.com>',
                          message.get('To'))

        self.assertEquals('=?utf-8?q?Plone_Admin?= <plone@plone.local>',
                          message.get('From'))

        self.assertRegexpMatches(
            message.get('Subject'),
            r'^=\?utf-?8\?q\?The_Invitation_to_')

    def test_accepting_sets_roles_on_context(self):
        login(self.portal, 'james.bond')
        invitation = Invitation(target=self.folder,
                                email='felix@leiter.com',
                                inviter='james.bond',
                                roles=['Reader', 'Contributor'])

        login(self.portal, 'felix.leiter')
        view = self.portal.restrictedTraverse('accept_invitation')
        view(iid=invitation.iid)

        self.assertItemsEqual(
            ['Reader', 'Contributor'],
            dict(self.folder.get_local_roles()).get('felix.leiter'))

    def test_Reader_role_is_added_by_default(self):
        login(self.portal, 'james.bond')
        invitation = Invitation(target=self.folder,
                                email='felix@leiter.com',
                                inviter='james.bond',
                                roles=['Contributor'])

        login(self.portal, 'felix.leiter')
        view = self.portal.restrictedTraverse('accept_invitation')
        view(iid=invitation.iid)

        self.assertItemsEqual(
            ['Reader', 'Contributor'],
            dict(self.folder.get_local_roles()).get('felix.leiter'))

    def test_Reader_role_is_not_added_when_multiple_roles_disabled(self):
        # When allow_multiple_roles is disabled (default is enabled), we
        # only want to have one single role set.
        # In this case the default Reader role should not be appended,
        # otherwise we would have multiple roles against the configuration,
        # producing problems such as when changing roles with
        # radio buttons.

        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_multiple_roles = False

        login(self.portal, 'james.bond')
        invitation = Invitation(target=self.folder,
                                email='felix@leiter.com',
                                inviter='james.bond',
                                roles=['Contributor'])

        login(self.portal, 'felix.leiter')
        view = self.portal.restrictedTraverse('accept_invitation')
        view(iid=invitation.iid)

        self.assertItemsEqual(
            ['Contributor'],
            dict(self.folder.get_local_roles()).get('felix.leiter'))
