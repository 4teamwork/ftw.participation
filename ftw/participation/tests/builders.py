from AccessControl import getSecurityManager
from ftw.builder import builder_registry
from ftw.participation.invitation import Invitation
import transaction


class InvitationBuilder(object):

    def __init__(self, session):
        self.session = session
        self.arguments = {
            'target': None,
            'email': None,
            'inviter': getSecurityManager().getUser().getId(),
            'roles': ['Reader']}

    def having(self, **kwargs):
        self.arguments.update(kwargs)
        return self

    def to(self, target):
        return self.having(target=target)

    def inviting(self, user):
        return self.having(email=user.getProperty('email'))

    def invited_by(self, user):
        return self.having(inviter=user.getId())

    def create(self, **kwargs):
        self.before_create()
        obj = Invitation(**self.arguments)
        self.after_create(obj)
        return obj

    def before_create(self):
        pass

    def after_create(self, obj):
        if self.session.auto_commit:
            transaction.commit()


builder_registry.register('invitation', InvitationBuilder)
