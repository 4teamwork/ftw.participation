from ftw.participation.interfaces import IInvitationStorage
from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.invitation import Invitation
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.participation.tests.pages import ParticipantsView
from ftw.testing.mailing import Mailing
from ftw.testing.pages import Plone
from unittest2 import TestCase
from zope.interface import alsoProvides
import transaction


class TestParticipantsView(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.folder = create(Builder('folder'))
        alsoProvides(self.folder, IParticipationSupport)
        Mailing(self.layer['portal']).set_up()
        transaction.commit()

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    def test_listing_shows_users_fullnames(self):
        hugo = create(Builder('user').named('Hugo', 'Boss'))
        self.folder.manage_setLocalRoles(hugo.getId(), ('Reader'))
        transaction.commit()

        Plone().login()
        ParticipantsView().visit_on(self.folder)
        self.assertIn('Boss Hugo (hugo@boss.com)',
                      ParticipantsView().participant_fullnames)

    def test_user_sorting_workws_with_umlauts_in_names(self):
        fraenzi = create(Builder('user').named('Fr\xc3\xa4nzi',
                                               'M\xc3\xbcller'))
        self.folder.manage_setLocalRoles(fraenzi.getId(), ('Reader'))

        juergen = create(Builder('user').named('J\xc3\xbcrgen',
                                               'R\xc3\xbcegsegger'))
        Invitation(target=self.folder,
                   email=juergen.getProperty('email'),
                   inviter=fraenzi.getId(),
                   roles=['Reader'])

        transaction.commit()

        Plone().login()
        ParticipantsView().visit_on(self.folder)
        self.assertEquals(['ja1-4rgen@ra1-4egsegger.com',
                           u'M\xfcLler Fr\xe4Nzi (fra-nzi@ma1-4ller.com)',
                           'test_user_1_'],
                          ParticipantsView().participant_fullnames)

    def test_user_with_umlaut_and_no_email_is_working(self):
        fraenzi = create(Builder('user')
                         .named('Fr\xc3\xa4nzi', 'M\xc3\xbcller'))
        fraenzi.setMemberProperties({'email': ''})
        self.folder.manage_setLocalRoles(fraenzi.getId(), ('Reader'))
        transaction.commit()

        Plone().login()
        ParticipantsView().visit_on(self.folder)
        self.assertEquals([u'M\xfcLler Fr\xe4Nzi',
                           'test_user_1_'],
                          ParticipantsView().participant_fullnames)
