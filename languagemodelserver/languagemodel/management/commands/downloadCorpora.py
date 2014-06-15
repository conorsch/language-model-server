from __future__ import print_function
from django.core.management.base import NoArgsCommand
import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        print("Downloading all NLTK corpora... ", end="")
        nltk.download('all-corpora', quiet=True)
        print("done.")
