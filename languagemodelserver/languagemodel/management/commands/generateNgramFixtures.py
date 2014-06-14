from django.core.management.base import NoArgsCommand
from django.core import serializers
import languagemodelserver.languagemodel.models as models
import languagemodelserver.settings as settings
import sys
import os

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # now do the things that you want with your models here
        order = 2
        fixturesFile = os.path.join(settings.BASE_DIR, 'fixtures', "%sgrams.json" % order)
        print("Generating fixtures from %s-grams in database..." % order)
        with open(fixturesFile, 'w') as out:
            serializers.serialize("json", models.Ngram.objects.iterator(), stream=out)

        print("Finished generating fixtures.")

