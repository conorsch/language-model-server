from __future__ import print_function
from django.core.management.base import NoArgsCommand
import languagemodelserver.settings as settings
import os
import string
import subprocess

import nltk


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        b = nltk.corpus.brown
        corpusName = 'brown'
        corpusSentences = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'_sentences')
        countsFile = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'_counts')
        lmFilepath = os.path.join(settings.BASE_DIR, 'corpus', corpusName+'.lm')

        print("Dumping raw sentences from '%s' corpus... " % corpusName, end="")
        with open(corpusSentences, 'wb') as f:
            for tokens in b.sents():
                s = "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()
                f.write(s+"\n")

        print("done.")

        
        print("Generating ngram counts (%s)... " % countsFile, end="")
        ngramCommand = "ngram-count -text %s -sort -write %s -order %s -unk" % (corpusSentences, countsFile, settings.NGRAM_ORDER)
        subprocess.check_call(ngramCommand.split())
        print("done.")

        print("Building language model (%s)... " % lmFilepath, end="")
        lmCommand = "make-big-lm -read %s -lm %s -name %s -order %s -unk" % (countsFile, lmFilepath, lmFilepath, settings.NGRAM_ORDER)
        subprocess.check_call(lmCommand.split())
        print("done.")



