import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import TypeAdapter
from app.models.block import Block, BlockCreate, BlockType
from app.models.workflow import Workflow, WorkflowCreate, WorkflowUpdate


# Entity type for each block — used to prevent semantically incompatible chains
# (e.g. enrich_company output fed into a lead-level block).
# "any" blocks are neutral and compatible with any entity type.
# Uncomment enrich_company when implemented, then activate the check in
# _validate_block_chain below.
# _ENTITY_TYPE: Dict[BlockType, str] = {
#     BlockType.READ_CSV:       "any",
#     BlockType.FILTER:         "any",
#     BlockType.SAVE_CSV:       "any",
#     BlockType.ENRICH_LEAD:    "lead",
#     BlockType.FIND_EMAIL:     "lead",
#     BlockType.ENRICH_COMPANY: "company",
# }

# In-memory storage: workflow_id -> Workflow
_workflows: Dict[str, Workflow] = {}

_block_adapter: TypeAdapter[Block] = TypeAdapter(Block)


def _validate_block_chain(blocks: List[Block]) -> None:
    """Validate that the block sequence is logically consistent.

    Current rules (structural):
      - First block must be read_csv (it is the only data source)
      - read_csv cannot appear after position 0 (it would discard all prior work)

    To add entity-type compatibility checks (e.g. enrich_company cannot be
    followed by find_email), uncomment _ENTITY_TYPE above and add logic here
    that iterates blocks, tracks the active entity type, and raises ValueError
    on a mismatch.
    """
    if not blocks:
        return

    if blocks[0].type != BlockType.READ_CSV:
        raise ValueError("First block must be 'read_csv'")

    for block in blocks[1:]:
        if block.type == BlockType.READ_CSV:
            raise ValueError("'read_csv' can only appear as the first block")


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

    blocks = _make_blocks(payload.blocks)
    _validate_block_chain(blocks)

    workflow = Workflow(
        id=workflow_id,
        name=name,
        description=payload.description,
        blocks=blocks,
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

    if "name" in updated_fields and updated_fields["name"] is None:
        del updated_fields["name"]

    if "blocks" in updated_fields:
        if payload.blocks is None:
            del updated_fields["blocks"]
        else:
            updated_fields["blocks"] = _make_blocks(payload.blocks)
            _validate_block_chain(updated_fields["blocks"])

    if not updated_fields:
        return workflow

    updated_fields["updated_at"] = datetime.now(timezone.utc)
    updated_workflow = workflow.model_copy(update=updated_fields)
    _workflows[workflow_id] = updated_workflow
    return updated_workflow


def delete_workflow(workflow_id: str) -> bool:
    return _workflows.pop(workflow_id, None) is not None
