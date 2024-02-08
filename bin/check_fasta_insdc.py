#!/usr/bin/env python

import argparse
import gzip
import hashlib

from itertools import groupby

import requests
from ebi_eva_common_pyutils.logger import logging_config

import yaml
from requests import HTTPError
from retry import retry

REFGET_SERVER = 'https://www.ebi.ac.uk/ena/cram'

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
    "first open the file outside "
    fin = open(input_fasta, 'r')

    # ditch the boolean (x[0]) and just keep the header or sequence since
    # we know they alternate.
    faiter = (x[1] for x in groupby(fin, lambda line: line[0] == ">"))

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


def assess_fasta(input_fasta):
    results = {'sequences': []}
    all_insdc = True
    for header, sequence in fasta_iter(input_fasta):
        name = header.split()[0]
        md5_digest = refget_md5_digest(sequence)
        sequence_metadata = get_refget_metadata(md5_digest)
        results['sequences'].append({'sequence_name': name, 'sequence_md5': md5_digest, 'insdc': bool(sequence_metadata)})
        all_insdc = all_insdc and bool(sequence_metadata)
    results['all_insdc'] = all_insdc
    return results


def main():
    arg_parser = argparse.ArgumentParser(
        description='Calculate each sequence's Refget MD5 digest and compare these against INSDC Refget server.')
    arg_parser.add_argument('--input_fasta', required=True, dest='input_fasta',
                            help='Fasta file that contains the sequence to be checked')
    arg_parser.add_argument('--output_yaml', required=True, dest='output_yaml',
                            help='Path to the location of the results')
    args = arg_parser.parse_args()
    logging_config.add_stdout_handler()
    results = assess_fasta(args.input_fasta)
    write_result_yaml(args.output_yaml, results)


if __name__ == "__main__":
    main()
