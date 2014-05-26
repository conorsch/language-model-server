from django.core.management.base import NoArgsCommand
import languagemodelserver.languagemodel.models as models
import sys

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # now do the things that you want with your models here
        print("Inserting ngrams into database...")
        lmFilepath = '/home/conor/gits/language-model-server/output-counts/cna_tokenized_lower.lm'
        order = 2
        ngrams = models.getNgrams(lmFilepath, order)
        counter = 0

        print("Creating empty list for StagingArea...")
        stagingArea = list()

        for n in ngrams:
            ngram = models.Ngram(**n)
            stagingArea.append(ngram)
            counter += 1
            
            # Commit often, to avoid heavy memory consumption.
            if counter % 1000 == 0:
                models.Ngram.objects.bulk_create(stagingArea)
                sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
                sys.stdout.flush()

        print("Finished loading database.")
        transaction.commit()

