from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from ftw.participation import _
from ftw.participation.events import InvitationRetractedEvent
from ftw.participation.events import LocalRoleRemoved
from ftw.participation.interfaces import IInvitationStorage
from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.interfaces import IParticipationSupport
from plone.app.workflow.interfaces import ISharingPageRole
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Forbidden
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.event import notify
from zope.i18n import translate
import pkg_resources


try:
    pkg_resources.get_distribution('ftw.lawgiver')
except pkg_resources.DistributionNotFound:
    HAS_LAWGIVER = False
else:
    HAS_LAWGIVER = True
    from ftw.lawgiver.interfaces import IDynamicRoleAdapter


ROLES_WHITE_LIST = ['Owner']


def get_friendly_role_names(names, context, request):
    friendly_names = []

    for name in names:
        title = None
        if HAS_LAWGIVER:
            adapter = queryMultiAdapter((context, request),
                                        IDynamicRoleAdapter,
                                        name=name)
            if adapter:
                title = adapter.get_title()

        if title is None:
            utility = queryUtility(ISharingPageRole, name=name)
            if utility:
                title = utility.title

        if title is None and name not in ROLES_WHITE_LIST:
            continue
        elif title is None:
            friendly_names.append(name)
        else:
            friendly_names.append(translate(title, context=request))
    friendly_names.sort()
    return friendly_names


def inherited(context):
    """Return True if local roles are inherited here.
    """
    return not bool(
        getattr(aq_base(context), '__ac_local_roles_block__', None))


class ManageParticipants(BrowserView):
    """Manage Participants
    """

    template = ViewPageTemplateFile('participants.pt')
    form = ViewPageTemplateFile('participants_form.pt')

    def __call__(self):
        form = self.request.form

        del_userids = form.get('userids', [])
        del_invitations = form.get('invitations', [])

        if form.get('form.delete') and (del_userids or del_invitations):
            self.remove_users(del_userids)
            self.remove_invitations(del_invitations)

            IStatusMessage(self.request).addStatusMessage(_(u"Changes saved."),
                                                          type='info')

        elif form.get('form.cancel'):
            return self.request.RESPONSE.redirect(self.cancel_url())

        return self.template()

    def render_form(self):
        return self.form()

    def can_manage(self):
        sm = getSecurityManager()
        has_permission = sm.checkPermission('Sharing page: Delegate roles',
                                            self.context)
        return has_permission and self.has_participation_support()

    def require_manage(self):
        if not self.can_manage():
            raise Forbidden

    def remove_invitations(self, iids):
        self.require_manage()

        storage = IInvitationStorage(self.context)

        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()

        for iid in iids:
            invitation = storage.get_invitation_by_iid(iid)
            if invitation is None:
                continue

            if invitation.inviter != member.getId():
                raise Forbidden

            storage.remove_invitation(invitation)
            notify(InvitationRetractedEvent(invitation.get_target(),
                                            invitation))

    def remove_users(self, userids):
        self.require_manage()

        deletable = [p['userid'] for p in filter(
            lambda p: not p['readonly'],
            self.get_participants())]

        # we should not remove readonly participants (like myself)
        for userid in userids:
            if userid not in deletable:
                raise Forbidden
            notify(LocalRoleRemoved(self.context, userid))

        # now we need to remove the local roles recursively
        query = dict(path='/'.join(self.context.getPhysicalPath()))
        for brain in self.context.portal_catalog(query):
            obj = brain.getObject()
            obj_local_roles = dict(obj.get_local_roles())

            # do we have to change something?
            obj_to_delete = tuple(
                set(userids) & set(obj_local_roles.keys()))
            if len(obj_to_delete) > 0:
                obj.manage_delLocalRoles(userids=obj_to_delete)

        # we need to reindex the object security
        self.context.reindexObjectSecurity()

    def cancel_url(self):
        return self.context.absolute_url()

    def get_roles_settings(self):
        context = self.context
        portal = getToolByName(context, 'portal_url').getPortalObject()
        result = {}

        def get_roles(context, acquired=False):

            for userid, roles in context.get_local_roles():
                roles = list(roles)
                if 'Owner' in roles and acquired:
                    roles.remove('Owner')

                if userid not in result:
                    result[userid] = dict((role, acquired) for role in roles)
                else:
                    current_roles = result[userid]
                    for role in roles:
                        if role not in current_roles:
                            current_roles[role] = acquired

            parent = aq_parent(context)
            if parent != portal and inherited(context):
                get_roles(parent, acquired=True)

        get_roles(context)
        result = list(result.items())
        return result

    def get_participants(self):
        """Returns some items for the template. Participants are local_roles..
        """
        mtool = getToolByName(self.context, 'portal_membership')
        users = []

        for userid, roles in self.get_roles_settings():

            member = mtool.getMemberById(userid)
            # skip groups
            if member is not None:
                email = member.getProperty('email', '')
                name = member.getProperty('fullname', '')

                all_roles = roles.keys()
                inherited_roles = [r for r, v in roles.items()
                                   if v]

                item = dict(
                    userid=userid,
                    roles=get_friendly_role_names(
                        all_roles, self.context, self.request),
                    inherited_roles=get_friendly_role_names(
                        inherited_roles, self.context, self.request),
                    readonly=self.cannot_remove_user(userid),
                    type_='userids')
                if name and email:
                    item['name'] = u'%s (%s)' % (name.decode('utf-8'),
                                                 email.decode('utf-8'))
                elif name:
                    item['name'] = name.decode('utf-8')
                else:
                    item['name'] = userid.decode('utf-8')

                if item.get('roles') or item.get('inherited_roles'):
                    users.append(item)

        users.sort(key=lambda item: item['name'].lower())
        return users

    def cannot_remove_user(self, userid):
        if not self.can_manage():
            return True

        mtool = getToolByName(self.context, 'portal_membership')
        user = mtool.getMemberById(userid)

        if not user:
            return False

        elif 'Owner' in user.getRolesInContext(self.context):
            return True

        else:
            authenticated_member = mtool.getAuthenticatedMember()
            return userid == authenticated_member.getId()

    def get_pending_invitations(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        mtool = getToolByName(self.context, 'portal_membership')
        storage = IInvitationStorage(portal)

        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()

        invitations = []
        for invitation in storage.get_invitations_for_context(self.context):
            inviter = mtool.getMemberById(invitation.inviter)
            if inviter:
                inviter_name = inviter.getProperty('fullname',
                                                   invitation.inviter)
            else:
                inviter_name = invitation.inviter

            item = dict(name=invitation.email,
                        roles=get_friendly_role_names(
                            invitation.roles, self.context, self.request),
                        inherited_roles=[],
                        inviter=inviter_name,
                        readonly=not member.getId() == invitation.inviter,
                        type_='invitations',
                        iid=invitation.iid)
            invitations.append(item)

        return invitations

    def get_users(self):
        result = self.get_participants() + self.get_pending_invitations()
        result.sort(key=lambda x: x['name'].lower())
        return result

    def hide_cancel_button(self):
        return not(self.has_participation_support())

    def has_participation_support(self):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        allow_invitation = config.allow_invite_users or config.allow_invite_email
        return IParticipationSupport.providedBy(
            self.context) and allow_invitation
