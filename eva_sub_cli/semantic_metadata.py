import yaml

from retry import retry
from ebi_eva_common_pyutils.ena_utils import download_xml_from_ena
from ebi_eva_common_pyutils.logger import AppLogger


PROJECT_KEY = 'project'
PARENT_PROJECT_KEY = 'parentProject'
CHILD_PROJECTS_KEY = 'childProjects'
PEER_PROJECTS_KEY = 'peerProjects'
SAMPLE_KEY = 'sample'
BIOSAMPLE_OBJECT_KEY = 'bioSampleObject'
CHARACTERISTICS_KEY = 'characteristics'
TAX_ID_KEY = 'taxId'


def cast_list(l, type_to_cast=str):
    for e in l:
        yield type_to_cast(e)


class SemanticMetadataChecker(AppLogger):

    def __init__(self, metadata):
        self.metadata = metadata
        self.errors = []

    def write_result_yaml(self, output_path):
        with open(output_path, 'w') as open_yaml:
            yaml.safe_dump(data=self.errors, stream=open_yaml)

    def check_all(self):
        self.check_all_project_accessions()
        self.check_all_taxonomy_codes()

    def check_all_project_accessions(self):
        """Check that ENA project accessions exist and are public"""
        project = self.metadata[PROJECT_KEY]
        self.check_project_accession(project[PARENT_PROJECT_KEY], f'/{PROJECT_KEY}/{PARENT_PROJECT_KEY}')
        for idx, accession in enumerate(project[CHILD_PROJECTS_KEY]):
            self.check_project_accession(accession, f'/{PROJECT_KEY}/{CHILD_PROJECTS_KEY}/{idx}')
        for idx, accession in enumerate(project[PEER_PROJECTS_KEY]):
            self.check_project_accession(accession, f'/{PROJECT_KEY}/{PEER_PROJECTS_KEY}/{idx}')

    def check_all_taxonomy_codes(self):
        """Check that taxonomy IDs are valid according to ENA"""
        project = self.metadata[PROJECT_KEY]
        self.check_taxonomy_code(project[TAX_ID_KEY], f'/{PROJECT_KEY}/{TAX_ID_KEY}')
        # Check sample taxonomies for novel samples
        for idx, sample in enumerate(self.metadata[SAMPLE_KEY]):
            if BIOSAMPLE_OBJECT_KEY in sample:
                self.check_taxonomy_code(sample[BIOSAMPLE_OBJECT_KEY][CHARACTERISTICS_KEY][TAX_ID_KEY],
                                         f'/{SAMPLE_KEY}/{idx}.{CHARACTERISTICS_KEY}/{TAX_ID_KEY}')

    @retry(tries=4, delay=2, backoff=1.2, jitter=(1, 3))
    def check_project_accession(self, project_acc, json_path):
        try:
            download_xml_from_ena(f'https://www.ebi.ac.uk/ena/browser/api/xml/{project_acc}')
        except Exception:
            self.add_error(json_path, f'{project_acc} does not exist or is private')

    @retry(tries=4, delay=2, backoff=1.2, jitter=(1, 3))
    def check_taxonomy_code(self, taxonomy_code, json_path):
        try:
            download_xml_from_ena(f'https://www.ebi.ac.uk/ena/browser/api/xml/{taxonomy_code}')
        except Exception:
            self.add_error(json_path, f'{taxonomy_code} is not a valid taxonomy code')

    def add_error(self, property, description):
        # Ensure that errors match the format of biovalidator errors
        self.errors.append({'property': property, 'description': description})

    def check_analysis_alias_coherence(self):
        # TODO modify these two methods
        """Check that the same analysis aliases are used in analysis, sample, and files"""
        analysis_aliases = [analysis_row['Analysis Alias'] for analysis_row in self.metadata['Analysis']]
        self.same_set(
            analysis_aliases,
            [analysis_alias.strip() for sample_row in self.metadata['Sample'] for analysis_alias in
             sample_row['Analysis Alias'].split(',')],
            'Analysis Alias', 'Samples'
        )
        self.same_set(analysis_aliases, [file_row['Analysis Alias'] for file_row in self.metadata['Files']],
                      'Analysis Alias', 'Files')

    def same_set(self, list1, list2, list1_desc, list2_desc):
        if not set(list1) == set(list2):
            list1_list2 = sorted(cast_list(set(list1).difference(list2)))
            list2_list1 = sorted(cast_list(set(list2).difference(list1)))
            errors = []
            if list1_list2:
                errors.append('%s present in %s not in %s' % (','.join(list1_list2), list1_desc, list2_desc))
            if list2_list1:
                errors.append('%s present in %s not in %s' % (','.join(list2_list1), list2_desc, list1_desc))
            self.error_list.append('Check %s vs %s: %s' % (list1_desc, list2_desc, ' -- '.join(errors)))
    #
    # def _validate_existing_biosample(sample_data, row_num, accession):
    #     """This function only check if the existing sample has the expected fields present"""
    #     found_collection_date = False
    #     for key in ['collection_date', 'collection date']:
    #         if key in sample_data['characteristics'] and \
    #                 # TODO date just needs to exist, format should be checked in json schema (?)
    #             self._check_date(sample_data['characteristics'][key][0]['text']):
    #         found_collection_date = True
    #     if not found_collection_date:
    #         self.error_list.append(
    #             f'In row {row_num}, existing sample accession {accession} does not have a valid collection date')
    #     found_geo_loc = False
    #     for key in ['geographic location (country and/or sea)']:
    #         if key in sample_data['characteristics'] and sample_data['characteristics'][key][0]['text']:
    #             found_geo_loc = True
    #     if not found_geo_loc:
    #         self.error_list.append(
    #             f'In row {row_num}, existing sample accession {accession} does not have a valid geographic location')
    #
    # def check_all_sample_accessions(metadata):
    #     """Check that BioSample accessions exist and are public"""
    #     for row in self.metadata['Sample']:
    #         if row.get('Sample Accession'):
    #             sample_accession = row.get('Sample Accession').strip()
    #             try:
    #                 sample_data = self.communicator.follows_link('samples', join_url=sample_accession)
    #                 _validate_existing_biosample(sample_data, row.get('row_num'), sample_accession)
    #             except ValueError:
    #                 self.error_list.append(
    #                     f'In Sample, row {row.get("row_num")} BioSamples accession {sample_accession} '
    #                     f'does not exist or is private')
