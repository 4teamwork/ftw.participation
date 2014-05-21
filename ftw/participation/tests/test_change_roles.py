from ftw.builder import Builder
from ftw.builder import create
from ftw.participation.interfaces import IParticipationSupport
from ftw.participation.tests.layer import FTW_PARTICIPATION_FUNCTIONAL_TESTING
from ftw.testbrowser import browsing
from unittest2 import TestCase
from zExceptions import BadRequest
import transaction


class TestChangeRoles(TestCase):

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
        self.assertEquals('Can add, Can edit, Can view', table[1][2])

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
    def test_do_not_remove_unmanaged_roles(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', 'Contributor', 'Editor',
                                  on=self.folder))

        self.folder.manage_permission(
            'Sharing page: Delegate Reader role',
            roles=[],
            acquire=False)
        transaction.commit()

        data = {'form.widgets.memberid': john.getId()}
        browser.login().visit(self.folder, view='change_roles', data=data)
        browser.fill(
            {'form.widgets.roles:list': []}).submit()

        self.assertIn(('john.doe', ('Reader', )),
                      self.folder.get_local_roles(),
                      'john should be still Reader')

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

    @browsing
    def test_change_role_view_respects_the_delegate_permissions(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Reader', on=self.folder))

        # Remove delegate contributor role permission
        self.layer['portal'].manage_permission(
            'Sharing page: Delegate Contributor role',
            roles=[],
            acquire=False)
        transaction.commit()

        data = {'form.widgets.memberid': john.getId()}
        browser.login().visit(self.folder, view='change_roles', data=data)

        checkboxes = browser.css('#content input[type="checkbox"]')
        self.assertEquals(1, len(checkboxes), 'Expect only one checkbox')
        self.assertEquals('Editor', checkboxes.first.node.attrib['value'])

    @browsing
    def test_no_change_link_on_pending_invitations(self, browser):
        john = create(Builder('user'))
        hugo = create(Builder('user').named('hugo', 'b'))
        create(Builder('invitation')
               .inviting(john)
               .to(self.folder)
               .invited_by(hugo))

        browser.login().visit(self.folder, view='@@participants')
        table = browser.css('table').first.lists()

        self.assertEquals('Pending', table[1][-2])
        self.assertEquals('', table[1][-1])

    @browsing
    def test_user_cannot_change_its_own_roles(self, browser):
        john = create(Builder('user')
                      .named('John', 'Doe')
                      .with_roles('Member')
                      .with_roles('Manager', 'Editor', on=self.folder))

        browser.login(john.getId()).visit(self.folder, view="@@participants")

        self.assertEquals('', browser.css('table').first.lists()[1][-1])
