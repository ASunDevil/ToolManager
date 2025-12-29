import os
from typing import Optional, Dict, List, Any
from pybuildkite.buildkite import Buildkite

def _get_client() -> Buildkite:
    token = os.environ.get("BUILDKITE_API_TOKEN")
    if not token:
        raise ValueError("BUILDKITE_API_TOKEN environment variable is not set.")
    bk = Buildkite()
    bk.set_access_token(token)
    return bk

def buildkite_trigger_build(
    organization: str,
    pipeline: str,
    commit: str,
    branch: str,
    message: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    meta_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Triggers a new build in Buildkite.

    Args:
        organization: The slug of the organization.
        pipeline: The slug of the pipeline.
        commit: The commit hash to build.
        branch: The branch to build.
        message: Optional message for the build.
        env: Optional dictionary of environment variables.
        meta_data: Optional dictionary of meta-data.

    Returns:
        The response from Buildkite API containing build details.
    """
    bk = _get_client()
    # pybuildkite's create_build signature:
    # create_build(self, organization, pipeline, commit, branch, author=None, clean_checkout=None, env=None, ignore_pipeline_branch_filters=None, message=None, meta_data=None, pull_request_base_branch=None, pull_request_id=None, pull_request_repository=None, pull_request_labels=None)

    return bk.builds().create_build(
        organization=organization,
        pipeline=pipeline,
        commit=commit,
        branch=branch,
        message=message,
        env=env,
        meta_data=meta_data
    )

def buildkite_get_build_status(
    organization: str,
    pipeline: str,
    build_number: int
) -> Dict[str, Any]:
    """
    Retrieves the status of a specific build.

    Args:
        organization: The slug of the organization.
        pipeline: The slug of the pipeline.
        build_number: The build number.

    Returns:
        A dictionary containing the build state, url, and other details.
    """
    bk = _get_client()
    return bk.builds().get_build_by_number(
        organization=organization,
        pipeline=pipeline,
        build_number=build_number
    )

def buildkite_list_builds(
    organization: str,
    pipeline: str,
    states: Optional[List[str]] = None,
    branch: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Lists builds for a pipeline.

    Args:
        organization: The slug of the organization.
        pipeline: The slug of the pipeline.
        states: Optional list of states to filter by (e.g., ['running', 'passed']).
        branch: Optional branch to filter by.
        limit: Number of builds to return (default: 10).

    Returns:
        A list of build details.
    """
    bk = _get_client()
    # Note: pybuildkite uses 'page' and 'per_page' (via client init) for pagination.
    # We can use per_page logic or just fetch defaults.
    # But wait, list_all_for_pipeline doesn't accept 'per_page' as arg, it's on client.
    # Let's re-init client with per_page if limit is custom?
    # Or just slice the result. Pagination defaults to 100.

    # Let's stick to default client and slice, as 'limit' is usually small.
    # We request page=1 to ensure we don't fetch all history if the library auto-paginates.

    builds = bk.builds().list_all_for_pipeline(
        organization=organization,
        pipeline=pipeline,
        states=states or [],
        branch=branch,
        page=1
    )

    # API might return more (up to 100 by default), slice it.
    return builds[:limit]
