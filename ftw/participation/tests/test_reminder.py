from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from ftw.testing.mailing import Mailing
from plone.app.testing import login
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone import api
from unittest import TestCase
import transaction


class TestReminder(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):

        self.portal = self.layer['portal']
        Mailing(self.portal).set_up()
        transaction.commit()

        self.folder = create(Builder('folder')
                             .titled(u'The F\xf6lder')
                             .providing(IParticipationSupport))

        self.inviter = api.user.get(userid=TEST_USER_ID)
        self.grant('Manager')

    def grant(self, *roles):
        setRoles(self.portal, TEST_USER_ID, list(roles))
        transaction.commit()

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    @browsing
    def test_send_reminder_mail(self, browser):

        hugo = create(Builder('user')
                          .named(u'Hugo', u'B\xf6ss'))

        create(Builder('invitation')
               .inviting(hugo)
               .to(self.folder)
               .invited_by(self.inviter))

        browser.login()
        browser.visit(self.folder, view='participants')
        browser.fill({
            'invitations:list': True
        })
        browser.find('Resend Invitations').click()

        mail = Mailing(self.portal).pop()
        self.assertIn("hugo@boss.com", mail)
        self.assertIn("This is a reminder.", mail)

    @browsing
    def test_no_user_selected(self, browser):

        browser.login()
        browser.visit(self.folder, view='participants')

        browser.find('Resend Invitations').click()

        mails = Mailing(self.portal)
        self.assertEqual(len(mails.get_messages()), 0)
