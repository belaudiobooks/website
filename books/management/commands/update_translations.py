'''
See Command desription.
'''

import os
from typing import List
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
import polib
import belorthography



class Command(BaseCommand):
    '''See help.'''

    help = 'Updates localization files and lacinifies them.'

    def handle(self, *args, **options):
        lang='be_Latn'
        call_command('makemessages', locale=[lang], ignore=['venv', 'data'])
        dir = settings.LOCALE_PATHS[0]
        po_file= polib.pofile(os.path.join(dir, lang, 'LC_MESSAGES', 'django.po'))
        for entry in po_file:
            entry.msgstr = belorthography.convert(
                entry.msgid,
                belorthography.Orthography.OFFICIAL,
                belorthography.Orthography.LATIN
            )
        # Set creation date to constant so that re-running update_translation doesn't
        # mark file as changed when it there are no actual changes in messages.
        po_file.metadata['POT-Creation-Date'] = '2024-01-01 03:32+0000'
        po_file.save()
        call_command('compilemessages', ignore=['venv', 'data'], use_fuzzy=True)
