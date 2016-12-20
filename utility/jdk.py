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

class JdkOverride:
    
    def __init__(self, jdk_override):
        sorted_jdks = sorted(jdk_override, key=itemgetter('end_date'), reverse=True)

        for jdk in xrange(len(sorted_jdks)):

            # Ensure that all required fields are configured
            for field in required_fields:
                if field not in sorted_jdks[jdk]:
                    logger.fatal('field %s missing from jdk_override jdk %s' % (field, str(sorted_jdks[jdk])))
                    sys.exit(1)

            if jdk < len(sorted_jdks) - 1:
                # Calculate generated start date from which this jdk should be used
                sorted_jdks[jdk]['start_date'] = sorted_jdks[jdk+1]['end_date'] + timedelta(1)
        self.overrides = sorted_jdks

    def get_jdk_override(self, commit_date):
        if len(self.overrides) == 0:
            return None

        for jdk_index in xrange(len(self.overrides)):
            if jdk_index == 0 and self.overrides[jdk_index]['end_date'] < commit_date:
                # no override
                return None
    
            if jdk_index < len(self.overrides) - 1:
                if self.overrides[jdk_index]['end_date'] >= commit_date >= self.overrides[jdk_index]['start_date']:
                    return self.overrides[jdk_index]
            else:
                return self.overrides[jdk_index]
