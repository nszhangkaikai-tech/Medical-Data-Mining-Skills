#!/usr/bin/perl -w
use strict;
use warnings;

my $file=$ARGV[0];

#use Data::Dumper;
use JSON;
my $json = new JSON;
my $js;

open JFILE, "$file";
while(<JFILE>) {
	$js .= "$_";
}
my $obj = $json->decode($js);
#print $obj->[0]->{'cases'}->[0]->{'diagnoses'}->[0]->{'vital_status'} . "\n";

open(WF,">time.txt") or  die $!;
print WF "id\tfutime\tfustat\n";
my %hash=();
for my $i(@{$obj})
{
	my $vitalsStatus=$i->{'cases'}->[0]->{'diagnoses'}->[0]->{'vital_status'};
	my $submitterId=$i->{'cases'}->[0]->{'diagnoses'}->[0]->{'treatments'}->[0]->{'submitter_id'};
	my @subId=split(/\_/,$submitterId);
	if(exists $hash{$subId[0]})
	{
		#print $subId[0] . "\n";
		next;
	}
	else
	{
		$hash{$subId[0]}=1;
	}
	
	if($vitalsStatus eq 'alive')
	{
		my $days_to_last_follow_up=$i->{'cases'}->[0]->{'diagnoses'}->[0]->{'days_to_last_follow_up'};
		if(defined $days_to_last_follow_up)
		{
			print WF "$subId[0]\t$days_to_last_follow_up\t0\n";
		}
	}
	else
	{
		my $days_to_death=$i->{'cases'}->[0]->{'diagnoses'}->[0]->{'days_to_death'};
		if(defined $days_to_death)
		{
			print WF "$subId[0]\t$days_to_death\t1\n";
		}
	}
}
close(WF);
#print Dumper $obj
