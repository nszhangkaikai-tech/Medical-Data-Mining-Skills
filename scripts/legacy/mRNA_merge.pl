#!/usr/bin/perl -w
use strict;
use warnings;

my $file=$ARGV[0];

#use Data::Dumper;
use JSON;

my $json = new JSON;
my $js;

my %hash=();
my @normalSamples=();
my @tumorSamples=();

open JFILE, "$file";
while(<JFILE>) {
	$js .= "$_";
}
my $obj = $json->decode($js);
for my $i(@{$obj})
{
	      my $file_name=$i->{'file_name'};
        my $file_id=$i->{'file_id'};
        my $entity_submitter_id=$i->{'associated_entities'}->[0]->{'entity_submitter_id'};
        $file_name=~s/\.gz//g;
        if(-f $file_name)
        {
        	my @idArr=split(/\-/,$entity_submitter_id);
        	if($idArr[3]=~/^0/)
        	{
        		push(@tumorSamples,$entity_submitter_id);
        	}
        	else
        	{
        	  push(@normalSamples,$entity_submitter_id);
          }        	
        	open(RF,"$file_name") or die $!;
        	while(my $line=<RF>)
        	{
        		next if($line=~/^\n/);
        		next if($line=~/^\_/);
        		chomp($line);
        		my @arr=split(/\t/,$line);
        		${$hash{$arr[0]}}{$entity_submitter_id}=$arr[1];
        	}
        	close(RF);
        }
}
#print Dumper $obj

open(WF,">mRNAmatrix.txt") or die $!;
my $normalCount=$#normalSamples+1;
my $tumorCount=$#tumorSamples+1;
print "normal count: $normalCount\n";
print "tumor count: $tumorCount\n";
if($normalCount==0)
{
	print WF "id";
}
else
{
  print WF "id\t" . join("\t",@normalSamples);
}
print WF "\t" . join("\t",@tumorSamples) . "\n";
foreach my $key(keys %hash)
{
	print WF $key;
	foreach my $normal(@normalSamples)
	{
		print WF "\t" . ${$hash{$key}}{$normal};
	}
	foreach my $tumor(@tumorSamples)
	{
		print WF "\t" . ${$hash{$key}}{$tumor};
	}
	print WF "\n";
}
close(WF);
