from __future__ import print_function
from django.core.management.base import NoArgsCommand
import nltk
import sys


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        sys.stdout.write("Downloading all NLTK corpora... ")
        sys.stdout.flush()
        nltk.download(['all-corpora', 'punkt'], quiet=True, download_dir="/home/vagrant/.nltk_data")
        sys.stdout.write("done.\n")
        sys.stdout.flush()
