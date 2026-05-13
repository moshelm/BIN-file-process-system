import asyncio

from process_service.src.orchestrator import Orchestrator
from shared.schemas import ParseResult, ParseStatus


class DummyParser:
    def __init__(self, result):
        self.result = result

    def parse_file(self, file_path):
        return self.result

    def parse(self, file_path, ardupilot):
        return self.result

    def parse_file_by_only_gps_messages(self, file_path):
        return self.result

    def parse_only_by_pymavlink(self, file_path):
        return self.result


def create_result():
    return ParseResult(
        parser_name="dummy",
        information="dummy info",
        duration=0.0,
        count=0,
        status=ParseStatus.SUCCESS,
        file_path="dummy",
    )


def test_parser_methods_return_expected_results():
    orchestrator = Orchestrator()
    result = create_result()

    orchestrator.python_parser = DummyParser(result)
    orchestrator.multiprocess_parser = DummyParser(result)
    orchestrator.pymavlink_parser = DummyParser(result)
    orchestrator.ardupilot = object()

    assert asyncio.run(orchestrator.parser_pure_python("ignored")) == result
    assert asyncio.run(orchestrator.parser_file_multiprocess("ignored")) == result
    assert asyncio.run(orchestrator.parser_all_file_mavlink("ignored")) == result
    assert asyncio.run(orchestrator.parser_gps_messages("ignored")) == result


def test_do_all_parsers_yields_three_results():
    orchestrator = Orchestrator()
    result = create_result()

    orchestrator.python_parser = DummyParser(result)
    orchestrator.multiprocess_parser = DummyParser(result)
    orchestrator.pymavlink_parser = DummyParser(result)
    orchestrator.ardupilot = object()

    async def collect_results():
        return [item for item in orchestrator.do_all_parsers("ignored")]

    assert asyncio.run(collect_results()) == [result, result, result]
