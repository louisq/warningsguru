"""
The MIT License (MIT)

Copyright (c) 2016-2017 Louis-Philippe Querel l_querel@encs.concordia.ca

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""
The TOIF adapters & assimilator return the full file path of a compiled file. We need to use the mapping from the runner
to determine which source file is associated with the specified compiled file
"""


class OriginalFilePathGenerator:

    def __init__(self, project_root_path, mapping):
        self.root_path = project_root_path
        self.mapping = mapping

    def transform(self, path):

        path = _remove_leading_slash(self._remove_root(path))
        if path not in self.mapping:
            return None
        return "/%s" % self.mapping[path]

    """
    We need to have the path from the root of the analysed project and not the computer root
    """
    def _remove_root(self, path):
        return path[len(self.root_path):]


def _remove_leading_slash(path):
    if path[0] == "/":
        return path[1:]
    else:
        return path
