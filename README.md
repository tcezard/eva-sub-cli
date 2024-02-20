# eva-sub-cli
EVA Submission Command Line Interface for Validation


## Installation

There are currently three ways to install and run the tool: using conda, from source using Docker,
and from source natively (i.e. managing dependencies on your own).

### Conda

The most straightforward way to install eva-sub-cli and its dependencies is through conda.
For example the following installs eva-sub-cli in a new environment called `eva`, activates the environment, and prints
the help message:
```bash
conda create -n eva -c conda-forge -c bioconda eva-sub-cli
conda activate eva
eva-sub-cli.py --help
````

### From source using Docker

This method requires just Python 3.8+ and [Docker](https://docs.docker.com/engine/install/) to be installed.
Then either clone the git repository, or download the newest tagged release from [here](https://github.com/EBIvariation/eva-sub-cli/tags):
```bash
git clone git@github.com:EBIvariation/eva-sub-cli.git
# OR
wget -O eva-sub-cli.zip https://github.com/EBIvariation/eva-sub-cli/archive/refs/tags/v0.2.zip
unzip eva-sub-cli.zip
```

Then install the library and its dependencies as follows (e.g. in a virtual environment):
```bash
cd eva-sub-cli
pip install -r requirements.txt
python setup.py install
```

### From source natively

This method requires the following:
* Python 3.8+
* [Nextflow](https://www.nextflow.io/docs/latest/getstarted.html) 21.10+
* [biovalidator](https://github.com/elixir-europe/biovalidator) 2.1.0+
* [vcf-validator](https://github.com/EBIvariation/vcf-validator) 0.9.6+

Install each of these and ensure they are available on the path.
Then git clone the repo or install the newest release as described above.

## Input files for the validation and submission tool

There are two ways of specifying the VCF files and associated assembly

### Using  `--vcf_files` and `--assembly_fasta`

This allows you to provide multiple VCF files to validate and a single associated genome file.
The VCF files and the associated genome file must use the same chromosome naming convention 

### Using  `--vcf_files_mapping`

The path to the VCF files are provided via CSV file that links the VCF to their respective fasta sequence. This allows 
us to support different assemblies for each VCF file 
The CSV file `vcf_mapping.csv` contains the following columns vcf, fasta, report providing respectively:
 - The VCF to validate/upload
 - The assembly in fasta format that was used to derive the VCF
 - (Optional) The assembly report associated with the assembly (if available) as found in NCBI assemblies (https://www.ncbi.nlm.nih.gov/genome/doc/ftpfaq/#files)

Example:
```shell
vcf,fasta,report
/full/path/to/vcf_file1.vcf,/full/path/to/genome.fa,/full/path/to/genome_assembly_report.txt
/full/path/to/vcf_file2.vcf,/full/path/to/genome.fa,/full/path/to/genome_assembly_report.txt
/full/path/to/vcf_file3.vcf,/full/path/to/genome2.fa,/full/path/to/genome_assembly_report2.txt
```

### The metadata spreadsheet 

The metadata template can be found within the etc folder at `eva_sub_cli/etc/EVA_Submission_template.xlsx`
It should be populated following the instruction provided within the template

### The metadata JSON

The metadata can also be provided via a JSON file which should conform to the schema located  at 
`eva_sub_cli/etc/eva_schema.json` 

More detail documentation to follow 

## Execution

Note for Docker users: for each of the below commands, add the command line option `--executor docker`, which will
fetch and manage the docker container for you.

### Validate and submit your dataset

To validate and submit run the following command

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx \
               --vcf_files vcf_file1.vcf vcf_file2.vcf --assembly_fasta assembly.fa --submission_dir submission_dir
```

### Validate only

To validate and not submit run the following command

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx \
               --vcf_files_mapping vcf_mapping.csv --submission_dir submission_dir 
               --tasks VALIDATE
```
### Submit only

All submission must have been validated. You cannot run the submission without validation. Once validated running 

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx \
               --vcf_files_mapping vcf_mapping.csv --submission_dir submission_dir
```
or 
```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx \
               --vcf_files_mapping vcf_mapping.csv --submission_dir submission_dir --tasks SUBMIT
```
Will only submit the data and not validate.
