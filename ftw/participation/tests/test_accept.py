from ftw.participation.tests.layer import FTW_PARTICIPATION_INTEGRATION_TESTING
from unittest2 import TestCase
from plone.app.testing import login, setRoles
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.interfaces import IParticipationBrowserLayer
from ftw.participation.invitation import Invitation
from zope.interface import alsoProvides
from ftw.testing.mailing import Mailing
from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
import re


class TestInvitationAcceptmail(TestCase):

    layer = FTW_PARTICIPATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        alsoProvides(self.portal.REQUEST, IParticipationBrowserLayer)
        self.portal_url = self.portal.portal_url()




        create(Builder('user').named('Felix', 'Leiter').with_roles('Manager'))

        create(Builder('user').named('James', 'Bond').with_roles('Manager'))

        self.folder = create(Builder('folder'))

        login(self.portal, 'felix.leiter')

        alsoProvides(self.folder, IParticipationSupport)
        Mailing(self.layer['portal']).set_up()

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    def test_accept_mail(self):
        invitation = Invitation(target=self.folder,
                                email='felix@leiter.com',
                                inviter='james.bond',
                                roles=['Reader'])

        view = self.portal.restrictedTraverse('accept_invitation')
        view(iid=invitation.iid)
        mail = Mailing(self.portal).pop()
        self.assertIn('Content-Type: text/plain; charset="utf-8"', mail)
        self.assertIn('Content-Type: text/html; charset="utf-8"', mail)
        self.assertIn('Content-Type: text/html; charset="utf-8"', mail)
        regex = re.compile(r'Subject: =\?utf-?8\?q\?The_Invitation_to_participate_in_Plone_site_was_accepted_by_Lei')
        match = regex.search(mail)
        self.assertTrue(match)
        self.assertIn('To: =?utf-8?q?Bond_James?= <james@bond.com>', mail)
