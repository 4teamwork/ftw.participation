from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests.layer import FTW_PARTICIPATION_INTEGRATION_TESTING
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase
from zExceptions import Forbidden
from zope.interface import alsoProvides


class TestParticipation(TestCase):

    layer = FTW_PARTICIPATION_INTEGRATION_TESTING

    def setUp(self):
        super(TestParticipation, self).setUp()

        self.portal = self.layer['portal']
        self.portal_url = self.portal.portal_url()

        login(self.portal, TEST_USER_NAME)

        self.demo_folder = self.portal.get(self.portal.invokeFactory(
            'Folder', 'demo-folder'))
        alsoProvides(self.demo_folder, IParticipationSupport)

        self.view = self.demo_folder.restrictedTraverse('@@participants')
        self.layer['request'].set('ACTUAL_URL', '/'.join((
            self.demo_folder.absolute_url(), '@@participants')))

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
                   'roles': ['Owner'],
                   'inherited_roles': [],
                   'type_': 'userids'},
                  {'name': 'Usera (user@email.com)',
                   'userid': 'usera',
                   'inherited_roles': [],
                   'readonly': False,
                   'roles': [u'Can view'],
                   'type_': 'userids'}, ]

        self.assertEquals(expect, self.view.get_participants())

    def test_get_pending_invitations(self):
        invitation = Invitation(target=self.demo_folder,
                                email='user@email.com',
                                inviter=TEST_USER_NAME,
                                roles=['Reader'])

        expect = [dict(name='user@email.com',
                            roles=[u'Can view'],
                            inherited_roles=[],
                            inviter=invitation.inviter,
                            type_='invitations',
                            iid=invitation.iid,
                            readonly=True)]

        self.assertEquals(expect, self.view.get_pending_invitations())

    def test_sorted_result(self):
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('usera', 'secret',
                          properties={'username': 'usera',
                                      'fullname': '\xc3\x9csera',
                                      'email': 'user@email.com'})

        regtool.addMember('inviter', 'secret',
                          properties={'username': 'inviter',
                                      'fullname': 'invit\xc3\xb6r',
                                      'email': 'user@email.com'})

        self.demo_folder.manage_setLocalRoles('inviter', ['Owner'])

        Invitation(
            target=self.demo_folder,
            email='user@email.com',
            inviter=TEST_USER_NAME,
            roles=['Reader'])

        self.assertTrue(self.view.get_users())

    def test_readonly_user_cannot_remove_itself(self):
        self.assertTrue(self.view.get_participants()[0]['readonly'],
                        'The user should not be able to remove itself')

    def test_readonly_if_user_is_owner(self):
        user = create(Builder('user').with_roles('Owner', on=self.demo_folder))

        self.assertTrue(self.view.cannot_remove_user(user.getId()),
                        'It should not be possible to remove a owner')

    def test_not_readonly_if_only_local_roles_exists_and_no_user(self):
        userid = 'dummyid'
        self.demo_folder.manage_setLocalRoles(userid, ['Reader'])

        self.assertFalse(self.view.cannot_remove_user(userid),
                         'It should be possible to remove local roles if the '
                         'user does not longer exists')

    def test_readonly_if_not_inviter(self):
        Invitation(
            target=self.demo_folder,
            email='user@email.com',
            inviter='dummyuser',
            roles=['Reader'])

        self.assertTrue(self.view.get_pending_invitations(),
                        'It should no be possible to remove invitations if '
                        'the current user is not the inviter')

    def test_remove_user(self):
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

        assert len(self.view.get_participants()) == 2, 'Expect 2 participants'

        form = {'userids': ['usera'],
                'form.delete': True}

        self.view.request.form = form
        self.view()

        self.assertEquals(1,
                          len(self.view.get_participants()),
                          'Expect only one participant the owner')

    def test_remove_user_forbidden(self):
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

        logout()
        login(self.portal, 'usera')

        assert len(self.view.get_participants()) == 2, 'Expect 2 participants'

        form = {'userids': ['usera'],
                'form.delete': True}
        self.view.request.form = form

        self.assertRaises(Forbidden, self.view, *[])

    def test_remove_invitation(self):
        invitation = Invitation(target=self.demo_folder,
                                email='user@email.com',
                                inviter=TEST_USER_ID,
                                roles=['Reader'])

        assert len(self.view.get_pending_invitations()) == 1

        form = {'invitations': [invitation.iid],
                'form.delete': True}

        self.view.request.form = form
        self.view()

        self.assertEquals(0,
                          len(self.view.get_pending_invitations()),
                          'Expect no invitation')

    def test_remove_invitation_forbidden(self):
        invitation = Invitation(target=self.demo_folder,
                                email='user@email.com',
                                inviter='dummyuser',
                                roles=['Reader'])

        assert len(self.view.get_pending_invitations()) == 1

        form = {'invitations': [invitation.iid],
                'form.delete': True}

        self.view.request.form = form
        self.assertRaises(Forbidden, self.view, *[])

        self.assertEquals(1,
                          len(self.view.get_participants()),
                          'Expect one invitation')

    def test_participants_inherited_roles(self):

        folder = create(Builder('folder')
                        .titled('Folder'))

        subfolder = create(Builder('folder')
                           .within(folder)
                           .titled('Subfolder')
                           .providing(IParticipationSupport))

        create(Builder('user')
               .named('Hugo', 'Boss')
               .with_roles('Reader', on=folder)
               .with_roles('Contributor', on=subfolder))

        expect = [{'name': u'Boss Hugo (hugo@boss.com)',
                   'userid': 'hugo.boss',
                   'readonly': False,
                   'roles': [u'Can add', u'Can view'],
                   'inherited_roles': [u'Can view'],
                   'type_': 'userids'},
                  {'name': unicode(TEST_USER_ID),
                   'userid': TEST_USER_ID,
                   'readonly': True,
                   'roles': ['Owner'],
                   'inherited_roles': [],
                   'type_': 'userids'}, ]

        view = subfolder.restrictedTraverse('@@participants')
        self.maxDiff = None
        self.assertEquals(expect, view.get_participants())

    def test_participants_inherited_roles_not_acquired(self):

        folder = create(Builder('folder')
                        .titled('Folder'))

        subfolder = create(Builder('folder')
                           .within(folder)
                           .titled('Subfolder')
                           .providing(IParticipationSupport))
        setattr(subfolder, '__ac_local_roles_block__', True)

        create(Builder('user')
               .named('Hugo', 'Boss')
               .with_roles('Reader', on=folder)
               .with_roles('Contributor', on=subfolder))

        expect = [{'name': u'Boss Hugo (hugo@boss.com)',
                   'userid': 'hugo.boss',
                   'readonly': False,
                   'roles': [u'Can add'],
                   'inherited_roles': [],
                   'type_': 'userids'},
                  {'name': unicode(TEST_USER_ID),
                   'userid': TEST_USER_ID,
                   'readonly': True,
                   'roles': ['Owner'],
                   'inherited_roles': [],
                   'type_': 'userids'}, ]

        view = subfolder.restrictedTraverse('@@participants')
        self.maxDiff = None
        self.assertEquals(expect, view.get_participants())

    def test_participants_show_only_inherited_roles(self):

        folder = create(Builder('folder')
                        .titled('Folder'))

        subfolder = create(Builder('folder')
                           .within(folder)
                           .titled('Subfolder')
                           .providing(IParticipationSupport))

        create(Builder('user')
               .named('Hugo', 'Boss')
               .with_roles('Contributor', on=folder))

        expect = [{'name': u'Boss Hugo (hugo@boss.com)',
                   'userid': 'hugo.boss',
                   'readonly': False,
                   'roles': [u'Can add'],
                   'inherited_roles': [u'Can add'],
                   'type_': 'userids'},
                  {'name': unicode(TEST_USER_ID),
                   'userid': TEST_USER_ID,
                   'readonly': True,
                   'roles': ['Owner'],
                   'inherited_roles': [],
                   'type_': 'userids'}, ]

        view = subfolder.restrictedTraverse('@@participants')
        self.maxDiff = None
        self.assertEquals(expect, view.get_participants())

    def test_participants_do_not_show_inherited_owner_role(self):

        folder = create(Builder('folder')
                        .titled('Folder'))

        subfolder = create(Builder('folder')
                           .within(folder)
                           .titled('Subfolder')
                           .providing(IParticipationSupport))
        del subfolder.__ac_local_roles__[TEST_USER_ID]
        subfolder._p_changed=True

        subfolder.manage_setLocalRoles(TEST_USER_ID, ['Editor'])

        expect = [{'name': unicode(TEST_USER_ID),
                   'userid': TEST_USER_ID,
                   'readonly': True,
                   'roles': ['Can edit'],
                   'inherited_roles': [],
                   'type_': 'userids'}, ]

        view = subfolder.restrictedTraverse('@@participants')
        self.maxDiff = None
        self.assertEquals(expect, view.get_participants())

    def test_exclude_inherited_users_without_roles(self):

        folder = create(Builder('folder')
                        .titled('Folder'))

        subfolder = create(Builder('folder')
                           .within(folder)
                           .titled('Subfolder')
                           .providing(IParticipationSupport))
        del subfolder.__ac_local_roles__[TEST_USER_ID]
        subfolder._p_changed=True

        expect = []
        view = subfolder.restrictedTraverse('@@participants')
        self.maxDiff = None
        self.assertEquals(expect, view.get_participants())
