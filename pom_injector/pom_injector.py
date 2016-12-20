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
from lxml import etree
from update_pom import update_pom

from utility.Logging import logger

POM_NS_PATTERN = re.compile("xmlns=\"(http.+/POM/[\d.]+)\"")


def pom_injector(file_path, adaptor_root_path, repo_path, adaptor_output_dir, commit):
    plugin_xml = _update_plugin_parameters(adaptor_root_path, repo_path, adaptor_output_dir)
    namespaces = _determine_pom_namespace(file_path)

    if len(namespaces) == 0:
        logger.warn("%s: Namespace of pom not identified. Using legacy extractor" % commit)
        return update_pom(file_path, adaptor_root_path, repo_path, adaptor_output_dir, commit)
    else:
        namespace = namespaces[0]
        if len(namespaces) > 1:
            logger.error("%s: Multiple POM namespaces found [%s]. Using %s" % (commit, str(namespaces), namespace))

        _remove_existing_plugin(file_path, commit)
        return _update_pom(file_path, plugin_xml, namespace, commit)


def _update_pom(file_path, plugin_xml, namespace, commit):
    tree = etree.parse(file_path)
    build = tree.getroot().find("./a:build", namespaces={"a": namespace})

    if build:
        plugin_management = build.find("./a:pluginManagement", namespaces={"a": namespace})

        if plugin_management:
            plugins = plugin_management.find("./a:pluginsd", namespaces={"a": namespace})

            if plugins:
                plugins.append(etree.fromstring(plugin_xml))

            else:
                # Where the plugins tag is missing we will add it to the pom
                logger.info("%s: Adding missing <plugins> tag in <pluginManagement>" % commit)
                plugin_management.append(etree.fromstring(_add_plugins_xml(plugin_xml)))

        else:
            # Where the pluginManagement tag is missing we will add it to the pom
            logger.info("%s: Adding missing <pluginManagement><plugins> tags in <build>" % commit)
            plugin_management.append(etree.fromstring(_add_pluginmanagement_xml(plugin_xml)))
    else:
        logger.error("%s: build tag not in pom file" % commit)
        return False

    tree.write(file_path)
    return True


def _determine_pom_namespace(file_path):
    # We need to know the namespace to be able to properly reference tags in the tree
    with open(file_path, 'r') as f:
        pom_data = f.read()
    f.close()

    return POM_NS_PATTERN.findall(pom_data)


def _remove_existing_plugin(file_path, commit):
    # TODO replace this method is possible with one that uses lxml to modify tree instead of using regex

    with open(file_path, 'rw') as f:
        pom_data = f.read()
        if "exec-maven-plugin" in pom_data:
            pattern = re.compile("<plugin>[\n\s<>/\w\d.]*exec-maven-plugin[\n\s<>/\w\d.]*</plugin>")
            match = pattern.match(pom_data)

            if match:
                logger.info("%s: Updated pom to remove exec-maven-plugin" % commit)
                # TODO handle the case where we might have multiple instances of it in the file

                f.write(pom_data[:match.start()] + pom_data[match.end():])

    f.close()


def _update_plugin_parameters(adaptor_root_path, repo_path, adaptor_output_dir):
    runner_script_path = os.path.join(adaptor_root_path, 'RunAdaptors.py')
    default_housekeeping_path = os.path.join(adaptor_root_path, 'Housekeeping.txt')

    return PLUGIN.format(runner_path=runner_script_path, adaptor_output_dir=adaptor_output_dir,
                         housekeeping_path=default_housekeeping_path, repo_path=repo_path)


def _add_pluginmanagement_xml(plugin):
    return "<pluginManagement>{}</pluginManagement>".format(_add_plugins_xml(plugin))


def _add_plugins_xml(plugin):
    return "<plugins>{}</plugins>".format(plugin)

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
