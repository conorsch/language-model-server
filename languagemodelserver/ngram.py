#!/usr/bin/env python
from __future__ import print_function
import sys
from sqlalchemy import Column, Integer, Unicode, Float
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from textwrap import dedent

Base = declarative_base()

class Ngram(Base):
    __tablename__ = 'ngrams'
    id = Column(Integer, primary_key=True)
    order = Column(Integer)
    text = Column(Unicode(40))
    conditionalProbability = Column(Float)
    backoffWeight = Column(Float)

    def __init__(self, text, n=None, conditionalProbability=None, backoffWeight=None):
        # Set up a default 'n' value for this ngram
        if not n:
            n = 1

        # Set attributes.
        self.order = int(n)
        self.n = self.order
        self.conditionalProbability = float(conditionalProbability)
        self.backoffWeight = float(backoffWeight)
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

def getNgrams(filepath, n):
    """Returns all ngrams in corpus of order 'n'."""

    with open(filepath, 'r') as f:
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
                print("\nFinished reading %s-grams block..." % n)
                break
            # It's important to decode from UTF8 here, otherwise SQLAlchemy will toss its head.
            yield parseNgramLine(line.decode('utf-8').strip(), n=n)

def parseNgramLine(line, n=None):
    """Returns Ngram object from tab-delinated line of conditionalProbability, text, backoffWeight."""

    parts = line.split("\t")
    # Python 2.7 doesn't support partial unpacking, so let's do it the long way.
    # Some ngram lines in the language model don't have an 'backoffWeight' value, 
    # so make it optional.
    (conditionalProbability, ngramRaw), backoffWeight = parts[:2], parts[2:]

    # For more information on the ngram-format, see:
    # http://www.speech.sri.com/projects/srilm/manpages/ngram-format.5.html

    try:
        # Side-effect of partial unpacking means we have a list, so pop it.
        backoffWeight = backoffWeight.pop()
    except IndexError as e:
        backoffWeight = 0

    if not ngramRaw:
        raise Exception("Failed to find ngram in this line: %s" % line)

    if not n:
        n = len(ngramRaw.split())

    return Ngram(ngramRaw, n=n, conditionalProbability=conditionalProbability, backoffWeight=backoffWeight)