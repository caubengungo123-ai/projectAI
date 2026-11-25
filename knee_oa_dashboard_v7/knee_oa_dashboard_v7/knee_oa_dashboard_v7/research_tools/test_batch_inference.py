"""Check CSV scoring with the packaged demo model and artificial example rows."""
from pathlib import Path
import sys
import unittest

import pandas as pd

WEB = Path(__file__).resolve().parents[1] / 'web_deploy'
sys.path.insert(0, str(WEB))
from batch_inference import EXAMPLE_CSV, MAX_ROWS, read_batch, score_batch
from dashboard_core import assess, load_context


class BatchInferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_context(WEB)

    def test_reordered_columns_and_bom_match_single_record(self):
        batch = score_batch(self.context, '\ufeffbmi,age,osteoporosis_baseline,smoking\n28.1,68,0,0\n'.encode())
        individual = assess(self.context, {'age': 68, 'bmi': 28.1, 'osteoporosis_baseline': 0, 'smoking': 0})
        actual = batch.iloc[0]
        self.assertEqual(actual.nhan_du_doan, individual['prediction']['label'])
        self.assertAlmostEqual(actual.diem_nhan_1, individual['prediction']['score'])

    def test_only_valid_rows_receive_scores_and_row_order_is_preserved(self):
        raw = (EXAMPLE_CSV + '95,29,0,0\n68,,0,0\n66,30,2,0\n67,30,0,inf\n').encode()
        result = score_batch(self.context, raw)
        self.assertEqual(result.ho_so.tolist(), list(range(1, 7)))
        self.assertEqual(result.ly_do.tolist(), ['', '', 'age', 'bmi', 'smoking', 'osteoporosis_baseline'])
        self.assertTrue(result.loc[2:, 'diem_nhan_1'].isna().all())
        self.assertTrue(result.loc[2:, 'nhan_du_doan'].isna().all())
        self.assertTrue(pd.notna(result.loc[0, 'diem_nhan_1']))

    def test_bad_csv_is_rejected(self):
        prefix = EXAMPLE_CSV.splitlines()[0].encode() + b'\n'
        invalid = [
            prefix + b'62,27,0,0,unexpected\n',
            prefix + b'\xff',
            prefix,
            prefix + b'65,27,0,0\n' * (MAX_ROWS + 1),
            b'age,bmi,bmi,smoking\n68,20,20,0\n',
            b'age,bmi,smoking,osteoporosis_baseline,person_id\n65,27,0,0,example\n',
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:100]):
                with self.assertRaises(ValueError):
                    read_batch(raw)


if __name__ == '__main__':
    unittest.main()
