#!/usr/bin/env python
#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

"""
Verify that we have proper strings like Copyright notices on all the
right files in our distributions.

Note that this is a source file and packaging test, not a functional test,
so the name of this script doesn't end in *Tests.py.
"""

import fnmatch
import os
import os.path
import re
import string

import TestCmd
import TestSCons

# Use TestCmd, not TestSCons, so we don't chdir to a temporary directory.
test = TestCmd.TestCmd()

scons_version = TestSCons.SConsVersion

def build_path(*args):
    return apply(os.path.join, ('build',)+args)

build_scons     = build_path('scons')
build_local     = build_path('scons-local', 'scons-local-'+scons_version)
build_src       = build_path('scons-src')

class Checker:
    def __init__(self, directory, search_list = [], remove_list=[]):
        self.directory = directory
        self.search_list = search_list
        self.remove_dict = {}
        for r in remove_list:
            self.remove_dict[os.path.join(directory, r)] = 1

    def directory_exists(self):
        return os.path.exists(self.directory)

    def remove_path(self, path):
        return self.remove_dict.get(path)

    def search_this(self, path):
        if self.search_list:
            for pattern in self.search_list:
                if fnmatch.fnmatch(path, pattern):
                    return 1
            return None
        else:
            return os.path.isfile(path)

    def visit(self, result, dirname, names):
        make_path_tuple = lambda n, d=dirname: (n, os.path.join(d, n))
        for name, path in map(make_path_tuple, names):
            if self.remove_path(path):
                names.remove(name)
            elif self.search_this(path):
                body = open(path, 'r').read()
                for expr in self.expressions:
                    if not expr.search(body):
                        msg = '%s: missing %s' % (path, repr(expr.pattern))
                        result.append(msg)

    def find_missing(self):
        result = []
        os.path.walk(self.directory, self.visit, result)
        return result

class CheckUnexpandedStrings(Checker):
    expressions = [
        re.compile('__COPYRIGHT__'),
        re.compile('__FILE__ __REVISION__ __DATE__ __DEVELOPER__'),
    ]
    def must_be_built(self):
        return None

class CheckExpandedCopyright(Checker):
    expressions = [
        re.compile('Copyright.*The SCons Foundation'),
    ]
    def must_be_built(self):
        return 1

check_list = [

    CheckUnexpandedStrings(
        'src',
        search_list = [ '*.py' ],
        remove_list = [
            'engine/SCons/compat/_subprocess.py',
            'engine/SCons/Conftest.py',
            'engine/SCons/dblite.py',
            'engine/SCons/Optik',
        ],
    ),

    CheckUnexpandedStrings(
        'test',
        search_list = [ '*.py' ],
    ),

    CheckExpandedCopyright(
        build_scons,
        remove_list = [
            'build',
            'build-stamp',
            'configure-stamp',
            'debian',
            'dist',
            'engine/SCons/compat/_subprocess.py',
            'engine/SCons/Conftest.py',
            'engine/SCons/dblite.py',
            'engine/SCons/Optik',
            'MANIFEST',
            'os_spawnv_fix.diff',
            'setup.cfg',
        ],
    ),

    CheckExpandedCopyright(
        build_local,
        remove_list = [
            'SCons/compat/_subprocess.py',
            'SCons/Conftest.py',
            'SCons/dblite.py',
            'SCons/Optik',
        ],
    ),

    CheckExpandedCopyright(
        build_src,
        remove_list = [
            'bin',
            'config',
            'debian',
            'doc/design',
            'doc/MANIFEST',
            'doc/python10',
            'doc/reference',
            'doc/man/MANIFEST',
            'doc/user/cons.pl',
            'doc/user/MANIFEST',
            'doc/user/SCons-win32-install-1.jpg',
            'doc/user/SCons-win32-install-2.jpg',
            'doc/user/SCons-win32-install-3.jpg',
            'doc/user/SCons-win32-install-4.jpg',
            'gentoo',
            'QMTest/classes.qmc',
            'QMTest/configuration',
            'QMTest/TestCmd.py',
            'QMTest/TestCommon.py',
            'QMTest/unittest.py',
            'src/os_spawnv_fix.diff',
            'src/MANIFEST.in',
            'src/setup.cfg',
            'src/engine/MANIFEST.in',
            'src/engine/MANIFEST-xml.in',
            'src/engine/setup.cfg',
            'src/engine/SCons/compat/_subprocess.py',
            'src/engine/SCons/Conftest.py',
            'src/engine/SCons/dblite.py',
            'src/engine/SCons/Optik',
            'src/script/MANIFEST.in',
            'src/script/setup.cfg',
        ],
    ),

]

missing_strings = []
not_built = []

for collector in check_list:
    if collector.directory_exists():
        missing_strings.extend(collector.find_missing())
    elif collector.must_be_built():
        not_built.append(collector.directory)

if missing_strings:
    print "Found the following files with missing strings:"
    print "\t" + string.join(missing_strings, "\n\t")
    test.fail_test(1)

if not_built:
    print "Cannot check all strings, the following have apparently not been built:"
    print "\t" + string.join(not_built, "\n\t")
    test.no_result(1)

test.pass_test()