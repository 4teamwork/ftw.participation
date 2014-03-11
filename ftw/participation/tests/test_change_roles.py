from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from unittest2 import TestCase
from zExceptions import BadRequest


class TestParticipantsView(TestCase):

    layer = FTW_PARTICIPATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.folder = create(Builder('folder')
                             .titled('The Folder')
                             .providing(IParticipationSupport))

    @browsing
    def test_change_local_roles(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', on=self.folder))

        data = {'form.widgets.memberid': john.getId()}
        browser.login().visit(self.folder, view='change_roles', data=data)

        browser.fill(
            {'form.widgets.roles:list': ['Contributor', 'Editor']}).submit()
        self.assertEquals(
            '{0}/@@participants'.format(self.folder.absolute_url()),
            browser.url)

        browser.open(self.folder, view='@@participants')
        table = browser.css('table.listing').first.lists()
        self.assertEquals('Can view, Can add, Can edit', table[1][2])

    @browsing
    def test_form_with_default_value(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', 'Contributor', on=self.folder))

        data = {'form.widgets.memberid': john.getId()}
        browser.login().visit(self.folder, view='change_roles', data=data)

        self.assertEquals('Contributor',
                          browser.css('[checked="checked"]').first.value)

    @browsing
    def test_remove_all_roles_user_should_be_still_reader(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', 'Contributor', 'Editor',
                                  on=self.folder))

        data = {'form.widgets.memberid': john.getId()}
        browser.login().visit(self.folder, view='change_roles', data=data)
        browser.fill(
            {'form.widgets.roles:list': []}).submit()

        browser.open(self.folder, view='@@participants')
        table = browser.css('table.listing').first.lists()
        self.assertEquals('Can view', table[1][2])

    @browsing
    def test_raise_bad_request_if_no_memberid_is_given(self, browser):
        with self.assertRaises(BadRequest):
            browser.login().visit(self.folder, view='change_roles')

    @browsing
    def test_raise_bad_request_if_no_valid_memberid_is_given(self, browser):
        with self.assertRaises(BadRequest):
            data = {'form.widgets.memberid': 'invalid_member_id'}
            browser.login().visit(self.folder, view='change_roles', data=data)

    @browsing
    def test_show_change_link_if_user_can_change_local_roles(self, browser):
        create(Builder('user')
               .named('John', 'Doe')
               .with_roles('Member')
               .with_roles('Reader', 'Contributor', 'Editor',
                           on=self.folder))

        browser.login().visit(self.folder, view='@@participants')

        self.assertEquals('change',
                          browser.css('table').first.lists()[1][-1])
        self.assertEquals('change',
                          browser.css('a.ChangeRoles').first.text,
                          'Expect a change link')

    @browsing
    def test_do_not_show_change_link(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', on=self.folder))

        browser.login(john.getId()).visit(self.folder, view='@@participants')
        self.assertFalse(browser.css('a.ChangeRoles'),
                         'Do not expect a change link.')
