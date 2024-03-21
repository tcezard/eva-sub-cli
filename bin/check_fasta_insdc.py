#!/usr/bin/env python

import argparse
import gzip
import hashlib
import json

from itertools import groupby

import requests
from ebi_eva_common_pyutils.logger import logging_config

import yaml
from requests import HTTPError
from retry import retry

from eva_sub_cli.metadata_utils import get_files_per_analysis, get_analysis_for_vcf_file, \
    get_reference_assembly_for_analysis

REFGET_SERVER = 'https://www.ebi.ac.uk/ena/cram'
CONTIG_ALIAS_SERVER = 'https://www.ebi.ac.uk/eva/webservices/contig-alias/v1/chromosomes/md5checksum'

logger = logging_config.get_logger(__name__)


def open_gzip_if_required(input_file):
    if input_file.endswith('.gz'):
        return gzip.open(input_file, 'rt')
    else:
        return open(input_file, 'r')


def write_result_yaml(output_yaml, results):
    with open(output_yaml, 'w') as open_yaml:
        yaml.safe_dump(data=results, stream=open_yaml)


def refget_md5_digest(sequence):
    return hashlib.md5(sequence.upper().encode('utf-8')).hexdigest()


def fasta_iter(input_fasta):
    """
    Given a fasta file. yield tuples of header, sequence
    """
    # first open the file outside
    with open(input_fasta, 'r') as open_file:

        # ditch the boolean (x[0]) and just keep the header or sequence since
        # we know they alternate.
        faiter = (x[1] for x in groupby(open_file, lambda line: line[0] == ">"))

        for header in faiter:
            # drop the ">"
            headerStr = header.__next__()[1:].strip()

            # join all sequence lines to one.
            seq = "".join(s.strip() for s in faiter.__next__())
            yield (headerStr, seq)


@retry(exceptions=(HTTPError,), tries=3, delay=2, backoff=1.2, jitter=(1, 3))
def get_refget_metadata(md5_digest):
    response = requests.get(f'{REFGET_SERVER}/sequence/{md5_digest}/metadata')
    if 500 <= response.status_code < 600:
        raise HTTPError(f"{response.status_code} Server Error: {response.reason} for url: {response.url}", response=response)
    if 200 <= response.status_code < 300:
        return response.json()
    return None


@retry(exceptions=(HTTPError,), tries=3, delay=2, backoff=1.2, jitter=(1, 3))
def _get_containing_assemblies_paged(url):
    response = requests.get(url)
    if 500 <= response.status_code < 600:
        raise HTTPError(f"{response.status_code} Server Error: {response.reason} for url: {response.url}",
                        response=response)
    if 200 <= response.status_code < 300:
        results = set()
        response_data = response.json()
        if '_embedded' in response_data and 'chromosomeEntities' in response_data['_embedded']:
            for contigEntity in response_data['_embedded']['chromosomeEntities']:
                results.add(contigEntity['assembly']['insdcAccession'])
        if '_links' in response_data and 'next' in response_data['_links']:
            # Add results from next page if needed
            results |= _get_containing_assemblies_paged(response_data['_links']['next'])
        return results
    return set()


def get_containing_assemblies(md5_digest):
    # Wrapper method to handle pagination
    url = f'{CONTIG_ALIAS_SERVER}/{md5_digest}'
    return _get_containing_assemblies_paged(url)


def assess_fasta(input_fasta, analyses, metadata_insdc):
    """
    Check whether all sequences in fasta file are INSDC, and if so whether the INSDC accession provided in the metadata
    is compatible.
    :param input_fasta: path to fasta file
    :param analyses: aliases of all analyses associated with this fasta (used only for reporting)
    :param metadata_insdc: INSDC accession from metadata (if None will only do the first check)
    :returns: dict of results
    """
    results = {'sequences': []}
    all_insdc = True
    possible_assemblies = set()
    for header, sequence in fasta_iter(input_fasta):
        name = header.split()[0]
        md5_digest = refget_md5_digest(sequence)
        sequence_metadata = get_refget_metadata(md5_digest)
        is_insdc = bool(sequence_metadata)
        if is_insdc:
            containing_assemblies = get_containing_assemblies(md5_digest)
            if len(containing_assemblies) == 0:
                logger.warning(f'Sequence with this MD5 is INSDC but not found in contig alias: {md5_digest}')
                continue
            if len(possible_assemblies) == 0:
                possible_assemblies = containing_assemblies
            else:
                possible_assemblies &= containing_assemblies
        results['sequences'].append({'sequence_name': name, 'sequence_md5': md5_digest, 'insdc': is_insdc})
        all_insdc = all_insdc and is_insdc
    results['all_insdc'] = all_insdc

    # Only report on metadata concordance if all of the following hold:
    #  1) All sequences in FASTA file are INSDC
    #  2) At least one compatible assembly accession was found in contig alias
    #  3) Found a single assembly accession in the metadata to compare against this FASTA file
    # If (3) is missing but (1) and (2) hold, we will still report possible INSDC assemblies.
    if all_insdc and possible_assemblies:
        results['possible_assemblies'] = possible_assemblies
    if all_insdc and possible_assemblies and metadata_insdc:
        results['metadata_assembly_compatible'] = (metadata_insdc in possible_assemblies)
        results['associated_analyses'] = analyses
        results['assembly_in_metadata'] = metadata_insdc
    return results


def get_analyses_and_reference_genome_from_metadata(vcf_files, json_file):
    with open(json_file) as open_json:
        metadata = json.load(open_json)
        files_per_analysis = get_files_per_analysis(metadata)
        # Get all analyses associated with all vcf files
        all_analyses = set()
        for vcf_file in vcf_files:
            analysis_aliases = get_analysis_for_vcf_file(vcf_file, files_per_analysis)
            if len(analysis_aliases) != 1:
                logger.error(f'Could not determine analysis associated with VCF file: {vcf_file}')
            else:
                all_analyses.add(analysis_aliases[0])
        # Get (single) assembly associated with all analyses
        assemblies = [get_reference_assembly_for_analysis(metadata, analysis) for analysis in all_analyses]
        if len(assemblies) != 1:
            logger.error(f'Could not determine assembly accession to check against fasta file, out of: {assemblies}')
            return all_analyses, None
        return all_analyses, assemblies[0]


def main():
    arg_parser = argparse.ArgumentParser(
        description="Calculate each sequence's Refget MD5 digest and compare these against INSDC Refget server.")
    arg_parser.add_argument('--input_fasta', required=True, dest='input_fasta',
                            help='Fasta file that contains the sequence to be checked')
    arg_parser.add_argument('--vcf_files', dest='vcf_files', nargs='+',
                            help='VCF files, used to connect fasta file to assembly accession in metadata via analysis')
    arg_parser.add_argument('--metadata_json', required=True, dest='metadata_json', help='EVA metadata json file')
    arg_parser.add_argument('--output_yaml', required=True, dest='output_yaml',
                            help='Path to the location of the results')
    args = arg_parser.parse_args()
    logging_config.add_stdout_handler()
    analyses, metadata_insdc = get_analyses_and_reference_genome_from_metadata(args.vcf_files, args.metadata_json)
    results = assess_fasta(args.input_fasta, analyses, metadata_insdc)
    write_result_yaml(args.output_yaml, results)


if __name__ == "__main__":
    main()
