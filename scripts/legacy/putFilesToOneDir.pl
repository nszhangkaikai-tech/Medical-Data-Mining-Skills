use strict;
use warnings;

my $newDir="files";
unless(-d $newDir)
{
	mkdir $newDir or die $!;
}

my @allFiles=glob("*");
foreach my $subDir(@allFiles)
{
	if(-d $subDir)
	{
		opendir(SUB,".\\$subDir") or die $!;
		while(my $file=readdir(SUB))
		{
			if($file=~/\.gz$/)
			{
				`copy .\\$subDir\\$file .\\$newDir`; 
			}
		}
		close(SUB);
	}
}
