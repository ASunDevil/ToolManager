"""
Buildkite Integration Tools.
This module provides functions to interact with the Buildkite API,
wrapping the 'pybuildkite' library.
"""

import os
from typing import Optional, Dict, List, Any
from pybuildkite.buildkite import Buildkite

def _get_client() -> Buildkite:
    """
    Helper function to initialize the Buildkite client.

    It retrieves the API token from the 'BUILDKITE_API_TOKEN' environment variable.

    Returns:
        An authenticated Buildkite client instance.

    Raises:
        ValueError: If 'BUILDKITE_API_TOKEN' is not set.
    """
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
    Triggers a new build in Buildkite for a specific pipeline.

    Args:
        organization: The slug of the organization (e.g., 'my-org').
        pipeline: The slug of the pipeline (e.g., 'my-pipeline').
        commit: The commit hash to build (e.g., 'HEAD' or a specific SHA).
        branch: The branch to build (e.g., 'main').
        message: Optional message for the build.
        env: Optional dictionary of environment variables to set for the build.
        meta_data: Optional dictionary of meta-data to attach to the build.

    Returns:
        A dictionary containing details of the created build (from Buildkite API).
    """
    bk = _get_client()

    # Delegate to pybuildkite's create_build method
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
    Retrieves the status and details of a specific build.

    Args:
        organization: The slug of the organization.
        pipeline: The slug of the pipeline.
        build_number: The build number to retrieve.

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
    Lists recent builds for a pipeline, optionally filtered by state or branch.

    Args:
        organization: The slug of the organization.
        pipeline: The slug of the pipeline.
        states: Optional list of states to filter by (e.g., ['running', 'passed', 'failed']).
        branch: Optional branch to filter by.
        limit: Number of builds to return (default: 10).

    Returns:
        A list of dictionaries, where each dictionary represents a build.
    """
    bk = _get_client()

    # We request page=1 explicitly. By default, pybuildkite might auto-paginate
    # to fetch all results if not careful, or default to 100 items per page.
    # Requesting page 1 is efficient for retrieving the latest builds.

    builds = bk.builds().list_all_for_pipeline(
        organization=organization,
        pipeline=pipeline,
        states=states or [],
        branch=branch,
        page=1
    )

    # slice the result to respect the requested limit
    return builds[:limit]
