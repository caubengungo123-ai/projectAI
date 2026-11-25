"""Use artificial inputs to verify joining, missingness and eligibility."""
import json
from pathlib import Path
import tempfile
import unittest

from prepare_longitudinal import prepare
from test_early_warning import test_manifest


class PrepareLongitudinalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        template = Path(__file__).parent / 'templates' / 'oai_mapping_template.json'
        self.mapping = json.loads(template.read_text(encoding='utf-8'))
        self.mapping.update(source_id='SOFTWARE_TEST_ONLY', cohort_id='TEST')
        clinical, baseline, followup, status = self.mapping['tables'].values()
        clinical.update(delimiter='|')
        clinical['missing_codes'] = {'bmi_baseline': ['999']}
        for table in [baseline, followup]:
            table['value_maps'] = {'knee_side': {'2': 'L', '1': 'R'}}
        self.write('clinical_baseline', '0001|63|27\n0002|68|999\n0003|59|26\n')
        self.write('xray_baseline', '0001,1,0\n0001,2,1\n0002,1,0\n0003,1,0\n')
        self.write('xray_followup', '0002,1,0,1\n0001,2,2,1\n0003,1,3,1\n')
        self.write('followup_status', '0001,R,48,0,0\n0001,L,48,0,0\n0002,R,48,0,0\n0003,R,48,0,1\n')
        self.config = self.folder / 'mapping.json'

    def write(self, table, records):
        spec = self.mapping['tables'][table]
        columns = spec['delimiter'].join(spec['columns'].values())
        (self.folder / spec['path']).write_text(columns + '\n' + records, encoding='utf-8')

    def run_prepare(self, manifest=None):
        self.config.write_text(json.dumps(self.mapping), encoding='utf-8')
        return prepare(self.config, test_manifest() if manifest is None else manifest)

    def test_same_knee_missing_followup_missing_bmi_and_replacement(self):
        joined, report, issues = self.run_prepare()
        self.assertEqual(joined.participant_id.tolist(), ['0001', '0001', '0002', '0003'])
        self.assertEqual(joined.knee_side.tolist(), ['R', 'L', 'R', 'R'])
        self.assertEqual(joined.kl_followup.tolist(), ['', '2', '0', '3'])
        self.assertEqual(joined.bmi_baseline.tolist(), ['27', '27', '', '26'])
        self.assertEqual(report['links']['xray_followup']['unmatched_baseline_knees'], 1)
        self.assertEqual(report['audit']['class_counts'], {'1': 1})
        self.assertEqual(issues.reasons.eq('').tolist(), [False, True, False, False])

    def test_duplicate_keys_and_unmapped_side_stop_import(self):
        self.write('xray_followup', '0001,1,2,1\n0001,1,2,1\n')
        with self.assertRaisesRegex(ValueError, 'trùng khóa'):
            self.run_prepare()
        self.write('xray_followup', '0001,9,2,1\n')
        with self.assertRaisesRegex(ValueError, 'ngoài bảng ánh xạ'):
            self.run_prepare()

    def test_incomplete_manifest_blocks_eligibility_and_missing_codes_remain_blank(self):
        joined, report, _ = self.run_prepare({})
        self.assertEqual(len(joined), 4)
        self.assertEqual(report['audit']['eligible_rows'], 0)
        self.assertTrue(report['audit']['global_errors'])
        self.mapping['tables']['clinical_baseline']['value_maps'] = {'bmi_baseline': {'': '0'}}
        with self.assertRaisesRegex(ValueError, 'mã gốc có giá trị'):
            self.run_prepare()
