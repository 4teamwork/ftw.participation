from ftw.participation import _
from ftw.participation.interfaces import IInvitationStorage
from plone.app.workflow.interfaces import ISharingPageRole
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Forbidden
from zope.component import queryUtility
from zope.i18n import translate


def get_friendly_role_name(names, request):
    friendly_names = []

    for name in names:
        utility = queryUtility(ISharingPageRole, name=name)
        if utility is None:
            friendly_names.append(name)
        else:
            friendly_names.append(translate(utility.title, context=request))
    return ', '.join(friendly_names)


class ManageParticipants(BrowserView):
    """Manage Participants
    """

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

        return super(ManageParticipants, self).__call__()

    def remove_invitations(self, iids):
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

    def remove_users(self, userids):
        deletable = [p['userid'] for p in filter(
                lambda p: not p['readonly'],
                self.get_participants())]

        # we should not remove readonly participants (like myself)
        for userid in userids:
            if userid not in deletable:
                raise Forbidden

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

    def get_participants(self):
        """Returns some items for the template. Participants are local_roles..
        """
        mtool = getToolByName(self.context, 'portal_membership')
        authenticated_member = mtool.getAuthenticatedMember()
        users = []
        for userid, roles in self.context.get_local_roles():
            member = mtool.getMemberById(userid)
            # skip groups
            if member is not None:
                email = member.getProperty('email', '')
                name = member.getProperty('fullname', '')
                item = dict(userid=userid,
                            roles=get_friendly_role_name(roles, self.request),
                            readonly=userid == authenticated_member.getId(),
                            type_='userids')
                if name and email:
                    item['name'] = u'%s (%s)' % (name.decode('utf-8'),
                                                 email.decode('utf-8'))
                elif name:
                    item['name'] = name
                else:
                    item['name'] = userid
                users.append(item)
        return users

    def get_pending_invitations(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        storage = IInvitationStorage(portal)

        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()

        invitations = []
        for invitation in storage.get_invitations_for_context(self.context):

            item = dict(name=invitation.email,
                        roles=get_friendly_role_name(invitation.roles,
                                                     self.request),
                        inviter=invitation.inviter,
                        readonly=not member.getId() == invitation.inviter,
                        type_='invitations',
                        iid=invitation.iid)
            invitations.append(item)

        return invitations

    def get_users(self):
        result = self.get_participants() + self.get_pending_invitations()
        result.sort(key=lambda x: x['name'].lower())
        return result

