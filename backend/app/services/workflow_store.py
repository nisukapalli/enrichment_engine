import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import TypeAdapter
from app.models.block import Block, BlockCreate
from app.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate


# In-memory storage: workflow_id -> Workflow
_workflows: Dict[str, Workflow] = {}

_block_adapter: TypeAdapter[Block] = TypeAdapter(Block)


def generate_default_name() -> str:
    allocated_numbers = set()
    for workflow in _workflows.values():
        if workflow.name.startswith("Workflow "):
            suffix = workflow.name[len("Workflow "):]
            if suffix.isdigit():
                allocated_numbers.add(int(suffix))

    i = 1
    while True:
        if i not in allocated_numbers:
            return f"Workflow {i}"
        i += 1


def _make_blocks(block_creates: List[BlockCreate]) -> List[Block]:
    return [
        _block_adapter.validate_python(bc.model_dump() | {"id": uuid.uuid4().hex})
        for bc in block_creates
    ]


def list_workflows() -> List[Workflow]:
    return list(_workflows.values())


def get_workflow(workflow_id: str) -> Optional[Workflow]:
    return _workflows.get(workflow_id)


def create_workflow(payload: WorkflowCreate) -> Workflow:
    workflow_id = uuid.uuid4().hex
    name = payload.name
    if name is None:
        name = generate_default_name()
    created_at = datetime.now(timezone.utc)

    workflow = Workflow(
        id=workflow_id,
        name=name,
        description=payload.description,
        blocks=_make_blocks(payload.blocks),
        created_at=created_at,
        updated_at=created_at,
    )
    _workflows[workflow_id] = workflow
    return workflow


def update_workflow(workflow_id: str, payload: WorkflowUpdate) -> Optional[Workflow]:
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        return None

    updated_fields = payload.model_dump(exclude_unset=True)
    if not updated_fields:
        return workflow

    if "blocks" in updated_fields:
        updated_fields["blocks"] = _make_blocks(payload.blocks)

    updated_fields["updated_at"] = datetime.now(timezone.utc)
    updated_workflow = workflow.model_copy(update=updated_fields)
    _workflows[workflow_id] = updated_workflow
    return updated_workflow


def delete_workflow(workflow_id: str) -> bool:
    return _workflows.pop(workflow_id, None) is not None
