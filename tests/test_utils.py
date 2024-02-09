import csv
import os


def create_mapping_file(mapping_file, vcf_files, fasta_files, assembly_reports):
    with open(mapping_file, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(['vcf', 'fasta', 'report'])
        for vcf_file, fasta_file, assembly_reports in zip(vcf_files, fasta_files, assembly_reports):
            writer.writerow([vcf_file, fasta_file, assembly_reports])