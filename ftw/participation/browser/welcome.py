from Products.Five.browser import BrowserView
import os.path


class WelcomeInvitedView(BrowserView):
    """If a user is invited and clicks on the link in the e-mail, he is
    redirected to this view.

    """

    def __call__(self):
        """Just redirect to @@register by default. This view can be
        customized dependendig on your project..

        """
        url = os.path.join(self.context.portal_url(), '@@register')
        return self.request.RESPONSE.redirect(url)
