from plone.app.testing import login
from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.participation.tests.pages import participants_view
from ftw.testbrowser import browsing
from ftw.testing.mailing import Mailing
from unittest2 import TestCase
import transaction


class TestParticipantsView(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        Mailing(self.layer['portal']).set_up()
        self.john = create(Builder('user')
                           .named('John', 'Doe')
                           .with_roles('Contributor'))

        login(self.layer['portal'], self.john.getId())
        self.folder = create(Builder('folder')
                             .providing(IParticipationSupport))

    def tearDown(self):
        Mailing(self.layer['portal']).tear_down()

    @browsing
    def test_participants_are_listed_in_table(self, browser):
        create(Builder('user')
               .named('Hugo', 'Boss')
               .with_roles('Reader', 'Contributor', on=self.folder))

        browser.login().visit(self.folder, view='participants')
        self.assertIn({u'': '',
                       u'User': u'Boss Hugo (hugo@boss.com)',
                       u'Roles': u'Can view, Can add',
                       u'Invited by': u'',
                       u'Status': u'Accepted'},
                      participants_view.table())

    @browsing
    def test_invitations_are_listed_in_table(self, browser):
        hugo = create(Builder('user').named('Hugo', 'Boss'))
        fraenzi = create(Builder('user')
                         .named('Fr\xc3\xa4nzi', 'M\xc3\xbcller'))

        create(Builder('invitation')
               .inviting(fraenzi)
               .to(self.folder)
               .invited_by(hugo))

        browser.login().visit(self.folder, view='participants')
        self.assertIn({u'': '',
                       'User': 'franzi@muller.com',
                       'Roles': 'Can view',
                       'Invited by': 'Boss Hugo',
                       'Status': 'Pending'},
                      participants_view.table())

    @browsing
    def test_user_sorting_works_with_umlauts_in_names(self, browser):
        fraenzi = create(Builder('user')
                         .named('Fr\xc3\xa4nzi', 'M\xc3\xbcller')
                         .with_roles('Reader', on=self.folder))

        juergen = create(Builder('user')
                         .named('J\xc3\xbcrgen', 'R\xc3\xbcegsegger'))

        create(Builder('invitation')
               .inviting(juergen)
               .to(self.folder)
               .invited_by(fraenzi))

        browser.login().visit(self.folder, view='participants')
        self.assertEquals([u'Doe John (john@doe.com)',
                           u'jurgen@ruegsegger.com',
                           u'M\xfcLler Fr\xe4Nzi (franzi@muller.com)'],
                          participants_view.users_column())

    @browsing
    def test_user_with_umlaut_and_no_email_is_working(self, browser):
        fraenzi = create(Builder('user')
                         .named('Fr\xc3\xa4nzi', 'M\xc3\xbcller')
                         .with_roles('Reader', on=self.folder))
        fraenzi.setMemberProperties({'email': ''})
        transaction.commit()

        browser.login().visit(self.folder, view='participants')
        self.assertEquals([u'Doe John (john@doe.com)',
                           u'M\xfcLler Fr\xe4Nzi'],
                          participants_view.users_column())
