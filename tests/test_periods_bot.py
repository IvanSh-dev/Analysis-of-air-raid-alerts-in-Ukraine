import json
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from urllib.error import URLError

from alerts_forecast.periods import period_panel,coherent_probabilities,choose_probability,probability_metrics,add_presence
from alerts_forecast.pipeline import check_fit_availability,local_midnight,ROOT
from alerts_forecast.telegram_bot import command,find_region,handle_update,TelegramAPI,ApiFailure,percent
from tests.test_pipeline import tiny_archive

class PeriodTests(unittest.TestCase):
    def sample(self):
        return pd.DataFrame({'region':['R']*4,'date':['2026-08-01','2026-08-02','2026-08-03','2026-08-04'],
            'y':[0,2,0,0],'label_available_at':['2026-08-03T09:00:00Z','2026-08-04T09:00:00Z','2026-08-05T09:00:00Z','2026-08-06T09:00:00Z']})

    def test_window_event_and_total_not_sum_of_probabilities(self):
        frame=period_panel(self.sample(),3)
        self.assertEqual(frame.count_total.tolist(),[2,2])
        self.assertEqual(frame.event.tolist(),[1,1])
        self.assertEqual(frame.period_end.iloc[0],'2026-08-03')
        self.assertEqual(frame.label_available_at.iloc[0],'2026-08-05T09:00:00Z')

    def test_incomplete_tail_is_dropped_not_zero(self):
        self.assertEqual(len(period_panel(self.sample(),3)),2)
        self.assertEqual(len(period_panel(self.sample(),7)),0)

    def test_gapped_window_rejected(self):
        frame=self.sample().drop(index=1)
        with self.assertRaisesRegex(ValueError,'Non-contiguous'):
            period_panel(frame,3)

    def test_later_window_label_cannot_train_early(self):
        frame=period_panel(self.sample(),3)
        frame['feature_available_at']='2026-07-30T09:00:00Z';frame['origin']='2026-08-01T00:00:00+03:00'
        with self.assertRaisesRegex(ValueError,'Training label'):
            check_fit_availability(frame,local_midnight('2026-08-05'))

    def test_probabilities_coherent_and_no_missing_horizon(self):
        frame=pd.DataFrame({'date':['D']*3,'region':['R']*3,'horizon':[1,3,7],
            'prior':[.8,.7,.9],'logistic':[.9,.5,.7]})
        result=coherent_probabilities(frame)
        self.assertEqual(result.logistic.tolist(),[.9,.9,.9])
        self.assertEqual(result.prior.tolist(),[.8,.8,.9])
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            coherent_probabilities(frame.iloc[:2])

    def test_selection_cannot_use_test(self):
        frame=pd.DataFrame({'stage':['test','test'],'model':['prior','logistic'],'brier':[.2,.1]})
        with self.assertRaisesRegex(ValueError,'rolling validation'):
            choose_probability(frame)

    def test_unknown_diagnostic_outcome_stays_missing(self):
        frame=pd.DataFrame({'date':['D']*3,'region':['R']*3,'horizon':[1,3,7],
            'prior':[.5,.6,.7],'logistic':[.6,.7,.8],'event':[1,1,np.nan]})
        output=coherent_probabilities(frame)
        self.assertTrue(pd.isna(output.loc[output.horizon.eq(7),'event'].iloc[0]))

    def test_brier_is_proper_binary_score(self):
        frame=pd.DataFrame({'horizon':[1,1],'region':['R','R'],'event':[0,1],'prior':[.5,.5],'logistic':[.1,.9]})
        _,metrics=probability_metrics(frame,'rolling_validation')
        self.assertAlmostEqual(metrics.set_index('model').loc['logistic','brier'],.01)

    def test_presence_uses_no_future_snapshot(self):
        archive=tiny_archive();basic=archive.feature_rows('2026-08-01')
        a=add_presence(archive,basic)
        archive.frames[archive.times[-1]].iloc[:]=0
        pd.testing.assert_frame_equal(a,add_presence(archive,basic))

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Small fixture independent of generated model artifacts.
        cls.data={'forecastDate':'2026-10-16','dataVersion':'2026-10-15','regions':[
            {'id':'Kyiv City','iso':'UA-30','name':'м. Київ','reason':'',
             'periods':{str(h):{'end':'2026-10-'+str(15+h),'probability':.8,
                'baselineProbability':.7,'count':2.5*h,'countBaseline':2*h} for h in [1,3,7]}},
            {'id':'Kyivska oblast','iso':'UA-32','name':'Київська','reason':'','periods':{}},
            {'id':'Zakarpatska oblast','iso':'UA-21','name':'Закарпатська','reason':'Дані застаріли',
             'periods':{'1':{'end':'2026-10-16','probability':None}}}]}

    def test_city_and_oblast_distinct(self):
        self.assertEqual(find_region(self.data,'Київ')['iso'],'UA-30')
        self.assertEqual(find_region(self.data,'Київська область')['iso'],'UA-32')

    def test_period_and_percent_semantics(self):
        text,keyboard=command('/forecast Київ 3',self.data)
        self.assertIn('80,0%',text);self.assertIn('2026-10-18',text)
        self.assertIn('за весь період',text)
        self.assertEqual(len(keyboard['inline_keyboard'][0]),3)
        with self.assertRaises(ValueError):command('/forecast Київ 2',self.data)

    def test_unknown_region_is_not_defaulted(self):
        with self.assertRaises(ValueError):command('/forecast Atlantis 1',self.data)

    def test_unavailable_is_never_zero_probability(self):
        text,_=command('/forecast Закарпатська 1',self.data)
        self.assertIn('недоступний',text);self.assertNotIn('0,0%',text)

    def test_reply_only_to_private_requests_and_callbacks(self):
        class Fake:
            def __init__(self):self.calls=[]
            def call(self,m,p):self.calls.append((m,p));return True
        api=Fake()
        handle_update({'message':{'chat':{'id':1,'type':'group'},'text':'/start'}},self.data,api)
        self.assertEqual(api.calls,[])
        handle_update({'message':{'chat':{'id':1,'type':'private'},'text':'/forecast Київ 7'}},self.data,api)
        self.assertEqual(api.calls[0][0],'sendMessage')
        handle_update({'callback_query':{'id':'callback','data':'f:UA-30:3','message':{'chat':{'id':1,'type':'private'}}}},self.data,api)
        self.assertEqual([m for m,p in api.calls][-2:],['answerCallbackQuery','sendMessage'])

    def test_network_errors_do_not_expose_token(self):
        with patch('alerts_forecast.telegram_bot.urlopen',side_effect=URLError('sensitive-url')):
            with self.assertRaises(ApiFailure) as err:TelegramAPI('123:EXAMPLE_TEST_TOKEN').call('getMe',{})
        self.assertNotIn('EXAMPLE_TEST_TOKEN',str(err.exception));self.assertNotIn('sensitive',str(err.exception))

    def test_invalid_token_never_appears_in_exception(self):
        secret='malformed secret token'
        with self.assertRaises(ApiFailure) as err:TelegramAPI(secret)
        self.assertNotIn(secret,str(err.exception))

    def test_rounding_does_not_promise_certainty(self):
        self.assertEqual(percent(.9999),'>99,9%')
        self.assertEqual(percent(.00001),'<0,1%')
