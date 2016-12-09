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
        user = create(Builder('user').named(u'J\xf6hn', u'Doe')
                      .with_roles('Manager'))
        folder = create(Builder('folder').providing(IParticipationSupport))
        browser.login(user).open(folder, view='invite_participants')
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
                 'actor': 'john.doe',
                 'path': '/plone/folder',
                 'invitation:inviter': u'john.doe',
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
             'byline': u'Invitation created now by Doe J\xf6hn',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            u'Doe J\xf6hn has invited hugo@boss.com as Can add.',
            newest_event.body_text)

    @browsing
    def test_invitation_accepted_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named(u'J\xf6hn', u'Doe'))
        user = create(Builder('user').named(u'Hugo', u'B\xf6ss'))
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
             'byline': u'Invitation accepted now by B\xf6ss Hugo',
             'title': ''},
            newest_event.infos())

    @browsing
    def test_invitation_rejected_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named(u'J\xf6hn', u'Doe'))
        user = create(Builder('user').named(u'Hugo', u'B\xf6ss'))
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
             'byline': u'Invitation rejected now by B\xf6ss Hugo',
             'title': ''},
            newest_event.infos())

    @browsing
    def test_invitation_retracted_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named(u'J\xf6hn', u'Doe'))
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
             'byline': u'Invitation retracted now by Doe J\xf6hn',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            u'Doe J\xf6hn has retracted the invitation for foo@bar.com.',
            newest_event.body_text)

    @browsing
    def test_roles_changed_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))

        hugo = create(Builder('user').named(u'Hugo', u'B\xf6ss')
               .with_roles('Manager', on=folder))
        create(Builder('user').named(u'J\xf6hn', u'Doe')
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
             'byline': u'Role changed now by B\xf6ss Hugo',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            u'B\xf6ss Hugo has changed the role of Doe J\xf6hn'
            u' from Can edit to Can add.',
            newest_event.body_text)

    @browsing
    def test_local_role_removed(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        hugo = create(Builder('user').named(u'Hugo', u'B\xf6ss')
               .with_roles('Manager', on=folder))
        user = create(Builder('user').named(u'J\xf6hn', u'Doe')
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
             'byline': u'Participant removed now by B\xf6ss Hugo',
             'title': ''},
            newest_event.infos())
        self.assertEquals(
            u'B\xf6ss Hugo has removed the participant Doe J\xf6hn.',
            newest_event.body_text)
