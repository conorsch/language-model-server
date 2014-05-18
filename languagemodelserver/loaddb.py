#!/usr/bin/env python
from __future__ import print_function
import sys
import ngram

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


testlm = 'output-counts/cna_tokenized_lower.lm'

dbpath = 'sqlite:////tmp/teste.db'
engine = create_engine(dbpath)
Base = declarative_base(bind=engine)

def loadNgramsToDatabase(lmFilepath, order):
    """Reads in LM, exports n-grams of order n to SQLite database."""

    print("Creating session handler...")
    Session = sessionmaker(bind=engine)
    s = Session()
    print("Inserting ngrams into database...")
    Base.metadata.create_all()
    ngrams = ngram.getNgrams(lmFilepath, order)
    counter = 0
    for n in ngrams:
        s.add(n)
        counter += 1
        
        if counter % 10000 == 0:
            s.flush()
            s.commit()
            sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(order), str(counter)))
            sys.stdout.flush()

    print("Finished loading database.")
    s.close()

if __name__ == '__main__':
    n = 2
    loadNgramsToDatabase(testlm, n)

