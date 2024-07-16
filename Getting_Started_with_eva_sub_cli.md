# How to generate inputs for the eva-sub-cli 

The eva-sub-cli tool requires the following inputs:

- One or several valid VCF files
- Completed metadata spreadsheet
- list 3 Reference genome in fasta format

The VCF file must adhere to official VCF specifications, and the metadata spreadsheet provides contextual information about the dataset. In the following sections, we will examine each of these inputs in detail.

# VCF File

A VCF (Variant Call Format) file is a type of file used in bioinformatics to store information about genetic variants. It includes data about the differences (or variants) between a sample's DNA and a reference genome. Typically, generating a VCF file involves several steps: preparing your sample, sequencing the DNA, aligning it to a reference genome, identifying variants, and finally, formatting this information into a VCF file. The overall goal is to systematically capture and record genetic differences in a standardised format. A VCF file consists of two main parts: the header and the body.
Header: The header contains metadata about the file, such as the format version, reference genome information, and descriptions of the data fields. Each line in the header starts with a double ##, except for the last header line which starts with a single #.

# Metadata Spreadsheet

The spreadsheet provides comprehensive contextual information about the dataset, ensuring that each submission is accompanied by detailed descriptions that facilitate proper understanding and use of the data. Key elements included in the metadata spreadsheet are analysis and project information, sample information, sequencing methodologies, experimental details. 

# Validation checks 

The CLI tool performs the following validation checks and generates corresponding reports:

- Metadata check to ensure that the metadata fields have been correctly filled in
- VCF check to ensure that the VCF file follows the VCF format specification
- Assembly check to ensure that the genome and the VCF match
- Sample name check to ensure that the samples in the metadata can be associated with the sames in the VCF

In the following sections, we will examine each of these checks in detail, starting with the Metadata check.

