import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ── Association tables ───────────────────────────────────────────

template_sub_templates = Table(
    "template_sub_templates",
    Base.metadata,
    Column("parent_template_id", String(36), ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True),
    Column("child_template_id", String(36), ForeignKey("templates.id", ondelete="CASCADE"), primary_key=True),
)

item_relationships = Table(
    "item_relationships",
    Base.metadata,
    Column("source_item_id", String(36), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("target_item_id", String(36), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("relationship_type", String(50), default="related"),
)


# ── Entity models ────────────────────────────────────────────────


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan", order_by="Project.sort_order")

    def __repr__(self):
        return f"<Workspace(id={self.id!r}, name={self.name!r})>"


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_project_workspace_name"),
        Index("ix_project_workspace_id", "workspace_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    workspace = relationship("Workspace", back_populates="projects")
    templates = relationship("Template", back_populates="project", cascade="all, delete-orphan", order_by="Template.sort_order")
    items = relationship("Item", back_populates="project", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan", order_by="Snapshot.created_at.desc()")

    def __repr__(self):
        return f"<Project(id={self.id!r}, name={self.name!r})>"


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_template_project_name"),
        Index("ix_template_project_id", "project_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    project = relationship("Project", back_populates="templates")
    fields = relationship("Field", back_populates="template", cascade="all, delete-orphan", order_by="Field.sort_order", foreign_keys="[Field.template_id]")

    sub_templates = relationship(
        "Template",
        secondary=template_sub_templates,
        primaryjoin=id == template_sub_templates.c.parent_template_id,
        secondaryjoin=id == template_sub_templates.c.child_template_id,
        backref="parent_templates",
    )

    def __repr__(self):
        return f"<Template(id={self.id!r}, name={self.name!r})>"


class Field(Base):
    __tablename__ = "fields"
    __table_args__ = (Index("ix_field_template_id", "template_id"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    field_type = Column(String(50), nullable=False)  # text, number, checkbox, select, date, textarea, template_item
    label = Column(String(200), default="")
    required = Column(Boolean, default=False)
    default_val = Column(Text, default="")
    options = Column(Text, default="[]")  # JSON-serialized list for select/template_item
    ref_tmpl_id = Column(String(36), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True)
    multi_select = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    template = relationship("Template", back_populates="fields", foreign_keys=[template_id])
    ref_template = relationship("Template", foreign_keys=[ref_tmpl_id])

    def __repr__(self):
        return f"<Field(id={self.id!r}, name={self.name!r}, type={self.field_type!r})>"


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_item_project_id", "project_id"),
        Index("ix_item_template_id", "template_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    field_values = Column(Text, default="{}")  # JSON-serialized dict
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    project = relationship("Project", back_populates="items")
    template = relationship("Template")

    related_items = relationship(
        "Item",
        secondary=item_relationships,
        primaryjoin=id == item_relationships.c.source_item_id,
        secondaryjoin=id == item_relationships.c.target_item_id,
    )

    def __repr__(self):
        return f"<Item(id={self.id!r}, title={self.title!r})>"


class Snapshot(Base):
    __tablename__ = "snapshots"
    __table_args__ = (Index("ix_snapshot_project_id", "project_id"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    snapshot_data = Column(Text, nullable=False)  # JSON blob of full project state
    created_at = Column(DateTime, default=_utcnow)

    project = relationship("Project", back_populates="snapshots")

    def __repr__(self):
        return f"<Snapshot(id={self.id!r}, name={self.name!r})>"
