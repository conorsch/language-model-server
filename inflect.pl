#! /usr/share/perl -ws
# Usage details: perl inflect.pl num noun
# If num = "0", provide a plural noun and get back a singular noun as output.
# If num = "1", provide a singular noun and get back a plural noun as output.

use Lingua::EN::Inflect qw { PL PL_N };

$num = $ARGV[0];
$noun = $ARGV[1];

if (!$num) {

	print PL($noun), "\n";
	
} else {

	print PL_N($noun), "\n";
	
}