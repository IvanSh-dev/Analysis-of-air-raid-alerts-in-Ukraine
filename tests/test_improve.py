import unittest
import pandas as pd
from alerts_forecast.improve import choose, enrich, CONFIGS, FOLDS
from tests.test_pipeline import tiny_archive

class ImprovementTests(unittest.TestCase):
    def test_diagnostic_cannot_select_model(self):
        frame=pd.DataFrame({'stage':['diagnostic'],'model':['boost_7'],'mae':[0.]})
        with self.assertRaisesRegex(ValueError,'rolling validation'):
            choose(frame)

    def test_future_revisions_do_not_change_new_features(self):
        archive=tiny_archive()
        basic=archive.feature_rows('2026-08-01')
        before=enrich(archive,basic)
        archive.frames[archive.times[-1]].iloc[:]=999999
        pd.testing.assert_frame_equal(before,enrich(archive,basic))

    def test_validation_ends_before_exposed_period(self):
        self.assertTrue(all(end<'2026-09-16' for start,end in FOLDS))
        self.assertEqual(len(CONFIGS),8)

    def test_missing_input_not_imputed_in_enrichment(self):
        archive=tiny_archive()
        basic=archive.feature_rows('2026-08-01')
        archive.frames[archive.times[0]].iloc[-3]=float('nan')
        with self.assertRaisesRegex(ValueError,'Missing archive query'):
            enrich(archive,basic)
