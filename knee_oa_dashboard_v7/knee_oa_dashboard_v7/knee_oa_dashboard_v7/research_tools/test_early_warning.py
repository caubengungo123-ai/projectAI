"""Artificial software fixtures only: no patient data or clinical performance claims."""
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web_deploy'))
from early_warning import COLUMNS, CHECKS, TARGET, audit, read_csv, manifest_template
from train_early_warning import research_split, make_pipeline
from sklearn.linear_model import LogisticRegression


def test_manifest():
    m = manifest_template()
    m['sources'] = [dict(source_id='SOFTWARE_TEST_ONLY', cohort_id='TEST', source_url='https://example.invalid/test',
                         version='test', license_or_access_terms='artificial test fixture',
                         codebook_reference='unit test definitions', **{k: True for k in CHECKS})]
    # False here exercises the positive validation branch; this manifest is never exported as research data.
    return m


def fixture(n=1):
    rows=[]
    for p in range(n):
        for side in ['L','R']:
            rows.append(dict(zip(COLUMNS, ['SOFTWARE_TEST_ONLY','TEST',f'{p:04d}',side,'V00','V06',
                       60+p%20,22+p%9,p%2,2 if p%2 else 0,48,1,0,0,0,0,1,3])))
    return pd.DataFrame(rows)


class EndpointTests(unittest.TestCase):
    def test_targets_and_missing_optional(self):
        df=fixture(2); df['smoking_baseline']=''
        result, eligible, _=audit(df,test_manifest())
        self.assertEqual(result['eligible_rows'],4)
        self.assertEqual(eligible[TARGET].tolist(),[0,0,1,1])
        self.assertTrue(eligible.smoking_baseline.isna().all())

    def test_followup_window_and_missing_outcome_not_zero(self):
        for field, value in [('followup_months',12),('kl_followup',''),('outcome_verified',0),
                             ('kl_baseline',2),('knee_replacement_before_followup',1),
                             ('prior_knee_replacement','')]:
            df=fixture().astype(object); df.loc[0,field]=value
            result, eligible, _=audit(df,test_manifest())
            self.assertEqual(len(eligible),1,(field,value,result))

    def test_do_not_round_kl_or_accept_mixed_binary_codes(self):
        for field,value in [('kl_baseline',1.5),('smoking_baseline',.4),('pain_nrs_baseline',50),
                            ('bmi_baseline',float('inf')),('age_baseline','not a number')]:
            df=fixture().astype(object); df.loc[0,field]=value
            result,eligible,_=audit(df,test_manifest())
            self.assertEqual(len(eligible),1,(field,result))

    def test_cross_source_duplicates_rejected(self):
        m=test_manifest(); copy=dict(m['sources'][0]);copy['source_id']='COPY';m['sources'].append(copy)
        df=fixture(); second=df.iloc[[0]].copy();second['source_id']='COPY'
        result,eligible,_=audit(pd.concat([df,second],ignore_index=True),m)
        self.assertEqual(len(eligible),1)
        self.assertEqual(result['excluded_rows'],2)

    def test_extra_future_or_identifier_column_blocks_dataset(self):
        for column in ['name','womac_post','kl_future_predictor']:
            df=fixture();df[column]='must not enter model'
            result,eligible,_=audit(df,test_manifest())
            self.assertTrue(result['global_errors']); self.assertTrue(eligible.empty)

    def test_unknown_source_and_bad_manifest_block(self):
        for manifest in [manifest_template(),None,{},dict(test_manifest(),is_synthetic=True)]:
            r,e,_=audit(fixture(),manifest)
            self.assertEqual(r['eligible_rows'],0)
        df=fixture();df['source_id']='undeclared'
        self.assertEqual(audit(df,test_manifest())[0]['eligible_rows'],0)

    def test_literal_na_and_leading_zero_identifier_preserved(self):
        df=fixture();df['participant_id']='0001'
        self.assertEqual(read_csv(io.StringIO(df.to_csv(index=False))).participant_id.iloc[0],'0001')
        df['participant_id']='NA'
        self.assertEqual(read_csv(io.StringIO(df.to_csv(index=False))).participant_id.iloc[0],'NA')

    def test_legacy_labels_cannot_become_48month_targets(self):
        old=pd.DataFrame({'age':[68],'bmi':[28],'koa_followup':[1]})
        r,e,_=audit(old,test_manifest())
        self.assertEqual(r['eligible_rows'],0);self.assertTrue(r['global_errors'])

    def test_group_holdout_and_every_cv_fold_separate_people(self):
        _,df,_=audit(fixture(100),test_manifest())
        train,test,cv,_=research_split(df)
        self.assertFalse(set(df.iloc[train]._person_group)&set(df.iloc[test]._person_group))
        for a,b in cv:
            self.assertFalse(set(df.iloc[train].iloc[a]._person_group)&set(df.iloc[train].iloc[b]._person_group))

    def test_external_cohort_not_in_development(self):
        df=fixture(120); df.loc[df.index>=200,'cohort_id']='EXTERNAL'
        m=test_manifest(); second=dict(m['sources'][0]);second.update(source_id='EXT',cohort_id='EXTERNAL')
        m['sources'].append(second);df.loc[df.cohort_id.eq('EXTERNAL'),'source_id']='EXT'
        _,df,_=audit(df,m)
        train,test,_,_=research_split(df,'EXTERNAL')
        self.assertTrue(df.iloc[test].cohort_id.eq('EXTERNAL').all())
        self.assertTrue(df.iloc[train].cohort_id.ne('EXTERNAL').all())

    def test_pipeline_imputation_fit_only_on_training(self):
        from early_warning import FEATURES
        _,df,_=audit(fixture(30),test_manifest())
        df['smoking_baseline']=np.nan
        model=make_pipeline(LogisticRegression(max_iter=2000),FEATURES)
        model.fit(df[FEATURES],df[TARGET])
        before=model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_.copy()
        test=df[FEATURES].iloc[:2].copy();test['bmi_baseline']=69
        p=model.predict_proba(test)
        np.testing.assert_array_equal(before,model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_)
        self.assertEqual(p.shape,(2,2));self.assertTrue(np.isfinite(p).all())


if __name__=='__main__':
    unittest.main()
