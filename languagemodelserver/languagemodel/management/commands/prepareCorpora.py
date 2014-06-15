from __future__ import print_function
from django.core.management.base import NoArgsCommand
import languagemodelserver.settings as settings
import os
import sys
import string
from subprocess import Popen, PIPE

import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        b = nltk.corpus.brown
        corpusName = 'brown'
        corpusSentences = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'_sentences')
        countsFile = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'_counts')
        lmFilepath = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'.lm')

        sys.stdout.write("Dumping raw sentences from '%s' corpus... " % corpusName)
        sys.stdout.flush()
        with open(corpusSentences, 'wb') as f:
            for tokens in b.sents():
                s = "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()
                f.write(s+"\n")
        sys.stdout.write("done.\n")
        sys.stdout.flush()
        
        sys.stdout.write("Generating ngram counts (%s)... " % countsFile)
        sys.stdout.flush()
        ngramCommand = "/usr/bin/env ngram-count -text %s -sort -write %s -order %s -unk" % (corpusSentences, countsFile, settings.NGRAM_ORDER)
        Popen(ngramCommand.split(), stdout=PIPE, stderr=PIPE).communicate()
        sys.stdout.write("done.\n")
        sys.stdout.flush()

        sys.stdout.write("Building language model (%s)... " % lmFilepath)
        sys.stdout.flush()
        lmCommand = "/usr/bin/env make-big-lm -read %s -lm %s -name %s -order %s -unk" % (countsFile, lmFilepath, lmFilepath, settings.NGRAM_ORDER)
        Popen(lmCommand.split(), stdout=PIPE, stderr=PIPE).communicate()
        sys.stdout.write("done.\n")
        sys.stdout.flush()
