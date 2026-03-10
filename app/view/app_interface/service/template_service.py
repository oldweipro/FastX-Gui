import json

from loguru import logger

from app.view.app_interface.database.repository import UnitOfWork


class TemplateService:
    """Business logic for template and field management."""

    def list_templates(self, project_id: str) -> list[dict]:
        with UnitOfWork() as uow:
            rows = uow.templates.get_by_project(project_id)
            return [
                {
                    "id": t.id,
                    "project_id": t.project_id,
                    "name": t.name,
                    "description": t.description,
                    "field_count": len(t.fields),
                    "sort_order": t.sort_order,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in rows
            ]

    def get_template(self, tmpl_id: str) -> dict | None:
        with UnitOfWork() as uow:
            t = uow.templates.get_by_id_with_fields(tmpl_id)
            if t is None:
                return None
            return {
                "id": t.id,
                "project_id": t.project_id,
                "name": t.name,
                "description": t.description,
                "fields": [self._field_to_dict(f) for f in t.fields],
                "sub_templates": [st.id for st in t.sub_templates],
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }

    def create_template(
        self, project_id: str, name: str, description: str = "", fields: list[dict] | None = None
    ) -> dict:
        name = name.strip()
        if not name:
            raise ValueError("Template name cannot be empty")
        with UnitOfWork() as uow:
            tmpl = uow.templates.create(project_id=project_id, name=name, description=description)
            if fields:
                for idx, fd in enumerate(fields):
                    clean = {k: v for k, v in fd.items() if k not in ("id", "template_id")}
                    clean["sort_order"] = idx
                    uow.fields.create(template_id=tmpl.id, **clean)
            uow.commit()
            logger.info(f"[TemplateService] Created template: {tmpl.name} ({tmpl.id})")
            return {"id": tmpl.id, "name": tmpl.name, "description": tmpl.description}

    def update_template(self, tmpl_id: str, **kwargs) -> dict | None:
        fields_data = kwargs.pop("fields", None)
        if "name" in kwargs:
            kwargs["name"] = kwargs["name"].strip()
            if not kwargs["name"]:
                raise ValueError("Template name cannot be empty")
        with UnitOfWork() as uow:
            tmpl = uow.templates.update(tmpl_id, **kwargs)
            if tmpl is None:
                return None
            if fields_data is not None:
                # Replace all fields: remove existing, create new
                existing = uow.fields.get_by_template(tmpl_id)
                for f in existing:
                    uow.fields.delete(f.id)
                for idx, fd in enumerate(fields_data):
                    clean = {k: v for k, v in fd.items() if k not in ("id", "template_id")}
                    clean["sort_order"] = idx
                    uow.fields.create(template_id=tmpl_id, **clean)
            uow.commit()
            logger.info(f"[TemplateService] Updated template: {tmpl.name} ({tmpl.id})")
            return {"id": tmpl.id, "name": tmpl.name, "description": tmpl.description}

    def delete_template(self, tmpl_id: str) -> bool:
        """Delete a template. Returns False if items still reference it."""
        with UnitOfWork() as uow:
            items = uow.items.get_by_project_and_template(
                uow.templates.get_by_id(tmpl_id).project_id if uow.templates.get_by_id(tmpl_id) else "",
                tmpl_id,
            )
            if items:
                raise ValueError(f"Cannot delete template: {len(items)} item(s) still use it")
            ok = uow.templates.delete(tmpl_id)
            if ok:
                uow.commit()
                logger.info(f"[TemplateService] Deleted template: {tmpl_id}")
            return ok

    def add_sub_template(self, parent_id: str, child_id: str) -> None:
        with UnitOfWork() as uow:
            uow.templates.add_sub_template(parent_id, child_id)
            uow.commit()

    def remove_sub_template(self, parent_id: str, child_id: str) -> None:
        with UnitOfWork() as uow:
            uow.templates.remove_sub_template(parent_id, child_id)
            uow.commit()

    def get_fields(self, template_id: str) -> list[dict]:
        with UnitOfWork() as uow:
            rows = uow.fields.get_by_template(template_id)
            return [self._field_to_dict(f) for f in rows]

    # ── helpers ──

    @staticmethod
    def _field_to_dict(f) -> dict:
        options = f.options
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except (json.JSONDecodeError, TypeError):
                options = []
        return {
            "id": f.id,
            "template_id": f.template_id,
            "name": f.name,
            "field_type": f.field_type,
            "label": f.label,
            "required": f.required,
            "default_val": f.default_val,
            "options": options,
            "ref_tmpl_id": f.ref_tmpl_id,
            "multi_select": f.multi_select,
            "sort_order": f.sort_order,
        }
