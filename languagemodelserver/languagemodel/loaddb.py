#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.append('/home/mulhod/Dropbox/Docs/corpora/grammatical_error_detection_shared_task_2013/language-model-server')
from django.db import transaction
import models
from models import Ngram


@transaction.commit_manually
def loadNgramsToDatabase(lmFilepath, order):
    """Reads in LM, exports n-grams of order n to SQLite database."""

    print("Inserting ngrams into database...")
    ngrams = models.getNgrams(lmFilepath, order)
    counter = 0
    for n in ngrams:
        ngram = Ngram(n)
        counter += 1
        ngram.save()
        
        # Commit often, to avoid heavy memory consumption.
        if counter % 1000 == 0:
            sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
            sys.stdout.flush()

    print("Finished loading database.")
    transaction.commit()

if __name__ == '__main__':
    testlm = '/media/mulhod/Windows7_OS/Users/win-mulhod/Documents/gigaword/cna-ngrams-order5-counts/cna-ngrams-order5-default.lm'
    n = 2

    loadNgramsToDatabase(testlm, n)
