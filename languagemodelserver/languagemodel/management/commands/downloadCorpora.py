from django.core.management.base import NoArgsCommand
import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        nltk.download('all-corpora')
        print("Finished downloading corpora.")
