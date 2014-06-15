from django.core.management.base import NoArgsCommand
from django.db import transaction
import sys
import os
import languagemodelserver.settings as settings
from languagemodelserver.languagemodel.models import Ngram, getNgrams
import dse
dse.patch_models(specific_models=[Ngram])
dse.ITEM_LIMIT = 10000

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # now do the things that you want with your models here
        lmFilepath = os.path.join(settings.BASE_DIR, 'corpus', 'brown.lm')
        order = 2
        counter = 0
        print("Extracting ngram args from flat file...")

        ngramArgs = getNgrams(lmFilepath, order)
        print("Inserting ngrams into database...")

        with transaction.commit_on_success():
            with Ngram.delayed as d:
                for n in ngramArgs:
                    counter += 1
                    d.insert(n)
                    # Commit often, to avoid heavy memory consumption.
                    if counter % 1000 == 0:
                        sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
                        sys.stdout.flush()
            
        print("Finished loading database.")
