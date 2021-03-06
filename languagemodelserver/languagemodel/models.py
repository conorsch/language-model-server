from django.db import models
import codecs

class Ngram(models.Model):
    order = models.IntegerField()
    text = models.CharField(max_length=1000)
    conditionalProbability = models.FloatField()
    backoffWeight = models.FloatField()

    @classmethod
    def create(cls, text, n=None, conditionalProbability=None, backoffWeight=None):
        # Set up a default 'n' value for this ngram
        if not n:
            n = 1

        ngram = Ngram(text, n=None, conditionalProbability=None, backoffWeight=None)
        return ngram

    def __repr__(self):
        representation = dedent("""\
            %(order)rgram: %(text)r
            Order: %(order)r
            """ % {
                'order': self.order,
                'text': self.text,
                }).strip()

        return representation

def getNgrams(filepath, n):
    """Returns all ngrams in corpus of order 'n'."""
    counter = 0

    # For some mad reason, SRILM writes out LM files 
    # as ISO-8859, rather than UTF-8, so we need to 
    # convert that to unicode()s. We'll use 'codecs' 
    # to do that.
    with codecs.open(filepath, 'r', 'ISO-8859-1') as f:
        for line in f:
            # Wait for start of ngram block for order n
            if line.strip() == "\%s-grams:" % n:
                break

        for line in f:
            # Check if we've read to the end of this ngram block
            if line.strip() == '\%s-grams:' % str(n + 1) or \
               line.strip() == '' or \
               line.strip() == '\end\\':
                break
            # We already have a unicode object, SQLAlchemy will be happy
            yield parseNgramLine(line.strip(), n=n)

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

    return {'text': ngramRaw, 'order': n, 'conditionalProbability': conditionalProbability, 'backoffWeight': backoffWeight}
