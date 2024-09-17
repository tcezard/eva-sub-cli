# eva-sub-cli
The eva-sub-cli tool is a command line interface tool for data validation and upload. The tool transforms the submission process at EVA by enabling users to take control of data validation process. Previously handled by our helpdesk team, validation can now be performed directly by users, streamlining and improving the overall submission workflow at the EVA. 


## Installation

There are currently three ways to install and run the tool : 
- Using conda
- From source using Docker
- From source natively (i.e. installing dependencies yourself)

### 1. Conda

The most straightforward way to install eva-sub-cli and its dependencies is through conda.
For instance, the following commands install eva-sub-cli in a new environment called `eva`, activate the environment, and print
the help message:
```bash
conda create -n eva -c conda-forge -c bioconda eva-sub-cli
conda activate eva
eva-sub-cli.py --help
````

### 2. From source using Docker

Docker provides an easy way to run eva-sub-cli without installing dependencies separately.
This method requires just Python 3.8+ and [Docker](https://docs.docker.com/engine/install/) to be installed.
Once it is set up, you can either clone the git repository, or download the newest tagged release from [here](https://github.com/EBIvariation/eva-sub-cli/tags):
```bash
git clone https://github.com/EBIvariation/eva-sub-cli.git

# OR (replace "v0.2" with the newest version)

wget -O eva-sub-cli.zip https://github.com/EBIvariation/eva-sub-cli/archive/refs/tags/v0.2.zip
unzip eva-sub-cli.zip && mv eva-sub-cli-* eva-sub-cli
```

Then install the library and its dependencies as follows (e.g. in a virtual environment):
```bash
cd eva-sub-cli
# Activate your virtual environment 
python -m pip install .
```

To verify that the cli tool is installed correctly, run the following command, and you should see the help message displayed : 
```bash
eva-sub-cli.py -h
```

### 3. From source natively

This installation method requires the following :
* Python 3.8+
* [Nextflow](https://www.nextflow.io/docs/latest/getstarted.html) 21.10+
* [biovalidator](https://github.com/elixir-europe/biovalidator) 2.1.0+
* [vcf-validator](https://github.com/EBIvariation/vcf-validator) 0.9.7+

Install each of these and ensure they are included in your PATH. Then, either clone the repository using Git or install the latest release as previously described.

## Getting started with the eva-sub-cli tool 


The ["Getting Started" guide](Getting_Started_with_eva_sub_cli.md) serves as an introduction for users of the eva-sub-cli tool. It includes instructions on how to prepare your data and metadata, ensuring that users are equipped with the necessary information to successfully submit variant data. This guide is essential for new users, offering practical advice and tips for a smooth onboarding experience with the eva-sub-cli tool.

## eva-sub-cli tool: Options and parameters guide

The eva-sub-cli tool provides several options/parameters that you can use to tailor its functionality to your needs. Understanding these parameters is crucial for configuring the tool correctly. Below is an overview of the key parameters and options:

| OPTIONS/PARAMETERS         | DESCRIPTION                                                                                                                                                                                                        |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --version                  | Shows version number of the program and exit                                                                                                                                                                       |
| --metadata_xlsx            | Excel spreadsheet that describe the project, analysis, samples and files                                                                                                                                           |
| --metadata_json            | Json file that describe the project, analysis, samples and files                                                                                                                                                   |
| --vcf_files                | One or several vcf files to validate.This allows you to provide multiple VCF files to validate and a single associated reference genome file. The VCF files and the associated reference genome file must use the same chromosome naming convention                                                                                                                                                                              |
| --reference_fasta          | The fasta file containing the reference genome from which the variants were derived                                                                                                                                |
| --submission_dir           | Path to the directory where all processing will be done and submission data is/will be stored                                                                                                                      |
| --tasks {validate,submit}  | Selecting VALIDATE will run the validation regardless of the outcome of previous runs. Selecting SUBMIT will run validate only if the validation was not performed successfully before and then run the submission |
| --executor {docker,native} | Select an execution type for running validation (default native)                                                                                                                                                   |
| --shallow                  | Set the validation to be performed on the first 10000 records of the VCF. Only applies if the number of record exceed 10000                                                                                        |
| --username                 | Username used for connecting to the ENA webin account                                                                                                                                                              |
| --password                 | Password used for connecting to the ENA webin account                                                                                                                                                              |


#### The metadata spreadsheet

The metadata template can be found within the etc folder at `eva_sub_cli/etc/EVA_Submission_template.xlsx`
It should be populated following the instruction provided within the template

#### The metadata JSON

The metadata can also be provided via a JSON file, which should conform to the schema located [here](eva_sub_cli/etc/eva_schema.json).


## Execution

### Validate only

To validate and not submit, run the following command:

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx --submission_dir submission_dir --tasks VALIDATE
```

**Note for Docker users:** 

Make sure that Docker is running in the background, e.g. by opening Docker Desktop.
For each of the below commands, add the command line option `--executor docker`, which will
fetch and manage the docker container for you. 

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx --submission_dir submission_dir --tasks VALIDATE --executor docker 
```

### Validate and submit your dataset

To validate and submit run the following command

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx \
               --vcf_files vcf_file1.vcf vcf_file2.vcf --reference_fasta assembly.fa --submission_dir submission_dir
```


### Submit only

All submissions must have been validated. You cannot run the submission without validation. Once validated, execute the following command:

```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx --submission_dir submission_dir
```
or 
```shell
eva-sub-cli.py --metadata_xlsx metadata_spreadsheet.xlsx --submission_dir submission_dir --tasks SUBMIT
```
Will only submit the data and not validate.

### Shallow validation

If you are working with large VCF files and find that validation takes a very long time, you can add the
argument `--shallow` to the command, which will validate only the first 10,000 lines in each VCF. Note that running
shallow validation will **not** be sufficient for actual submission.
