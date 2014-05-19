#!/usr/bin/env python
from __future__ import print_function
import sys
import ngram

from ngram import Ngram, db


testlm = 'output-counts/cna_tokenized_lower.lm'

def loadNgramsToDatabase(lmFilepath, order):
    """Reads in LM, exports n-grams of order n to SQLite database."""

    print("Creating session handler...")
    print("Inserting ngrams into database...")
    ngrams = ngram.getNgrams(lmFilepath, order)
    counter = 0
    for n in ngrams:
        db.session.add(n)
        counter += 1
        
        if counter % 10000 == 0:
            db.session.flush()
            db.session.commit()
            sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
            sys.stdout.flush()

    print("Finished loading database.")
    db.session.close()

if __name__ == '__main__':
    n = 2
    loadNgramsToDatabase(testlm, n)

