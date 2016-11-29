from ftw.activity.tests.helpers import get_soup_activities
from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests import FunctionalTestCase
from ftw.testbrowser import browsing
import transaction



class TestActivity(FunctionalTestCase):

    @browsing
    def test_invitation_created_activity(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        browser.login().open(folder, view='invite_participants')
        browser.fill({'E-Mail Addresses': 'hugo@boss.com',
                      'Roles': ['Contributor'],
                      'Comment': u'Hi th\xf6re'})
        browser.find('Invite').click()

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:invitation_created',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder',
                 'invitation:inviter': u'test_user_1_',
                 'invitation:email': u'hugo@boss.com',
                 'invitation:roles': (u'Contributor',),
                 'invitation:comment': u'Hi th\xf6re',
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'invitation:inviter',
                                 'invitation:email',
                                 'invitation:roles',
                                 'invitation:comment')))

    @browsing
    def test_invitation_accepted_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named('John', 'Doe'))
        user = create(Builder('user').named('Hugo', 'Boss'))
        Invitation(target=folder,
                   email=user.getProperty('email'),
                   inviter=inviter.getId(),
                   roles=['Reader'])
        transaction.commit()

        browser.login(user).open(view='invitations')
        browser.click_on("Yes, I'd like to participate")

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:invitation_accepted',
                 'actor': 'hugo.boss',
                 'path': '/plone/folder',
                 'invitation:inviter': 'john.doe',
                 'invitation:email': 'hugo@boss.com',
                 'invitation:roles': ('Reader',),
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'invitation:inviter',
                                 'invitation:email',
                                 'invitation:roles',)))

    @browsing
    def test_invitation_rejected_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named('John', 'Doe'))
        user = create(Builder('user').named('Hugo', 'Boss'))
        Invitation(target=folder,
                   email=user.getProperty('email'),
                   inviter=inviter.getId(),
                   roles=['Reader'])
        transaction.commit()

        browser.login(user).open(view='invitations')
        browser.click_on("No, I reject the invitation")

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:invitation_rejected',
                 'actor': 'hugo.boss',
                 'path': '/plone/folder',
                 'invitation:inviter': 'john.doe',
                 'invitation:email': 'hugo@boss.com',
                 'invitation:roles': ('Reader',),
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'invitation:inviter',
                                 'invitation:email',
                                 'invitation:roles',)))

    @browsing
    def test_invitation_retracted_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named('John', 'Doe'))
        invitation = Invitation(target=folder,
                                email='foo@bar.com',
                                inviter=inviter.getId(),
                                roles=['Reader'])
        transaction.commit()

        browser.login(inviter).open(view='invitations')
        browser.fill({'sent_invitations:list': invitation.iid})
        browser.click_on('Retract')

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:invitation_retracted',
                 'actor': 'john.doe',
                 'path': '/plone/folder',
                 'invitation:inviter': 'john.doe',
                 'invitation:email': 'foo@bar.com',
                 'invitation:roles': ('Reader',),
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'invitation:inviter',
                                 'invitation:email',
                                 'invitation:roles',)))

    @browsing
    def test_roles_changed_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))

        create(Builder('user').named('John', 'Doe')
               .with_roles('Editor', on=folder))

        browser.login().open(folder, view='participants')
        browser.click_on('change')
        # Only Editor and Contributor are selectable
        browser.fill({'Roles': ['Contributor']}).submit()

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:role_changed',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder',
                 'roles:userid': 'john.doe',
                 'roles:old': ('Editor',),
                 'roles:removed': ('Editor',),
                 'roles:new': ('Contributor',),
                 'roles:added': ('Contributor',),
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'roles:userid',
                                 'roles:old',
                                 'roles:removed',
                                 'roles:new',
                                 'roles:added')))

    @browsing
    def test_local_role_removed(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        user = create(Builder('user').named('John', 'Doe')
                      .with_roles('Editor', on=folder))

        browser.login().open(folder, view='participants')
        browser.fill({'userids:list': [user.getId()]}) \
               .find('Delete Participants').click()

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:role_removed',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder',
                 'roles:userid': 'john.doe',
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'roles:userid')))
