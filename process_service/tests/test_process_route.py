import asyncio
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from shared.schemas import ParseResult, ParseStatus

from process_service.src.api.process_route import stream_parsed_objects


class DummyManager:
    def __init__(self, parse_result):
        self.parse_result = parse_result

    async def do_all_parsers(self, file_path):
        yield self.parse_result


def test_stream_parsed_objects_produces_json_and_removes_file(tmp_path):
    temp_file = tmp_path / "temp.bin"
    temp_file.write_bytes(b"dummy")

    expected = ParseResult(
        parser_name="dummy",
        information="dummy info",
        duration=0.0,
        count=1,
        status=ParseStatus.SUCCESS,
        file_path=str(temp_file),
    )
    manager = DummyManager(expected)

    async def collect():
        results = []
        async for item in stream_parsed_objects(manager, str(temp_file)):
            results.append(item)
        return results

    output = asyncio.run(collect())

    assert len(output) == 1
    assert output[0].strip().startswith("{")
    assert not temp_file.exists()
