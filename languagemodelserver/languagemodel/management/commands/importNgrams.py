from django.core.management.base import NoArgsCommand
import sys
import os
import languagemodelserver.settings as settings
import languagemodelserver.languagemodel.models as models

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # now do the things that you want with your models here
        baseDir = settings.BASE_DIR
        lmFilepath = os.path.join(baseDir, 'output-counts', 'cna_tokenized_lower.lm')
        order = 2
        counter = 0
        print("Inserting ngrams into database...")
        ngramArgs = models.getNgrams(lmFilepath, order)

        print("Creating empty list for StagingArea...")
        commitBatch = list()

        for n in ngramArgs:
            ngram = models.Ngram(**n)
            commitBatch.append(ngram)
            counter += 1
            
            # Commit often, to avoid heavy memory consumption.
            if counter % 1000 == 0:
                models.Ngram.objects.bulk_create(commitBatch)
                sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
                sys.stdout.flush()

        print("Finished loading database.")
        transaction.commit()

