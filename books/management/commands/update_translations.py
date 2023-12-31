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
        po_file.save()
        call_command('compilemessages', ignore=['venv', 'data'], use_fuzzy=True)
