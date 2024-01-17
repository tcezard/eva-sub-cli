#!/usr/bin/env python
import argparse
import hashlib

import requests
from ebi_eva_common_pyutils.assembly_utils import retrieve_genbank_assembly_accessions_from_ncbi
from ebi_eva_common_pyutils.logger import logging_config

from retry import retry

logger = logging_config.get_logger(__name__)
_contig_alias_url = 'https://www.ebi.ac.uk/eva/webservices/contig-alias/'


class ContigAliasAssembly:
    """"""
    def __init__(self, assembly_accession):
        self.assembly_accession = assembly_accession
        self.chromosomes = []
        self._cache_assembly_dict()

    @retry(tries=3, delay=2, backoff=1.2, jitter=(1, 3))
    def _assembly_get(self, page=0, size=1000):
        url = _contig_alias_url + 'v1/assemblies/' + self.assembly_accession + f'/chromosomes?page={page}&size={size}'
        response = requests.get(url, headers={'accept': 'application/json'})
        response.raise_for_status()
        response_json = response.json()
        return response_json

    def _add_chromosomes(self, assembly_data):
        self.chromosomes.extend(assembly_data.get('chromosomeEntities', []))

    def _cache_assembly_dict(self):
        page = 0
        size = 1000
        response_json = self._assembly_get(page=page, size=size)
        self._add_chromosomes(response_json['_embedded'])
        while 'next' in response_json['_links']:
            page += 1
            response_json = self._assembly_get(page=page, size=size)
            self._add_chromosomes(response_json['_embedded'])


def fasta_parser(genome_fasta):
    with open(genome_fasta) as open_file:
        contig_name = None
        contig_sequence = []
        for line in open_file:
            if line.startswith('>'):
                if contig_name:
                    yield contig_name, ''.join(contig_sequence)
                contig_sequence = []
                contig_name = line.split()[0][1:]
            else:
                contig_sequence.append(line.strip().upper())
        if contig_name:
            yield contig_name, ''.join(contig_sequence)


def calculate_md5(sequence):
    return hashlib.md5(sequence.encode('utf-8')).hexdigest()


def is_insdc_sequence(sequence):
    md5_checksum = calculate_md5(sequence)
    metadata_endpoint = f'https://www.ebi.ac.uk/ena/cram/sequence/{md5_checksum}/metadata'
    response = requests.get(metadata_endpoint)
    if response.status_code == 200:
        return True
    else:
        return False


def get_ncbi_assembly_from_term(term):
    accessions = retrieve_genbank_assembly_accessions_from_ncbi(term)
    if accessions:
        return accessions


def check_assembly_exist_in_contig_alias(genome_accession):
    # First check that the assembly is available
    url = _contig_alias_url + 'v1/assemblies/' + genome_accession
    response = requests.get(url)
    if response.ok:
        return True
    return False


def _nb_overlap_elements(a: list, b: list):
    """
    Compare elements between two arrays. Helper function for individual elements used by workhorse compare_seqcols function
    """
    a_filtered = list(filter(lambda x: x in b, a))
    b_filtered = list(filter(lambda x: x in a, b))
    return min(len(a_filtered), len(b_filtered))  # counts duplicates


def compare_contig_alias_and_fasta(genome_accession, fasta_genome):
    fasta_length = [len(sequence) for name, sequence in fasta_genome]
    fasta_name = [name for name, sequence in fasta_genome]
    contig_alias_genome = ContigAliasAssembly(genome_accession)
    contig_alias_lengths = [entity.get('seqLength') for entity in contig_alias_genome.chromosomes]
    same_length = _nb_overlap_elements(fasta_length, contig_alias_lengths) == len(contig_alias_genome.chromosomes)
    for naming_convention in ['genbankSequenceName', 'enaSequenceName', 'insdcAccession', 'refseq', 'ucscName']:
        contig_alias_names = [entity.get(naming_convention) for entity in contig_alias_genome.chromosomes]
        if same_length and _nb_overlap_elements(fasta_name, contig_alias_names):
            return True, naming_convention
    return False, None


def compare_genome_and_name(genome_name, genome_fasta):
    genome_accessions = get_ncbi_assembly_from_term(genome_name)
    fasta_genome = list(fasta_parser(genome_fasta))
    results = {'genome_name': genome_name}
    for genome_accession in genome_accessions:
        same_chromosomes, naming_convention = compare_contig_alias_and_fasta(genome_accession, fasta_genome)
        if same_chromosomes:
            results['genome_accession'] = genome_accession
            results['naming_convention'] = naming_convention
            break
    return results


def test_sequence_in_insdc(genome_fasta):
    return all(is_insdc_sequence(sequence)
               for name, sequence in fasta_parser(genome_fasta))


def main():
    arg_parser = argparse.ArgumentParser(
        description='Compare the genome fasta file provided with the genome name provided.')
    arg_parser.add_argument('--metadata_json', required=True, dest='metadata_json',
                            help='EVA metadata json file')
    arg_parser.add_argument('--genome_fasta', dest='genome_fasta',
                            help='Path to the file containing the reference genome')

    args = arg_parser.parse_args()
    logging_config.add_stdout_handler()


if __name__ == "__main__":
    main()
