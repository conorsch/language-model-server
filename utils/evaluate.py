#!/usr/bin/python -tt
import sys
import os
import argparse
import logging
import re
import csv

class file_data():
	"""A class for file_data objects."""
	
	def __init__(self):
		"""Constructor method."""
	
		self.gs_lines = [] # Store the gold standard file's lines as lists
			# of the lower-case tokens in each line
		self.ol_tagged = [] # Store the original file's tagged
			# lines as lists of the word_tag tokens in each line
		self.ol_untagged = [] # Store the original file's untagged
			# lines as lists of the lower-case word tokens in each line
		self.so_lines = [] # Store the sytem output file's
			# lines as lists of the lower-case tokens in each line
		self.tags = [] # Store the POS-tags of the file's lines as lists
			# of the POS-tags in each line
		self.annotations = [] # Store a list of annotation objects for the
			# file (both gold and system) that contains instances of both
			# agreement (for tokens with NN/NNS tags that are unannotated
			# in both the gold standard and system output files) and
			# disagreement
	
	
	def add_gs_lines(self, path):
		"""A member subroutine that reads lines from the given file and stores them in the file_data object's gs_lines member variable."""
		
		with open(path, 'rU') as gs_file:
			for line in gs_file.readlines():
				toks = []
				lineToks = line.lower().split()
				# Get rid of trailing punctuation in the original token for corrections,
				# i.e., "theft.***thefts" --> "theft***thefts"
				for tok in lineToks:
					re.sub(r'[\.,:;\-\'\\"\(\)\[\]\{\}_`~\+\!@#%]+\*\*\*', r'***', tok)
					toks.append(tok)
				self.gs_lines.append(toks)
		gs_file.close()
	
	
	def add_ol_tagged(self, path):
		"""A member subroutine that reads lines from the given file and stores them in the file_data object's ol_tagged member variable."""
		
		with open(path, 'rU') as orig_file:
			for line in orig_file.readlines():
				if len(line.split()) > 0:
					if line.split()[0].upper() == "CLAUSE" or line.split()[0].upper() == "NONCLAUSE":
						self.ol_tagged.append(line.split()[1:])
					else:
						self.ol_tagged.append(line.split())
		orig_file.close()
	
	
	def add_so_lines(self, path):
		"""A member subroutine that reads lines from the given file and stores them in the file_data object's so_lines member variable."""
		
		with open(path, 'rU') as so_file:
			for line in so_file.readlines():
				self.so_lines.append(line.lower().split())
		so_file.close()
	
	
	def set_tags_and_ol_untagged(self):
		"""A member subroutine that sets the file_data object's ol_untagged and tags member variables."""
		
		for line in self.ol_tagged:
			tags = []
			words = []
			for word_tag in line:
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
					words.append(word_tag.split("_")[0].lower())
					tags.append(word_tag.split("_")[1])
			
			self.tags.append(tags)
			self.ol_untagged.append(words)
	
	
	def add_annotation(self, annotation_obj):
		"""A member subroutine that adds an annotation object to the file_data object's annotations member variable."""
		
		self.annotations.append(annotation_obj)


class annotation():
	"""A class for annotation objects."""
	
	def __init__(self, orig_token, gold_token, system_token):
		"""Constructor Method."""
		
		self.orig_tok = orig_token # Store the original token
		self.gold_tok = gold_token # Store the gold standard correction
		self.system_tok = system_token # Store the
			# system correction
		self.orig_tag = None # Store the POS-tag of the original token
		self.line_index = None # Store the line index that the annotation
			# occurs in
		self.tok_index = None # Store the token index that the annotation
			# occurs at
	
	
	def set_orig_tag(self, tag_string):
		"""A member subroutine that sets the annotation object's orig_tag member variable."""
		
		self.orig_tag = tag_string
	
	
	def set_line_index(self, index):
		"""A member subroutine that sets the annotation object's line_index member variable."""
		
		self.line_index = index
	
	
	def set_tok_index(self, index):
		"""A member subroutine that sets the annotation object's tok_index member variable."""
		
		self.tok_index = index



def add_annotations(file_obj):
	"""Populate annotations in file_obj.annotations."""
	
	# List of determiners to exclude from consideration
	dets = ["the", "this", "these", "that", "those", "a", "an", "any", "some", "none"]
	
	# List of POS-tags to include
	tags = ["nn", "nns", "nn-sbj", "nns-sbj"]
	
	# Go through the lines in the test file and find all the opportunities
	# for agreement and disagreement (i.e., for tokens that are tagged as NN or 
	# NNS) and create annotation objects for them and add them to the
	# file_data_obj.annotations
	for l in range(len(file_obj.gs_lines)):
		for t in range(len(file_obj.gs_lines[l])):
			# If the tag is NN or NNS ...
			if file_obj.tags[l][t].lower() in tags:
				logging.debug('\nFound NN/NNS-tagged token:\nOriginal: {}\nSystem output: {}\nGold standard: {}'.format(file_obj.ol_untagged[l][t], file_obj.so_lines[l][t], file_obj.gs_lines[l][t]))
				# If there is a correction in the gold standard token
				# (but maybe also in the system output token as well), create
				# an annotation object and add to list
				if re.search(r'\*\*\*', file_obj.gs_lines[l][t]):
					# If the gold standard corrected token is the empty string, then
					# that means the correction was one of deletion, so it's not a
					# correction we're dealing with, i.e., skip to next token
					if file_obj.gs_lines[l][t].split("***")[1] == "":
						logging.debug('Found gold standard deletion correction:\nGold standard: {}\n\n'.format(file_obj.gs_lines[l][t]))
						logging.debug('Skipping to next token.')
						continue
					# Else if the correction involved a determiner, skip to next
					# token
					elif file_obj.gs_lines[l][t].split("***")[1] in dets:
						logging.debug('Found gold standard correction for a determiner:\nGold standard: {}\n\n'.format(file_obj.gs_lines[l][t]))
						logging.debug('Skipping to next token.')
						continue
					# Otherwise, the gold standard token is a correction of a real
					# noun, most likely, so make an annotation object
					else:
						logging.debug('Creating annotation object for correction:\nGold standard: {}\n\n'.format(file_obj.gs_lines[l][t]))
						anno = annotation(file_obj.ol_untagged[l][t], file_obj.gs_lines[l][t].split("***")[1], file_obj.so_lines[l][t])
						anno.set_orig_tag(file_obj.tags[l][t])
						anno.set_line_index(l)
						anno.set_tok_index(t)
						file_obj.add_annotation(anno)
				# Else if there is a correction in the system output token
				# (but not in the gold standard token since it would have
				# already been found), create an annotation object and add to
				# list
				elif file_obj.so_lines[l][t] != file_obj.ol_untagged[l][t]:
					logging.debug('Found system output correction, creating annotation object:\nOriginal: {}\nSystem output: {}\n Gold standard: {}\n\n'.format(file_obj.ol_untagged[l][t], file_obj.so_lines[l][t], file_obj.gs_lines[l][t]))
					anno = annotation(file_obj.ol_untagged[l][t], file_obj.gs_lines[l][t], file_obj.so_lines[l][t])
					anno.set_orig_tag(file_obj.tags[l][t])
					anno.set_line_index(l)
					anno.set_tok_index(t)
					file_obj.add_annotation(anno)
				# Else there is an agreement on a non-annotation of a noun, i.e.,
				# a true negative, so create an annotation object and add to list
				else:
					logging.debug('Found an instance of agreed-upon non-annotation, i.e., a true negative, creating annotation object:\nOriginal: {}\nSystem output: {}\n Gold standard: {}\n\n'.format(file_obj.ol_untagged[l][t], file_obj.so_lines[l][t], file_obj.gs_lines[l][t]))
					anno = annotation(file_obj.ol_untagged[l][t], file_obj.gs_lines[l][t], file_obj.so_lines[l][t])
					anno.set_orig_tag(file_obj.tags[l][t])
					anno.set_line_index(l)
					anno.set_tok_index(t)
					file_obj.add_annotation(anno)


def calc_prf(true_pos, true_neg, false_pos, false_neg):
	"""Return precision, recall, and f-measure."""
	
	# Convert true_pos, true_neg, false_pos, and false_neg to float values
	# for the calculation of precision, recall, and f-measure
	(tp, tn, fp, fn) = (float(true_pos), float(true_neg), float(false_pos), float(false_neg))
	
	# Calculate precision, recall, and f-measure
	if tp + fp > 0.0:
		p = tp/(tp + fp)
	else:
		p = "undefined, division by zero"
	
	if tp + fn > 0.0:
		r = tp/(tp + fn)
	else:
		r = "undefined, division by zero"
	
	if p == "undefined, division by zero" or r == "undefined, division by zero":
		f = "undefined, division by zero"
	elif p + r > 0.0:
		f = float(2)*((p*r)/(p + r))
	else:
		f = "undefined, division by zero"
	
	return (p, r, f)


def calc_confusion_matrix(annotations):
	"""Return true positives, true negatives, false positives, and false negatives."""
	
	(tp, tn, fp, fn) = (0, 0, 0, 0)
	for anno in annotations:
		# If there should have been a correction in system output...
		if anno.gold_tok != anno.orig_tok:
			# ...and there was, increment tp
			if anno.gold_tok == anno.system_tok:
				tp += 1
			# ...but there wasn't, increment fn
			else:
				fn += 1
		# Else if there was a correction in the system output, but there
		# shouldn't have been one, increment fp
		elif anno.system_tok != anno.orig_tok:
			fp += 1
		# Else if there should not have been a correction and there wasn't,
		# increment tn
		else:
			tn += 1
	
	return (tp, tn, fp, fn)


def make_output_file(output_file_path, file_obj):
	"""Write output file to given path.
	
	The output file will consist of tab-separated lines for disagreements, both of under- and over-generation. The lines will include columns for line number, token index, line, original POS-tag, original token, system output token, gold standard token, and two columns with boolean values indicating whether the particular disagreement was a result of under-generation and over-generation, respectively."""
	
	with open(output_file_path, 'w') as o:
		tsvwriter = csv.writer(o, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
		tsvwriter.writerow(["line_number", "token_index", "line", "tag", "orig_token",
			"system_output", "gold_standard", "undergeneration", "overgeneration"])
		for anno in file_obj.annotations:
			# If there is a disagreement...
			if anno.gold_tok != anno.system_tok:
				# and it is an under-generation:
				if anno.gold_tok != anno.orig_tok:
					tsvwriter.writerow([str(anno.line_index + 1), str(anno.tok_index), " ".join(file_obj.ol_untagged[anno.line_index]), anno.orig_tag, anno.orig_tok, anno.system_tok, anno.gold_tok, "1", "0"])
				# and it is an over-generation
				else:
					tsvwriter.writerow([str(anno.line_index + 1), str(anno.tok_index), " ".join(file_obj.ol_untagged[anno.line_index]), anno.orig_tag, anno.orig_tok, anno.system_tok, anno.gold_tok, "0", "1"])
	o.close()


def main():
	if len(sys.argv) != 11:
		logging.info(r'usage: python(2.7) ./evaluate.py --gold_standard gold_standard_file --orig original_file --system_output system_output_file --output output_file --results results_file')
		sys.exit(1)
	
	parser = argparse.ArgumentParser()
	parser.add_argument('--gold_standard', '-g', help='The input gold standard file consisting of pre-tokenized sentences, one per line. The corrected tokens can optionally be of the form \"[corrected token]***[original token]\".', required=True)
	parser.add_argument('--orig', '-o', help='The input original file consisting of pre-tokenized and tagged sentences, one per line.', required=True)
	parser.add_argument('--system_output', '-s', help='The input file consisting of the output from a system with pre-tokenized sentences, one per line.', required=True)
	parser.add_argument('--output', '-out', help='The output file resulting from the script.', required=True)
	parser.add_argument('--results', '-res', help='The evaluation results file generated by the script.', required=True)
	
	# Parse arguments and assign full paths to variables
	args = parser.parse_args()
	gold_standard_path = os.path.abspath(args.gold_standard)
	orig_path = os.path.abspath(args.orig)
	system_output_path = os.path.abspath(args.system_output)
	output_path = os.path.abspath(args.output)
	results_path = os.path.abspath(args.results)
	
	# Check to see if the input files/paths exist
	paths = [gold_standard_path, orig_path, system_output_path]
	for path in paths:
		if not os.path.exists(path):
			sys.stderr.write('\n\nAt least one of the given input paths is invalid.\n')
			sys.exit(1)
	
	# Ensure that the paths to the output files exist and make directories
	# as needed
	output_paths = [output_path, results_path]
	for path in output_paths:
		if not os.path.exists(os.path.dirname(path)):
			os.makedirs(os.path.dirname(path))
	
	# initialize the loggers
	logging.basicConfig(level=logging.DEBUG)
	#logging.basicConfig(level=logging.INFO)
	#logging.basicConfig(level=logging.WARNING)
	
	# Create new object for the test file and populate the gold standard
	# lines, original tagged and untagged lines, system output lines, and
	# tags
	logging.info('Making file_data object ... \n')
	file_data_obj = file_data()
	file_data_obj.add_gs_lines(gold_standard_path)
	file_data_obj.add_ol_tagged(orig_path)
	file_data_obj.add_so_lines(system_output_path)
	file_data_obj.set_tags_and_ol_untagged()
	
	# Populate file_data_obj.annotations
	logging.info('Adding annotations ... \n')
	add_annotations(file_data_obj)
	
	# Calculate precision, recall, and f-measure
	logging.info('Calculating precision, recall, and f-measure ... \n')
	(tp, tn, fp, fn) = calc_confusion_matrix(file_data_obj.annotations)
	(p, r, f) = calc_prf(tp, tn, fp, fn)
	
	# Write output file
	logging.info('Creating output file ... \n')
	make_output_file(output_path, file_data_obj)
	
	# Write results file
	logging.info('Creating results file ... \n')
	with open(results_path, 'wa') as res:
		res.write("Evaluation metrics for {}\n\n".format(os.path.basename(system_output_path)))
		res.write("Precision: " + str(p) + "\n")
		res.write("Recall: " + str(r) + "\n")
		res.write("F-measure: " + str(f) + "\n\n")
		res.write("Confusion matrix:\n(actual along top and predicted along side):\n\n")
		res.write("\t\tP\tN\n")
		res.write("\tP\t{}\t{}\n".format(str(tp), str(fp)))
		res.write("\tN\t{}\t{}\n".format(str(fn), str(tn)))
	res.close()
	logging.info('Finished. \n')


if __name__ == '__main__':
	main()