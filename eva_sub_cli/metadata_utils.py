import os
from collections import defaultdict

from ebi_eva_common_pyutils.logger import logging_config

logger = logging_config.get_logger(__name__)


def get_samples_per_analysis(metadata):
    """Returns mapping of analysis alias to sample names, based on metadata."""
    samples_per_analysis = defaultdict(list)
    for sample_info in metadata.get('sample', []):
        for analysis_alias in sample_info.get('analysisAlias', []):
            samples_per_analysis[analysis_alias].append(sample_info.get('sampleInVCF'))
    return {
        analysis_alias: set(samples)
        for analysis_alias, samples in samples_per_analysis.items()
    }


def get_files_per_analysis(metadata):
    """Returns mapping of analysis alias to filenames, based on metadata."""
    files_per_analysis = defaultdict(list)
    for file_info in metadata.get('files', []):
        files_per_analysis[file_info.get('analysisAlias')].append(file_info.get('fileName'))
    return {
        analysis_alias: set(filepaths)
        for analysis_alias, filepaths in files_per_analysis.items()
    }


def get_reference_assembly_for_analysis(metadata, analysis_alias):
    """Returns the reference assembly for this analysis (does not validate format)."""
    for analysis in metadata.get('analysis', []):
        if analysis.get('analysisAlias') == analysis_alias:
            return analysis.get('referenceGenome')
    return None


def get_analysis_for_vcf_file(vcf_file, files_per_analysis):
    """Returns list of analysis aliases associated with the vcf file path."""
    if not os.path.exists(vcf_file):
        raise FileNotFoundError(f'{vcf_file} cannot be resolved')
    analysis_aliases = [analysis_alias for analysis_alias in files_per_analysis
                        if os.path.basename(vcf_file) in files_per_analysis[analysis_alias]]
    return analysis_aliases
