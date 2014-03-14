from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests.layer import FTW_PARTICIPATION_INTEGRATION_TESTING
from ftw.testing.mailing import Mailing
from plone.app.testing import login
from unittest2 import TestCase
from zope.interface import alsoProvides
import email


class TestAcceptInvitation(TestCase):

    layer = FTW_PARTICIPATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.folder = create(Builder('folder'))
        alsoProvides(self.folder, IParticipationSupport)

        create(Builder('user').named('Felix', 'Leiter'))
        create(Builder('user').named('James', 'Bond'))

        Mailing(self.layer['portal']).set_up()

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

        self.assertRegexpMatches(
            message.get('Subject'),
            r'^=\?utf-?8\?q\?The_Invitation_to_')
