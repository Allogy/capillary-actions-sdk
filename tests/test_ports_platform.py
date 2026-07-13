from __future__ import annotations

from uuid import uuid4

import pytest

from capillary_actions_sdk.ports.platform import (
    EventStreamPort,
    ResumeWorkflowPort,
    ResumeWorkflowRequest,
    ResumeWorkflowResponse,
    RunWorkflowPort,
    RunWorkflowRequest,
    RunWorkflowResponse,
    StateManagerPort,
)

# ---------------------------------------------------------------------------
# Request / Response DTO tests
# ---------------------------------------------------------------------------


class TestRunWorkflowRequest:
    def test_creation_with_all_args(self):
        wf_id = uuid4()
        org_id = uuid4()
        req = RunWorkflowRequest(
            workflow_id=wf_id,
            thread_id="thread-abc",
            input_data={"key": "value"},
            org_id=org_id,
        )
        assert req.workflow_id == wf_id
        assert req.thread_id == "thread-abc"
        assert req.input_data == {"key": "value"}
        assert req.org_id == org_id

    def test_optional_fields_accept_none(self):
        req = RunWorkflowRequest(
            workflow_id=uuid4(),
            thread_id="thread-1",
            input_data=None,
            org_id=None,
        )
        assert req.input_data is None
        assert req.org_id is None


class TestRunWorkflowResponse:
    def test_creation_with_all_args(self):
        resp = RunWorkflowResponse(
            run_id="run-123",
            output={"answer": 42},
            status="completed",
        )
        assert resp.run_id == "run-123"
        assert resp.output == {"answer": 42}
        assert resp.status == "completed"

    def test_empty_output(self):
        resp = RunWorkflowResponse(run_id="run-0", output={}, status="failed")
        assert resp.output == {}
        assert resp.status == "failed"


class TestResumeWorkflowRequest:
    def test_creation_with_all_args(self):
        run_id = uuid4()
        req = ResumeWorkflowRequest(
            workflow_run_id=run_id,
            thread_id="thread-xyz",
            decision="approve",
            input_data={"extra": "data"},
            comment="Looks good",
            node_id="node-123",
        )
        assert req.workflow_run_id == run_id
        assert req.thread_id == "thread-xyz"
        assert req.node_id == "node-123"
        assert req.decision == "approve"
        assert req.input_data == {"extra": "data"}
        assert req.comment == "Looks good"

    def test_optional_fields_accept_none(self):
        req = ResumeWorkflowRequest(
            workflow_run_id=uuid4(),
            thread_id="thread-1",
            decision=None,
            input_data=None,
            comment=None,
            node_id="node-1",
        )
        assert req.node_id == "node-1"
        assert req.decision is None
        assert req.input_data is None
        assert req.comment is None


class TestResumeWorkflowResponse:
    def test_creation_with_all_args(self):
        resp = ResumeWorkflowResponse(run_id="run-456", status="completed")
        assert resp.run_id == "run-456"
        assert resp.status == "completed"

    def test_rejected_status(self):
        resp = ResumeWorkflowResponse(run_id="run-789", status="rejected")
        assert resp.status == "rejected"


# ---------------------------------------------------------------------------
# ABC instantiation tests
# ---------------------------------------------------------------------------


class TestRunWorkflowPortIsAbstract:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            RunWorkflowPort()  # type: ignore[abstract]


class TestResumeWorkflowPortIsAbstract:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            ResumeWorkflowPort()  # type: ignore[abstract]


class TestEventStreamPortIsAbstract:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            EventStreamPort()  # type: ignore[abstract]


class TestStateManagerPortIsAbstract:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            StateManagerPort()  # type: ignore[abstract]
