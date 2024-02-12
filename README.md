# eva-sub-cli
EVA Submission Command Line Interface for Validation


## Installation

TBD

## Input files for the validation and submission tool

There are two ways of specifying the VCF files and associated assembly

### Using  `--vcf_files` and `--assembly_fasta`

This allows you to provide multiple VCF file to validate and a single genome file associated. 
The VCF file and genome associated must use the same chromosome naming convention 

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
