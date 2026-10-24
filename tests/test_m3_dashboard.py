"""M3-B contracts, independent source comparisons and Streamlit UI regression."""

import copy
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import m3_dashboard as dashboard

STREAMLIT = importlib.util.find_spec("streamlit") is not None


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def dump_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_fixture(root):
    """Small synthetic payload using the official dates; never scientific evidence."""
    manifest = json.loads((ROOT / dashboard.SOURCES["manifest"]).read_text(encoding="utf-8"))
    dates = manifest["coverage"]["rebalance_dates"]
    label_rows, profile_rows, feature_rows = [], [], []
    for day in dates:
        period = "development" if day < "2024-01-01" else "holdout"
        for cluster, ticker in ((0, "AAA"), (1, "FPT")):
            sid = f"fixture:{ticker}"
            label_rows.append(dict(snapshot_date=day, security_id=sid, ticker=ticker,
                                   cluster_label=cluster, membership_period=period))
            profile_rows.append(dict(snapshot_date=day, cluster_label=cluster, size=1,
                                     size_ratio=0.5, membership_period=period,
                                     **{f: 999.0 for f in dashboard.MARKET_FEATURES}))
            feature_rows.append(dict(as_of_date=day, security_id=sid, ticker=ticker,
                                     **{f: float(cluster) for f in dashboard.MARKET_FEATURES}))
    manifest["coverage"]["total_member_observations"] = len(label_rows)
    for name, rows in (("labels", label_rows), ("profiles", profile_rows)):
        path = root / dashboard.SOURCES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        manifest["artifacts_sha256"][path.name] = digest(path)
    dump_json(root / dashboard.SOURCES["manifest"], manifest)
    feature_path = root / dashboard.SOURCES["features"]
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text("".join(json.dumps(r) + "\n" for r in feature_rows), encoding="utf-8")
    feature_hash = digest(feature_path)
    securities_path = root / dashboard.SOURCES["securities"]
    securities_path.write_text("".join(json.dumps({"security_id": f"fixture:{ticker}", "ticker": ticker,
                                                  "company_name": f"Fixture {ticker}"}) + "\n"
                                       for ticker in ("AAA", "FPT")), encoding="utf-8")
    dump_json(root / dashboard.SOURCES["feature_manifest"],
              {"outputs": {"canonical/feature_snapshots.jsonl": feature_hash,
                           "canonical/securities.jsonl": digest(securities_path)}})
    manifest_hash = digest(root / dashboard.SOURCES["feature_manifest"])
    dump_json(root / dashboard.SOURCES["development_manifest"], {
        "status": "PASS", "lineage": {"c8_feature_sha256": feature_hash},
        "source_manifest_hash": manifest_hash,
    })
    dump_json(root / dashboard.SOURCES["holdout_manifest"], {
        "status": "complete", "c8_feature_sha256": feature_hash,
        "c8_manifest_sha256": manifest_hash,
    })


class DashboardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        make_fixture(cls.root)
        cls.data = dashboard.load_market_data(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_stock_features_never_come_from_cluster_profile(self):
        day = dashboard.list_decision_dates(self.data)[0]
        result = dashboard.get_market_company(self.data, "AAA", day)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(set(result["features"].values()), {0.0})
        self.assertEqual(self.data["profiles"][0]["mom_21"], 999.0)

    def test_invalid_and_malformed_queries_do_not_crash(self):
        day = dashboard.list_decision_dates(self.data)[0]
        for value in (None, [], {}, 42, "2026-08-28", "2025-12-30"):
            self.assertEqual(dashboard.get_market_company(self.data, "FPT", value)["status"],
                             "SNAPSHOT_NOT_FOUND")
            self.assertEqual(dashboard.get_market_overview(self.data, value)["status"],
                             "SNAPSHOT_NOT_FOUND")
        for ticker in (None, [], {}, "NOT_A_TICKER", ""):
            self.assertEqual(dashboard.get_market_company(self.data, ticker, day)["status"],
                             "TICKER_NOT_FOUND")

    def test_missing_feature_row_preserves_cluster_and_reports_partial(self):
        data = copy.deepcopy(self.data)
        day = dashboard.list_decision_dates(data)[0]
        del data["feature_rows"][(day, "fixture:FPT")]
        result = dashboard.get_market_company(data, "FPT", day)
        self.assertEqual(result["status"], "MARKET_FEATURES_NOT_FOUND")
        self.assertEqual(result["cluster"]["cluster_label"], 1)
        self.assertIsNone(result["features"])
        audit = dashboard.validate_market_contract(data["manifest"], data["labels"],
                                                   data["profiles"], self.feature_source(data))
        self.assertEqual(audit["status"], "PARTIAL")
        self.assertEqual(audit["missing_feature_rows"], 1)

    def test_missing_value_is_not_zero_filled(self):
        data = copy.deepcopy(self.data)
        day = dashboard.list_decision_dates(data)[0]
        data["feature_rows"][(day, "fixture:FPT")]["mom_21"] = None
        result = dashboard.get_market_company(data, "FPT", day)
        self.assertEqual(result["status"], "MARKET_FEATURE_VALUES_MISSING")
        self.assertIsNone(result["features"]["mom_21"])

    def test_descriptive_names_follow_profile_instead_of_numeric_label(self):
        profiles = [dict(r) for r in self.data["profiles"][:2]]
        profiles[0].update(liquidity_21=10, size=100)
        profiles[1].update(liquidity_21=100, size=2)
        self.assertEqual(dashboard.cluster_display_names(profiles),
                         {1: "Dẫn đầu thanh khoản", 0: "Đại trà"})
        profiles[0]["liquidity_21"] = 100
        self.assertEqual(dashboard.cluster_display_names(profiles), {0: "Nhóm A", 1: "Nhóm B"})
        profiles[0]["liquidity_21"] = None
        self.assertEqual(dashboard.cluster_display_names(profiles), {0: "Nhóm A", 1: "Nhóm B"})

    def test_scatter_is_exact_stock_features_and_reports_missing_coordinates(self):
        day = dashboard.list_decision_dates(self.data)[0]
        data = copy.deepcopy(self.data)
        result = dashboard.get_market_scatter(data, day)
        self.assertEqual(len(result["rows"]), 2)
        for row in result["rows"]:
            expected = data["feature_rows"][(day, row["security_id"])]
            self.assertEqual({f: row[f] for f in dashboard.MARKET_FEATURES},
                             {f: expected[f] for f in dashboard.MARKET_FEATURES})
        for axis in (dashboard.SCATTER_X, dashboard.SCATTER_Y):
            missing_data = copy.deepcopy(data)
            missing_data["feature_rows"][(day, "fixture:FPT")][axis] = None
            result = dashboard.get_market_scatter(missing_data, day)
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(result["missing_count"], 1)
            self.assertEqual([r["ticker"] for r in result["rows"]], ["AAA"])

    def test_scatter_preserves_real_zero_and_does_not_require_old_axes(self):
        data = copy.deepcopy(self.data)
        day = dashboard.list_decision_dates(data)[0]
        data["feature_rows"][(day, "fixture:AAA")]["mom_252"] = None
        data["feature_rows"][(day, "fixture:AAA")]["mom_63"] = None
        result = dashboard.get_market_scatter(data, day)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(len(result["rows"]), 2)
        aaa = next(r for r in result["rows"] if r["ticker"] == "AAA")
        self.assertEqual(aaa["liquidity_21"], 0.0)
        self.assertEqual(aaa["beta_126"], 0.0)
        self.assertIsNone(aaa["mom_252"])

    def test_member_search_pagination_and_invalid_queries(self):
        data = copy.deepcopy(self.data)
        day = dashboard.list_decision_dates(data)[0]
        for i in range(30):
            ticker, sid = f"TEST{i:02}", f"fixture:TEST{i:02}"
            data["labels"].append(dict(snapshot_date=day, security_id=sid, ticker=ticker,
                                       cluster_label=0, membership_period="development"))
            data["company_names"][sid] = {"ticker": ticker, "company_name": "Test Company"}
            data["feature_rows"][(day, sid)] = {**data["feature_rows"][(day, "fixture:AAA")], "ticker": ticker}
        result = dashboard.get_market_members(data, day, 0, page=2, page_size=10)
        self.assertEqual((result["total"], result["total_pages"], len(result["rows"])), (31, 4, 10))
        self.assertEqual(result["rows"][0]["ticker"], "TEST09")
        self.assertEqual(result["rows"][0]["mom_21"], 0.0)
        self.assertEqual(dashboard.get_market_members(data, day, 0, search="test company")["total"], 30)
        self.assertEqual(dashboard.get_market_members(data, day, 0, search="tEsT09")["total"], 1)
        self.assertEqual(dashboard.get_market_members(data, day, 0, search="no match")["rows"], [])
        self.assertEqual(dashboard.get_market_members(data, day, 0, page=99)["page"], 4)
        for params in ({"page": 0}, {"page": []}, {"page_size": 7}, {"search": None}):
            self.assertEqual(dashboard.get_market_members(data, day, 0, **params)["status"], "INVALID_QUERY_STATE")

    def test_missing_cluster_row_does_not_crash(self):
        data = copy.deepcopy(self.data)
        day = dashboard.list_decision_dates(data)[0]
        del data["labels_by_ticker_date"][(day, "FPT")]
        self.assertEqual(dashboard.get_market_company(data, "FPT", day)["status"],
                         "MARKET_CLUSTER_NOT_FOUND")

    def feature_source(self, data):
        return {"rows": data["feature_rows"], "row_count": 168, "snapshot_count": 84,
                "feature_only_rows": 0, "feature_only_m2_dates": 0}

    def test_duplicate_label_and_many_to_many_are_blocked(self):
        rows = self.data["labels"] + [dict(self.data["labels"][0])]
        with self.assertRaisesRegex(dashboard.DataContractError, "Duplicate"):
            dashboard.validate_market_contract(
                {**self.data["manifest"], "coverage": {
                    **self.data["manifest"]["coverage"], "total_member_observations": len(rows)}},
                rows, self.data["profiles"], self.feature_source(self.data))

    def test_duplicate_feature_and_ticker_ambiguity_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "features.jsonl"
            row = {"as_of_date": "2019-01-31", "security_id": "fixture:AAA", "ticker": "AAA",
                   **{f: 0.0 for f in dashboard.MARKET_FEATURES}}
            for second in (row, {**row, "security_id": "fixture:OTHER"}):
                path.write_text(json.dumps(row) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
                with self.assertRaises(dashboard.DataContractError):
                    dashboard.load_market_features(path, self.data["labels"])

    def test_ticker_mismatch_is_blocked(self):
        data = copy.deepcopy(self.data)
        next(iter(data["feature_rows"].values()))["ticker"] = "OTHER"
        with self.assertRaisesRegex(dashboard.DataContractError, "Ticker mismatch"):
            dashboard.validate_market_contract(data["manifest"], data["labels"],
                                               data["profiles"], self.feature_source(data))

    def test_profile_size_and_snapshot_date_mismatch_are_blocked(self):
        for change in ("size", "date"):
            data = copy.deepcopy(self.data)
            if change == "size":
                data["profiles"][0]["size"] = 12
            else:
                data["manifest"]["coverage"]["rebalance_dates"][0] = "2019-01-30"
            with self.assertRaises(dashboard.DataContractError):
                dashboard.validate_market_contract(data["manifest"], data["labels"],
                                                   data["profiles"], self.feature_source(data))

    def test_file_tamper_and_lineage_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_fixture(root)
            labels_path = root / dashboard.SOURCES["labels"]
            original = labels_path.read_bytes()
            labels_path.write_bytes(original + b"\n")
            with self.assertRaisesRegex(dashboard.DataContractError, "Checksum mismatch"):
                dashboard.load_market_data(root)
            labels_path.write_bytes(original)
            manifest_path = root / dashboard.SOURCES["holdout_manifest"]
            manifest = json.loads(manifest_path.read_text())
            manifest["c8_feature_sha256"] = "0" * 64
            dump_json(manifest_path, manifest)
            with self.assertRaisesRegex(dashboard.DataContractError, "lineage"):
                dashboard.load_market_data(root)

    def test_missing_column_bad_date_and_non_numeric_feature_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "features.jsonl"
            valid = {"as_of_date": "2019-01-31", "security_id": "fixture:AAA", "ticker": "AAA",
                     **{f: 0.0 for f in dashboard.MARKET_FEATURES}}
            missing = dict(valid)
            del missing["mom_21"]
            for row in (missing, {**valid, "as_of_date": "not-a-date"},
                        {**valid, "mom_21": "invalid"}):
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                with self.assertRaises(dashboard.DataContractError):
                    dashboard.load_market_features(path, self.data["labels"])


@unittest.skipUnless((ROOT / dashboard.SOURCES["features"]).exists(), "Local heavy C8 artifact required")
class DashboardRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = dashboard.load_market_data()
        cls.labels = read_csv(ROOT / dashboard.SOURCES["labels"])
        cls.profiles = read_csv(ROOT / dashboard.SOURCES["profiles"])
        cls.samples = {}
        with (ROOT / dashboard.SOURCES["features"]).open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row["ticker"] in ("FPT", "AAA", "VNM", "VCB") and row["as_of_date"] in (
                        "2019-01-31", "2024-01-31", "2025-12-31"):
                    cls.samples[(row["as_of_date"], row["security_id"])] = row

    def test_real_data_contract_and_official_selector(self):
        dates = dashboard.list_decision_dates(self.data)
        manifest = json.loads((ROOT / dashboard.SOURCES["manifest"]).read_text())
        self.assertEqual(dates, manifest["coverage"]["rebalance_dates"])
        self.assertEqual(len(dates), 84)
        self.assertEqual(sum(d < "2024" for d in dates), 60)
        self.assertEqual(sum(d >= "2024" for d in dates), 24)
        self.assertEqual((dates[0], dates[-1]), ("2019-01-31", "2025-12-31"))
        self.assertEqual(self.data["audit"]["status"], "PASS")
        self.assertEqual(self.data["audit"]["missing_feature_rows"], 0)
        self.assertEqual(self.data["audit"]["label_rows"], 75801)
        self.assertEqual(self.data["audit"]["feature_rows"], 179880)
        self.assertEqual(self.data["audit"]["summary_profiles"], 6)

    def test_development_and_holdout_overview_equal_source(self):
        for day in ("2019-01-31", "2024-01-31", "2025-12-31"):
            result = dashboard.get_market_overview(self.data, day)
            self.assertEqual(result["status"], "OK")
            for profile in result["profiles"]:
                cluster = profile["cluster_label"]
                source = [r for r in self.profiles if r["snapshot_date"] == day
                          and int(r["cluster_label"]) == cluster]
                self.assertEqual(len(source), 1)
                self.assertEqual(profile["size"], int(source[0]["size"]))
                for field in ("size_ratio", *dashboard.MARKET_FEATURES):
                    self.assertEqual(profile[field], float(source[0][field]))
                expected_members = sorted(r["security_id"] for r in self.labels
                                          if r["snapshot_date"] == day and int(r["cluster_label"]) == cluster)
                self.assertEqual(sorted(r["security_id"] for r in result["members"][cluster]),
                                 expected_members)

    def test_representative_stock_values_equal_original_jsonl(self):
        seen = set()
        for label in self.labels:
            key = (label["snapshot_date"], label["security_id"])
            if key not in self.samples:
                continue
            result = dashboard.get_market_company(self.data, label["ticker"], label["snapshot_date"])
            self.assertEqual(result["status"], "OK")
            self.assertEqual(result["cluster"]["cluster_label"], int(label["cluster_label"]))
            self.assertEqual(result["features"], {f: self.samples[key][f] for f in dashboard.MARKET_FEATURES})
            seen.add((label["ticker"], label["snapshot_date"]))
        self.assertIn(("FPT", "2019-01-31"), seen)
        self.assertIn(("FPT", "2025-12-31"), seen)
        self.assertGreaterEqual(len(seen), 6)

    @unittest.skipUnless(STREAMLIT, "Install .[dashboard]")
    def test_real_streamlit_date_changes_and_displayed_values(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(ROOT / "m3_dashboard.py"), default_timeout=45).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(app.selectbox(key="decision_date").options,
                         dashboard.list_decision_dates(self.data))
        for day in ("2019-01-31", "2025-12-31"):
            app.selectbox(key="decision_date").select(day).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.radio), 0)
            chart_spec = json.loads(app.get("vega_lite_chart")[0].proto.spec)
            self.assertEqual(chart_spec["encoding"]["x"]["field"], "liquidity_21")
            self.assertEqual(chart_spec["encoding"]["x"]["scale"]["type"], "symlog")
            self.assertEqual(chart_spec["encoding"]["x"]["scale"]["constant"], 1e9)
            self.assertEqual(chart_spec["encoding"]["y"]["field"], "beta_126")
            self.assertEqual(chart_spec["encoding"]["y"]["scale"]["type"], "linear")
            displayed = app.dataframe[0].value
            expected = [r for r in self.profiles if r["snapshot_date"] == day]
            self.assertEqual(sum(displayed["Số mã"]), sum(int(r["size"]) for r in expected))
            aliases = dashboard.cluster_display_names([r for r in self.data["profiles"] if r["snapshot_date"] == day])
            for _, shown in displayed.iterrows():
                source = next(r for r in expected if aliases[int(r["cluster_label"])] == shown["Nhóm"])
                self.assertEqual(shown["Số mã"], int(source["size"]))
                self.assertEqual(shown["Tỷ trọng"], float(source["size_ratio"]))
                for feature in dashboard.MARKET_FEATURES:
                    self.assertEqual(float(shown[feature]), float(source[feature]))
            scatter = dashboard.get_market_scatter(self.data, day)
            self.assertEqual(len(scatter["rows"]), sum(int(r["size"]) for r in expected))
            self.assertEqual(scatter["missing_count"], 0)
            for label in (0, 1):
                page = dashboard.get_market_members(self.data, day, label, page_size=10)
                source_members = sorted([r for r in self.labels if r["snapshot_date"] == day and int(r["cluster_label"]) == label],
                                        key=lambda r: r["ticker"])
                self.assertEqual(page["total"], len(source_members))
                self.assertEqual([r["security_id"] for r in page["rows"]], [r["security_id"] for r in source_members[:10]])
        # Full-precision source assertions migrate to the member table now that
        # the user explicitly removed the separate Stock Detail screen.
        app.text_input(key="member_search").input("FPT").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.dataframe[1].value["Mã"].tolist(), ["FPT"])
        source = self.samples[("2025-12-31", "KBS:HOSE:FPT")]
        displayed = app.dataframe[1].value.iloc[0]
        self.assertEqual({f: float(displayed[f]) for f in dashboard.MARKET_FEATURES},
                         {f: source[f] for f in dashboard.MARKET_FEATURES})


@unittest.skipUnless(STREAMLIT, "Install .[dashboard] to run Streamlit tests")
class DashboardStreamlitTests(unittest.TestCase):
    def app(self, root):
        from streamlit.testing.v1 import AppTest

        def boot(root_string):
            from pathlib import Path
            from m3_dashboard import main
            main(Path(root_string))

        return AppTest.from_function(boot, args=(str(root),), default_timeout=30)

    def test_ui_dates_stock_missing_value_cache_invalidation_and_bad_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_fixture(root)
            app = self.app(root).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.selectbox(key="decision_date").options), 84)
            self.assertEqual(len(app.date_input), 0)
            self.assertEqual(len(app.radio), 0)
            self.assertFalse(hasattr(dashboard, "render_stock_detail"))
            # Layout now has filter/content columns per the reference; both remain Market-only.
            self.assertGreaterEqual(len(app.columns), 2)
            self.assertEqual(app.metric[1].value, "2")
            app.selectbox(key="decision_date").select("2019-01-31").run()
            self.assertEqual(app.metric[0].value, "2")
            self.assertEqual(app.dataframe[0].value["Nhóm"].tolist(), ["Nhóm A", "Nhóm B"])
            app.text_input(key="member_search").input("NO_MATCH").run()
            self.assertTrue(any("Không tìm thấy mã" in e.value for e in app.info))
            app.text_input(key="member_search").input("aaa").run()
            self.assertEqual(app.dataframe[1].value["Mã"].tolist(), ["AAA"])
            app.button_group(key="member_cluster").set_value(1).run()
            app.text_input(key="member_search").input("FPT").run()
            self.assertEqual(app.dataframe[1].value["Mã"].tolist(), ["FPT"])
            self.assertEqual({float(app.dataframe[1].value.iloc[0][f]) for f in dashboard.MARKET_FEATURES}, {1.0})
            # A real source change must invalidate the cached successful load.
            path = root / dashboard.SOURCES["features"]
            content = path.read_bytes()
            path.write_bytes(content + b"\n")
            app.run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("DATA_CONTRACT_BLOCKED" in e.value for e in app.error))
            path.write_bytes(content)
            app.session_state["decision_date"] = "2026-08-28"
            app.run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("SNAPSHOT_NOT_FOUND" in e.value for e in app.error))
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.selectbox(key="decision_date").value, "2025-12-31")

    def test_missing_source_shows_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = self.app(Path(tmp)).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("DATA_CONTRACT_BLOCKED" in e.value for e in app.error))

    def test_ui_explicit_missing_states(self):
        from streamlit.testing.v1 import AppTest

        def boot(data):
            import streamlit as st
            from m3_dashboard import render_overview
            render_overview(st, data, "2019-01-31")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_fixture(root)
            data = dashboard.load_market_data(root)
            data["feature_rows"][("2019-01-31", "fixture:FPT")]["mom_21"] = None
            app = AppTest.from_function(boot, args=(data,), default_timeout=30).run()
            app.button_group(key="member_cluster").set_value(1).run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn(b"MISSING", app.dataframe[1].proto.arrow_data.styler.display_values)
            self.assertTrue(any("MARKET_FEATURE_VALUES_MISSING" in w.value for w in app.warning))
            del data["feature_rows"][("2019-01-31", "fixture:FPT")]
            app = AppTest.from_function(boot, args=(data,), default_timeout=30).run()
            app.button_group(key="member_cluster").set_value(1).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("MARKET_FEATURES_NOT_FOUND" in w.value for w in app.warning))


if __name__ == "__main__":
    unittest.main()
