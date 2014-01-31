from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.participation.tests.layer import TEST_USER_ID_2, TEST_USER_PW_2
from plone.testing.z2 import Browser
from unittest2 import TestCase
from ftw.participation.invitation import Invitation
import transaction


class TestInvitation(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        super(TestInvitation, self).setUp()

        self.portal = self.layer['portal']
        self.portal_url = self.portal.portal_url()

        self.demo_folder = self.portal.get(self.portal.invokeFactory(
            'Folder', 'demo-folder'))
        transaction.commit()

        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False

    def test_userid_differ_userlogin(self):
        member = self.portal.portal_membership.getMemberById(TEST_USER_ID_2)
        member.setMemberProperties({'email':'foo@bar.com'})
        inv1 = Invitation(target=self.demo_folder, email='foo@bar.com', inviter='admin',
                          roles=['Reader'])
        url = '%s/@@invitations?iid=%s' % (self.portal_url, inv1.iid)
        transaction.commit()
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (
            TEST_USER_ID_2, TEST_USER_PW_2, ))

        self.browser.open(url)
        self.assertIn('Invitations', self.browser.contents)
