#!/usr/bin/env python
from __future__ import print_function
import sys
import ngram

from ngram import Ngram, db


def loadNgramsToDatabase(lmFilepath, order):
    """Reads in LM, exports n-grams of order n to SQLite database."""

    print("Inserting ngrams into database...")
    ngrams = ngram.getNgrams(lmFilepath, order)
    counter = 0
    for n in ngrams:
        db.session.add(n)
        counter += 1
        
        # Commit often, to avoid heavy memory consumption.
        if counter % 10000 == 0:
            db.session.commit()
            sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
            sys.stdout.flush()

    print("Finished loading database.")
    db.session.close()

if __name__ == '__main__':
    testlm = 'output-counts/cna_tokenized_lower.lm'
    n = 2

    # Necessary to create tables before inserting
    db.create_all()

    loadNgramsToDatabase(testlm, n)
