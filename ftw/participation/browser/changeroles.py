from ftw.participation import _
from ftw.participation.events import RolesChangedEvent
from ftw.participation.interfaces import IParticipationRegistry
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.form.interfaces import HIDDEN_MODE
from zExceptions import BadRequest
from zope import schema
from zope.component import getUtility
from zope.event import notify
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory


def get_user_local_roles(memberid, context):
    member = getToolByName(
        context,
        'portal_membership').getMemberById(memberid)

    if not member:
        raise BadRequest('No valid member id.')

    local_roles = dict(context.get_local_roles())
    return list(local_roles.get(member.getId(), []))


def extract_roles(context):
    factory = getUtility(IVocabularyFactory,
                         name='ftw.participation.roles')
    return [term.token for term in factory(context)]


class IChangeRoleSchema(Interface):

    roles = schema.List(
        title=_(u'label_roles', default=u'Roles'),
        value_type=schema.Choice(
            vocabulary=u'ftw.participation.roles'),
        required=False)

    memberid = schema.TextLine()


class ChangeRolesForm(Form):

    label = _(u'label_changerole_form', default=u'Change roles')

    ignoreContext = True
    fields = Fields(IChangeRoleSchema)

    def update(self):
        memberid = self.request.form.get('form.widgets.memberid')
        if not memberid:
            raise BadRequest('No member given')

        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        if config.allow_multiple_roles:
            self.fields['roles'].widgetFactory = CheckBoxFieldWidget
        else:
            self.fields['roles'].widgetFactory = RadioFieldWidget

        if not self.request.form.get('form.widgets.roles-empty-marker'):
            default_roles = set(
                get_user_local_roles(memberid, self.context)).intersection(set(
                extract_roles(self.context)))
            self.request.form['form.widgets.roles'] = list(default_roles)

        super(ChangeRolesForm, self).update()

    def updateWidgets(self):
        super(ChangeRolesForm, self).updateWidgets()

        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        roles_widget = self.widgets['roles']
        if not config.allow_multiple_roles:
            roles_widget.required = True

        memberid_widget = self.widgets['memberid']
        memberid_widget.mode = HIDDEN_MODE

    @buttonAndHandler(_(u'button_save', default=u'Save'))
    def handle_save(self, action):
        data, errors = self.extractData()

        if errors:
            return

        data['roles'] = map(lambda role: role.encode('utf-8'), data['roles'])
        data['memberid'] = data['memberid'].encode('utf-8')

        notify(RolesChangedEvent(
            self.context,
            userid=data['memberid'],
            old_roles=get_user_local_roles(data['memberid'], self.context),
            new_roles=data['roles']))

        self.save_local_roles(data)
        return self.redirect()

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        return self.redirect()

    def redirect(self):
        url = '{0}/@@participants'.format(self.context.absolute_url())
        return self.request.RESPONSE.redirect(url)

    def save_local_roles(self, data):
        # Remove all managed roles
        user_roles = get_user_local_roles(data['memberid'], self.context)
        managed_roles = extract_roles(self.context)
        filtered = filter(lambda role: role not in managed_roles, user_roles)

        # Append new roles
        filtered.extend(data['roles'])
        self.context.manage_setLocalRoles(data['memberid'], filtered)
        self.context.reindexObjectSecurity()
        msg = _(u'message_roles_changes', default=u'Changed roles')
        IStatusMessage(self.request).addStatusMessage(msg, type='info')
