"""Repository layer + UnitOfWork for database operations."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.database.engine import SessionLocal
from app.database.models import (
    Field,
    Item,
    Project,
    Snapshot,
    Template,
    Workspace,
    template_sub_templates,
)

# ── Base Repository ──────────────────────────────────────────────


class _BaseRepository:
    """Thin CRUD base shared by all entity repositories."""

    model = None

    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, entity_id: str):
        return self._session.get(self.model, entity_id)

    def get_all(self):
        return self._session.query(self.model).order_by(self.model.sort_order).all()

    def delete(self, entity_id: str) -> bool:
        obj = self.get_by_id(entity_id)
        if obj is None:
            return False
        self._session.delete(obj)
        return True


# ── Workspace ────────────────────────────────────────────────────


class WorkspaceRepository(_BaseRepository):
    model = Workspace

    def create(self, name: str, description: str = "") -> Workspace:
        ws = Workspace(name=name, description=description)
        self._session.add(ws)
        self._session.flush()
        return ws

    def update(self, ws_id: str, **kwargs) -> Workspace | None:
        ws = self.get_by_id(ws_id)
        if ws is None:
            return None
        for key, value in kwargs.items():
            if hasattr(ws, key):
                setattr(ws, key, value)
        ws.updated_at = datetime.now(UTC)
        self._session.flush()
        return ws


# ── Project ──────────────────────────────────────────────────────


class ProjectRepository(_BaseRepository):
    model = Project

    def get_by_workspace(self, workspace_id: str) -> list[Project]:
        return (
            self._session.query(Project)
            .filter(Project.workspace_id == workspace_id)
            .order_by(Project.sort_order)
            .all()
        )

    def create(self, workspace_id: str, name: str, description: str = "") -> Project:
        proj = Project(workspace_id=workspace_id, name=name, description=description)
        self._session.add(proj)
        self._session.flush()
        return proj

    def update(self, proj_id: str, **kwargs) -> Project | None:
        proj = self.get_by_id(proj_id)
        if proj is None:
            return None
        for key, value in kwargs.items():
            if hasattr(proj, key):
                setattr(proj, key, value)
        proj.updated_at = datetime.now(UTC)
        self._session.flush()
        return proj

    def get_stats(self, proj_id: str) -> dict[str, int]:
        """Return counts of templates, items, and snapshots for a project."""
        t_count = self._session.query(Template).filter(Template.project_id == proj_id).count()
        i_count = self._session.query(Item).filter(Item.project_id == proj_id).count()
        s_count = self._session.query(Snapshot).filter(Snapshot.project_id == proj_id).count()
        return {"templates": t_count, "items": i_count, "snapshots": s_count}


# ── Template ─────────────────────────────────────────────────────


class TemplateRepository(_BaseRepository):
    model = Template

    def get_by_project(self, project_id: str) -> list[Template]:
        return (
            self._session.query(Template)
            .filter(Template.project_id == project_id)
            .options(joinedload(Template.fields))
            .order_by(Template.sort_order)
            .all()
        )

    def get_by_id_with_fields(self, template_id: str) -> Template | None:
        return (
            self._session.query(Template)
            .filter(Template.id == template_id)
            .options(joinedload(Template.fields))
            .first()
        )

    def create(self, project_id: str, name: str, description: str = "") -> Template:
        tmpl = Template(project_id=project_id, name=name, description=description)
        self._session.add(tmpl)
        self._session.flush()
        return tmpl

    def update(self, tmpl_id: str, **kwargs) -> Template | None:
        tmpl = self.get_by_id(tmpl_id)
        if tmpl is None:
            return None
        for key, value in kwargs.items():
            if hasattr(tmpl, key):
                setattr(tmpl, key, value)
        tmpl.updated_at = datetime.now(UTC)
        self._session.flush()
        return tmpl

    def add_sub_template(self, parent_id: str, child_id: str) -> None:
        self._session.execute(
            template_sub_templates.insert().values(parent_template_id=parent_id, child_template_id=child_id)
        )

    def remove_sub_template(self, parent_id: str, child_id: str) -> None:
        self._session.execute(
            template_sub_templates.delete().where(
                (template_sub_templates.c.parent_template_id == parent_id)
                & (template_sub_templates.c.child_template_id == child_id)
            )
        )


# ── Field ────────────────────────────────────────────────────────


class FieldRepository(_BaseRepository):
    model = Field

    def get_all(self):
        return self._session.query(Field).order_by(Field.sort_order).all()

    def get_by_template(self, template_id: str) -> list[Field]:
        return (
            self._session.query(Field)
            .filter(Field.template_id == template_id)
            .order_by(Field.sort_order)
            .all()
        )

    def create(self, template_id: str, **attrs) -> Field:
        # Serialize options list to JSON string
        if "options" in attrs and isinstance(attrs["options"], list):
            attrs["options"] = json.dumps(attrs["options"], ensure_ascii=False)
        field = Field(template_id=template_id, **attrs)
        self._session.add(field)
        self._session.flush()
        return field

    def update(self, field_id: str, **kwargs) -> Field | None:
        field = self.get_by_id(field_id)
        if field is None:
            return None
        if "options" in kwargs and isinstance(kwargs["options"], list):
            kwargs["options"] = json.dumps(kwargs["options"], ensure_ascii=False)
        for key, value in kwargs.items():
            if hasattr(field, key):
                setattr(field, key, value)
        self._session.flush()
        return field

    def reorder(self, template_id: str, ordered_ids: list[str]) -> None:
        for idx, fid in enumerate(ordered_ids):
            field = self.get_by_id(fid)
            if field and field.template_id == template_id:
                field.sort_order = idx
        self._session.flush()


# ── Item ─────────────────────────────────────────────────────────


class ItemRepository(_BaseRepository):
    model = Item

    def get_all(self):
        return self._session.query(Item).order_by(Item.created_at.desc()).all()

    def get_by_project(self, project_id: str) -> list[Item]:
        return (
            self._session.query(Item)
            .filter(Item.project_id == project_id)
            .order_by(Item.created_at.desc())
            .all()
        )

    def get_by_project_and_template(self, project_id: str, template_id: str) -> list[Item]:
        return (
            self._session.query(Item)
            .filter(Item.project_id == project_id, Item.template_id == template_id)
            .order_by(Item.created_at.desc())
            .all()
        )

    def create(self, project_id: str, template_id: str, title: str, field_values: dict[str, Any] | None = None) -> Item:
        fv = json.dumps(field_values or {}, ensure_ascii=False)
        item = Item(project_id=project_id, template_id=template_id, title=title, field_values=fv)
        self._session.add(item)
        self._session.flush()
        return item

    def update(self, item_id: str, **kwargs) -> Item | None:
        item = self.get_by_id(item_id)
        if item is None:
            return None
        if "field_values" in kwargs and isinstance(kwargs["field_values"], dict):
            kwargs["field_values"] = json.dumps(kwargs["field_values"], ensure_ascii=False)
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.now(UTC)
        self._session.flush()
        return item

    def bulk_create(self, items_data: list[dict]) -> list[Item]:
        created = []
        for data in items_data:
            fv = data.get("field_values", {})
            if isinstance(fv, dict):
                fv = json.dumps(fv, ensure_ascii=False)
            item = Item(
                project_id=data["project_id"],
                template_id=data["template_id"],
                title=data["title"],
                field_values=fv,
            )
            self._session.add(item)
            created.append(item)
        self._session.flush()
        return created


# ── Snapshot ─────────────────────────────────────────────────────


class SnapshotRepository(_BaseRepository):
    model = Snapshot

    def get_all(self):
        return self._session.query(Snapshot).order_by(Snapshot.created_at.desc()).all()

    def get_by_project(self, project_id: str) -> list[Snapshot]:
        return (
            self._session.query(Snapshot)
            .filter(Snapshot.project_id == project_id)
            .order_by(Snapshot.created_at.desc())
            .all()
        )

    def create(self, project_id: str, name: str, description: str, snapshot_data: str) -> Snapshot:
        snap = Snapshot(project_id=project_id, name=name, description=description, snapshot_data=snapshot_data)
        self._session.add(snap)
        self._session.flush()
        return snap


# ── Unit of Work ─────────────────────────────────────────────────


class UnitOfWork:
    """Transactional unit of work — create one per logical operation.

    Usage:
        with UnitOfWork() as uow:
            ws = uow.workspaces.create("My Workspace")
            uow.commit()
    """

    def __init__(self):
        self._session: Session | None = None

    def __enter__(self):
        self._session = SessionLocal()
        self.workspaces = WorkspaceRepository(self._session)
        self.projects = ProjectRepository(self._session)
        self.templates = TemplateRepository(self._session)
        self.fields = FieldRepository(self._session)
        self.items = ItemRepository(self._session)
        self.snapshots = SnapshotRepository(self._session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._session.rollback()
        self._session.close()
        self._session = None

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    @property
    def session(self) -> Session:
        return self._session
