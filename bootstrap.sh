#!/bin/bash

# Generates ngram counts for partial corpus.
# Assumes partial corpus is present, and SRILM is installed.

# Ensure 'ngram-count' is installed (requires SRILM)
if ! type -P ngram-count &> /dev/null; then
    cat <<MSG
Command 'ngram-count' not found.
The SRILM toolset is not installed, or is not 
present in your PATH. See this page to install SRILM:

http://www.speech.sri.com/projects/srilm/download.html

Exiting...
MSG
    exit 1;
fi

# Ensure we have a corpus to work with
testcorpus='corpus/cna_tokenized_lower.txt'
if [[ ! -f $testcorpus ]] ; then
    cat <<MSG
Dataset '$testcorpus' was not found. Add it, then try again.
MSG
    exit 2;
fi

outputdir='output-counts'
mkdir -p $outputdir

countsfile="$outputdir/$(basename $testcorpus | perl -npe 's/(\.)(\w+)$/$1counts/')"
languagemodel="$outputdir/$(basename $testcorpus | perl -npe 's/(\.)(\w+)$/$1lm/')"

echo "Dataset: '$testcorpus'"

echo -n "Generating ngram counts ($countsfile)..."
ngram-count -text $testcorpus -sort -write $countsfile -order 5 -unk
echo " done."

echo "Building language model ($languagemodel)..."
make-big-lm -read $countsfile -lm $languagemodel -name $languagemodel -order 5 -unk
echo " done."

# Don't bother starting server
#echo "Running ngram server..."
#ngram -server-port 3433 -order 5 -debug 3 -memuse -lm $languagemodel -unk
