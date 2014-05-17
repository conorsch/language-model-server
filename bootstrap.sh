#!/bin/bash

# Generates ngram counts for partial corpus.
# Assumes partial corpus is present, and SRILM is installed.

# Ensure 'ngram-count' is installed (requires SRILM)
if ! type -P ngram-count &> /dev/null; then
    cat <<MSG
Command 'ngram-count' not found.
The SCRILM toolset is not installed, or is not 
present in your PATH. See this page to install SCRILM:

http://www.speech.sri.com/projects/srilm/download.html

Exiting...
MSG
    exit 1;
fi

testcorpus='corpus/cna_tokenized_lower.txt'
outputdir='output-counts'
mkdir -p $outputdir

countsfile="$outputdir/cna-ngrams-order5-default"
languagemodel="$outputdir/cna-ngrams-order5-default.lm"

echo -n "Generating ngram counts..."
ngram-count -text $testcorpus -sort -write $countsfile -order 5 -unk
echo " done."

echo "Building language model..."
ngram-count -read $countsfile \
        -lm $languagemodel -unk
echo " done."

echo "Running ngram server..."
ngram -server-port 3433 -order 5 -debug 3 -memuse \
        -lm $languagemodel -unk
