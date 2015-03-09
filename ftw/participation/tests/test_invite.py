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
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.registry.interfaces import IRegistry
from unittest2 import TestCase
from zExceptions import NotFound
from zope.component import getUtility
from zope.interface import alsoProvides
import transaction


class TestInviteForm(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.folder = create(Builder('folder').titled('F\xc3\xb6lder'))
        alsoProvides(self.folder, IParticipationSupport)
        self.portal = self.layer['portal']
        Mailing(self.portal).set_up()
        transaction.commit()

    def tearDown(self):
        Mailing(self.portal).tear_down()

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
        self.portal.portal_properties.email_from_name = 'M\xc3\xa4i Site'
        transaction.commit()
        self.assertEquals([], self.get_invitations(email='hugo@boss.com'))

        browser.login().visit(self.folder, view='invite_participants')
        browser.fill({'E-Mail Addresses': 'hugo@boss.com',
                      'Roles': ['Contributor'],
                      'Comment': u'Hi th\xf6re'})
        browser.find('Invite').click()
        statusmessages.assert_no_error_messages()
        statusmessages.assert_message(
            'The invitation mails were sent to hugo@boss.com.')

        self.assertEquals(1, len(self.get_invitations(email='hugo@boss.com')),
                          'Expected one invitation to be available for hugo@boss.com')
        invitation, = self.get_invitations(email='hugo@boss.com')
        self.assertEquals(['Contributor'], invitation.roles)
        mail = Mailing(self.portal).pop()
        self.assertIn('From: =?utf-8?q?M=C3=A4i_Site?= <test@localhost>', mail)
        self.assertIn('To: hugo@boss.com', mail)
        self.assertIn('Content-Type: text/plain; charset="utf-8"', mail)
        self.assertIn('Content-Type: text/html; charset="utf-8"', mail)
        self.assertIn('=?utf-8?q?Invitation_for_paticipating_in_F=C3=B6lder?=',
                      mail)
        self.assertIn('Hi th=C3=B6re', mail)


    @browsing
    def test_query_users(self, browser):
        create(Builder('user').named('Hugo', 'Boss'))
        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals([['hugo.boss', 'Boss Hugo']],
                          browser.find('Users').query('Hugo'))

    @browsing
    def test_inviting_a_user_by_userid(self, browser):
        self.portal.portal_properties.email_from_name = 'M\xc3\xa4i Site'
        user = create(Builder('user').named('H\xc3\xbcgo', 'Boss'))
        self.assertEquals([], self.get_invitations(user=user))

        browser.login().visit(self.folder, view='invite_participants')
        browser.fill({'Users': [user.getId()],
                      'Roles': ['Contributor'],
                      'Comment': u'Hi th\xf6re'})
        browser.find('Invite').click()
        statusmessages.assert_no_error_messages()
        statusmessages.assert_message(
            'The invitation mails were sent to hugo@boss.com.')

        self.assertEquals(1, len(self.get_invitations(email='hugo@boss.com')),
                          'Expected one invitation to be available for hugo@boss.com')
        invitation, = self.get_invitations(email='hugo@boss.com')
        self.assertEquals(['Contributor'], invitation.roles)
        mail = Mailing(self.portal).pop()
        self.assertIn('From: =?utf-8?q?M=C3=A4i_Site?= <test@localhost>', mail)
        self.assertIn('To: hugo@boss.com', mail)
        self.assertIn('Content-Type: text/plain; charset="utf-8"', mail)
        self.assertIn('Content-Type: text/html; charset="utf-8"', mail)
        self.assertIn('=?utf-8?q?Invitation_for_paticipating_in_F=C3=B6lder?=',
                      mail)
        self.assertIn('Hi th=C3=B6re', mail)

    @browsing
    def test_get_invitations_from_context_providing_inavigationroot(
            self,
            browser):
        self.portal.portal_properties.email_from_name = 'M\xc3\xa4i Site'
        transaction.commit()

        subfolder = create(Builder('folder')
                           .within(self.portal)
                           .providing(INavigationRoot))

        user = create(Builder('user').named('H\xc3\xbcgo', 'Boss'))
        browser.login().visit(self.folder, view='invite_participants')
        browser.fill({'Users': [user.getId()],
                      'Roles': ['Contributor'],
                      'Comment': u'Hi th\xf6re'})
        browser.find('Invite').click()

        browser.login().visit(subfolder, view='invitations')
        self.assertEquals(
            ['hugo@boss.com'],
            browser.css('.invited-users-listing tbody .inv-user').text)

    def get_invitations(self, email=None, user=None):
        assert email or user, '"email" or "user" argument required'
        assert not (email and user), 'only one orgument of "email" and "user" allowed'
        if user:
            email = user.getProperty('email')

        self.layer['request'].SESSION = {}
        storage = IInvitationStorage(self.layer['portal'])
        return storage.get_invitations_for_email(email)

    @browsing
    def test_invite_raises_notfound_if_participation_isnt_possible(self, browser):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_invite_users = False
        config.allow_invite_email = False
        transaction.commit()

        with self.assertRaises(NotFound):
            browser.login().visit(self.folder, view='invite_participants')

    @browsing
    def test_invitation_only_by_users_is_possible(self, browser):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_invite_users = True
        config.allow_invite_email = False
        transaction.commit()

        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals(
            'Invite participants',
            browser.css('.documentFirstHeading').first.text
        )

    @browsing
    def test_invitation_only_by_email_is_possible(self, browser):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_invite_users = False
        config.allow_invite_email = True
        transaction.commit()

        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals(
            'Invite participants',
            browser.css('.documentFirstHeading').first.text
        )

    @browsing
    def test_invitation_by_users_and_email_is_possible(self, browser):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_invite_users = True
        config.allow_invite_email = True
        transaction.commit()

        browser.login().visit(self.folder, view='invite_participants')
        self.assertEquals(
            'Invite participants',
            browser.css('.documentFirstHeading').first.text
        )
