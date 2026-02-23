"""
Comprehensive tests for /files endpoints.

Covers:
  - POST /files/upload
  - GET  /files/download/{filename}

Including path traversal security, content handling, and edge cases.
"""
import os
import io
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def csv_bytes(content="name,age\nAlice,30\nBob,25\n"):
    return content.encode()


def upload(client, filename, content=None, content_type="text/csv"):
    data = content or csv_bytes()
    return client.post(
        "/files/upload",
        files={"file": (filename, io.BytesIO(data), content_type)},
    )


_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
_OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


@pytest.fixture(autouse=True)
def clean_uploads_dir():
    """Wipe uploads/ before and after each test so overwrite-protection tests
    are not affected by files left over from previous runs."""
    os.makedirs(_UPLOADS_DIR, exist_ok=True)
    for f in os.listdir(_UPLOADS_DIR):
        os.remove(os.path.join(_UPLOADS_DIR, f))
    yield
    for f in os.listdir(_UPLOADS_DIR):
        os.remove(os.path.join(_UPLOADS_DIR, f))


# ===========================================================================
# POST /files/upload
# ===========================================================================

class TestUploadFile:

    def test_upload_csv_returns_201(self, client):
        r = upload(client, "test.csv")
        assert r.status_code == 201

    def test_upload_returns_filename(self, client):
        r = upload(client, "leads.csv")
        assert r.json() == {"filename": "leads.csv"}

    def test_upload_creates_file_on_disk(self, client):
        upload(client, "disk_test.csv")
        assert os.path.exists(os.path.join(_UPLOADS_DIR, "disk_test.csv"))

    def test_upload_file_content_is_preserved(self, client):
        content = b"col1,col2\n1,2\n3,4\n"
        upload(client, "content_test.csv", content=content)
        with open(os.path.join(_UPLOADS_DIR, "content_test.csv"), "rb") as f:
            assert f.read() == content

    def test_upload_duplicate_filename_returns_409(self, client):
        """Uploading the same filename twice returns 409 Conflict."""
        upload(client, "dup.csv", content=b"first")
        r = upload(client, "dup.csv", content=b"second")
        assert r.status_code == 409
        assert "already exists" in r.json()["detail"].lower()

    def test_upload_duplicate_does_not_overwrite_original(self, client):
        """On 409, the original file content is preserved."""
        upload(client, "safe.csv", content=b"original")
        upload(client, "safe.csv", content=b"overwrite-attempt")
        with open(os.path.join(_UPLOADS_DIR, "safe.csv"), "rb") as f:
            assert f.read() == b"original"

    def test_upload_empty_file_is_accepted(self, client):
        r = upload(client, "empty.csv", content=b"")
        assert r.status_code == 201

    def test_upload_non_csv_file_returns_400(self, client):
        """Only .csv files are allowed — non-CSV is rejected with 400."""
        r = upload(client, "data.json", content=b'{"key": "val"}', content_type="application/json")
        assert r.status_code == 400
        assert ".csv" in r.json()["detail"].lower()

    def test_upload_txt_file_returns_400(self, client):
        r = upload(client, "notes.txt", content=b"hello", content_type="text/plain")
        assert r.status_code == 400

    def test_upload_no_extension_returns_400(self, client):
        r = upload(client, "nodotcsv", content=b"data")
        assert r.status_code == 400

    def test_upload_strips_path_traversal_in_filename(self, client):
        """../secret.csv → stripped to secret.csv (still a .csv, accepted)."""
        r = upload(client, "../secret.csv")
        assert r.status_code == 201
        assert r.json()["filename"] == "secret.csv"

    def test_upload_deep_path_traversal_rejected_by_csv_check(self, client):
        """../../../etc/passwd → basename 'passwd' has no .csv extension → 400."""
        r = upload(client, "../../../etc/passwd")
        assert r.status_code == 400

    def test_upload_strips_windows_style_path(self, client):
        """Windows-style \\ is not a separator on unix — whole string is the filename."""
        r = upload(client, "subdir\\file.csv")
        assert r.status_code == 201

    def test_upload_no_file_returns_422(self, client):
        r = client.post("/files/upload")
        assert r.status_code == 422

    def test_upload_with_spaces_in_filename(self, client):
        r = upload(client, "my file.csv")
        assert r.status_code == 201
        assert r.json()["filename"] == "my file.csv"

    def test_upload_large_csv(self, client):
        rows = "\n".join(f"row{i},{i}" for i in range(10000))
        content = f"name,value\n{rows}\n".encode()
        r = upload(client, "large.csv", content=content)
        assert r.status_code == 201


# ===========================================================================
# GET /files/download/{filename}
# ===========================================================================

class TestDownloadFile:

    def _put_output_file(self, filename, content=b"col\nval\n"):
        os.makedirs(_OUTPUTS_DIR, exist_ok=True)
        with open(os.path.join(_OUTPUTS_DIR, filename), "wb") as f:
            f.write(content)

    def test_download_existing_file_returns_200(self, client):
        self._put_output_file("result.csv")
        r = client.get("/files/download/result.csv")
        assert r.status_code == 200

    def test_download_returns_csv_content(self, client):
        content = b"name,score\nAlice,99\n"
        self._put_output_file("scores.csv", content=content)
        r = client.get("/files/download/scores.csv")
        assert r.content == content

    def test_download_content_type_is_csv(self, client):
        self._put_output_file("typed.csv")
        r = client.get("/files/download/typed.csv")
        assert "text/csv" in r.headers.get("content-type", "")

    def test_download_nonexistent_file_returns_404(self, client):
        r = client.get("/files/download/no_such_file.csv")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_download_path_traversal_url_encoded_slash(self, client):
        r = client.get("/files/download/..%2F..%2Fetc%2Fpasswd")
        assert r.status_code in (400, 404)

    def test_download_empty_filename_segment(self, client):
        r = client.get("/files/download/")
        assert r.status_code in (400, 404, 405)

    def test_download_uploads_file_not_accessible(self, client):
        """Files uploaded to uploads/ are not accessible via the download endpoint."""
        upload(client, "uploaded_only.csv")
        r = client.get("/files/download/uploaded_only.csv")
        assert r.status_code == 404

    def test_download_content_disposition_header(self, client):
        self._put_output_file("download_me.csv")
        r = client.get("/files/download/download_me.csv")
        assert r.status_code == 200
        assert "download_me.csv" in r.headers.get("content-disposition", "")
