#!/usr/bin/env python
from __future__ import print_function
import sys

from sqlalchemy import Column, Integer, Unicode, Float
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from textwrap import dedent

testlm = 'output-counts/cna_tokenized_lower.lm'

dbpath = 'sqlite:////tmp/teste.db'
engine = create_engine(dbpath)
Base = declarative_base(bind=engine)

class Ngram(Base):
    __tablename__ = 'ngrams'
    id = Column(Integer, primary_key=True)
    order = Column(Integer)
    text = Column(Unicode(40))
    lprobability = Column(Float)
    rprobability = Column(Float)

    def __init__(self, text, n=None, lprobability=None, rprobability=None):
        # Set up a default 'n' value for this ngram
        if not n:
            n = 1

        # Set attributes.
        self.order = int(n)
        self.n = self.order
        self.lprobability = float(lprobability)
        self.rprobability = float(rprobability)
        self.text = unicode(text)

    def __str__(self):
        representation = dedent("""\
            %(n)sgram: %(text)s
            Order: %(n)s
            """ % {
                'n': self.n,
                'text': self.text,
                }).strip()

        return representation

def getNgrams(n):
    """Returns all ngrams in corpus of order 'n'."""

    with open(testlm, 'r') as f:
        for line in f:
            # Wait for start of ngram block for order n
            if line.strip() == "\%s-grams:" % n:
                print("Found start of %s-grams block..." % n)
                break
        for line in f:
            # Check if we've read to the end of this ngram block
            if line.strip() == '\%s-grams:' % str(n + 1) or \
               line.strip() == '' or \
               line.strip() == '\end\\':
                print("Finished reading %s-grams block..." % n)
                break
            # It's important to decode from UTF8 here, otherwise SQLAlchemy will toss its head.
            yield parseNgramLine(line.decode('utf-8').strip(), n=n)

def parseNgramLine(line, n=None):
    """Returns Ngram object from tab-delinated line of lpos, ngram, rpos."""

    parts = line.split("\t")
    # Python 2.7 doesn't support partial unpacking, so let's do it the long way.
    # Some ngram lines in the language model don't have an 'rprobability' value, 
    # so make it optional.
    (lprobability, ngramRaw), rprobability = parts[:2], parts[2:]

    try:
        rprobability = rprobability[0]
    except IndexError as e:
        rprobability = 0

    if not ngramRaw:
        raise Exception("Failed to find ngram in this line: %s" % line)

    if not n:
        n = len(ngramRaw.split())

    return Ngram(ngramRaw, n=n, lprobability=lprobability, rprobability=rprobability)

def loadNgramsToDatabase(n):
    """Reads in LM, exports n-grams of order n to SQLite database."""

    print("Creating session handler...")
    Session = sessionmaker(bind=engine)
    s = Session()
    print("Inserting ngrams into database...")
    Base.metadata.create_all()
    ngrams = getNgrams(n)
    counter = 0
    for ngram in ngrams:
        s.add(ngram)
        counter += 1
        
        if counter % 10000 == 0:
            s.flush()
            s.commit()
            sys.stdout.write("\rNumber of %s-grams committed to database: %s"% (str(n), str(counter)))
            sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()
    s.close()

if __name__ == '__main__':
    n = 2
    loadNgramsToDatabase(n)
