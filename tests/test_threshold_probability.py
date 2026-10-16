import json
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from alerts_forecast.pipeline import ROOT, local_midnight
from alerts_forecast.threshold_probability import (add_threshold_presence, threshold_panel,
    fixed_baselines, predict_probability, scores, MODELS, run)
from alerts_forecast.telegram_bot import command, handle_update
from tests.test_pipeline import tiny_archive


class ThresholdTimingTests(unittest.TestCase):
    def test_separate_experiment_cannot_overwrite_original_outputs(self):
        with self.assertRaisesRegex(ValueError,'Cannot overwrite'):
            run(ROOT/'results/probability',ROOT/'.tmp/unused-check-output')

    def panel(self):
        return pd.DataFrame({'date':pd.date_range('2026-08-01',periods=5).strftime('%Y-%m-%d'),
            'region':['R']*5,'y':[1,1,1,3,0],
            'label_available_at':pd.date_range('2026-08-03',periods=5,tz='UTC').astype(str),
            'feature_available_at':['2026-07-30T09:00:00Z']*5,
            'origin':['2026-08-01T00:00:00+03:00']*5})

    def test_inclusive_daily_threshold_not_window_total(self):
        output=threshold_panel(self.panel(),3)
        self.assertEqual(output.event.tolist(),[0,1,1])
        self.assertEqual(output.count_total.tolist(),[3,5,4])
        self.assertEqual(output.period_end.iloc[0],'2026-08-03')
        self.assertEqual(len(output),3)

    def test_future_window_labels_rejected_before_new_model_fit(self):
        train=threshold_panel(self.panel(),3)
        with patch('alerts_forecast.threshold_probability.LogisticRegression.fit') as fit:
            with self.assertRaisesRegex(ValueError,'Training label'):
                predict_probability(train,train,local_midnight('2026-08-05'))
            fit.assert_not_called()

    def test_features_ignore_future_snapshot_and_use_inclusive_threshold(self):
        archive=tiny_archive()
        frame=archive.feature_rows('2026-08-01')
        t=archive.before(local_midnight('2026-08-01'))
        archive.frames[t].iloc[:]=3
        expected=add_threshold_presence(archive,frame)
        self.assertTrue(expected.ge3_7.eq(1).all())
        self.assertTrue(expected.ge3_28.eq(1).all())
        archive.frames[archive.times[-1]].iloc[:]=0
        pd.testing.assert_frame_equal(expected,add_threshold_presence(archive,frame))

    def test_missing_threshold_history_is_not_zero(self):
        archive=tiny_archive();frame=archive.feature_rows('2026-08-01')
        t=archive.before(local_midnight('2026-08-01'))
        archive.frames[t]=archive.frames[t].astype(float)
        archive.frames[t].iloc[:]=np.nan
        with self.assertRaisesRegex(ValueError,'Missing threshold history'):
            add_threshold_presence(archive,frame)

    def test_baselines_use_available_train_labels_not_evaluation_outcomes(self):
        train=threshold_panel(self.panel(),1)
        frame=pd.DataFrame({'region':['R','R'],'event':[0,1]})
        first=fixed_baselines(train,frame,local_midnight('2026-08-09'))
        frame['event']=[1,0]
        second=fixed_baselines(train,frame,local_midnight('2026-08-09'))
        np.testing.assert_equal(first['train_frequency'],[.2,.2])
        np.testing.assert_equal(first['train_majority'],[0,0])
        for key in first:np.testing.assert_equal(first[key],second[key])
        with self.assertRaisesRegex(ValueError,'Training label'):
            fixed_baselines(train,frame,local_midnight('2026-08-05'))

    def test_auc_excludes_constant_regions_and_brier_uses_unclipped_constants(self):
        frame=pd.DataFrame({'horizon':[1]*4,'region':['variable']*2+['constant']*2,'event':[0,1,1,1]})
        for name in MODELS:frame[name]=[0,1,1,1]
        frame['always_one']=1
        regional,macro=scores(frame,'check')
        self.assertTrue(regional[regional.region.eq('constant')].roc_auc.isna().all())
        row=macro[macro.model.eq('logistic')].iloc[0]
        self.assertEqual(row.roc_auc,1)
        self.assertEqual(row.auc_regions,1)
        self.assertEqual(macro[macro.model.eq('always_one')].brier.iloc[0],.25)


class ThresholdIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'site/data.json').read_text(encoding='utf-8'))

    def test_both_targets_all_region_periods_and_distinct_commands(self):
        for region in self.data['regions']:
            for horizon in [1,3,7]:
                text,keyboard=command(f'/threshold {region["iso"]} {horizon}',self.data)
                self.assertIn('≥3',text)
                self.assertIn('?target=ge3&region='+region['iso']+'&days='+str(horizon),text)
                self.assertIn(':ge3',keyboard['inline_keyboard'][0][0]['callback_data'])
                value=region['ge3Periods'][str(horizon)]['probability']
                if value is None:self.assertIn('недоступний',text)
                self.assertEqual(command(f'/forecast {region["iso"]} {horizon} ge3',self.data),(text,keyboard))
        self.assertNotEqual(command('/forecast Київ 1',self.data)[0],command('/threshold Київ 1',self.data)[0])

    def test_callbacks_keep_event_and_accept_legacy_buttons(self):
        class Fake:
            def __init__(self):self.calls=[]
            def call(self,m,p):self.calls.append((m,p));return True
        for callback,expected in [('f:UA-30:3:ge3','Хоча б одна доба з ≥3'),('f:UA-30:3','Хоча б один запис')]:
            api=Fake()
            handle_update({'callback_query':{'id':'test','data':callback,'message':{'chat':{'id':1,'type':'private'}}}},self.data,api)
            self.assertIn(expected,api.calls[-1][1]['text'])

    def test_new_target_is_not_silently_replaced_when_data_missing(self):
        incomplete={'forecastDate':'2026-10-16','dataVersion':'2026-10-15','regions':[{'id':'Kyiv City','iso':'UA-30','name':'м. Київ','periods':{}}]}
        with self.assertRaisesRegex(ValueError,'не містить'):
            command('/threshold Київ 3',incomplete)
