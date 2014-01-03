from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IInvitationStorage
from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.participation.tests.pages import inviteform
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from ftw.testing.mailing import Mailing
from plone.registry.interfaces import IRegistry
from unittest2 import TestCase
from zope.component import getUtility
from zope.interface import alsoProvides
import transaction


class TestInviteForm(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.folder = create(Builder('folder'))
        alsoProvides(self.folder, IParticipationSupport)
        Mailing(self.layer['portal']).set_up()
        transaction.commit()

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    @browsing
    def test_multiple_roles_selectable(self, browser):
        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals(['checkbox'], inviteform.roles_input_types())

    @browsing
    def test_only_one_role_selectable_by_configuration_setting(self, browser):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_multiple_roles = False
        transaction.commit()

        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals(['radio'], inviteform.roles_input_types())

    @browsing
    def test_inviting_a_user_by_email(self, browser):
        self.assertEquals([], self.get_invitations(email='hugo@boss.com'))

        browser.login().visit(self.folder, view='invite_participants')
        browser.fill({'E-Mail Addresses': 'hugo@boss.com',
                      'Roles': ['Contributor'],
                      'Comment': 'Hi there'})
        browser.find('Invite').click()
        statusmessages.assert_no_error_messages()
        statusmessages.assert_message(
            'The invitation mails were sent to hugo@boss.com.')

        self.assertEquals(1, len(self.get_invitations(email='hugo@boss.com')),
                          'Expected one invitation to be available for hugo@boss.com')
        invitation, = self.get_invitations(email='hugo@boss.com')
        self.assertEquals(['Contributor'], invitation.roles)

    @browsing
    def test_query_users(self, browser):
        create(Builder('user').named('Hugo', 'Boss'))
        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals([['hugo.boss', 'Boss Hugo']],
                          browser.find('Users').query('Hugo'))

    @browsing
    def test_inviting_a_user_by_userid(self, browser):
        user = create(Builder('user').named('Hugo', 'Boss'))
        self.assertEquals([], self.get_invitations(user=user))

        browser.login().visit(self.folder, view='invite_participants')
        browser.fill({'Users': [user.getId()],
                      'Roles': ['Contributor'],
                      'Comment': 'Join us'})
        browser.find('Invite').click()
        statusmessages.assert_no_error_messages()
        statusmessages.assert_message(
            'The invitation mails were sent to hugo@boss.com.')

        self.assertEquals(1, len(self.get_invitations(email='hugo@boss.com')),
                          'Expected one invitation to be available for hugo@boss.com')
        invitation, = self.get_invitations(email='hugo@boss.com')
        self.assertEquals(['Contributor'], invitation.roles)

    def get_invitations(self, email=None, user=None):
        assert email or user, '"email" or "user" argument required'
        assert not (email and user), 'only one orgument of "email" and "user" allowed'
        if user:
            email = user.getProperty('email')

        self.layer['request'].SESSION = {}
        storage = IInvitationStorage(self.layer['portal'])
        return storage.get_invitations_for_email(email)