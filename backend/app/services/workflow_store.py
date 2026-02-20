import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate


# In-memory storage: workflow_id -> Workflow
_workflows: Dict[str, Workflow] = {}


def generate_default_name() -> str:
    pass


def list_workflows() -> List[Workflow]:
    return list(_workflows.values())


def get_workflow(workflow_id: str) -> Optional[Workflow]:
    return _workflows.get(workflow_id, None)


def create_workflow(payload: WorkflowCreate) -> Workflow:
    """
    - generate workflow id
    - fill default name if missing
    - validate duplicate block ids
    - set created_at/updated_at
    - store in _workflows
    """
    id = str(uuid.uuid4().hex)
    if payload.name is None:
        payload.name = generate_default_name()
    created_at = datetime.now(timezone.utc)
    updated_at = created_at

    # TODO: validate duplicate block ids

    raise NotImplementedError


def update_workflow(workflow_id: str, payload: WorkflowUpdate) -> Optional[Workflow]:
    """
    - 404 behavior handled by route; return None if missing
    - apply PATCH semantics (only fields provided)
    - validate duplicate block ids if blocks updated
    - bump updated_at
    """
    raise NotImplementedError


def delete_workflow(workflow_id: str) -> bool:
    raise NotImplementedError