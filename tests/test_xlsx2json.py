import json
import os
from unittest import TestCase


from cli import ETC_DIR
from cli.xlsx2json import XlsxParser, create_xls_template_from_yaml


class TestXlsReader(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')
    output_yaml = os.path.join(resource_dir, 'validation_output', 'sample_checker.yaml')

    def test_conversion_2_json(self) -> None:
        conf_filename = os.path.join(ETC_DIR, 'spreadsheet2json_conf.yaml')
        xls_filename = os.path.join(self.resource_dir, 'EVA_Submission_template.V1.1.4.xlsx')
        self.parser = XlsxParser(xls_filename, conf_filename)
        output_json = os.path.join(self.resource_dir, 'EVA_Submission_template.V1.1.4.json')
        self.parser.json(output_json)
        sample1 = {'analysisAlias': 'VD1,VD2,VD3', 'BioSampleAccession': 'SAME00001', 'sampleInVCF': 'sample1'}
        with open(output_json) as open_file:
            json_data = json.load(open_file)
            assert sorted(json_data.keys()) == ['analysis', 'file', 'project', 'sample', 'submitterDetails']
            assert sample1 in json_data['sample']

    def test_create_xls_template(self):
        metadata_file = os.path.join(self.resource_dir, 'metadata_not_existing.xlsx')
        yaml_schema = os.path.join(ETC_DIR, 'spreadsheet2json_conf.yaml')
        create_xls_template_from_yaml(metadata_file, yaml_schema)
        assert os.path.exists(metadata_file)
