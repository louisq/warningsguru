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


