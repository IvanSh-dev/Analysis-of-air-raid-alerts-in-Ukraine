"""Offline preparation, chronological evaluation and next-day prediction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TZ = "Europe/Kyiv"
PUBLICATION_BUFFER = pd.Timedelta(hours=6)
FEATURES = ["lag2", "lag3", "lag7", "mean7", "mean28", "dow_sin", "dow_cos"]
EXCLUDED = {"Luhanska oblast":"stale archive; persistent-alert coverage unresolved",
            "Zakarpatska oblast":"archive stops in July 2026; recent coverage unavailable",
            "Autonomous Republic of Crimea":"absent from source",
            "Sevastopol City":"absent from source"}
TRAIN = ("2026-05-01", "2026-07-29")
VALIDATION = ("2026-08-01", "2026-09-12")
TEST = ("2026-09-16", "2026-10-13")


def local_midnight(date):
    return pd.Timestamp(date).tz_localize(TZ)


class Vintages:
    def __init__(self, root=ROOT):
        raw = gzip.decompress((root/"data/vintage_counts.csv.gz").read_bytes())
        expected = (root/"data/vintage_counts.sha256").read_text().strip()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Compact input checksum mismatch")
        self.data = pd.read_csv(root/"data/vintage_counts.csv.gz")
        self.data["vintage"] = pd.to_datetime(self.data.vintage, utc=True)
        if self.data.duplicated(["vintage","date","region"]).any():
            raise ValueError("Duplicate vintage/date/region keys")
        self.times = sorted(self.data.vintage.unique())
        self.times = [pd.Timestamp(t) for t in self.times]
        self.available = {t:t+PUBLICATION_BUFFER for t in self.times}
        self.frames = {pd.Timestamp(t):g.pivot(index="date",columns="region",values="archive_records")
                       for t,g in self.data.groupby("vintage")}
        self.regions = sorted(set(self.data.region)-set(EXCLUDED))
        self.manifest = json.loads((root/"data/snapshot_manifest.json").read_text())
        self.latest = self.frames[self.times[-1]]

    def before(self, origin):
        usable = [t for t in self.times if self.available[t] < origin]
        if not usable:
            raise ValueError("No snapshot available before forecast origin")
        t = usable[-1]
        if origin-self.available[t] > pd.Timedelta(hours=72):
            raise ValueError("Archive snapshot too stale")
        return t

    def feature_rows(self, day):
        origin = local_midnight(day)
        t = self.before(origin)
        frame = self.frames[t]
        # Ignore yesterday: it was not a full day at the previous daily update.
        days = [(origin-pd.DateOffset(days=k)).strftime("%Y-%m-%d") for k in range(2,30)]
        history = frame.reindex(days)[self.regions]
        if history.isna().any().any():
            raise ValueError("Missing historical query; cannot replace with zero")
        values = history.to_numpy()
        rows = pd.DataFrame({"date":day, "region":self.regions,
            "origin":origin.isoformat(), "feature_vintage":t.isoformat(),
            "feature_available_at":self.available[t].isoformat(),
            "latest_feature_date":days[0], "lag2":values[0],"lag3":values[1],
            "lag7":values[5],"mean7":values[:7].mean(axis=0),"mean28":values.mean(axis=0),
            "dow_sin":np.sin(2*np.pi*origin.dayofweek/7),
            "dow_cos":np.cos(2*np.pi*origin.dayofweek/7)})
        assert self.available[t] < origin
        assert max(days) < day
        return rows

    def label(self, day):
        # Fixed target vintage, instead of retrospectively repaired latest counts.
        mature_after = local_midnight(day)+pd.DateOffset(days=2)
        usable = [t for t in self.times if t >= mature_after]
        if not usable or usable[0] >= mature_after+pd.DateOffset(days=1):
            raise ValueError("No daily target vintage in the required maturity window")
        t = usable[0]
        values = self.frames[t].loc[day,self.regions]
        if values.isna().any():
            raise ValueError("Missing target query")
        return t, values.to_numpy()

    def panel(self):
        records=[]
        for stamp in pd.date_range(TRAIN[0],TEST[1]):
            day=stamp.strftime("%Y-%m-%d")
            row=self.feature_rows(day)
            t, y=self.label(day)
            row["y"]=y
            row["label_vintage"]=t.isoformat()
            row["label_available_at"]=self.available[t].isoformat()
            records.append(row)
        return pd.concat(records,ignore_index=True)


def block(panel, bounds):
    return panel[panel.date.between(*bounds)].copy()


def check_fit_availability(train, fit_origin):
    available=pd.to_datetime(train.label_available_at,utc=True)
    if not (available < fit_origin).all():
        raise ValueError("Training label was not available at fit time")
    if not (pd.to_datetime(train.feature_available_at,utc=True)<pd.to_datetime(train.origin,utc=True)).all():
        raise ValueError("Feature snapshot came after its historical forecast origin")


def fit_model(train, fit_origin):
    check_fit_availability(train,fit_origin)
    # All learned transforms are fitted only on the supplied training rows.
    preprocess=ColumnTransformer([
        ("numeric",StandardScaler(),FEATURES),
        ("region",OneHotEncoder(handle_unknown="error",sparse_output=False),["region"]),
    ])
    model=make_pipeline(preprocess,PoissonRegressor(alpha=0.1,max_iter=2000,tol=1e-8))
    model.fit(train[FEATURES+["region"]],train.y)
    return model


def predict(frame,model):
    output=frame[["date","region","y"]].copy()
    output["baseline"]=frame.mean7.to_numpy()
    output["poisson"]=model.predict(frame[FEATURES+["region"]])
    if not np.isfinite(output[["baseline","poisson"]]).all().all():
        raise ValueError("Non-finite prediction")
    return output


def metrics(predictions,split):
    rows=[]
    for region, group in predictions.groupby("region"):
        for name in ("baseline","poisson"):
            error=group[name]-group.y
            rows.append({"split":split,"region":region,"model":name,"n":len(group),
                "mae":float(error.abs().mean()),"rmse":float(np.sqrt((error**2).mean())),
                "bias":float(error.mean()),"mean_target":float(group.y.mean())})
    regional=pd.DataFrame(rows)
    macro=regional.groupby(["split","model"])[["mae","rmse","bias"]].mean().reset_index()
    macro["regions"]=regional.region.nunique()
    return regional,macro


def select_on_validation(macro):
    if set(macro["split"]) != {"validation"}:
        raise ValueError("Model selection accepts validation metrics only")
    score=macro.set_index("model").mae
    return "poisson" if score["poisson"] < score["baseline"] else "baseline"


def coverage(vintages):
    latest=vintages.manifest[-1]["last_start_by_region"]
    rows=[]
    for region in sorted(set(latest)|set(EXCLUDED)):
        supported=region in vintages.regions
        rows.append({"region":region,"forecast_supported":supported,
            "last_observed_start_utc":latest.get(region),
            "last_complete_actual_alert_day":None,
            "last_mature_archive_target_day":TEST[1] if supported else None,
            "status":"source-defined proxy; actual completeness unverified" if supported else EXCLUDED[region]})
    return pd.DataFrame(rows)


def plots(panel,regional,predictions,selected,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    heat=panel.pivot(index="region",columns="date",values="y")
    fig,ax=plt.subplots(figsize=(13,8))
    image=ax.imshow(heat,aspect="auto",interpolation="nearest",cmap="YlOrRd")
    ax.set_yticks(range(len(heat)),heat.index)
    ticks=list(range(0,len(heat.columns),28))
    ax.set_xticks(ticks,[heat.columns[i] for i in ticks],rotation=30,ha="right")
    ax.set_title("Daily archive-recorded starts, 23 regions\nFixed maturity snapshots; not verified actual alert counts")
    fig.colorbar(image,ax=ax,label="Archive records")
    fig.tight_layout();fig.savefig(out/"regional_activity.png",dpi=150);plt.close(fig)

    table=regional[regional.split.eq("test")].pivot(index="region",columns="model",values="mae")
    fig,ax=plt.subplots(figsize=(11,8))
    y=np.arange(len(table))
    ax.barh(y-.18,table.baseline,height=.35,label="7-day mean baseline",color="#8695a8")
    ax.barh(y+.18,table.poisson,height=.35,label="Pooled Poisson",color="#287ca7")
    ax.set_yticks(y,table.index);ax.invert_yaxis();ax.set_xlabel("MAE: archive records per region-day")
    ax.set_title("Final test by region — all regions shown");ax.legend()
    fig.tight_layout();fig.savefig(out/"test_mae_by_region.png",dpi=150);plt.close(fig)

    examples=["Kharkivska oblast","Kyiv City","Lvivska oblast"]
    fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
    for ax,region in zip(axes,examples):
        group=predictions[predictions.region.eq(region)]
        dates=pd.to_datetime(group.date)
        ax.plot(dates,group.y,"o-",label="Observed archive target",color="#25354b",markersize=3)
        ax.plot(dates,group.baseline,label="Baseline",color="#d49b40")
        ax.plot(dates,group.poisson,label="Poisson",color="#287ca7")
        ax.set_ylabel("Records");ax.set_title(region,loc="left")
    axes[0].legend(ncol=3);fig.suptitle(f"Next-day predictions on final test; validation selected {selected}")
    fig.autofmt_xdate();fig.tight_layout();fig.savefig(out/"test_predictions.png",dpi=150);plt.close(fig)


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    vintages=Vintages()
    panel=vintages.panel()
    assert len(vintages.regions)==23
    train,val,test=(block(panel,b) for b in (TRAIN,VALIDATION,TEST))
    assert train.date.max()<val.date.min() and val.date.max()<test.date.min()
    assert test.groupby("region").size().eq(28).all()
    train_model=fit_model(train,local_midnight(VALIDATION[0]))
    val_predictions=predict(val,train_model)
    val_regional,val_macro=metrics(val_predictions,"validation")
    selected=select_on_validation(val_macro)
    decision={"selected":selected,"criterion":"lowest equal-region macro MAE on validation; ties choose baseline",
        "validation":list(VALIDATION),"simulated_selection_deadline":str(local_midnight(TEST[0])),
        "validation_macro":val_macro.to_dict("records"),"poisson_alpha":0.1,"hyperparameter_search":False}
    # Persist selection BEFORE any final-test prediction/metric is computed.
    (out/"model_selection.json").write_text(json.dumps(decision,indent=2)+"\n")
    final_train=pd.concat([train,val],ignore_index=True)
    model=fit_model(final_train,local_midnight(TEST[0]))
    test_predictions=predict(test,model)
    test_regional,test_macro=metrics(test_predictions,"test")
    regional=pd.concat([val_regional,test_regional],ignore_index=True)
    macro=pd.concat([val_macro,test_macro],ignore_index=True)
    regional.to_csv(out/"metrics_by_region.csv",index=False)
    macro.to_csv(out/"metrics_macro.csv",index=False)
    test_predictions.to_csv(out/"test_predictions.csv",index=False)
    val_predictions.to_csv(out/"validation_predictions.csv",index=False)
    errors=test_predictions.copy()
    errors["selected_prediction"]=errors[selected]
    errors["absolute_error"]=(errors.selected_prediction-errors.y).abs()
    errors.nlargest(12,"absolute_error").to_csv(out/"largest_errors.csv",index=False)
    panel.to_csv(out/"model_panel.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    coverage(vintages).to_csv(out/"coverage.csv",index=False)

    # Deployment demonstration after evaluation, with selection still fixed.
    forecast_day="2026-10-16"
    features=vintages.feature_rows(forecast_day)
    usable=panel[pd.to_datetime(panel.label_available_at,utc=True)<local_midnight(forecast_day)]
    deploy_model=fit_model(usable,local_midnight(forecast_day))
    features["baseline"]=features.mean7
    features["poisson"]=deploy_model.predict(features[FEATURES+["region"]])
    forecast=features[["date","region","feature_vintage","feature_available_at","baseline","poisson"]].copy()
    forecast["selected_model"]=selected
    forecast["forecast"]=forecast[selected]
    forecast["status"]="proxy forecast; not a safety notification"
    absent=pd.DataFrame([{"date":forecast_day,"region":r,"status":reason} for r,reason in EXCLUDED.items()])
    pd.concat([forecast,absent],ignore_index=True).sort_values("region").to_csv(out/"next_day_forecast.csv",index=False)

    revisions=[]
    for day, group in panel.groupby("date"):
        latest=vintages.latest.loc[day,group.region].to_numpy()
        revisions.extend(latest-group.y.to_numpy())
    verification={"snapshots":len(vintages.times),"regions_modelled":len(vintages.regions),
        "regions_registry":len(coverage(vintages)),"panel_rows":len(panel),
        "train_rows":len(train),"validation_rows":len(val),"test_rows":len(test),
        "train_dates":list(TRAIN),"validation_dates":list(VALIDATION),"test_dates":list(TEST),
        "latest_mature_archive_day":TEST[1],"snapshot_time_buffer_hours":6,
        "archive_queries_changed_in_later_snapshots":int(np.count_nonzero(revisions)),
        "publication_timestamp_assumption":"Git commit time plus 6 hours; actual first public availability is not independently verified",
        "future_snapshot_features":0,"unavailable_fit_labels":0,"test_used_for_selection":False,
        "target_is_actual_alert_count":False,"unknown_actual_counts_filled_with_zero":False}
    (out/"verification.json").write_text(json.dumps(verification,indent=2)+"\n")
    plots(panel,regional,test_predictions,selected,out)
    print(macro.to_string(index=False))
    print("Selected on validation:",selected)
    print(json.dumps(verification,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"results")
    args=parser.parse_args()
    run(args.output)


if __name__=="__main__":
    main()
