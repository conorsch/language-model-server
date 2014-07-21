#!/usr/bin/python -tt
from nltk.probability import FreqDist
from nltk.probability import SimpleGoodTuringProbDist as sgt_pdist

ngram_fdist_dict = {}

def make_fdist(file_path, n):
	"""Count n-grams in text.
	
	Parameters
	----------
		file_path : str
			Path to text file.
		n : int
			Order n
	
	Raises
	------
		TypeError
			If n is not greater than zero.
	
	Returns
	-------
		dict
			Dictionary containing a frequency distribution of the n-grams up to the given value of n in the given text file. The dictionary will contain a mapping between strings and frequencies.
	"""
	
	global ngram_fdist_dict
	
	if n <= 0:
		raise TypeError('n is not greater than zero.')
	
	with open(file_path, 'r') as corpus:
		text = corpus.readlines()
		# Limited to first 100,000 lines of file just
		# for testing purposes
		#for line in text:
		for line in text[:100000]:
			if not line.strip():
				continue
			# Add in beginning- and end-of-sentence tags
			line = "<s> {} </s>".format(line)
			grams = line.split()
			# For n-grams for n = 1 to n
			if n > 1:
				for j in range(1, n):
					get_ngrams(grams, j)
			else:
				get_ngrams(grams, 1)
	
	return ngram_fdist_dict


def get_ngrams(grams, n):
	"""Compile list of n-grams and add to global dict ngram_fdist_dict.
	
	Parameters
	----------
		grams : list of str
			Tokens, i.e., "grams"
		n : int
			Order n > 0
	
	Raises
	------
		TypeError
			If n is not greater than zero.
	"""
	
	global ngram_fdist_dict
	
	if n <= 0:
		raise TypeError('n is not greater than zero.')
	
	for i in range(len(grams)):
		if i + (n - 1) < len(grams):
			ngram = ""
			for m in range(n):
				ngram = "{} {}".format(ngram.strip(),
					grams[m])
			# Strip off leading/trailing spaces
			ngram = ngram.strip()
			# Add ngram to ngram_fdist_dict
			ngram_fdist_dict[ngram] = \
				ngram_fdist_dict.get(ngram, 0) + 1


def make_freq_of_freq_dist(freq_dist):
	"""Return a frequency of frequencies distribution.
	
	Parameters
	----------
		freq_dist : dict
			Dictionary containing a frequency distribution, i.e., a mapping from strings to frequencies.
	
	Returns
	-------
		dict
			Dictionary containing the frequency of frequencies distribution, i.e., a mapping from frequencies to frequencies.
	"""
	
	f_of_fdist = {}
	
	for key in freq_dist.keys():
		f_of_fdist[freq_dist[key]] = f_of_fdist.get( \
			freq_dist[key], 0) + 1
	
	return f_of_fdist


def make_simple_good_turing_prob_dist(freq_dist):
	"""Return a Simple Good-Turing probability distribution.
	
	Parameters
	----------
		freq_dist : dict
			Dictionary containing a frequency distribution, i.e., a mapping from strings to frequencies.
	
	Returns
	-------
		SimpleGoodTuringProbDist object
			A Simple Good-Turing probability distribution object, i.e., a mapping from strings to probabilities and methods/variables for related information.
	"""
	
	# Instantiate a FreqDist object with the freq_dist
	fdist = FreqDist(freq_dist)
	
	# Instantiate and return a SimpleGoodTuringProbDist with fdist
	return sgt_pdist(fdist)


def get_sample_probs(simple_good_turing_prob_dist):
	"""Print out a list of 20 samples, their original counts, and their Simple Good-Turing probabilities.
	
	Parameters
	----------
		simple_good_turing_prob_dist : SimpleGoodTuringProbDist object
			A Simple Good-Turing probability distribution object, i.e., a mapping from strings to probabilities and methods/variables for related information.
	"""
	
	assert len(simple_good_turing_prob_dist._freqdist.keys()) \
		> 20, "There are not enough samples."
		
	
	for key in \
		simple_good_turing_prob_dist._freqdist.keys()[0:20]:
		print "Sample: \"{}\"".format(key)
		print "Count: {}".format(str( \
			simple_good_turing_prob_dist._freqdist[key]))
		print "Probability: {}".format( \
			simple_good_turing_prob_dist.prob(key))
		print "\n"