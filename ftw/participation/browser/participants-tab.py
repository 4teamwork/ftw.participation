from ftw.participation.browser.participants import ManageParticipants


class ParticipantsTab(ManageParticipants):

    def __call__(self):

        return self.form()
