from ftw.activity.tests.helpers import get_soup_activities
from ftw.activity.tests.pages import activity
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

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Invitation created now by test_user_1_',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            'test_user_1_ has invited hugo@boss.com as Can add.',
            newest_event.body_text)

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

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Invitation accepted now by Boss Hugo',
             'title': ''},
            newest_event.infos())

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

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Invitation rejected now by Boss Hugo',
             'title': ''},
            newest_event.infos())

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

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Invitation retracted now by Doe John',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            'Doe John has retracted the invitation for foo@bar.com.',
            newest_event.body_text)

    @browsing
    def test_roles_changed_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))

        hugo = create(Builder('user').named('Hugo', 'Boss')
               .with_roles('Manager', on=folder))
        create(Builder('user').named('John', 'Doe')
               .with_roles('Editor', on=folder))

        browser.login(hugo).open(folder, view='participants')
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
                 'actor': 'hugo.boss',
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

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Role changed now by Boss Hugo',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            'Boss Hugo has changed the role of Doe John'
            ' from Can edit to Can add.',
            newest_event.body_text)

    @browsing
    def test_local_role_removed(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        hugo = create(Builder('user').named('Hugo', 'Boss')
               .with_roles('Manager', on=folder))
        user = create(Builder('user').named('John', 'Doe')
                      .with_roles('Editor', on=folder))

        browser.login(hugo).open(folder, view='participants')
        browser.fill({'userids:list': [user.getId()]}) \
               .find('Delete Participants').click()

        self.maxDiff = None
        self.assertEquals(
            [
                {'action': 'added',
                 'actor': 'test_user_1_',
                 'path': '/plone/folder'},

                {'action': 'participation:role_removed',
                 'actor': 'hugo.boss',
                 'path': '/plone/folder',
                 'roles:userid': 'john.doe',
                },
            ],

            get_soup_activities(('path',
                                 'action',
                                 'actor',
                                 'roles:userid')))

        browser.open(folder, view='@@activity')
        newest_event = activity.events()[0]
        self.assertEquals(
            {'url': 'http://nohost/plone/folder',
             'byline': 'Participant removed now by Boss Hugo',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            'Boss Hugo has removed the participant Doe John.',
            newest_event.body_text)
