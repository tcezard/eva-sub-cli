#!/usr/bin/env nextflow

nextflow.enable.dsl=2

def helpMessage() {
    log.info"""
    Validate a set of VCF files to check if they are valid to be submitted to EVA.

    Inputs:
            --vcf_files_mapping     csv file with the mappings for vcf files, fasta and assembly report
            --output_dir            output_directory where the reports will be output
    """
}

params.vcf_files_mapping = null
params.output_dir = null
// executables
params.executable = ["vcf_validator": "vcf_validator", "vcf_assembly_checker": "vcf_assembly_checker"]
// validation tasks
params.validation_tasks = [ "vcf_check", "assembly_check"]
// container validation dir (prefix for vcf files)
params.container_validation_dir = "/opt/vcf_validation"
// help
params.help = null

// Show help message
if (params.help) exit 0, helpMessage()


// Test input files
if (!params.vcf_files_mapping || !params.output_dir) {
    if (!params.vcf_files_mapping)      log.warn('Provide a csv file with the mappings (vcf, fasta, assembly report) --vcf_files_mapping')
    if (!params.output_dir)             log.warn('Provide an output directory where the reports will be copied using --output_dir')
    exit 1, helpMessage()
}



workflow {
    vcf_channel = Channel.fromPath(params.vcf_files_mapping)
        .splitCsv(header:true)
        .map{row -> tuple(
            file(params.container_validation_dir+row.vcf),
            file(params.container_validation_dir+row.fasta),
            file(params.container_validation_dir+row.report)
        )}


    if ("vcf_check" in params.validation_tasks) {
        check_vcf_valid(vcf_channel)
    }
    if ("assembly_check" in params.validation_tasks) {
        check_vcf_reference(vcf_channel)
    }
}

/*
* Validate the VCF file format
*/
process check_vcf_valid {
    publishDir "$params.output_dir",
            overwrite: false,
            mode: "copy"

    input:
    tuple path(vcf), path(fasta), path(report)

    output:
    path "vcf_format/*.errors.*.db", emit: vcf_validation_db
    path "vcf_format/*.errors.*.txt", emit: vcf_validation_txt
    path "vcf_format/*.vcf_format.log", emit: vcf_validation_log

    """
    trap 'if [[ \$? == 1 ]]; then exit 0; fi' EXIT

    mkdir -p vcf_format
    $params.executable.vcf_validator -i $vcf -r database,text -o vcf_format --require-evidence > vcf_format/${vcf}.vcf_format.log 2>&1
    """
}


/*
* Validate the VCF reference allele
*/
process check_vcf_reference {
    publishDir "$params.output_dir",
            overwrite: true,
            mode: "copy"

    input:
    tuple path(vcf), path(fasta), path(report)

    output:
    path "assembly_check/*valid_assembly_report*", emit: vcf_assembly_valid
    path "assembly_check/*text_assembly_report*", emit: assembly_check_report
    path "assembly_check/*.assembly_check.log", emit: assembly_check_log

    when:
    "assembly_check" in params.validation_tasks

    """
    trap 'if [[ \$? == 1 || \$? == 139 ]]; then exit 0; fi' EXIT

    mkdir -p assembly_check
    $params.executable.vcf_assembly_checker -i $vcf -f $fasta -a $report -r summary,text,valid  -o assembly_check --require-genbank > assembly_check/${vcf}.assembly_check.log 2>&1
    """
}
