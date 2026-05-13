from pathlib import Path

from fastapi.responses import FileResponse

from process_service.src.api.gps_route import headers_handling, health_check


def test_headers_handling_sets_expected_headers(tmp_path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("data")
    response = FileResponse(path=str(sample_file), media_type="text/plain", filename="sample.txt")

    headers_handling(response, 7, 2.53)

    assert response.headers["X-Total-Count"] == "7"
    assert response.headers["X-Process-Duration"] == "2.53"


def test_health_check_reports_healthy():
    assert health_check() == {"status": "healthy"}
