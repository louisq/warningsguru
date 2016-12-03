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
import re

from utility.Logging import logger

PLUGINS_PATTERN = re.compile("(<plugins>)", re.MULTILINE)

PLUGIN = """
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>exec-maven-plugin</artifactId>
  <configuration>
      <executable>python</executable>
      <workingDirectory>target/classes/</workingDirectory>
      <commandlineArgs>{runner_path} {repo_path} {adaptor_output_dir} {housekeeping_path}</commandlineArgs>
  </configuration>
  <executions>
      <execution>
          <id>staticguru_runadaptors</id>
          <phase>prepare-package</phase>
          <goals>
              <goal>exec</goal>
          </goals>
      </execution>
  </executions>
</plugin>
"""
PLUGINS = """
<plugins>%s</plugins>
""" % PLUGIN


def update_pom(pom_file_path, tool_root_path, repo_path, adaptor_output_dir):
    f = open(pom_file_path, 'r')
    pom_file = f.read()
    f.close()

    plugin_tag_location = PLUGINS_PATTERN.search(pom_file)

    runner_script_path = os.path.join(tool_root_path, 'RunAdaptors.py')
    default_housekeeping_path = os.path.join(tool_root_path, 'Housekeeping.txt')

    plugin = PLUGIN.format(runner_path=runner_script_path, adaptor_output_dir=adaptor_output_dir,
                           housekeeping_path=default_housekeeping_path, repo_path=repo_path)

    # TODO need to log message if we are unable to inject toif in pom file

    if plugin_tag_location.end() < 0:
        return False

    updated_pom_file = pom_file[0:plugin_tag_location.end()] + plugin + pom_file[plugin_tag_location.end():len(pom_file)]

    f = open(pom_file_path, 'w')
    f.write(updated_pom_file)
    f.close()

    return True
