import yaml

from retry import retry
from ebi_eva_common_pyutils.ena_utils import download_xml_from_ena
from ebi_eva_common_pyutils.logger import AppLogger


PROJECT_KEY = 'project'
ANALYSIS_KEY = 'analysis'
SAMPLE_KEY = 'sample'
FILES_KEY = 'files'
PARENT_PROJECT_KEY = 'parentProject'
CHILD_PROJECTS_KEY = 'childProjects'
PEER_PROJECTS_KEY = 'peerProjects'
BIOSAMPLE_OBJECT_KEY = 'bioSampleObject'
CHARACTERISTICS_KEY = 'characteristics'
TAX_ID_KEY = 'taxId'
ANALYSIS_ALIAS_KEY = 'analysisAlias'


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
        self.check_analysis_alias_coherence()

    def check_all_project_accessions(self):
        """Check that ENA project accessions exist and are public."""
        project = self.metadata[PROJECT_KEY]
        if PARENT_PROJECT_KEY in project:
            self.check_project_accession(project[PARENT_PROJECT_KEY], f'/{PROJECT_KEY}/{PARENT_PROJECT_KEY}')
        for idx, accession in enumerate(project.get(CHILD_PROJECTS_KEY, [])):
            self.check_project_accession(accession, f'/{PROJECT_KEY}/{CHILD_PROJECTS_KEY}/{idx}')
        for idx, accession in enumerate(project.get(PEER_PROJECTS_KEY, [])):
            self.check_project_accession(accession, f'/{PROJECT_KEY}/{PEER_PROJECTS_KEY}/{idx}')

    def check_all_taxonomy_codes(self):
        """Check that taxonomy IDs are valid according to ENA."""
        project = self.metadata[PROJECT_KEY]
        self.check_taxonomy_code(project[TAX_ID_KEY], f'/{PROJECT_KEY}/{TAX_ID_KEY}')
        # Check sample taxonomies for novel samples
        for idx, sample in enumerate(self.metadata[SAMPLE_KEY]):
            if BIOSAMPLE_OBJECT_KEY in sample:
                self.check_taxonomy_code(sample[BIOSAMPLE_OBJECT_KEY][CHARACTERISTICS_KEY][TAX_ID_KEY][0]['text'],
                                         f'/{SAMPLE_KEY}/{idx}/{BIOSAMPLE_OBJECT_KEY}/{CHARACTERISTICS_KEY}/{TAX_ID_KEY}')

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
        """
        Add an error, conforming to the format of biovalidator errors.

        :param property: JSON property of the error. This will be converted to sheet/row/column in spreadsheet if needed.
        :param description: description of the error.
        """
        self.errors.append({'property': property, 'description': description})

    def check_analysis_alias_coherence(self):
        """Check that the same analysis aliases are used in analysis, sample, and files."""
        analysis_aliases = [analysis[ANALYSIS_ALIAS_KEY] for analysis in self.metadata[ANALYSIS_KEY]]
        aliases_in_samples = [alias for sample in self.metadata[SAMPLE_KEY] for alias in sample[ANALYSIS_ALIAS_KEY]]
        aliases_in_files = [file[ANALYSIS_ALIAS_KEY] for file in self.metadata[FILES_KEY]]

        self.same_set(analysis_aliases, aliases_in_samples, 'Analysis', 'Samples',
                      f'/{SAMPLE_KEY}/{ANALYSIS_ALIAS_KEY}')
        self.same_set(analysis_aliases, aliases_in_files, 'Analysis', 'Files',
                      f'/{FILES_KEY}/{ANALYSIS_ALIAS_KEY}')

    def same_set(self, list1, list2, list1_desc, list2_desc, json_path):
        """
        Compare contents of two lists and add error messages.

        :param list1: first list to compare
        :param list2: second list to compare
        :param list1_desc: text description of first list, used only in error message
        :param list2_desc: text description of second list, used only in error message
        :param json_path: property where the error message will appear
        """
        if not set(list1) == set(list2):
            list1_list2 = sorted(cast_list(set(list1).difference(list2)))
            list2_list1 = sorted(cast_list(set(list2).difference(list1)))
            if list1_list2:
                self.add_error(
                    property=json_path,
                    description=f'{",".join(list1_list2)} present in {list1_desc} not in {list2_desc}'
                )
            if list2_list1:
                self.add_error(
                    property=json_path,
                    description=f'{",".join(list2_list1)} present in {list2_desc} not in {list1_desc}'
                )
