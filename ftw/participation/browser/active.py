from Products.Five.browser import BrowserView
from ftw.participation.interfaces import IParticipationSupport


class ParticipationActive(BrowserView):
    """Checks if the participation is active on this context.
    """

    def __call__(self):
        return IParticipationSupport.providedBy(self.context)
