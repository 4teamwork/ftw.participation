from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests.layer import FTW_PARTICIPATION_INTEGRARION_TESTING
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase
from zope.interface import alsoProvides


class TestParticipation(TestCase):

    layer = FTW_PARTICIPATION_INTEGRARION_TESTING

    def setUp(self):
        super(TestParticipation, self).setUp()

        self.portal = self.layer['portal']
        self.portal_url = self.portal.portal_url()

        self.demo_folder = self.portal.get(self.portal.invokeFactory(
            'Folder', 'demo-folder'))
        alsoProvides(self.demo_folder, IParticipationSupport)

        self.view = self.demo_folder.restrictedTraverse('@@participants')

    def test_view_available(self):
        self.assertIsNotNone(self.view, 'Participants view is not available')

    def test_participants(self):
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('usera', 'secret',
                          properties={'username': 'usera',
                                      'fullname': 'Usera',
                                      'email': 'user@email.com'})

        self.portal.portal_membership.setLocalRoles(
            obj=self.demo_folder,
            member_ids=['usera', ],
            member_role="Reader",
            reindex=True)

        expect = [{'name': TEST_USER_ID,
                   'userid': TEST_USER_ID,
                   'readonly': True,
                   'roles': 'Owner'},
                  {'name': 'Usera (user@email.com)',
                   'userid': 'usera',
                   'readonly': False,
                   'roles': u'Can view'}, ]

        self.assertEquals(expect, self.view.get_participants())

    def test_get_pending_invitations(self):
        Invitation(
            target=self.demo_folder,
            email='user@email.com',
            inviter=TEST_USER_NAME,
            roles=['Reader'])

        expect = [dict(name='user@email.com',
                            roles=u'Can view',
                            inviter=TEST_USER_NAME)]

        self.assertEquals(expect, self.view.get_pending_invitations())
