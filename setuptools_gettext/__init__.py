# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2009, 2011 Canonical Ltd.
# Copyright (C) 2022 Breezy Developers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# This code is from bzr-explorer and modified for bzr.

"""build_mo command for setup.py"""

import os
import re
from distutils import log
from distutils.core import Command
from distutils.dep_util import newer
from distutils.spawn import find_executable
from distutils.command.build import build
from distutils.command.clean import clean

__version__ = (0, 1, 4)


def lang_from_dir(source_dir: os.PathLike) -> list[str]:
    re_po = re.compile(r'^([a-zA-Z_]+)\.po$')
    lang = []
    for i in os.listdir(source_dir):
        mo = re_po.match(i)
        if mo:
            lang.append(mo.group(1))
    return lang


def parse_lang(lang: str) -> list[str]:
    return [i.strip() for i in lang.split(',') if i.strip()]


class build_mo(Command):
    """Subcommand of build command: build_mo"""

    description = 'compile po files to mo files'

    # List of options:
    #   - long name,
    #   - short name (None if no short name),
    #   - help string.
    user_options = [('build-dir=', 'd', 'Directory to build locale files'),
                    ('output-base=', 'o', 'mo-files base name'),
                    ('source-dir=', None, 'Directory with sources po files'),
                    ('force', 'f', 'Force creation of mo files'),
                    ('lang=', None, 'Comma-separated list of languages '
                                    'to process'),
                    ]

    boolean_options = ['force']

    def initialize_options(self):
        self.build_dir = None
        self.output_base = None
        self.source_dir = None
        self.force = None
        self.lang = None

    def finalize_options(self):
        self.set_undefined_options('build', ('force', 'force'))
        self.prj_name = self.distribution.get_name()
        if self.build_dir is None:
            self.build_dir = 'breezy/locale'
        if not self.output_base:
            self.output_base = self.prj_name or 'messages'
        if self.source_dir is None:
            self.source_dir = 'po'
        if self.lang is None:
            self.lang = lang_from_dir(self.source_dir)
        else:
            self.lang = parse_lang(self.lang)

    def run(self):
        """Run msgfmt for each language"""
        if not self.lang:
            return

        if find_executable('msgfmt') is None:
            log.warn("GNU gettext msgfmt utility not found!")
            log.warn("Skip compiling po files.")
            return

        if 'en' in self.lang:
            if find_executable('msginit') is None:
                log.warn("GNU gettext msginit utility not found!")
                log.warn("Skip creating English PO file.")
            else:
                log.info('Creating English PO file...')
                pot = (self.prj_name or 'messages') + '.pot'
                en_po = 'en.po'
                self.spawn(['msginit',
                            '--no-translator',
                            '-l', 'en',
                            '-i', os.path.join(self.source_dir, pot),
                            '-o', os.path.join(self.source_dir, en_po),
                            ])

        basename = self.output_base
        if not basename.endswith('.mo'):
            basename += '.mo'

        for lang in self.lang:
            po = os.path.join('po', lang + '.po')
            if not os.path.isfile(po):
                po = os.path.join('po', lang + '.po')
            dir_ = os.path.join(self.build_dir, lang, 'LC_MESSAGES')
            self.mkpath(dir_)
            mo = os.path.join(dir_, basename)
            if self.force or newer(po, mo):
                log.info('Compile: %s -> %s' % (po, mo))
                self.spawn(['msgfmt', '-o', mo, po])


class clean_mo(Command):
    description = 'clean .mo files'

    user_options = [('build-dir=', 'd', 'Directory to build locale files')]

    def initialize_options(self):
        self.build_dir = None

    def finalize_options(self):
        if self.build_dir is None:
            self.build_dir = 'breezy/locale'

    def run(self):
        for root, dirs, files in os.walk(self.build_dir):
            for file_ in files:
                if file_.endswith('.mo'):
                    os.unlink(os.path.join(root, file_))


def has_gettext(d):
    return True


build.sub_commands.append(('build_mo', has_gettext))
clean.sub_commands.append(('clean_mo', has_gettext))
