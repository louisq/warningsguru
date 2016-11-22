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

"""
The TOIF adapters & assimilator return the full file path of a compiled file. The compile file therefore may have the
following issues:
 1. Doesn't have the same file extension (.class instead of .java)
 2. May have additional extension values if it's an inner class
 3. Won't be contained in the src directory
 4. And contain the full path to the system root

 This tool takes the TOIF path and attempts to convert it back to the format of the project
"""
import re

CHILDCLASS_PATTERN = re.compile("((?:\$\w*)+)\.")


class OriginalFilePathGenerator:

    def __init__(self, project_root_path):
        self.root_path = project_root_path

    def transform(self, path):

        path = self._remove_root(path)
        path = self._replace_build_directory(path)
        path = self._replace_file_extension(path)
        path = self._remove_nested_class_element(path)
        return path

    """
    We need to have the path from the root of the analysed project and not the computer root
    """
    def _remove_root(self, path):
        return path[len(self.root_path):]

    """
    When a project is build the class files are put in a separate directory. We need to obtain the original directory
    """
    def _replace_build_directory(self, path):
        # TODO We might be loosing some files that are not being placed in the default location and are still built
        return path.replace("target/classes/.", "src/main/java").replace("target/classes/", "src/main/java/")

    def _replace_file_extension(self, path):
        # TODO this version will only work with native java files. If we have groovy or scala files for example that get
        # compiled to .class we would not know
        # TODO This does not support where the file as none standard case for the file extension
        return path.replace(".class", ".java")

    """
    Nested classes get compiled as a seperate class file named 'parentClass$Childclass.class' We need to reconcile it
    with it's parent class by removing the child section.
    """
    def _remove_nested_class_element(self, path):
        # TODO determine if child class line number is different then parent class file
        if path.find("$") >= 0:
            return re.sub("((?:\$\w*)+)\.", ".", path)
        else:
            return path