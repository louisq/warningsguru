"""
The MIT License (MIT)

Copyright (c) 2016 Louis-Philippe Querel l_querel@encs.concordia.ca

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

import os


class FilePathExtractor:

    def __init__(self, toif_components):
        self.toif = toif_components
        self.cache = {}

    def getPath(self, component_id):

        if component_id in self.cache:
            return self.cache.get(component_id)
        else:
            current_component = self.toif.get(component_id)

            if 'DirectoryIsContainedInDirectory' in current_component:
                path = os.path.join(self.getPath(current_component.get('DirectoryIsContainedInDirectory')),
                                    current_component.get('name'))
            elif 'FileIsContainedInDirectory' in current_component:
                path = os.path.join(self.getPath(current_component.get('FileIsContainedInDirectory')),
                                    current_component.get('name'))
            else:
                path = current_component.get('name')

            self.cache[component_id] = path
            return path


