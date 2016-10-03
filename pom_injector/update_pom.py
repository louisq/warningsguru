import os
import re

PLUGINS_PATTERN = re.compile("(<plugins>)", re.MULTILINE)

PLUGIN = """
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>exec-maven-plugin</artifactId>
  <configuration>
      <executable>python</executable>
      <workingDirectory>target/classes/</workingDirectory>
      <arguments>
          <argument>{runner_path}</argument>
          <argument>{repo_path}</argument>
          <argument>{adaptor_output_dir}</argument>
          <argument>{housekeeping_path}</argument>
      </arguments>

  </configuration>
  <executions>

      <execution>

          <id>python-build</id>
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
        pass

    updated_pom_file = pom_file[0:plugin_tag_location.end()] + plugin + pom_file[plugin_tag_location.end():len(pom_file)]

    f = open(pom_file_path, 'w')
    f.write(updated_pom_file)
    f.close()