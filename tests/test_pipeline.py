import unittest
import numpy as np
import pandas as pd

from alerts_forecast.pipeline import (
    Vintages, local_midnight, check_fit_availability, metrics,
    select_on_validation, PUBLICATION_BUFFER,
)


def tiny_archive():
    archive=Vintages.__new__(Vintages)
    archive.regions=["Kyiv City"]
    old=pd.Timestamp("2026-07-30T03:00:00Z")
    future=pd.Timestamp("2026-08-01T03:00:00Z")
    archive.times=[old,future]
    archive.available={t:t+PUBLICATION_BUFFER for t in archive.times}
    dates=pd.date_range("2026-07-01","2026-07-31").strftime("%Y-%m-%d")
    archive.frames={old:pd.DataFrame({"Kyiv City":np.arange(31)},index=dates),
                    future:pd.DataFrame({"Kyiv City":np.full(31,9999)},index=dates)}
    return archive


class TemporalTests(unittest.TestCase):
    def test_local_midnight_has_correct_utc_boundary(self):
        self.assertEqual(str(local_midnight("2026-09-08").tz_convert("UTC")),"2026-09-07 21:00:00+00:00")

    def test_dst_day_is_calendar_day(self):
        start=local_midnight("2026-03-29")
        end=start+pd.DateOffset(days=1)
        self.assertEqual((end-start).total_seconds()/3600,23)

    def test_future_snapshot_cannot_change_past_features(self):
        archive=tiny_archive()
        before=archive.feature_rows("2026-08-01")
        archive.frames[archive.times[-1]].iloc[:]=888888
        after=archive.feature_rows("2026-08-01")
        pd.testing.assert_frame_equal(before,after)
        self.assertEqual(before.lag2.iloc[0],29)

    def test_missing_query_is_not_zero(self):
        archive=tiny_archive()
        archive.frames[archive.times[0]].loc["2026-07-30","Kyiv City"]=np.nan
        with self.assertRaisesRegex(ValueError,"Missing historical"):
            archive.feature_rows("2026-08-01")

    def test_future_training_label_is_rejected(self):
        data=pd.DataFrame({"label_available_at":["2026-08-02T00:00:00Z"],
                           "feature_available_at":["2026-07-28T00:00:00Z"],"origin":["2026-07-29T00:00:00Z"]})
        with self.assertRaisesRegex(ValueError,"Training label"):
            check_fit_availability(data,local_midnight("2026-08-01"))

    def test_future_feature_is_rejected(self):
        data=pd.DataFrame({"label_available_at":["2026-07-30T00:00:00Z"],
                           "feature_available_at":["2026-07-29T12:00:00Z"],"origin":["2026-07-29T00:00:00Z"]})
        with self.assertRaisesRegex(ValueError,"Feature snapshot"):
            check_fit_availability(data,local_midnight("2026-08-01"))

    def test_regional_macro_weights_are_equal(self):
        data=pd.DataFrame({"region":["A","B","B","B"],"y":[0,0,0,0],
                           "baseline":[1,3,3,3],"poisson":[1,3,3,3]})
        _,macro=metrics(data,"validation")
        self.assertTrue(macro.mae.eq(2).all())

    def test_selection_uses_validation_and_tie_prefers_baseline(self):
        score=pd.DataFrame({"split":["validation","validation"],"model":["baseline","poisson"],"mae":[1.,1.]})
        self.assertEqual(select_on_validation(score),"baseline")
        score.loc[1,"mae"]=.9
        self.assertEqual(select_on_validation(score),"poisson")

    def test_test_metrics_cannot_select_model(self):
        score=pd.DataFrame({"split":["test","test"],"model":["baseline","poisson"],"mae":[10.,0.]})
        with self.assertRaisesRegex(ValueError,"validation metrics only"):
            select_on_validation(score)

    def test_target_is_frozen_at_maturity_vintage(self):
        archive=tiny_archive()
        t,before=archive.label("2026-07-28")
        archive.frames[archive.times[-1]].iloc[:]=100000
        after_t,after=archive.label("2026-07-28")
        self.assertEqual(t,after_t)
        np.testing.assert_array_equal(before,after)

    def test_unmatured_target_is_not_available(self):
        archive=tiny_archive()
        with self.assertRaisesRegex(ValueError,"maturity window"):
            archive.label("2026-07-31")


if __name__=="__main__":
    unittest.main()
