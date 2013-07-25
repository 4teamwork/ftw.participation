from ftw.upgrade import UpgradeStep


class UpgradeRegistry(UpgradeStep):
    """Add allow_multiple_roles entry to registry
    """

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.participation.upgrades:1007')
