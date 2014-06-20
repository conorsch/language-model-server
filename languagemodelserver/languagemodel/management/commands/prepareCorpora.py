from __future__ import print_function
from django.core.management.base import NoArgsCommand
import languagemodelserver.settings as settings
import os
import sys
import string
import re
from subprocess import check_call, PIPE

import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):

        corporaWhitelist = "brown treebank gutenberg reuters state_union inaugural timit conll2000".split()
        counter = 0
        for c in corporaWhitelist:
            counter += 1
            corpus = getattr(nltk.corpus, c)
            corpus.name = self.getCorpusName(corpus)
            if corpus.name:

                # Assign output dirs, ensure they exist
                self.corpusDir = os.path.join(settings.BASE_DIR, 'corpus')
                self.countsDir = os.path.join(self.corpusDir, 'counts')
                self.sentencesDir = os.path.join(self.corpusDir, 'sentences')

                for directory in [self.corpusDir, self.countsDir, self.sentencesDir]:
                    if not os.path.exists(directory):
                            os.makedirs(directory)

                print("\r                                                                ", end='')
                print("\rGenerating countfile from corpus {0}/{1} ('{2}')... ".format(counter, len(corporaWhitelist), corpus.name), end='')
                sys.stdout.flush()

                self.generateCounts(corpus)

        print("")
        sys.stdout.flush()

        self.writeLM()

    def getCorpusName(self, corpus):
        """Return friendly name for corpus as str."""
        # Get first filepath for this corpus, since it will be in the corpus dir.
        f = corpus.abspaths()[0]
        try:
            corpusName = os.path.basename(os.path.dirname(f.path))
            return corpusName
        except AttributeError as e:
            pass

    def detokenizeSentences(self, corpus, filepath):
        """Export sentences from corpus as natural language.
        Strips punctuation and tags."""

        with open(filepath, 'w') as f:
            for tokens in corpus.sents():
                # Fake detokenization; reduces whitespace padding punctuation, but misses some.
                #sent = u"".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).encode('utf-8').strip()
                sent = "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()

                # Catch Unicode-related exceptions and report them.
                try:
                    f.write(sent+"\n".encode('utf-8'))
                except UnicodeEncodeError as e:
                    print("Skipping corpus '{0}' due to Unicode err".format(corpus.name))

    def generateCounts(self, corpus):
        """Accepts NLTK corpus and ngram count files for it."""
        
        sentencesFilepath = os.path.join(self.sentencesDir, corpus.name)
        self.detokenizeSentences(corpus, sentencesFilepath)

        countsFilepath = os.path.join(self.countsDir, corpus.name)

        ngramCommand = "/usr/bin/env ngram-count -text %s -sort -write %s -order %s -unk" % (sentencesFilepath, countsFilepath, settings.NGRAM_ORDER)
        check_call(ngramCommand.split(), stdout=PIPE, stderr=PIPE)

    def writeLM(self):
        """Reads all available count files and creates a combined SRILM ngram LM."""
        lmFilepath = os.path.join(self.corpusDir, 'nltk-combined.lm')
        # Need to get list of all count files
        countFiles = os.walk(self.countsDir).next()[2]
        # Then interpolate them via the -read option to make-big-lm

        readArgs = str()
        for c in countFiles:
            readArgs += "-read %s " % os.path.join(self.countsDir, c)

        sys.stdout.write("Building language model (%s)... " % lmFilepath)
        sys.stdout.flush()
        lmCommand = "/usr/bin/env make-big-lm %s -lm %s -name %s -order %s -unk" % (readArgs, lmFilepath, lmFilepath, settings.NGRAM_ORDER)
        check_call(lmCommand.split(), stdout=PIPE, stderr=PIPE)

        sys.stdout.write("done.\n")
        sys.stdout.flush()
