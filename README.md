# GraphUnzip

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4291093.svg)](https://doi.org/10.5281/zenodo.4291093)

Unzips an assembly graph using Hi-C data and/or long reads and/or linked reads. This branch is the master branch, use the article branch to reproduce the results of the article.

## Why use GraphUnzip ?

`GraphUnzip` improves the contiguity of an assembly and duplicates collapsed homozygous contigs, aiming at reconstituting an assembly with haplotypes assembled separately. `GraphUnzip` untangles an uncollapsed assembly graph in GFA format.   

Its naive approach makes no assumption about the ploidy or the heterozygosity rate of the organism and thus can be used on highly heterozygous genomes or metagenomes. If you want to know when GraphUnzip may be useful to you, take a look at [when is GraphUnzip useful](#usefulness) below.

Combined with a short read assembler, `GraphUnzip` makes a great hybrid (short/long read) assembler: go to the [bottom of the page](#hybridUnzip) to see an example.

## Installation

`GraphUnzip` requires python3 with numpy, scipy and zlib. 
To read bam-format data (Hi-C or linked reads) you'll also need pysam.

There are 3 options available for installing GraphUnzip:

1) Pip install directly from this git repository.
This is the best way to ensure you have the latest development version.

```bash
pip install git+https://github.com/nadegeguiglielmoni/GraphUnzip.git
```

2) Clone from this repository and install as a local Python package.
Do this if you plan on editing the code.

```bash
git clone https://github.com/nadegeguiglielmoni/GraphUnzip.git && cd graphunzip && pip install -e .
```

3) Install from Bioconda.
```bash
conda install -c bioconda graphunzip
```

Run `graphunzip --help` to verify installation.


## Usage

### Input

`GraphUnzip` needs two things to work :

An assembly graph in [GFA 1.0 format](https://gfa-spec.github.io/GFA-spec/GFA1.html) and any combination of :

1. Hi-C data. In the form of either:   
  A) The Hi-C reads mapped to the assembly in name-sorted bam format, or    
  B) A sparse contact matrix and a fragment list using the [formats output by hicstuff](https://github.com/koszullab/hicstuff#File-formats).   
  You can use [hicstuff](https://github.com/koszullab/hicstuff) to obtain these files, preferably using iterative mode :

```bash
# Convert GFA to FASTA
awk '/^S/{print ">"$2"\n"$3}' assembly.gfa > assembly.fasta

# Map the Hi-C reads to assembly and generate contact matrix.
hicstuff pipeline -t 8 --mapping=iterative -o mapping/ -g assembly.fasta -e DpnII HiC_reads_forward.fq HiC_reads_reverse.fq
```
and/or

2. Long reads (mapped to the GFA in the GAF format of [GraphAligner](https://github.com/maickrau/GraphAligner)).  
The best is to use an old version of GraphAligner (commit `5217838b436fee4eda5824aabee99406db2a137b`) with option `--global-alginment`.   
 Alternatively, you can use a more recent version with option `--multimap-score-fraction 1`.

```bash
# Align long reads to gfa using old GraphAligner
GraphAligner --global-alignment -x vg -f reads.fq -g graph.gfa -a longreads_aligned_on_gfa.gaf

# or with newer version
GraphAligner --threads 8 --multimap-score-fraction 1 -x vg \
-f reads.fq -g graph.gfa -a longreads_aligned_on_gfa.gaf
``` 
and/or

3. Barcoded linked reads mapped to the contigs of the assembly in [SAM format](https://samtools.github.io/hts-specs/SAMv1.pdf). Barcodes need to be designated in the SAM by a BX:Z: tag (e.g. BX:Z:AACTTGTCGGTCAT-1) at the end of each line. A possible pipeline to get this file from barcoded reads using BWA would be:

```bash
# Convert GFA to FASTA
awk '/^S/{print ">"$2"\n"$3}' assembly.gfa > assembly.fasta  		

# Index the assembly
bwa index assembly.fasta							

# Align the barcoded reads to the assembly.
# The -C option is very important here, to keep the barcodes in the sam file
bwa mem assembly barcoded_reads.fastq -C > reads_aligned_on_assembly.sam
```

Note: Linked reads support is an experimental option we added on demand from some users. It has not been extensively tested. We also expect results to be poorer than what is obtained using Hi-C or long reads.

### Running GraphUnzip

To use `GraphUnzip`, you generally need to proceed in two steps :

#### Step 1: Build an interaction matrix

If using Hi-C or linked reads, build the interaction matrix (a matrix quantifying the pairwise interaction between all contigs). For that use the `HiC-IM`, or `linked-reads-IM` command, depending on which type of data you have.

```bash
# For Hi-C data
graphunzip HiC-IM -m path/to/abs_fragments_contacts_weighted.txt -F path/to/fragments_list.txt -g assembly.gfa --HiC_IM hic_interactionmatrix.txt
# Output: hic_interactionmatrix.txt

# For linked reads
graphunzip linked-reads-IM --barcoded_SAM reads_aligned_on_assembly.sam -g assembly.gfa --linked_reads_IM linkedreads_interactionmatrix.txt
# Output: linkedreads_interactionmatrix.txt
```

#### Step 2: Unzip the graph
 
 Use the command `unzip` to unzip the graph using the interaction matrices built beforehand and/or the GAF file if using long-reads.

```bash
# Let's unzip our gfa using Hi-C, linked-reads, and long-reads :

graphunzip unzip -g assembly.gfa -i hic_interactionmatrix.txt -k linkedreads_interactionmatrix.txt -l longreads_aligned_on_gfa.gaf -o assembly_unzipped.gfa
# Output: assembly_unzipped.gfa

```


### Options

GraphUnzip has 5 sub-modules:  
- unzip: untangle the GFA file
- purge: retain only haploid contigs
- extract: extract haploid assembly with a close reference genome
- HiC-IM: to prepare Hi-C data
- linked-reads-IM: to prepare linked reads data

```
graphunzip --help

usage: graphunzip [-h] [-v] {unzip,purge,extract,HiC-IM,linked-reads-IM}

Unzips an assembly graph using Hi-C data and/or long reads and/or linked reads.

positional arguments:
  {unzip,purge,extract,HiC-IM,linked-reads-IM}
  
  Sub-command must be one of: 
  - unzip (untangle the GFA file), 
  - purge (retain only haploid contigs), 
  - extract (extract haploid assembly with a close reference genome),
  - HiC-IM (to prepare Hi-C data), or
  - linked-reads-IM (to prepare linked reads data)

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```

To run command unzip:

```
graphunzip unzip -h
usage: graphunzip [-h] -g GFA [-i HICINTERACTIONS] [-k LINKEDREADSINTERACTIONS] [-l LONGREADS] [-o OUTPUT] [-f FASTA_OUTPUT] [-b BAM_FILE] [-v] [-r] [--dont_merge] [-H] [-c] [-B] [-n] [-e]

options:
  -h, --help            show this help message and exit

Input of GraphUnzip:
  -g GFA, --gfa GFA     GFA file to phase
  -i HICINTERACTIONS, --HiCinteractions HICINTERACTIONS
                        File containing the Hi-C interaction matrix from HiC-IM [optional]
  -k LINKEDREADSINTERACTIONS, --linkedReadsInteractions LINKEDREADSINTERACTIONS
                        File containing the linked-reads interaction matrix from linked-reads-IM [optional]
  -l LONGREADS, --longreads LONGREADS
                        Long reads mapped to the GFA with GraphAligner (GAF format) or SPAligner (TSV format) [optional]

Output of GraphUnzip:
  -o OUTPUT, --output OUTPUT
                        Output GFA [default: output.gfa]
  -f FASTA_OUTPUT, --fasta_output FASTA_OUTPUT
                        Optional fasta output [default: None]
  -b BAM_FILE, --bam_file BAM_FILE
                        bam file of the Hi-C reads aligned on assembly. GraphUnzip will output bam_file.new.bam corresponding to the new bam file, ready to be used for scaffolding
                        [optional]

Behavior of GraphUnzip:
  -H, --haploid         Use this option if you wish to obtain a collapsed assembly of a multiploid genome.
  -c, --conservative    (Hi-C only) Output very robust contigs. Use this option if the coverage information of the graph is not reliable
  -B, --bold            (Hi-C only)[default] Proposes the best untangling it can get (can be misled by approximate coverage information). Use this option if the contig coverage
                        information of the graph can be trusted
  -n, --noisy           (Hi-C only) Use this option if you expect that the assembly may contain artefactual contigs, e.g. when you use the .p_utg.gfa of hifiasm
  -e, --exhaustive      (long reads only) All links not found in the .gaf will be removed

Other options:
  -v, --verbose
  -r, --dont_rename     Use if you don't want to name the resulting supercontigs with short names but want to keep the names of the original contigs
  --dont_merge          If you don't want the output to have all possible contigs merged
```

To run command HiC-IM:
```
graphunzip HiC-IM --help
usage: graphunzip [-h] -g GFA_GRAPH [-b BAM] [-m MATRIX] [-F FRAGMENTS] -i HIC_IM

options:
  -h, --help            show this help message and exit
  -g GFA_GRAPH, --gfa_graph GFA_GRAPH
                        GFA file that will be untangled (required)
  -b BAM, --bam BAM     Bam file of Hi-C reads aligned on assembly and sorted by name (if using bam format)
  -m MATRIX, --matrix MATRIX
                        Sparse Hi-C contact map (if using instaGRAAL format)
  -F FRAGMENTS, --fragments FRAGMENTS
                        Fragments list (if using instaGRAAL format)
  -i HIC_IM, --HiC_IM HIC_IM
                        Output file for the Hi-C interaction matrix (required)

```

To run command linked-reads-IM:
```
graphunzip linked-reads-IM --help
usage: graphunzip [-h] -g GFA_GRAPH -p LINKED_READS_IM -b BARCODED_SAM

options:
  -h, --help            show this help message and exit
  -g GFA_GRAPH, --gfa_graph GFA_GRAPH
                        GFA file that will be untangled (required)
  -p LINKED_READS_IM, --linked_reads_IM LINKED_READS_IM
                        Output file for the linked-read interaction matrix (required)
  -b BARCODED_SAM, --barcoded_SAM BARCODED_SAM
                        SAM file of the barcoded reads aligned to the assembly. Barcodes must still be there (use option -C if aligning with BWA) (required)
```

<a name="hybridUnzip"></a>
## Hybrid assembly

Combined with a short read assembler, GraphUnzip makes a great hybrid (short reads + long reads) assembler. Here is a suggested pipeline.

### Intallation

You'll need a working python >=3.8 installation to run this pipeline.

If not already done, install GraphUnzip:

```bash
pip install git+https://github.com/nadegeguiglielmoni/GraphUnzip.git
```

Install [SPAdes](github.com/ablab/spades) to have both a short read assembler and a graph-aligner (SPAligner). You can use another assembler if you prefer, but the installation of SPAdes is still recommended to have access to SPAligner.

```bash
wget http://cab.spbu.ru/files/release3.15.3/SPAdes-3.15.3-Linux.tar.gz
tar -xzf SPAdes-3.15.3-Linux.tar.gz
```

### Short read assembly
 
Run the short read assembler. If you are using SPAdes:

```bash
SPAdes-3.15.3-Linux/bin/spades.py --s short_reads.fastq -o short_read_assembly 
```

In this case, the short reads are unpaired. If using another type of library or if you want to tune other options, please refer to `spades.py --help`.

### Read alignment

We will use SPAligner to align long-reads to the assembly graph. If you want to tune the parameters, refer to the [gitHub of SPAligner](https://github.com/ablab/spades/tree/spades_3.15.3/assembler/src/projects/spaligner).

```bash
SPAdes-3.15.3-Linux/bin/spaligner SPAdes-3.15.3-Linux/share/spaligner/spaligner_config.yaml -d pacbio -g short_read_assembly/assembly_graph_with_scaffolds.gfa -k 127 -s long_reads.fastq.gz
```

### Untangling the short-read assembly

Now we use GraphUnzip:

```bash
graphunzip -g short_read_assembly/assembly_graph_with_scaffolds.gfa -l spaligner_result/alignment.tsv -o assembly.gfa -f assembly.fasta
```

The final assembly file are assembly.gfa (GFA format) and assembly.fasta (FASTA format)

<a name="usefulness">
</a>

## When is GraphUnzip useful ?

It is tempting to try to use GraphUnzip on any assembly to improve its contiguity. And you can! Yet on some assemblies it will not improve the results at all. You can generally know that beforehand by looking at what the assembly graph looks like with the tool [Bandage](https://github.com/rrwick/Bandage/).  

GraphUnzip untangles assembly graphs. Thus it likes having messy, tangled graphs as input. 

Here is an example of an assembly on which GraphUnzip will probably do well:
![tangled graph](https://github.com/nadegeguiglielmoni/GraphUnzip/blob/master/docs/gfa_tangled.png)

Conversely, some assemblies are very fragmented. For those, GraphUnzip cannot do much, since it cannot reconstitute the missing sequence between two contigs. You might consider using a scaffolder instead.   

Here is an example of a very fragmented assembly, which cannot be untangled much more:
![fragmented graph](https://github.com/nadegeguiglielmoni/GraphUnzip/blob/master/docs/gfa_split.png)


GraphUnzip will make use of sequencing-depth `DP` tags to detect collapsed homozygous contigs. If your assembly does not have depth tags, they can be added using [GraphTagger](https://github.com/adamtaranto/Graphtagger).

## Citation

Please cite `GraphUnzip` using the preprint:

[GraphUnzip: Unzipping assembly graphs with long-reads and Hi-C](https://www.biorxiv.org/content/10.1101/2021.01.29.428779v1) Roland Faure, Nadège Guiglielmoni and Jean-François Flot, bioRxiv (2020).
doi: https://doi.org/10.1101/2021.01.29.428779
