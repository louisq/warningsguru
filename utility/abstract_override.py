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

from operator import itemgetter
from datetime import timedelta
import sys

from Logging import logger

"""
Determines which jdk should be used for a specified commit date
"""
required_fields = ['version', 'path', 'end_date']


class AbstractOverride:
    
    def __init__(self, overrides):
        self.name = "ABSTRACT"

        sorted_overrides = sorted(overrides, key=itemgetter('end_date'), reverse=True)

        for override in xrange(len(sorted_overrides)):

            # Ensure that all required fields are configured
            for field in required_fields:
                if field not in sorted_overrides[override]:
                    logger.fatal('field %s missing from jdk_override jdk %s' % (field, str(sorted_overrides[override])))
                    sys.exit(1)

            if override < len(sorted_overrides) - 1:
                # Calculate generated start date from which this jdk should be used
                sorted_overrides[override]['start_date'] = sorted_overrides[override + 1]['end_date'] + timedelta(1)
        self.overrides = sorted_overrides

    def get_override(self, commit, commit_date):
        override = self._calculate_override(commit_date)
        if override:
            logger.info("%s: Overriding %s to use version %s" % (commit, self.name, override['version']))
            return self._get_override_format() % override['path']
        else:
            return self._get_default_format()

    def _calculate_override(self, commit_date):
        if len(self.overrides) == 0:
            return None

        for index in xrange(len(self.overrides)):
            if index == 0 and self.overrides[index]['end_date'] < commit_date:
                # no override
                return None
    
            if index < len(self.overrides) - 1:
                if self.overrides[index]['end_date'] >= commit_date >= self.overrides[index]['start_date']:
                    return self.overrides[index]
            else:
                # If we get to this point then the last override should be used
                return self.overrides[index]

    def _get_default_format(self):
        raise NotImplementedError("Class %s doesn't implement _get_default_format()" % self.__class__.__name__)

    def _get_override_format(self):
        raise NotImplementedError("Class %s doesn't implement _get_override_format()" % self.__class__.__name__)
