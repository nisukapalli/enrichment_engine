"""
Comprehensive unit tests for block_runners.py.

Tests run_read_csv, run_filter (all 8 operators + edge cases),
run_save_csv, run_enrich_lead, and run_find_email (with mocked API client).

No HTTP layer involved — these test the Python functions directly.
"""
import os
import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch

from app.models.block import (
    ReadCsvBlock,
    FilterBlock,
    FilterParams,
    FilterOperator,
    SaveCsvBlock,
    SaveCsvParams,
    ReadCsvParams,
    EnrichLeadBlock,
    EnrichLeadParams,
    FindEmailBlock,
    FindEmailParams,
    FindEmailMode,
)
from app.services.block_runners import (
    run_read_csv,
    run_filter,
    run_save_csv,
    run_enrich_lead,
    run_find_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_read_csv_block(path: str) -> ReadCsvBlock:
    return ReadCsvBlock(id="blk1", type="read_csv", params=ReadCsvParams(path=path))


def make_filter_block(column: str, operator: FilterOperator, value: str) -> FilterBlock:
    return FilterBlock(
        id="blk2",
        type="filter",
        params=FilterParams(column=column, operator=operator, value=value),
    )


def make_save_csv_block(path: str) -> SaveCsvBlock:
    return SaveCsvBlock(id="blk3", type="save_csv", params=SaveCsvParams(path=path))


def make_enrich_lead_block(struct: dict, research_plan=None) -> EnrichLeadBlock:
    return EnrichLeadBlock(
        id="blk4",
        type="enrich_lead",
        params=EnrichLeadParams(struct=struct, research_plan=research_plan),
    )


def make_find_email_block(mode=FindEmailMode.PROFESSIONAL) -> FindEmailBlock:
    return FindEmailBlock(
        id="blk5",
        type="find_email",
        params=FindEmailParams(mode=mode),
    )


# Sample DataFrame used across filter tests
SAMPLE_DF = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "age": [25, 30, 35, 28, 42],
    "score": [90.5, 80.0, 70.0, 95.0, 60.0],
    "tag": ["alpha", "beta", "alpha", "gamma", "beta"],
    "notes": [None, "has notes", "has notes", None, ""],
})


# ===========================================================================
# run_read_csv
# ===========================================================================

class TestRunReadCsv:

    def test_reads_valid_csv(self, tmp_path, monkeypatch):
        csv = tmp_path / "data.csv"
        csv.write_text("name,age\nAlice,30\nBob,25\n")
        monkeypatch.setattr("app.services.block_runners._UPLOADS_DIR", str(tmp_path))

        block = make_read_csv_block("data.csv")
        df = run_read_csv(block)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["name", "age"]
        assert len(df) == 2

    def test_reads_csv_values_correctly(self, tmp_path, monkeypatch):
        csv = tmp_path / "vals.csv"
        csv.write_text("x,y\n1,a\n2,b\n")
        monkeypatch.setattr("app.services.block_runners._UPLOADS_DIR", str(tmp_path))

        df = run_read_csv(make_read_csv_block("vals.csv"))
        assert df["x"].tolist() == [1, 2]
        assert df["y"].tolist() == ["a", "b"]

    def test_reads_empty_csv_returns_empty_df(self, tmp_path, monkeypatch):
        csv = tmp_path / "empty.csv"
        csv.write_text("col1,col2\n")
        monkeypatch.setattr("app.services.block_runners._UPLOADS_DIR", str(tmp_path))

        df = run_read_csv(make_read_csv_block("empty.csv"))
        assert len(df) == 0
        assert list(df.columns) == ["col1", "col2"]

    def test_raises_on_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.block_runners._UPLOADS_DIR", str(tmp_path))
        block = make_read_csv_block("nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            run_read_csv(block)

    def test_absolute_path_in_params_bypasses_uploads_dir(self, tmp_path, monkeypatch):
        """
        SECURITY BUG: os.path.join(uploads_dir, absolute_path) returns the
        absolute path directly. A block with path='/etc/passwd' could read
        arbitrary files from the filesystem.
        """
        monkeypatch.setattr("app.services.block_runners._UPLOADS_DIR", str(tmp_path))
        # Create a file outside uploads_dir to confirm the vulnerability
        external = tmp_path.parent / "external.csv"
        external.write_text("secret,data\n1,2\n")
        block = make_read_csv_block(str(external))  # absolute path
        # This should raise (path traversal blocked) but currently reads the file
        try:
            df = run_read_csv(block)
            pytest.fail(
                "SECURITY BUG: run_read_csv read a file outside uploads/ via absolute path. "
                f"Read {len(df)} rows from {external}"
            )
        except (FileNotFoundError, Exception):
            pass  # If it raises for another reason, that's also fine to document


# ===========================================================================
# run_filter
# ===========================================================================

class TestRunFilter:

    # --- CONTAINS ---

    def test_contains_matches_substring(self):
        block = make_filter_block("tag", FilterOperator.CONTAINS, "alpha")
        result = run_filter(block, SAMPLE_DF)
        assert set(result["name"]) == {"Alice", "Charlie"}

    def test_contains_is_case_sensitive(self):
        block = make_filter_block("tag", FilterOperator.CONTAINS, "ALPHA")
        result = run_filter(block, SAMPLE_DF)
        assert len(result) == 0  # no match — case sensitive

    def test_contains_with_nan_values(self):
        block = make_filter_block("notes", FilterOperator.CONTAINS, "has")
        result = run_filter(block, SAMPLE_DF)
        # NaN rows are excluded (na=False), matching rows with "has notes"
        assert len(result) == 2

    def test_contains_empty_string_matches_all(self):
        block = make_filter_block("name", FilterOperator.CONTAINS, "")
        result = run_filter(block, SAMPLE_DF)
        assert len(result) == len(SAMPLE_DF)

    def test_contains_resets_index(self):
        block = make_filter_block("tag", FilterOperator.CONTAINS, "alpha")
        result = run_filter(block, SAMPLE_DF)
        assert list(result.index) == list(range(len(result)))

    # --- NOT_CONTAINS ---

    def test_not_contains_excludes_matching_rows(self):
        block = make_filter_block("tag", FilterOperator.NOT_CONTAINS, "alpha")
        result = run_filter(block, SAMPLE_DF)
        assert "Alice" not in result["name"].values
        assert "Charlie" not in result["name"].values

    def test_not_contains_includes_nan_as_not_containing(self):
        block = make_filter_block("notes", FilterOperator.NOT_CONTAINS, "has")
        result = run_filter(block, SAMPLE_DF)
        # NaN rows don't contain "has" → included (na=False means NaN→False for contains, so NOT False → True)
        assert len(result) == 3  # Diana (None), Eve (""), and the inverse

    # --- EQUALS ---

    def test_equals_string_match(self):
        block = make_filter_block("tag", FilterOperator.EQUALS, "alpha")
        result = run_filter(block, SAMPLE_DF)
        assert set(result["name"]) == {"Alice", "Charlie"}

    def test_equals_numeric_match_via_float_coercion(self):
        block = make_filter_block("age", FilterOperator.EQUALS, "30")
        result = run_filter(block, SAMPLE_DF)
        assert set(result["name"]) == {"Bob"}

    def test_equals_numeric_string_like_1_0_on_int_column(self):
        df = pd.DataFrame({"val": [1, 2, 3]})
        block = make_filter_block("val", FilterOperator.EQUALS, "1.0")
        result = run_filter(block, df)
        assert len(result) == 1  # 1 == 1.0 via float coercion

    def test_equals_no_match(self):
        block = make_filter_block("tag", FilterOperator.EQUALS, "delta")
        result = run_filter(block, SAMPLE_DF)
        assert len(result) == 0

    # --- NOT_EQUALS ---

    def test_not_equals_string(self):
        block = make_filter_block("tag", FilterOperator.NOT_EQUALS, "alpha")
        result = run_filter(block, SAMPLE_DF)
        assert "Alice" not in result["name"].values

    def test_not_equals_all_rows_when_no_match(self):
        block = make_filter_block("tag", FilterOperator.NOT_EQUALS, "zzzz")
        result = run_filter(block, SAMPLE_DF)
        assert len(result) == len(SAMPLE_DF)

    # --- GT ---

    def test_gt_numeric(self):
        block = make_filter_block("age", FilterOperator.GT, "30")
        result = run_filter(block, SAMPLE_DF)
        assert all(result["age"] > 30)
        assert set(result["name"]) == {"Charlie", "Eve"}

    def test_gt_no_match_when_all_equal(self):
        df = pd.DataFrame({"x": [5, 5, 5]})
        block = make_filter_block("x", FilterOperator.GT, "5")
        result = run_filter(block, df)
        assert len(result) == 0

    def test_gt_raises_if_value_not_numeric(self):
        block = make_filter_block("age", FilterOperator.GT, "not_a_number")
        with pytest.raises(ValueError, match="numeric"):
            run_filter(block, SAMPLE_DF)

    def test_gt_non_numeric_column_values_become_nan_and_excluded(self):
        df = pd.DataFrame({"x": ["abc", "10", "xyz", "5"]})
        block = make_filter_block("x", FilterOperator.GT, "4")
        result = run_filter(block, df)
        # "abc" and "xyz" → NaN → excluded; "10" > 4, "5" > 4
        assert set(result["x"]) == {"10", "5"}

    # --- GTE ---

    def test_gte_includes_equal_values(self):
        block = make_filter_block("age", FilterOperator.GTE, "30")
        result = run_filter(block, SAMPLE_DF)
        assert all(result["age"] >= 30)
        assert "Bob" in result["name"].values  # age=30, included

    def test_gte_raises_if_value_not_numeric(self):
        block = make_filter_block("age", FilterOperator.GTE, "abc")
        with pytest.raises(ValueError):
            run_filter(block, SAMPLE_DF)

    # --- LT ---

    def test_lt_numeric(self):
        block = make_filter_block("age", FilterOperator.LT, "30")
        result = run_filter(block, SAMPLE_DF)
        assert all(result["age"] < 30)
        assert set(result["name"]) == {"Alice", "Diana"}

    def test_lt_raises_if_value_not_numeric(self):
        block = make_filter_block("age", FilterOperator.LT, "oops")
        with pytest.raises(ValueError):
            run_filter(block, SAMPLE_DF)

    # --- LTE ---

    def test_lte_includes_equal_values(self):
        block = make_filter_block("age", FilterOperator.LTE, "25")
        result = run_filter(block, SAMPLE_DF)
        assert all(result["age"] <= 25)
        assert "Alice" in result["name"].values  # age=25, included

    def test_lte_raises_if_value_not_numeric(self):
        block = make_filter_block("age", FilterOperator.LTE, "bad")
        with pytest.raises(ValueError):
            run_filter(block, SAMPLE_DF)

    # --- Edge cases ---

    def test_filter_on_nonexistent_column_raises_key_error(self):
        block = make_filter_block("nonexistent_col", FilterOperator.EQUALS, "x")
        with pytest.raises(KeyError):
            run_filter(block, SAMPLE_DF)

    def test_filter_on_empty_dataframe_returns_empty(self):
        empty_df = pd.DataFrame({"age": [], "name": []})
        block = make_filter_block("age", FilterOperator.GT, "10")
        result = run_filter(block, empty_df)
        assert len(result) == 0

    def test_filter_does_not_mutate_original_df(self):
        original_len = len(SAMPLE_DF)
        block = make_filter_block("age", FilterOperator.GT, "30")
        run_filter(block, SAMPLE_DF)
        assert len(SAMPLE_DF) == original_len


# ===========================================================================
# run_save_csv
# ===========================================================================

class TestRunSaveCsv:

    def test_saves_csv_to_outputs_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(tmp_path))
        block = make_save_csv_block("out.csv")
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        run_save_csv(block, df)
        assert os.path.exists(os.path.join(str(tmp_path), "out.csv"))

    def test_save_returns_same_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(tmp_path))
        block = make_save_csv_block("ret.csv")
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = run_save_csv(block, df)
        pd.testing.assert_frame_equal(result, df)

    def test_save_csv_content_is_correct(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(tmp_path))
        block = make_save_csv_block("check.csv")
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        run_save_csv(block, df)
        loaded = pd.read_csv(os.path.join(str(tmp_path), "check.csv"))
        pd.testing.assert_frame_equal(loaded, df)

    def test_save_creates_outputs_dir_if_missing(self, tmp_path, monkeypatch):
        new_dir = tmp_path / "new_outputs"
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(new_dir))
        block = make_save_csv_block("f.csv")
        run_save_csv(block, pd.DataFrame({"x": [1]}))
        assert os.path.exists(str(new_dir))

    def test_save_no_index_column(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(tmp_path))
        block = make_save_csv_block("noindex.csv")
        df = pd.DataFrame({"a": [1, 2]})
        run_save_csv(block, df)
        loaded = pd.read_csv(os.path.join(str(tmp_path), "noindex.csv"))
        assert "Unnamed: 0" not in loaded.columns

    def test_save_absolute_path_in_params_bypasses_outputs_dir(self, tmp_path, monkeypatch):
        """
        SECURITY BUG: save_csv has the same path traversal issue as read_csv.
        An absolute path in params.path can write to arbitrary filesystem locations.
        """
        monkeypatch.setattr("app.services.block_runners._OUTPUTS_DIR", str(tmp_path / "outputs"))
        external_path = str(tmp_path / "external_write.csv")
        block = make_save_csv_block(external_path)  # absolute path
        df = pd.DataFrame({"x": [1]})
        try:
            run_save_csv(block, df)
            if os.path.exists(external_path):
                pytest.fail(
                    f"SECURITY BUG: run_save_csv wrote to {external_path} outside outputs/ "
                    "via absolute path in block params."
                )
        except Exception:
            pass


# ===========================================================================
# run_enrich_lead  (mocked API client)
# ===========================================================================

class TestRunEnrichLead:

    @pytest.mark.asyncio
    async def test_enrich_adds_struct_columns(self):
        df = pd.DataFrame({
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
        })
        block = make_enrich_lead_block({"company": "company name", "title": "job title"})

        with (
            patch("app.services.sixtyfour_client.enrich_lead_async", new=AsyncMock(return_value="task-1")),
            patch("app.services.sixtyfour_client.poll_job_status", new=AsyncMock(
                side_effect=[
                    {"company": "Acme", "title": "Engineer"},
                    {"company": "Corp", "title": "Manager"},
                ]
            )),
        ):
            result = await run_enrich_lead(block, df)

        assert "company" in result.columns
        assert "title" in result.columns
        assert result["company"].tolist() == ["Acme", "Corp"]
        assert result["title"].tolist() == ["Engineer", "Manager"]

    @pytest.mark.asyncio
    async def test_enrich_preserves_original_columns(self):
        df = pd.DataFrame({"name": ["Alice"], "email": ["a@b.com"]})
        block = make_enrich_lead_block({"bio": "short bio"})

        with (
            patch("app.services.sixtyfour_client.enrich_lead_async", new=AsyncMock(return_value="t1")),
            patch("app.services.sixtyfour_client.poll_job_status", new=AsyncMock(return_value={"bio": "A person"})),
        ):
            result = await run_enrich_lead(block, df)

        assert "name" in result.columns
        assert "email" in result.columns

    @pytest.mark.asyncio
    async def test_enrich_missing_struct_key_in_result_becomes_none(self):
        df = pd.DataFrame({"name": ["Alice"]})
        block = make_enrich_lead_block({"company": "company"})

        with (
            patch("app.services.sixtyfour_client.enrich_lead_async", new=AsyncMock(return_value="t1")),
            patch("app.services.sixtyfour_client.poll_job_status", new=AsyncMock(return_value={})),
        ):
            result = await run_enrich_lead(block, df)

        assert result["company"].iloc[0] is None

    @pytest.mark.asyncio
    async def test_enrich_na_values_converted_to_none_in_lead_info(self):
        """NaN values in DataFrame are converted to None before sending to API."""
        df = pd.DataFrame({"name": ["Alice"], "middle": [float("nan")]})
        block = make_enrich_lead_block({"bio": "bio"})

        captured_calls = []

        async def fake_enrich(lead_info, struct, research_plan=None):
            captured_calls.append(lead_info)
            return "task-1"

        with (
            patch("app.services.sixtyfour_client.enrich_lead_async", new=fake_enrich),
            patch("app.services.sixtyfour_client.poll_job_status", new=AsyncMock(return_value={"bio": "X"})),
        ):
            await run_enrich_lead(block, df)

        assert captured_calls[0]["middle"] is None  # NaN converted to None

    @pytest.mark.asyncio
    async def test_enrich_empty_df_returns_empty(self):
        df = pd.DataFrame({"name": []})
        block = make_enrich_lead_block({"bio": "bio"})
        with (
            patch("app.services.sixtyfour_client.enrich_lead_async", new=AsyncMock(return_value="t1")),
            patch("app.services.sixtyfour_client.poll_job_status", new=AsyncMock(return_value={})),
        ):
            result = await run_enrich_lead(block, df)
        assert len(result) == 0
        assert "bio" in result.columns


# ===========================================================================
# run_find_email  (mocked API client)
# ===========================================================================

class TestRunFindEmail:

    @pytest.mark.asyncio
    async def test_find_email_adds_found_email_column(self):
        df = pd.DataFrame({"first_name": ["Alice", "Bob"], "last_name": ["Smith", "Jones"]})
        block = make_find_email_block(FindEmailMode.PROFESSIONAL)

        with patch(
            "app.services.sixtyfour_client.find_email",
            new=AsyncMock(side_effect=[
                {"email": "alice@acme.com"},
                {"email": "bob@corp.com"},
            ]),
        ):
            result = await run_find_email(block, df)

        assert "found_email" in result.columns
        assert result["found_email"].tolist() == ["alice@acme.com", "bob@corp.com"]

    @pytest.mark.asyncio
    async def test_find_email_preserves_original_columns(self):
        df = pd.DataFrame({"name": ["Alice"]})
        block = make_find_email_block()

        with patch(
            "app.services.sixtyfour_client.find_email",
            new=AsyncMock(return_value={"email": "a@b.com"}),
        ):
            result = await run_find_email(block, df)

        assert "name" in result.columns

    @pytest.mark.asyncio
    async def test_find_email_missing_email_key_becomes_none(self):
        df = pd.DataFrame({"name": ["Alice"]})
        block = make_find_email_block()

        with patch(
            "app.services.sixtyfour_client.find_email",
            new=AsyncMock(return_value={}),
        ):
            result = await run_find_email(block, df)

        assert result["found_email"].iloc[0] is None

    @pytest.mark.asyncio
    async def test_find_email_passes_mode_to_client(self):
        df = pd.DataFrame({"name": ["Alice"]})
        block = make_find_email_block(FindEmailMode.PERSONAL)

        calls = []

        async def mock_find(lead, mode):
            calls.append(mode)
            return {"email": "personal@email.com"}

        with patch("app.services.sixtyfour_client.find_email", new=mock_find):
            await run_find_email(block, df)

        assert calls[0] == "PERSONAL"

    @pytest.mark.asyncio
    async def test_find_email_na_values_converted_to_none(self):
        df = pd.DataFrame({"name": ["Alice"], "phone": [float("nan")]})
        block = make_find_email_block()

        captured = []

        async def mock_find(lead, mode):
            captured.append(lead)
            return {"email": "x@y.com"}

        with patch("app.services.sixtyfour_client.find_email", new=mock_find):
            await run_find_email(block, df)

        assert captured[0]["phone"] is None

    @pytest.mark.asyncio
    async def test_find_email_empty_df_returns_empty(self):
        df = pd.DataFrame({"name": []})
        block = make_find_email_block()

        with patch(
            "app.services.sixtyfour_client.find_email",
            new=AsyncMock(return_value={"email": "x@y.com"}),
        ):
            result = await run_find_email(block, df)

        assert len(result) == 0
        assert "found_email" in result.columns
