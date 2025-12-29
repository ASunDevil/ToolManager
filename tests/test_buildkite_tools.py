import pytest
from unittest.mock import MagicMock, patch
from src.tool_manager import ToolManager
from src.buildkite_tools import buildkite_trigger_build, buildkite_get_build_status, buildkite_list_builds

@pytest.fixture
def mock_buildkite():
    with patch("src.buildkite_tools.Buildkite") as mock:
        # Mock the client instance
        client_instance = mock.return_value

        # Mock the builds() service
        builds_service = MagicMock()
        client_instance.builds.return_value = builds_service

        yield builds_service

@pytest.mark.asyncio
async def test_buildkite_trigger_build(mock_buildkite):
    # Setup mock
    mock_buildkite.create_build.return_value = {"state": "scheduled", "number": 123}

    tm = ToolManager()
    tm.register_tool(buildkite_trigger_build)

    with patch.dict("os.environ", {"BUILDKITE_API_TOKEN": "test-token"}):
        result = await tm.call_tool(
            "buildkite_trigger_build",
            organization="my-org",
            pipeline="my-pipe",
            commit="HEAD",
            branch="main",
            message="Deploying"
        )

    assert not result["isError"]
    assert "'number': 123" in result["content"][0]["text"]

    mock_buildkite.create_build.assert_called_once_with(
        organization="my-org",
        pipeline="my-pipe",
        commit="HEAD",
        branch="main",
        message="Deploying",
        env=None,
        meta_data=None
    )

@pytest.mark.asyncio
async def test_buildkite_get_status(mock_buildkite):
    mock_buildkite.get_build_by_number.return_value = {"state": "passed"}

    tm = ToolManager()
    tm.register_tool(buildkite_get_build_status)

    with patch.dict("os.environ", {"BUILDKITE_API_TOKEN": "test-token"}):
        result = await tm.call_tool(
            "buildkite_get_build_status",
            organization="my-org",
            pipeline="my-pipe",
            build_number=123
        )

    assert "'state': 'passed'" in result["content"][0]["text"]

@pytest.mark.asyncio
async def test_buildkite_list_builds(mock_buildkite):
    mock_buildkite.list_all_for_pipeline.return_value = [{"number": 1}, {"number": 2}]

    tm = ToolManager()
    tm.register_tool(buildkite_list_builds)

    with patch.dict("os.environ", {"BUILDKITE_API_TOKEN": "test-token"}):
        result = await tm.call_tool(
            "buildkite_list_builds",
            organization="my-org",
            pipeline="my-pipe",
            limit=1
        )

    # Check limit logic in wrapper
    # result text is string rep of list, should contain only one item if wrapper sliced it
    assert "[{'number': 1}]" in result["content"][0]["text"]

    mock_buildkite.list_all_for_pipeline.assert_called_once()
