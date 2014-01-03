from ftw.testbrowser import browser


def roles_input_types():
    """Returns the type of input fields used for role selection.
    """
    label = browser.xpath('//label[normalize-space(text())="Roles"]').first
    inputs = label.parent('div.field').css('input')
    types = map(lambda node: node.attrib['type'], inputs)
    return list(set(types) - set(['hidden']))
