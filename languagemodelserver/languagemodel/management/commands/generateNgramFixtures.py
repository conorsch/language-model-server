from django.core.management.base import NoArgsCommand
from django.core import serializers
import languagemodelserver.languagemodel.models as models
import sys

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # now do the things that you want with your models here
        order = 2
        fixturesFile = '/home/conor/gits/language-model-server/fixturesfile/'+ "%sgrams.json" % order
        print("Generating fixtures from ngrams in database...")
        with open(fixturesFile, 'w') as out:
            serializers.serialize("json", models.Ngram.objects.all(), stream=out)

        print("Finished generating fixtures.")

