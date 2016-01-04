#metadataQA

A set of metadata harvesting and analysis scripts, largely built off the model/skeleton of Mark Phillips' wonderful work: 

- [pyoaiharvester](https://github.com/vphill/pyoaiharvester)
- [metadata_breakers](https://github.com/vphill/metadata_breakers)
- [Metadata Analysis at the Command Line](http://journal.code4lib.org/articles/7818)

So please give any gratitude for these scripts to Mark Phillips, and any complaints to Christina.

## Warning

A forthcoming presentation somewhat prompted me to finally collect and share these - the presentation will be linked here, along with accompanying blog post with thoughts on library metadata QA. However, they were built usually at midnight with huge metadata projects/migrations looming where I didn't have the tools I needed to properly review metadata for my work.

As such, these scripts are rather haphazard and very, very alpha. In particular the DPLA work, which was built in the context of the Digital Library of Tennessee Service hub, as a way to review our metadata once in the DPLA, is the most likely to break in unexpected and beautiful ways.

## Why not fork?

Because these scripts use new libraries*, and they change the original intent of the Phillip's work (working with nested XML, working with DPLA API and DPLA Json, eventually will share working with MARC via Pymarc), these are a new repo. I'd like to eventually pull these bits and pieces of helpful scripts together in a more coherent fashion for library metadata harvest and review; see the 'to be enhanced' section below.

*Some, not all, changes include:

- argparse instead of optparse to avoid depreciated libraries
- lxml.etree instead of elementtree alone to support better xpath queries for nested elements (MODS)
- rewritten for working with json for DPLA data
- adding support for DPLA analysis tool to find fields according to ObjectPath syntax
- adding support for MODS analysis tool to find elements according to XPath syntax

## Install

This was all built/test on python 2.7.10. It needs tweaking for python 3. I'm working on it - the analysis files except MARC work on python 3. The harvester doesn't work for python3 yet - considering moving to requests library instead of urllib/urlopen, which requires more 2 to 3 conversion work. Or, if you find something that works for 3, you can add it and submit a pull request. Please.

So, working with python 2.7:

1. Get this repository on your computer somehow. You can:
    1. change to file location where you want these scripts, then clone this git repository to your computer:
    ```
    $ git clone https://github.com/cmh2166/metadataQA.git
    ```
    1. download this repository to your computer from the [GitHub page](https://github.com/cmh2166/metadataQA) - use the 'Download Zip' button in bottom right corner. Move the zip file to the place you wish to have these scripts, then unzip.
2. once you've got the scripts on your computer, change to inside the metadataQA directory, and install the requirements: 
```
$ pip install -r requirements.txt 
```

Now you should be ready to use the scripts.

## Examples

This all works at present by using the harvest scripts to get a data file to your computer, then running an analysis script on that file. I'm looking into ways to have the analysis applied directly to the data streams instead of a local file.

### Harvesting

#### Harvest OAI feed

Note: **This script at present is set to default to pulling MODS from the UTK Islandora OAI feed and save to a 'output.xml' file.**

usage: python oaiharvest.py [options, see below] -l link to OAI feed -o file to save to.

optional arguments:

- -h: a help message
- -l: URL of OAI repository
- -o: write repository to this file
- -f: harvest records from this date yyyy-mm-dd
- -u: harvest records until this date yyyy-mm-dd
- -m: use the specified metadata format
- -s: harvest the specified set

This downloads all the MODS/XML data from the OAI feed at Florida State University, and saves it to the file 'fsuoai.mods.xml'.
```
$ python oaiharvest.py -m mods -o fsuoai.mods.xml -l https://fsu.digital.flvc.org/oai2
```

#### Harvest DPLA feed

You can pass your [DPLA API key](http://dp.la/info/developers/codex/policies/#get-a-key) to the script either using the -k flag or by setting it as an environmental variable DPLA_APIKEY.

usage: python dplaharvest.py [options, see below] -o file to save data to

optional arguments:

- -h: show a help message
- -o: file to write the data to
- -k: your unique DPLA API key
- -a: items with creation date after yyyy-mm-dd
- -f: items with creation date before yyyy-mm-dd
- -t: search these keywords in the items' titles
- -q: general keyword search
- -p: specify the metadata provider

This downloads all the DPLA data that has a creation date after 2020
```
$ python dplaharvest.py -k YourLongAPIKey -a 2020 -o FileToSaveDataTo.json 
```

### Analysis

All of the analysis scripts run similarly to what is described by Mark Phillips here for his own work: [Metadata Analysis at the Command Line](http://journal.code4lib.org/articles/7818)

#### oai dc analysis

Works most similarly to the original script created by Mark Phillips. 

usage: oaidc_analysis.py data_filename.xml [options, see below]

positional arguments:

- datafile              put the datafile you want analyzed here

optional arguments:

- -h: show a help message
- -e: element to print to screen
- -i: prepend meta_id/oai header id for record to line
- -s: only print stats for repository (default)
- -p: print if there is value of defined element in record
- -d: Dump all record data to a tab delimited format (*this has not been tested*)

To get a field report:
```
$ python oaidc_analysis.py test/output.dc.xml 
```

To get all the values for the dc:creator field:
```
$ python oaidc_analysis.py test/output.xml -e creator  
```

To get all the unique values for the dc:creator field, sorted by count:
```
$ python oaidc_analysis.py test/output.xml -e creator | sort | uniq -c  
```

#### oai mods analysis

This has added support for reviewing nested MODS elements, as well as perform queries with xpath.

usage: oaimods_analysis.py data_filename.xml [options, see below]

positional arguments:

- datafile              put the datafile you want analyzed here

optional arguments:

- -h: show a help message
- -e: MODS element to print to screen
- -x: get response of XPath expression on mods:mods record
- -i: prepend meta_id, oai header id for record to line
- -s: only print stats for repository (default)
- -p: print if there is value of defined element in record

To print a field report:
```
python oaimods_analysis.py test/DLTNphase1.mods.xml 
```

To get all the values for mods:title (this does not mean just top level mods:titleInfo/mods:title - but any mods:title element wherever it appears in the record):
```
python oaimods_analysis.py test/DLTNphase1.mods.xml -e title 
```

To get all the unique values for mods:form (again, wherever it appears) sorted by count:
```
python oaimods_analysis.py test/DLTNphase1.mods.xml -e form | sort | uniq -c
```

To get all the values that fit the 'mods:mods/mods:originInfo/mods:dateCreated[@encoding="edtf"]' Xpath query (i.e., all dateCreated for the object that have edtf encoding):
```
python oaimods_analysis.py test/DLTNphase1.mods.xml -x 'mods:originInfo/mods:dateCreated[@encoding="edtf"]'   
```

#### dpla analysis

To be written up.

#### marc analysis

To be written up.

## To Be Enhanced

To be written up.

