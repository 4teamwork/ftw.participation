from ftw.testing import browser
from ftw.testing.pages import Plone


class ParticipantsView(Plone):

    def visit_on(self, obj):
        return self.visit(obj, '@@participants')

    @property
    def participants(self):
        table = browser().find_by_css('#content table.listing')
        participants = []

        rows = table.find_by_css('tr')
        headers = [node.text.strip() for node in rows[0].find_by_css('th')]
        rows = rows[1:]

        for row in rows:
            line = {}
            cells = tuple(row.find_by_css('td'))
            for col, header in enumerate(headers):
                line[header] = cells[col].text.strip()
            del line[u'']  # checkbox column
            participants.append(line)

        return participants

    @property
    def participant_fullnames(self):
        return [user.get('User') for user in self.participants]
