import math
import signal
import sys
import time
import argparse
import subprocess
import freeling
import re
import numpy as np
import logging
import os.path as path
from os import getpgid, killpg
from functools import reduce
from nltk.util import ngrams
from psutil import process_iter
#import n-gram model server

ts_lookups = 0

def scoreAlternatives(alternatives, sentToks, j, tokLower, nmax, client):
	"""Returns the original score, the maximum score, and the candidate that had the highest score.
	
	Expects a list of alternatives, a list of original tokens, an index for the current token, the current form of the token, a maximum value of n for n-grams, and a server client."""
	
	global server_lookups
	origScore = 0
	maxScore = 0
	argmaxScore = False
	
	# Look up ngrams for all the alternatives at once
	arrayLengths = [] # A list of lengths of the ngrams being looked up for
		# each alternative (may not always be the same if one
		# alternative is a blank)
	allNgrams = [] # The complete list of ngrams for all alternatives
	
	# For each alternative, add all n-grams to allNgrams and add the number of
	# n-grams being looked up to arrayLengths
	for alt in alternatives:
		ngrams = extractAllNGramsWithAlternative(sentToks, j, nmax, alt)
		arrayLengths.append(len(ngrams))
		allNgrams.extend(ngrams)
	allUttScores = client.scores_for_utterances(allNgrams)
	server_lookups += len(allNgrams)
	
	# print(allNgrams)
	
	# Now find the best scoring alternative, its score, and the original
	# score
	startIdx = 0
	i = 0
	for alt in alternatives:
		ngrams = extractAllNGramsWithAlternative(sentToks, j, nmax, alt)
		
		uttScores = allUttScores[startIdx:(startIdx + arrayLengths[i])]
		
		scoresAreNonIntegers = reduce(lambda x, y: x | y, map(lambda x: int(x) != float(x), uttScores))
		if scoresAreNonIntegers:
			logging.info("ERROR: received a non-integer score from the server!\n")
			sys.exit(0)
		
		scores = [np.log(float(x) + 1.0) for x in uttScores]
		score = np.mean(scores)  # Normalize by the number of ngrams
		logging.debug('Score for alternative {} is {}'.format(alt, score))
		if score > maxScore:
			maxScore = score
			argmaxScore = alt
		if tokLower == alt:
			origScore = score
		
		# Adjust the indices forward to the scores for the ngrams for
		# the next alternative
		startIdx += arrayLengths[i]
		i += 1
	
	return origScore, maxScore, argmaxScore

	
def extractAllNGramsWithAlternativeHelper(toks, i, n, alt):
	"""Returns a list of n-grams of value n containing the alternative.
	
	Expects a list of original tokens, an index for the alternative, a value of n, and the alternative itself."""
	
	res = [] # A list of resulting n-grams containing the alternative
	
	# Make copy of toks with alternative substituted in for the original
	toksCopy = []
	toksCopy.extend(toks)
	toksCopy[i] = alt
	
	# For j in range of indices in toksCopy 0 (or more if the index of alt
	# is farther away from the beginning than the value of n is) up to the
	# index of alt itself (inclusive), append the n-word subsequences of
	# toksCopy to res
	for j in range(max(0, i - n + 1), i + 1):
		# If j + n > the length of toksCopy, then obviously this
		# particular n-gram starting at index j will not be able to be
		# created, so continue to next iteration of loop
		if j + n > len(toksCopy):
			continue # Might as well be break since j will only get
				# larger with subsequent iterations
		#pdb.set_trace()
		subsequence = toksCopy[j:j + n]
		res.append(" ".join(subsequence)) # Add n-gram as string with
			# tokens separated by spaces
	
	# Remove the extra space that would result from considering a blank in
	# place of the prep/det.
	res = map(lambda x: re.sub(r"  +", " ", x), res)
	res = map(str.strip, res)
	
	# Make sure the ngram is not just a unigram (if alt is a space)
	res = filter(lambda x: re.search(" ", x), res)
	
	return res


def extractAllNGramsWithAlternative(toks, i, nmax, alt):
	"""Returns a list of all n-grams of all values of n containing the alternative.
	
	Expects a list of original tokens, an index for the alternative, a maximum value of n, and the alternative itself."""
	
	res = [] # A list of resulting n-grams containing the alternative
	minval = 1 # The minimum value on n, i.e., unigram
	
	# For n = 1 to n = nmax (inclusive), add the n-grams to res
	for n in range(minval, nmax + 1):
		res.extend(extractAllNGramsWithAlternativeHelper(toks, i, n, alt))
	return res


def detect_pckimmo(tagged_sentence, server_client, scratch, threshold):
	"""Returns a corrected sentence given an original, tagged sentence. Uses PC-Kimmo."""
	
	logging.info('Detecting noun number error in sentence: {}'.format(tagged_sentence))
	corrected_sentence = []
	
	words = []
	tags = []
	clause = True # Boolean for whether the sentence is a clause or not
		# (initialized to False)
	sent_tokens = tagged_sentence.split()
	if len(sent_tokens) > 0:
		if sent_tokens[0].upper() == 'CLAUSE':
			sent_tokens = sent_tokens[1:]
		elif sent_tokens[0].upper() == 'NONCLAUSE':
			logging.debug('Found a non-clause, skipping sentence.')
			sent_tokens = sent_tokens[1:]
			clause = False
	
	for word_tag in sent_tokens:
		wt_list = word_tag.split("_")
		# If there is an underscore somewhere else in the word besides right
		# before the tag, this list will have more than 2 items
		if len(wt_list) > 2:
			# Make sure to get the final item as the tag
			tags.append(wt_list[-1])
			# And join all the previous items back together as they had
			# originally been
			words.append("_".join(wt_list[:-1]))
		else:
			words.append(word_tag.split("_")[0])
			tags.append(word_tag.split("_")[1])
	
	if not clause:
		return " ".join(words)
	
	nmax = 5 #max number of ngrams
	
	logging.debug('Looking for nouns that have potential errors...')
	for index, tag in enumerate(tags):
		# Check all common nouns and see if we can generate the sg/pl alternatives
		current_form = words[index].lower()
		alternatives = []
		if tag.lower() == 'nn':
			logging.debug('Found a singular noun at index {}: {}'.format(index, current_form))
			# Singular noun, generate plural 
			temp_file = scratch + "/temp"
			
			with open(temp_file, 'w') as writer:
				writer.write('s `{} +PL\n'.format(current_form))
			
			command_str = '/home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/pckimmo/pckimmo -g /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.grm -r /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.rul -l /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.lex -s /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.lex < {}'.format(temp_file)
			logging.debug('Running morphology on noun: {}'.format(current_form))
			try:
				output = subprocess.check_output(command_str, shell=True,stderr=subprocess.STDOUT).decode("utf-8")
			except CalledProcessError as e:
				print("Running command \"{}\" failed: {}".format(command_str, e.output))
				sys.stderr.flush()
				raise e
			
			logging.debug('Morphology output: {}'.format(output))
			output = output.split('\n')
			analysis = output[len(output)-3:]
			if re.search(r'\*\*\* NONE \*\*\*', analysis[0]):
				pass
			else:
				for line in analysis:
					if re.search(r'\>', line):
						if len(line.split('>')) == 2:
							analysis_output = line.strip().split('>')[1]
							if len(analysis_output) > 0:
								alternatives.append(analysis_output)
					else:
						if len(line.strip()) > 0: # If there's something in the line
							alternatives.append(line.strip())
		
		elif tag.lower() == 'nns':
			logging.debug('Found a plural noun at index {}: {}'.format(index, current_form))
			# Plural noun, generate singular 
			temp_file = scratch + "/temp"
			
			with open(temp_file, 'w') as writer:
				writer.write('r {}\n'.format(current_form))
			
			command_str = '/home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/pckimmo/pckimmo -r /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.rul -l /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.lex -s /home/research/acahill/dynamic/CoNLL-shared-task-2013/conll-shared-task-2013/morphology/pc-parse-20051207/english_morphology/english.lex < {}'.format(temp_file)
			
			logging.debug('Running morphology on noun: {}'.format(current_form))
			try:
				output = subprocess.check_output(command_str, shell=True,stderr=subprocess.STDOUT).decode("utf-8")
			except CalledProcessError as e:
				print("Running command \"{}\" failed: {}".format(command_str, e.output))
				sys.stderr.flush()
				raise e
			
			logging.debug('Morphology output: {}'.format(output))
			output = output.split('\n')
			
			for line in output:
				if re.search('\+PL', line):
					line = line.split()
					analysis = line[0]
					if re.search('>', analysis):
						analysis = analysis.split('>')[1]
						analysis = analysis.split('+')
						if len(analysis) == 2:
							analysis = re.sub(r'`', r'', analysis[0])
							if len(analysis) > 0:
								alternatives.append(analysis)
					else:
						analysis = analysis.split('+')
						if len(analysis) == 2:
							analysis = re.sub(r'`', r'', analysis[0])
							if len(analysis) > 0:
								alternatives.append(analysis)
		
		if len(alternatives) > 0:
			alternatives.append(current_form)
			logging.debug('Searching for the best choice among: {}'.format(alternatives))
			logging.debug('Words: {}'.format(words))
			logging.debug('Index: {}'.format(index))
			logging.debug('Current form: {}'.format(current_form))
			logging.debug('NMax: {}'.format(nmax))
			origScore, maxScore, argmaxScore = scoreAlternatives(alternatives, words, index, current_form, nmax, server_client)
			if origScore != maxScore:
				logging.debug('origScore: {}'.format(str(origScore)))
				logging.debug('maxScore: {}'.format(str(maxScore)))
				logging.debug('argmaxScore: {}'.format(argmaxScore))
				logging.debug('current_form: {}'.format(current_form))
				logging.debug('{}: {}'.format(tag, str(alternatives)))
			
			if (maxScore - origScore) > threshold:
				logging.info('Replacing {} with {} because ({} - {}) > {}'.format(current_form, argmaxScore, maxScore, origScore, threshold))
				# Replace the current form with the alternative
				corrected_sentence.append(argmaxScore)
			else:
				corrected_sentence.append(words[index])
		
		else:
			corrected_sentence.append(words[index])
	
	# Return the features
	return ' '.join(corrected_sentence)


def detect_freeling(tagged_sentence, server_client, threshold):
	"""Returns a corrected sentence given an original, tagged sentence. Uses the C++ resource Freeling Dictionary."""
	
	logging.info('Detecting noun number error in sentence: {}'.format(tagged_sentence))
	corrected_sentence = [] # A list to hold the tokens of the corrected
		# sentence
	
	words = []
	tags = []
	clause = True # Boolean for whether the sentence is a clause or not
		# (initialized to False)
	sent_tokens = tagged_sentence.split()
	if len(sent_tokens) > 0:
		if sent_tokens[0].upper() == 'CLAUSE':
			sent_tokens = sent_tokens[1:]
		elif sent_tokens[0].upper() == 'NONCLAUSE':
			logging.debug('Found a non-clause, skipping sentence.')
			sent_tokens = sent_tokens[1:]
			clause = False
	
	for word_tag in sent_tokens:
		wt_list = word_tag.split("_")
		# If there is an underscore somewhere else in the word besides right
		# before the tag, this list will have more than 2 items
		if len(wt_list) > 2:
			# Make sure to get the final item as the tag
			tags.append(wt_list[-1])
			# And join all the previous items back together as they had
			# originally been
			words.append("_".join(wt_list[:-1]))
		else:
			words.append(word_tag.split("_")[0])
			tags.append(word_tag.split("_")[1])
	
	sentence = " ".join(words)
	
	if not clause:
		return sentence
	
	sentence = sentence.strip()
	logging.debug('This is the sentence: {}'.format(sentence))
	
	# Modify this line to be your FreeLing installation directory
	FREELINGDIR = "/RHS/NLP/text-dynamic/mmulholland/conll-shared-task-2013/ets_noun_number/freeling-3.1"
	
	DATA = FREELINGDIR+"/data/"
	LANG ="en"
	
	freeling.util_init_locale("default")
	
	# Create options set for maco analyzer. Default values are Ok, except for data files.
	op = freeling.maco_options("en")
	op.set_active_modules(0,1,1,1,1,1,1,1,1,1)
	op.set_data_files("",DATA+LANG+"/locucions.dat", DATA+LANG+"/quantities.dat", DATA+LANG+"/afixos.dat", DATA+LANG+"/probabilitats.dat", DATA+LANG+"/dicc.src", DATA+LANG+"/np.dat", DATA+"common/punct.dat")
	
	# Create analyzers
	tk = freeling.tokenizer(DATA+LANG+"/tokenizer.dat")
	sp = freeling.splitter(DATA+LANG+"/splitter.dat")
	mf = freeling.maco(op)
	tg = freeling.hmm_tagger(DATA+LANG+"/tagger.dat",1,2)
	dic = freeling.dictionary("en", DATA+LANG+"/dicc.src",1,DATA+LANG+"/afixos.dat",1,1)
	
	sent = tk.tokenize(sentence)
	sent = sp.split(sent,1)
	sent = mf.analyze(sent)
	sent = tg.analyze(sent)
	sent = dic.analyze(sent)
	
	nmax = 5 # Max number of ngrams
	
	logging.debug('Looking for nouns that have potential errors...')
	for index, tag in enumerate(tags):
		# Check all common nouns and see if we can generate the sg/pl
		# alternatives
		current_form = words[index].lower()
		alternatives = [] # A list to store sg/pl alternatives of the
			# current_form
		new_form = None
		if tag == 'nn' or tag == 'NN':
			# Singular noun, generate plural
			logging.debug('Found a singular noun at index {}: {}'.format(index, current_form))
			logging.debug('Running morphology on noun: {}'.format(current_form))
			# Find the correct token in sent, which could be different
			# since Freeling analyzes sentences in a different way
			beg = index - 5
			end = index + 5
			if beg < 0:
				beg = 0
			if end > len(sent[0]) - 1:
				end = len(sent[0]) - 1
			ind = beg
			while ind <= end:
				logging.debug('Trying {} at index {} in sentence: {}'.format(sent[0][ind].get_form(), ind, sentence))
				if current_form == sent[0][ind].get_form():
					if len(dic.get_forms(sent[0][ind].get_lemma(), 'NNS')) > 0:
						new_form = dic.get_forms(sent[0][ind].get_lemma(), 'NNS')[0]
						logging.debug('Morphology output: {}'.format(new_form))
					break
				ind += 1
			if new_form == None:
				logging.debug('Could not find current_form, {}, in sentence!'.format(current_form))
				new_form = current_form # So that the value None is not appended to the
					# alternatives list
			if not new_form in alternatives:
				alternatives.append(new_form)
		elif tag == 'nns' or tag == 'NNS':
			# Plural noun, generate singular
			logging.debug('Found a plural noun at index {}: {}'.format(index, current_form))
			logging.debug('Running morphology on noun: {}'.format(current_form))
			# Find the correct token in sent, which could be different
			# since Freeling analyzes sentences in a different way
			beg = index - 5
			end = index + 5
			if beg < 0:
				beg = 0
			if end > len(sent[0]) - 1:
				end = len(sent[0]) - 1
			ind = beg
			while ind <= end:
				logging.debug('Trying {} at index {} in sentence: {}'.format(sent[0][ind].get_form(), ind, sentence))
				if current_form == sent[0][ind].get_form():
					if len(dic.get_forms(sent[0][ind].get_lemma(), 'NN')) > 0:
						new_form = dic.get_forms(sent[0][ind].get_lemma(), 'NN')[0]
						logging.debug('Morphology output: {}'.format(new_form))
					break
				ind += 1
			if new_form == None:
				logging.debug('Could not find current_form, {}, in sentence!'.format(current_form))
				new_form = current_form # So that the value None is not appended to the
					# alternatives list
			if not new_form in alternatives:
				alternatives.append(new_form)
		
		# If there are alternatives
		if len(alternatives) > 0:
			alternatives.append(current_form)
			logging.debug('Searching for the best choice among: {}'.format(alternatives))
			logging.debug('Words: {}'.format(words))
			logging.debug('Index: {}'.format(index))
			logging.debug('Current form: {}'.format(current_form))
			logging.debug('NMax: {}'.format(nmax))
			#print('Alternatives: {}\nWords: {}\nIndex: {} \nCurrent Form: {}\nNMax: {}'.format(alternatives, words, index, current_form, nmax))
			# Score the alternative, if this is a noun and an alternative could be
      # generated
			origScore, maxScore, argmaxScore = scoreAlternatives(alternatives, words, index, current_form, nmax, server_client)
			if origScore != maxScore:
				logging.debug('origScore: {}'.format(str(origScore)))
				logging.debug('maxScore: {}'.format(str(maxScore)))
				logging.debug('argmaxScore: {}'.format(argmaxScore))
				logging.debug('current_form: {}'.format(current_form))
				logging.debug('{}: {}'.format(tag, str(alternatives)))
			
			if (maxScore - origScore) > threshold:
				logging.info('Replacing {} with {} because ({} - {}) > {}'.format(current_form, argmaxScore, maxScore, origScore, threshold))
				# Replace the current form with the alternative
				corrected_sentence.append(argmaxScore)
			else:
				corrected_sentence.append(words[index])
		
		else:
			corrected_sentence.append(words[index])
	
	# Return the features
	return ' '.join(corrected_sentence)


def detect_lingua(tagged_sentence, server_client, threshold):
	"""Returns a corrected sentence given an original, tagged sentence. Uses the Perl module Lingua::EN::Inflect."""
	
	logging.info('Detecting noun number error in sentence: {}'.format(tagged_sentence))
	corrected_sentence = [] # A list to hold the tokens of the corrected
		# sentence
	
	words = []
	tags = []
	clause = True # Boolean for whether the sentence is a clause or not
		# (initialized to False)
	sent_tokens = tagged_sentence.split()
	if len(sent_tokens) > 0:
		if sent_tokens[0].upper() == 'CLAUSE':
			sent_tokens = sent_tokens[1:]
		elif sent_tokens[0].upper() == 'NONCLAUSE':
			logging.debug('Found a non-clause, skipping sentence.')
			sent_tokens = sent_tokens[1:]
			clause = False
	
	for word_tag in sent_tokens:
		wt_list = word_tag.split("_")
		# If there is an underscore somewhere else in the word besides right
		# before the tag, this list will have more than 2 items
		if len(wt_list) > 2:
			# Make sure to get the final item as the tag
			tags.append(wt_list[-1])
			# And join all the previous items back together as they had
			# originally been
			words.append("_".join(wt_list[:-1]))
		else:
			words.append(word_tag.split("_")[0])
			tags.append(word_tag.split("_")[1])
	
	if not clause:
		return " ".join(words)
	
	nmax = 5 # Max number of ngrams
	
	logging.debug('Looking for nouns that have potential errors...')
	for index, tag in enumerate(tags):
		# Check all common nouns and see if we can generate the sg/pl
		# alternatives
		current_form = words[index].lower()
		alternatives = [] # A list to store sg/pl alternatives of the
			# current_form
		new_form = None
		if tag == 'nn' or tag == 'NN':
			# Singular noun, generate plural
			logging.debug('Found a singular noun at index {}: {}'.format(index, current_form))
			logging.debug('Running morphology on noun: {}'.format(current_form))
			word = re.sub(r'([&*\$\%\#\@\!\~\`\?\<\>\.\,\:\;\{\}\[\]\'\"])', r'\\\1', words[index].lower())
			cmd = "perl /home/nlp-text/dynamic/mmulholland/conll-shared-task-2013/ets_noun_number/inflect.pl 1 {}".format(word)
			try:
				output = subprocess.check_output(cmd, shell=True,stderr=subprocess.STDOUT)
			except CalledProcessError as e:
				print("Running command \"{}\" failed: {}".format(cmd, e.output))
				sys.stderr.flush()
				raise e
			
			if output:
				logging.debug('Got morphological variant from Lingua::EN::Inflect module. The variant: {}'.format(output.decode("utf-8")))
				new_form = output.decode("utf-8").strip()
			else:
				logging.debug('The output of the Perl script was invalid.')
			
			if new_form and not new_form in alternatives:
				logging.debug('The variant found was not already in the list of alternatives, so it\'s being appended.')
				alternatives.append(new_form)
		elif tag == 'nns' or tag == 'NNS':
			# Plural noun, generate singular
			logging.debug('Found a plural noun at index {}: {}'.format(index, current_form))
			logging.debug('Running morphology on noun: {}'.format(current_form))
			word = re.sub(r'([&*\$\%\#\@\!\~\`\?\<\>\.\,\:\;\{\}\[\]\'\"])', r'\\\1', words[index].lower())
			cmd = "perl /home/nlp-text/dynamic/mmulholland/conll-shared-task-2013/ets_noun_number/inflect.pl 0 {}".format(word)
			try:
				output = subprocess.check_output(cmd, shell=True,stderr=subprocess.STDOUT)
			except CalledProcessError as e:
				print("Running command \"{}\" failed: {}".format(cmd, e.output))
				sys.stderr.flush()
				raise e
			
			if output:
				logging.debug('Got morphological variant from Lingua::EN::Inflect module. The variant: {}'.format(output.decode("utf-8")))
				new_form = output.decode("utf-8").strip()
			else:
				logging.debug('The output of the Perl script was invalid.')
			
			if new_form and not new_form in alternatives:
				logging.debug('The variant found was not already in the list of alternatives, so it\'s being appended.')
				alternatives.append(new_form)
		
		# If there are alternatives
		if len(alternatives) > 0:
			alternatives.append(current_form)
			logging.debug('Searching for the best choice among: {}'.format(alternatives))
			logging.debug('Words: {}'.format(words))
			logging.debug('Index: {}'.format(index))
			logging.debug('Current form: {}'.format(current_form))
			logging.debug('NMax: {}'.format(nmax))
			#print('Alternatives: {}\nWords: {}\nIndex: {} \nCurrent Form: {}\nNMax: {}'.format(alternatives, words, index, current_form, nmax))
			# Score the alternative, if this is a noun and an alternative could be
      # generated
			origScore, maxScore, argmaxScore = scoreAlternatives(alternatives, words, index, current_form, nmax, server_client)
			if origScore != maxScore:
				logging.debug('origScore: {}'.format(str(origScore)))
				logging.debug('maxScore: {}'.format(str(maxScore)))
				logging.debug('argmaxScore: {}'.format(argmaxScore))
				logging.debug('current_form: {}'.format(current_form))
				logging.debug('{}: {}'.format(tag, str(alternatives)))
			
			if (maxScore - origScore) > threshold:
				logging.info('Replacing {} with {} because ({} - {}) > {}'.format(current_form, argmaxScore, maxScore, origScore, threshold))
				# Replace the current form with the alternative
				corrected_sentence.append(argmaxScore)
			else:
				corrected_sentence.append(words[index])
		
		else:
			corrected_sentence.append(words[index])
	
	# Return the features
	return ' '.join(corrected_sentence)


def detect_jedimorph(tagged_sentence, server_client, threshold):
	"""Returns a corrected sentence given an original, tagged sentence. Uses Michael Flor's Jedimorph component."""
	
	logging.info('Detecting noun number error in sentence: {}'.format(tagged_sentence))
	corrected_sentence = [] # A list to hold the tokens of the corrected
		# sentence
	
	words = []
	tags = []
	clause = True # Boolean for whether the sentence is a clause or not
		# (initialized to False)
	sent_tokens = tagged_sentence.split()
	if len(sent_tokens) > 0:
		if sent_tokens[0].upper() == 'CLAUSE':
			sent_tokens = sent_tokens[1:]
		elif sent_tokens[0].upper() == 'NONCLAUSE':
			logging.debug('Found a non-clause, skipping sentence.')
			sent_tokens = sent_tokens[1:]
			clause = False
	
	for word_tag in sent_tokens:
		wt_list = word_tag.split("_")
		# If there is an underscore somewhere else in the word besides right
		# before the tag, this list will have more than 2 items
		if len(wt_list) > 2:
			# Make sure to get the final item as the tag
			tags.append(wt_list[-1])
			# And join all the previous items back together as they had
			# originally been
			words.append("_".join(wt_list[:-1]))
		else:
			words.append(word_tag.split("_")[0])
			tags.append(word_tag.split("_")[1])
	
	if not clause:
		return " ".join(words)
	
	nmax = 5 # Max number of ngrams
	
	logging.debug('Looking for nouns that have potential errors...')
	for index, tag in enumerate(tags):
		# Check all common nouns and see if we can generate the sg/pl
		# alternatives
		current_form = words[index].lower()
		alternatives = [] # A list to store sg/pl alternatives of the
			# current_form
		new_form = None
		nn_tags = ['NN', 'nn', 'NNS', 'nns']
		if tag in nn_tags:
			# Found singular or plural noun, generate other form(s)
			logging.debug('Found noun at index {}: {}'.format(index, current_form))
			logging.debug('Running morphology on noun: {}'.format(current_form))
			word = re.sub(r'([&*\$\%\#\@\!\~\`\?\<\>\.\,\:\;\{\}\[\]\'\"])', r'\\\1', words[index].lower())
			cmd = "java -jar /home/nlp-text/dynamic/NLPTools/jediMorph/v.0.2/jediMorph.jar dbfile=/home/nlp-text/dynamic/NLPTools/jediMorph/v.0.2/jediMorph2.tstb requests=getothernouns {}".format(word)
			try:
				output = subprocess.check_output(cmd, shell=True,stderr=subprocess.STDOUT)
			except CalledProcessError as e:
				print("Running command \"{}\" failed: {}".format(cmd, e.output))
				sys.stderr.flush()
				raise e
			
			if output:
				output = output.decode("utf-8")
				for line in output.split("\n"):
					if line.startswith(r"["):
						# If the length of the line is > 2, i.e., it has some
						# content in between the square brackets ...
						if len(line) > 2:
							new_form = line[1:-1] # Cut off square brackets
							logging.debug('Got morphological variant from jediMorph module. The variant: {}'.format(new_form))
							break
			else:
				logging.debug('The output from jediMorph was invalid.')
			
			if new_form and not new_form in alternatives:
				logging.debug('The variant found was not already in the list of alternatives, so it\'s being appended.')
				alternatives.append(new_form)
		
		# If there are alternatives
		if len(alternatives) > 0:
			alternatives.append(current_form)
			logging.debug('Searching for the best choice among: {}'.format(alternatives))
			logging.debug('Words: {}'.format(words))
			logging.debug('Index: {}'.format(index))
			logging.debug('Current form: {}'.format(current_form))
			logging.debug('NMax: {}'.format(nmax))
			#print('Alternatives: {}\nWords: {}\nIndex: {} \nCurrent Form: {}\nNMax: {}'.format(alternatives, words, index, current_form, nmax))
			# Score the alternative, if this is a noun and an alternative could be
      # generated
			origScore, maxScore, argmaxScore = scoreAlternatives(alternatives, words, index, current_form, nmax, server_client)
			if origScore != maxScore:
				logging.debug('origScore: {}'.format(str(origScore)))
				logging.debug('maxScore: {}'.format(str(maxScore)))
				logging.debug('argmaxScore: {}'.format(argmaxScore))
				logging.debug('current_form: {}'.format(current_form))
				logging.debug('{}: {}'.format(tag, str(alternatives)))
			
			if (maxScore - origScore) > threshold:
				logging.info('Replacing {} with {} because ({} - {}) > {}'.format(current_form, argmaxScore, maxScore, origScore, threshold))
				# Replace the current form with the alternative
				corrected_sentence.append(argmaxScore)
			else:
				corrected_sentence.append(words[index])
		
		else:
			corrected_sentence.append(words[index])
	
	# Return the features
	return ' '.join(corrected_sentence)


def main():
	# Get command line arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-i','--input_file', help="tagged input file", type=str, required=True)
	parser.add_argument('-o','--output_file', help="plain text output file", type=str, required=True)
	parser.add_argument('--morph', help="Morphological component to use: PC-KIMMO, Freeling, Lingua::EN::Inflect, or jediMorph.", choices=['pckimmo', 'freeling', 'lingua', 'jedimorph'], type=str, required=True)
	parser.add_argument('-p', '--port', help="port number to try to connect on", type=int, required=True)
	parser.add_argument('--scratch', help="a \"scratch\" path for writing temp files during processing", type=str, default='/scratch/mmulholland')
	parser.add_argument('--threshold', help="threshold value", type=float, default=0)
	parser.add_argument('--log_level', help="level of logging specificity", type=str, choices=['info', 'debug', 'warning'], default='info')
	
	args = parser.parse_args()
	
	# Initialize the loggers
	log = args.log_level
	if log == 'info':
		logging.basicConfig(level=logging.INFO)
	elif log == 'debug':
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.WARNING)
	
	logging.info('Making sure that all the paths and the threshold value are valid ...')
	# Make sure the threshold is a valid float integer that is greater
	# than or equal to 0
	# Note: The first part shouldn't be necessary since argparse should
	# require that this argument is a float by definition, but it's here
	# just in case.
	try:
		threshold = float(args.threshold)
		logging.info('Threshold: {}'.format(str(threshold)))
	except ValueError as e:
		logging.info('An invalid value was input for threshold. Exiting.')
		sys.exit(1)
	if threshold < 0:
		logging.info('A threshold of less than zero was attempted. Exiting.')
		sys.exit(1)
	
	# Check to see if the input/output/scratch paths exist
	if path.exists(path.abspath(args.input_file)):
		input_file = path.abspath(args.input_file)
	else:
		logging.info('\n\nThe input file could not be found. Exiting.')
		sys.exit(1)
	
	if path.exists(path.abspath(path.dirname(args.output_file))):
		output_file = path.abspath(args.output_file)
	else:
		logging.info('\n\nThe input file could not be found. Exiting.')
		sys.exit(1)
	
	if args.morph == "pckimmo":
		if not path.exists(path.abspath(args.scratch)):
			logging.info('The scratch path/directory, {}, is invalid. (Here\'s the absolute version, if it sheds any light on the issue: {}.) Exiting.'.format(args.scratch, path.abspath(args.scratch)))
			sys.exit(1)
		else:
			if args.scratch[-1] == "/":
				scratch = args.scratch[:-1]
			else:
				scratch = args.scratch
	logging.info('Everything appears good to go. Initiating processing.')
	
	# Read from input_file and append lines to tagged_sentences
	tagged_sentences = []
	with open(input_file, 'r') as reader:
		for line in reader.readlines():
			tagged_sentences.append(line.lower().strip())
	reader.close()
	
	# Check whether the server is running
	found = False
	for proc in process_iter():
		if proc.name == 'java':
			logging.debug('Found java process.')
			for arg in proc.cmdline:
				if arg.endswith('ts_server.py'):
					if str(args.port) in proc.cmdline:
						found = True
						logging.info('Found server at pid {} in pgid {}.\n'.format((str(proc.pid)), str(getpgid(proc.pid))))
						break
			if found:
				break
	
	if not found:
		logging.info('Cannot find server. Exiting.')
		sys.exit(1)
	
	# Initialize the client to connect to the running server
	while 1:
		logging.info('Trying to connect to the server ...')
		try:
			client = TrendStreamClient('localhost', args.port, 25)
		except:
			time.sleep(5)
		else:
			break
	
	# Using the morphological component passed in via the command-line, build
	# a list of corrected sentences
	if args.morph == 'pckimmo':
		logging.info('The chosen morphological component: PC-KIMMO')
		corrected_sentences = [detect_pckimmo(x, client, scratch, threshold) for x in tagged_sentences]
	elif args.morph == 'freeling':
		logging.info('The chosen morphological component: Freeling Dictionary')
		corrected_sentences = [detect_freeling(x, client, threshold) for x in tagged_sentences]
	elif args.morph == "lingua":
		logging.info('The chosen morphological component: The Perl Module, Lingua::EN::Inflect')
		corrected_sentences = [detect_lingua(x, client, threshold) for x in tagged_sentences]
	elif args.morph == "jedimorph":
		logging.info('The chosen morphological component: jediMorph')
		corrected_sentences = [detect_jedimorph(x, client, threshold) for x in tagged_sentences]
	else:
		# It probably should not be able to get to this point since
		# argparse should already have dealt with this kind of
		# issue, but nevertheless
		logging.info('The morphological component was not recognized. Exiting.')
		sys.exit(1)
	
	# Uncomment these lines if you want the server to be killed
	# after the script completes
	#logging.info('Now killing the server ...')
	# Kill the server if we started it
	#for proc in process_iter():
	#	if proc.name == 'java':
	#		for arg in proc.cmdline:
	#			if arg.endswith('ts_server.py'):
	#				sys.stderr.write('Found server at pid {} in pgid {}.\n'.format((str(proc.pid)), str(getpgid(proc.pid))))
	#				sys.stderr.write('Stopping server ... ')
	#				killpg(getpgid(proc.pid), signal.SIGTERM)
	#				time.sleep(2)
	#				sys.stderr.write('done.\n')
	
	logging.info('Writing output file ...')
	with open(output_file, 'w') as writer:
		for s in corrected_sentences:
			writer.write('{}\n'.format(s))
	writer.close()
	logging.info('Complete.')


if __name__ == '__main__':
	main()
