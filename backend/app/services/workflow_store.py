import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.models.block import Block
from app.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate


# In-memory storage: workflow_id -> Workflow
_workflows: Dict[str, Workflow] = {}


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


def check_duplicate_blocks(blocks: List[Block]) -> List[str]:
    block_ids = set()
    duplicate_ids = set()
    for block in blocks:
        if not block.id:
            raise ValueError("Block id is required")
        if block.id in block_ids:
            duplicate_ids.add(block.id)
        else:
            block_ids.add(block.id)
    return sorted(duplicate_ids)


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
    updated_at = created_at

    duplicate_ids = check_duplicate_blocks(payload.blocks)
    if duplicate_ids:
        raise ValueError(f"Duplicate block ids: {duplicate_ids}")

    workflow = Workflow(
        id=workflow_id,
        name=name,
        description=payload.description,
        blocks=payload.blocks,
        created_at=created_at,
        updated_at=updated_at,
    )
    _workflows[workflow_id] = workflow

    return workflow


def update_workflow(workflow_id: str, payload: WorkflowUpdate) -> Optional[Workflow]:
    """
    - 404 behavior handled by route; return None if missing
    - apply PATCH semantics (only fields provided)
    - validate duplicate block ids if blocks updated
    - bump updated_at
    """
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        return None

    updated_fields = payload.model_dump(exclude_unset=True)
    if not updated_fields:
        return workflow

    if "blocks" in updated_fields:
        new_blocks = updated_fields["blocks"]
        duplicate_ids = check_duplicate_blocks(new_blocks)
        if duplicate_ids:
            raise ValueError(f"Duplicate blocks: {duplicate_ids}")
    
    updated_fields["updated_at"] = datetime.now(timezone.utc)
    updated_workflow = workflow.model_copy(update=updated_fields)
    _workflows[workflow_id] = updated_workflow

    return updated_workflow


def delete_workflow(workflow_id: str) -> bool:
    return _workflows.pop(workflow_id, None) is not None