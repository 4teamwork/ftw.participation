from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.participation.tests.pages import participants_view
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import plone
from ftw.testing.mailing import Mailing
from plone.app.testing import login
from unittest2 import TestCase
from zExceptions import Forbidden
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
                             .titled('The Folder')
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

    @browsing
    def test_owner_can_remove_participants(self, browser):
        hugo = create(Builder('user')
                      .named('Hugo', 'Boss')
                      .with_roles('Reader', on=self.folder))
        hugos_name = u'Boss Hugo (hugo@boss.com)'

        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        self.assertIn(hugos_name, participants_view.users_column())

        browser.fill({'userids:list': [hugo.getId()]})
        browser.find('Delete Participants').click()
        self.assertNotIn(hugos_name, participants_view.users_column())

    @browsing
    def test_owner_can_invite_new_users(self, browser):
        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        browser.find('Invite participants').click()
        self.assertEquals('invite_participants', plone.view())

    @browsing
    def test_cancel_redirects_to_default_view(self, browser):
        browser.login().visit(self.folder, view='participants')
        browser.find('Cancel').click()
        self.assertRegexpMatches(browser.url, r'/the-folder$')

    @browsing
    def test_checkboxes_only_visible_for_privileged_users(self, browser):
        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        self.assertTrue(participants_view.checkboxes_visible())

        hugo = create(Builder('user')
                      .named('Hugo', 'Boss')
                      .with_roles('Reader', on=self.folder))
        browser.login(hugo.getId()).visit(self.folder, view='participants')
        self.assertFalse(participants_view.checkboxes_visible())

    @browsing
    def test_delete_button_only_visible_for_privileged_users(self, browser):
        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        self.assertTrue(browser.find('Delete Participants'))

        hugo = create(Builder('user')
                      .named('Hugo', 'Boss')
                      .with_roles('Reader', on=self.folder))
        browser.login(hugo.getId()).visit(self.folder, view='participants')
        self.assertFalse(browser.find('Delete Participants'))

    @browsing
    def test_invite_link_only_visible_for_privileged_users(self, browser):
        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        self.assertTrue(browser.find('Invite participants'))

        hugo = create(Builder('user')
                      .named('Hugo', 'Boss')
                      .with_roles('Reader', on=self.folder))
        browser.login(hugo.getId()).visit(self.folder, view='participants')
        self.assertFalse(browser.find('Invite participants'))

    @browsing
    def test_unprivileged_users_cannot_delete_participants(self, browser):
        # This is a security test.
        # Since normal users do not see the UI for deletion, we use a
        # privileged user for renering the UI and switch to a non-privileged
        # user for sending the delete request.

        jane = create(Builder('user')
                      .named('Jane', 'Doe')
                      .with_roles('Reader', on=self.folder))

        hugo = create(Builder('user')
                      .named('Hugo', 'Boss')
                      .with_roles('Reader', on=self.folder))

        browser.login(self.john.getId()).visit(self.folder,
                                               view='participants')
        browser.fill({'userids:list': [jane.getId()]})
        browser.login(hugo.getId())

        with self.assertRaises(Forbidden):
            browser.find('Delete Participants').click()
