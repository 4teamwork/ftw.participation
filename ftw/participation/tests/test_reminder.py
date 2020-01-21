from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IInvitationStorage
from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from ftw.testing.mailing import Mailing
from unittest import TestCase
from zope.interface import alsoProvides
import transaction


class TestReminder(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.folder = create(Builder('folder').titled('Folder'))
        alsoProvides(self.folder, IParticipationSupport)
        self.portal = self.layer['portal']
        Mailing(self.portal).set_up()
        transaction.commit()

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    @browsing
    def test_send_reminder_mail(self, browser):
        hugo = create(Builder('user').named('Hugo', 'Boss'))
        matthias = create(Builder('user')
                         .named('Matthias', 'Osswald'))

        create(Builder('invitation')
               .inviting(matthias)
               .to(self.folder)
               .invited_by(hugo))

        browser.login(self.hugo.getId()).visit(self.folder,
                                               view='participants')
        browser.css('td input').first.click()
        browser.find('Resend Invitations').click()

        mail = Mailing(portal).pop()
