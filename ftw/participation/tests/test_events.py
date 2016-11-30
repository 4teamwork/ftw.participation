from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IInvitationAcceptedEvent
from ftw.participation.interfaces import IInvitationCreatedEvent
from ftw.participation.interfaces import IInvitationRejectedEvent
from ftw.participation.interfaces import IInvitationRetractedEvent
from ftw.participation.interfaces import ILocalRoleRemoved
from ftw.participation.interfaces import IParticipationEvent
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.interfaces import IRolesChangedEvent
from ftw.participation.invitation import Invitation
from ftw.participation.tests import FunctionalTestCase
from ftw.testbrowser import browsing
import transaction


EVENTS = []

def record_event(event):
    EVENTS.append(event)


class TestEvents(FunctionalTestCase):

    def setUp(self):
        super(TestEvents, self).setUp()
        EVENTS[:] = []
        self.portal.getSiteManager().registerHandler(
            factory=record_event,
            required=(IParticipationEvent,))

    def tearDown(self):
        super(TestEvents, self).tearDown()
        self.portal.getSiteManager().unregisterHandler(
            factory=record_event,
            required=(IParticipationEvent,))

    @browsing
    def test_invitation_created_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        browser.login().open(folder, view='invite_participants')
        browser.fill({'E-Mail Addresses': 'hugo@boss.com',
                      'Roles': ['Contributor'],
                      'Comment': u'Hi th\xf6re'})
        browser.find('Invite').click()

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IInvitationCreatedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('hugo@boss.com', event.invitation.email)
        self.assertEquals(u'Hi th\xf6re', event.comment)

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

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IInvitationAcceptedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('hugo@boss.com', event.invitation.email)

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

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IInvitationRejectedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('hugo@boss.com', event.invitation.email)

    @browsing
    def test_invitation_retracted_event_on_invitations_view(self, browser):
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

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IInvitationRetractedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('foo@bar.com', event.invitation.email)

    @browsing
    def test_invitation_retracted_event_on_participants_view(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        inviter = create(Builder('user').named('John', 'Doe')
                         .with_roles('Manager', on=folder))
        invitation = Invitation(target=folder,
                                email='foo@bar.com',
                                inviter=inviter.getId(),
                                roles=['Reader'])
        transaction.commit()

        browser.login(inviter).open(folder, view='participants')
        browser.fill({'invitations:list': invitation.iid})
        browser.click_on('Delete Participants')

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IInvitationRetractedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('foo@bar.com', event.invitation.email)

    @browsing
    def test_roles_changed_event(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        create(Builder('user').named('John', 'Doe')
               .with_roles('Editor', on=folder))

        browser.login().open(folder, view='participants')
        browser.click_on('change')
        browser.fill({'Roles': ['Contributor']}).submit()

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(IRolesChangedEvent.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('john.doe', event.userid)
        self.assertEquals(['Editor'], event.old_roles)
        self.assertEquals(['Contributor'], event.new_roles)

    @browsing
    def test_local_role_removed(self, browser):
        self.grant('Manager')
        folder = create(Builder('folder').providing(IParticipationSupport))
        user = create(Builder('user').named('John', 'Doe')
                      .with_roles('Editor', on=folder))

        browser.login().open(folder, view='participants')
        browser.fill({'userids:list': [user.getId()]}) \
               .find('Delete Participants').click()

        self.assertEquals(1, len(EVENTS), 'Expected 1 event to be fired.')
        event, = EVENTS
        self.assertTrue(ILocalRoleRemoved.providedBy(event))
        self.assertEquals(folder.getPhysicalPath(),
                          event.object.getPhysicalPath())
        self.assertEquals('john.doe', event.userid)
