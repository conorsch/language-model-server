#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.append('/home/conor/language-model-server')
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
    testlm = '/home/conor/gits/language-model-server/output-counts/cna_tokenized_lower.lm'
    n = 2

    loadNgramsToDatabase(testlm, n)
