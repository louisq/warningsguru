from unittest import TestCase

from repos.git import GIT


class TestBlame(TestCase):

    def runTest(self):
        result = GIT().get_warning_blames("/home/lquerel/git/feature_flags", "paper/toggles_integrated.tex", [1, 4, 100, 200, 603])

        self.assertEqual(len(result), 5)
        # todo check content of

        pass


    pass
