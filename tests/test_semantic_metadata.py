from unittest import TestCase
from unittest.mock import patch

from ebi_eva_common_pyutils.biosamples_communicators import NoAuthHALCommunicator

from eva_sub_cli.semantic_metadata import SemanticMetadataChecker


class TestSemanticMetadata(TestCase):

    def test_check_all_project_accessions(self):
        metadata = {
            "project": {
                "parentProject": "PRJEB123",
                "childProjects": ["PRJEB456", "PRJEBNA"]
            },
        }
        checker = SemanticMetadataChecker(metadata)
        with patch('eva_sub_cli.semantic_metadata.download_xml_from_ena') as m_ena_download:
            m_ena_download.side_effect = [True, True, Exception('problem downloading')]
            checker.check_all_project_accessions()
            self.assertEqual(checker.errors, [
                {'property': '/project/childProjects/1', 'description': 'PRJEBNA does not exist or is private'}
            ])

    def test_check_all_taxonomy_codes(self):
        metadata = {
            "project": {
                "taxId": 9606,
            },
            "sample": [
                {
                    "bioSampleAccession": "SAME00003"
                },
                {
                    "bioSampleObject": {
                        "characteristics": {
                            "taxId": [{"text": "9606"}]
                        }
                    }
                },
                {
                    "bioSampleObject": {
                        "characteristics": {
                            "taxId": [{"text": "1234"}]
                        }
                    }
                }
            ]
        }
        checker = SemanticMetadataChecker(metadata)
        with patch('eva_sub_cli.semantic_metadata.download_xml_from_ena') as m_ena_download:
            # Mock should only be called once per taxonomy code
            m_ena_download.side_effect = [True, Exception('problem downloading')]
            checker.check_all_taxonomy_codes()
            self.assertEqual(checker.errors, [
                {
                    'property': '/sample/2/bioSampleObject/characteristics/taxId',
                    'description': '1234 is not a valid taxonomy code'
                }
            ])

    def test_check_existing_biosamples(self):
        metadata = {
            "sample": [
                {"bioSampleAccession": "SAME00001"},
                {"bioSampleAccession": "SAME00002"},
                {"bioSampleAccession": "SAME00003"}
            ]
        }
        checker = SemanticMetadataChecker(metadata)
        valid_sample = {
            'accession': 'SAME00001',
            'characteristics': {
                'organism': [{'text': 'Viridiplantae'}],
                'collection date': [{'text': '2018'}],
                'geo loc name': [{'text': 'France: Montferrier-sur-Lez'}]
            }
        }
        invalid_sample = {
            'accession': 'SAME00003',
            'characteristics': {
                'organism': [{'text': 'Viridiplantae'}]
            }
        }

        with patch.object(NoAuthHALCommunicator, 'follows_link',
                          side_effect=[valid_sample, ValueError, invalid_sample]) as m_follows_link:
            checker.check_existing_biosamples()
            self.assertEqual(checker.errors, [
                {
                    'property': '/sample/1/bioSampleAccession',
                    'description': 'SAME00002 does not exist or is private'
                },
                {
                    'property': '/sample/2/bioSampleAccession',
                    'description': 'Existing sample SAME00003 does not have a valid collection date'
                },
                {
                    'property': '/sample/2/bioSampleAccession',
                    'description': 'Existing sample SAME00003 does not have a valid geographic location'
                }
            ])

    def test_check_analysis_alias_coherence(self):
        metadata = {
            "analysis": [
                {"analysisAlias": "alias1"},
                {"analysisAlias": "alias2"}
            ],
            "sample": [
                {
                    "bioSampleAccession": "SAME00003",
                    "analysisAlias": ["alias_1", "alias_2"]
                },
                {
                    "bioSampleAccession": "SAME00004",
                    "analysisAlias": ["alias2"]
                }
            ],
            "files": [
                {
                    "analysisAlias": "alias1",
                    "fileName": "example1.vcf.gz"
                },
                {
                    "analysisAlias": "alias2",
                    "fileName": "example2.vcf.gz"
                }
            ]
        }
        checker = SemanticMetadataChecker(metadata)
        checker.check_analysis_alias_coherence()
        self.assertEqual(checker.errors, [
            {'property': '/sample/analysisAlias', 'description': 'alias1 present in Analysis not in Samples'},
            {'property': '/sample/analysisAlias', 'description': 'alias_1,alias_2 present in Samples not in Analysis'}
        ])
