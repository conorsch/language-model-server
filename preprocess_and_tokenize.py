#!/usr/bin
from __future__ import print_function
import sys
import re
import os
from nltk import word_tokenize
import nltk.data
import argparse

def tokenize(line):
	"""Tokenizes a line of text, separates out the sentences in the line (if more than one), and returns tokenized sentence(s) as list."""
	
	line = re.sub('`', r' ', line)
		# Doesn't work for some reason when run as part of this program
		# Yet, it works in testing on IDLE ...
	
	# Tokenize line(s)
	line_tokens = word_tokenize(line.strip())
	
	# Do sentence tokenization
	tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
	sents = tokenizer.tokenize(" ".join(line_tokens))
	
	return sents


def main():
	# Get command line arguments
	parser = argparse.ArgumentParser(description="Read in a Gigaword file and preprocess it, outputting to standard output.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('infile', help='Gigaword file; can be piped in via cat, more, etc.', type=argparse.FileType('r'), default='-', nargs='?')
	#parser.add_argument('-out', '--outfile', help='Output file', type=argparse.FileType('w'), required=True)
	args = parser.parse_args()
	
	# Punctuation set
	punct = set(['?', "'", '"', '!', '.', ')'])
	
	if args.infile.isatty():
		sys.stderr.write("You are running this script interactively. Press CTRL-D at the\
			start of a blank line to signal the end of your input. For help,\
			run it with --help\n")
	#else:
		#if os.path.exists(os.path.abspath(args.infile)) and os.path.exists(os.path.dirname(args.outfile)):
		#	output_file_path = os.path.abspath(output_file_path)
		#else:
		#	sys.stderr.write('The given outfile (and/or infile, if applicable) path arguments do not contain valid paths. Exiting.')
		#	sys.exit(1)
	
	lines = args.infile.readlines()
	i = 0
	while i < len(lines):
		
		# Get rid of beginning/end of sentence tags
		line = re.sub(r'</?s>', r'', lines[i])
		
		# Get rid of empty lines
		if len(line.strip()) == 0:
			i+=1
			continue
		
		# If end of line has a punctuation mark, do tokenization and move on.
		# Get rid of lines that have 15 or less total characters since they
		# are probably not good sentences.
		if line.strip()[-1] in punct:
			sents = tokenize(line.strip())
			for sent in sents:
				if len(sent) > 15:
					print("{}".format(sent),end="\n")
			i+=1
		# If the end of the line does not contain a punctuation mark, look at
		# the end of the following line and then the line after that to see if
		# they have line-ending punctuation. If so, include them as well so
		# that at least one sentence is included. It doesn't matter if there
		# are multiple sentences.
		else:
			one = False
			two = False
			try:
				
				if re.sub(r'</?s>', r'', lines[i + 1]).strip()[-1] in punct:
					line = line + " " + re.sub(r'</?s>', r'', lines[i + 1]).strip()
					one = True
				elif re.sub(r'</?s>', r'', lines[i + 2]).strip()[-1] in punct:
					line = line + " " + re.sub(r'</?s>', r'', lines[i + 1]).strip() + " " + re.sub(r'</?s>', r'', lines[i + 2]).strip()
					two = True
					
				if one:
					sents = tokenize(line)
					i += 2
				elif two:
					sents = tokenize(line)
					i += 3
				else:
					sents = tokenize(line.strip())
					i += 1
				
			except IndexError:
				sents = tokenize(line.strip())
				i += 1
			
			for sent in sents:
				if len(sent) > 15:
					print("{}".format(sent),end="\n")


if __name__ == '__main__':
	main()
