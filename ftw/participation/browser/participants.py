from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.participation import _
from zExceptions import Forbidden


class ManageParticipants(BrowserView):
    """Manage Participants
    """

    def __call__(self):
        form = self.request.form

        del_userids = form.get('userids')
        if form.get('form.delete') and del_userids:
            deletable = [p['userid'] for p in filter(
                    lambda p: not p['readonly'],
                    self.get_participants())]

            # we should not remove readonly participants (like myself)
            for userid in del_userids:
                if userid not in deletable:
                    raise Forbidden

            # now we need to remove the local roles recursively
            query = dict(path='/'.join(self.context.getPhysicalPath()))
            for brain in self.context.portal_catalog(query):
                obj = brain.getObject()
                obj_local_roles = dict(obj.get_local_roles())

                # do we have to change something?
                obj_to_delete = tuple(set(del_userids) & set(obj_local_roles.keys()))
                if len(obj_to_delete) > 0:
                    obj.manage_delLocalRoles(userids=obj_to_delete)

            # we need to reindex the object security
            self.context.reindexObjectSecurity()
            IStatusMessage(self.request).addStatusMessage(_(u"Changes saved."),
                                                          type='info')

        elif form.get('form.cancel'):
            return self.request.RESPONSE.redirect(self.cancel_url())

        return super(ManageParticipants, self).__call__()

    def cancel_url(self):
        return self.context.absolute_url()

    def get_participants(self):
        """Returns some items for the template. Participants are local_roles..
        """
        mtool = getToolByName(self.context, 'portal_membership')
        authenticated_member = mtool.getAuthenticatedMember()
        for userid, roles in self.context.get_local_roles():
            member = mtool.getMemberById(userid)
            # skip groups
            if member is not None:
                email = member.getProperty('email', '')
                name = member.getProperty('fullname', '')
                item = dict(member=member, userid=userid, roles=roles,
                            readonly=userid == authenticated_member.getId())
                if name and email:
                    item['name'] = '%s (%s)' % (name, email)
                elif name:
                    item['name'] = name
                else:
                    item['name'] = userid
                yield item
