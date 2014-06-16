from __future__ import print_function
from django.core.management.base import NoArgsCommand
import languagemodelserver.settings as settings
import os
import sys
import string
from subprocess import check_call, PIPE

import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        corpus = nltk.corpus.brown
        corpus.name = self.getCorpusName(corpus)

        # Assign output dirs, ensure they exist
        self.corpusDir = os.path.join(settings.BASE_DIR, 'corpus')
        self.countsDir = os.path.join(self.corpusDir, 'counts')
        self.sentencesDir = os.path.join(self.corpusDir, 'sentences')

        for directory in [self.corpusDir, self.countsDir, self.sentencesDir]:
            if not os.path.exists(directory):
                    os.makedirs(directory)

        lmFilepath = os.path.join(self.corpusDir, corpus.name+'.lm')

        self.writeLM(corpus, lmFilepath)

    def getCorpusName(self, corpus):
        """Return friendly name for corpus as str."""
        # Get first filepath for this corpus, since it will be in the corpus dir.
        f = corpus.abspaths()[0]
        return os.path.basename(os.path.dirname(f.path))

    def detokenizeSentences(self, corpus, filepath):
        """Export sentences from corpus as natural language.
        Strips punctuation and tags."""

        sys.stdout.write("Dumping raw sentences from '%s' corpus... " % corpus.name)
        sys.stdout.flush()

        with open(filepath, 'wb') as f:
            for tokens in corpus.sents():
                # Fake detokenization; reduces whitespace padding punctuation, but misses some.
                sent = "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()
                f.write(sent+"\n")

        sys.stdout.write("done.\n")
        sys.stdout.flush()

    def writeLM(self, corpus, lmFilepath):
        """Accepts NLTK corpus and generates a SRILM N-gram language model."""
        
        sentencesFilepath = os.path.join(self.sentencesDir, corpus.name)
        self.detokenizeSentences(corpus, sentencesFilepath)

        countsFilepath = os.path.join(self.countsDir, corpus.name)

        sys.stdout.write("Generating ngram counts (%s)... " % countsFilepath)
        sys.stdout.flush()
        ngramCommand = "/usr/bin/env ngram-count -text %s -sort -write %s -order %s -unk" % (sentencesFilepath, countsFilepath, settings.NGRAM_ORDER)
        check_call(ngramCommand.split(), stdout=PIPE, stderr=PIPE)
        sys.stdout.write("done.\n")
        sys.stdout.flush()

        sys.stdout.write("Building language model (%s)... " % lmFilepath)
        sys.stdout.flush()
        lmCommand = "/usr/bin/env make-big-lm -read %s -lm %s -name %s -order %s -unk" % (countsFilepath, lmFilepath, lmFilepath, settings.NGRAM_ORDER)
        check_call(lmCommand.split(), stdout=PIPE, stderr=PIPE)
        sys.stdout.write("done.\n")
        sys.stdout.flush()
