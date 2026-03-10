import json

from loguru import logger

from app.view.app_interface.database.repository import UnitOfWork


class SnapshotService:
    """Business logic for manual project snapshots."""

    def list_snapshots(self, project_id: str) -> list[dict]:
        with UnitOfWork() as uow:
            rows = uow.snapshots.get_by_project(project_id)
            return [
                {
                    "id": s.id,
                    "project_id": s.project_id,
                    "name": s.name,
                    "description": s.description,
                    "created_at": s.created_at,
                    "data_size": len(s.snapshot_data) if s.snapshot_data else 0,
                }
                for s in rows
            ]

    def get_snapshot(self, snap_id: str) -> dict | None:
        with UnitOfWork() as uow:
            s = uow.snapshots.get_by_id(snap_id)
            if s is None:
                return None
            return {
                "id": s.id,
                "project_id": s.project_id,
                "name": s.name,
                "description": s.description,
                "snapshot_data": json.loads(s.snapshot_data) if s.snapshot_data else {},
                "created_at": s.created_at,
            }

    def create_snapshot(self, project_id: str, name: str, description: str = "") -> dict:
        """Capture full project state as a JSON blob."""
        name = name.strip()
        if not name:
            raise ValueError("Snapshot name cannot be empty")
        with UnitOfWork() as uow:
            project = uow.projects.get_by_id(project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")

            # Serialize full project state
            templates_data = []
            for t in uow.templates.get_by_project(project_id):
                fields_data = []
                for f in uow.fields.get_by_template(t.id):
                    options = f.options
                    if isinstance(options, str):
                        try:
                            options = json.loads(options)
                        except (json.JSONDecodeError, TypeError):
                            options = []
                    fields_data.append({
                        "id": f.id,
                        "name": f.name,
                        "field_type": f.field_type,
                        "label": f.label,
                        "required": f.required,
                        "default_val": f.default_val,
                        "options": options,
                        "ref_tmpl_id": f.ref_tmpl_id,
                        "multi_select": f.multi_select,
                        "sort_order": f.sort_order,
                    })
                templates_data.append({
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "sort_order": t.sort_order,
                    "fields": fields_data,
                    "sub_templates": [st.id for st in t.sub_templates],
                })

            items_data = []
            for item in uow.items.get_by_project(project_id):
                fv = item.field_values
                if isinstance(fv, str):
                    try:
                        fv = json.loads(fv)
                    except (json.JSONDecodeError, TypeError):
                        fv = {}
                items_data.append({
                    "id": item.id,
                    "template_id": item.template_id,
                    "title": item.title,
                    "field_values": fv,
                })

            state = {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                },
                "templates": templates_data,
                "items": items_data,
            }
            snapshot_json = json.dumps(state, ensure_ascii=False, default=str)

            snap = uow.snapshots.create(
                project_id=project_id,
                name=name,
                description=description,
                snapshot_data=snapshot_json,
            )
            uow.commit()
            logger.info(f"[SnapshotService] Created snapshot: {snap.name} ({snap.id})")
            return {
                "id": snap.id,
                "name": snap.name,
                "description": snap.description,
                "created_at": snap.created_at,
                "data_size": len(snapshot_json),
            }

    def restore_snapshot(self, snap_id: str) -> bool:
        """Restore a project from a snapshot (destructive: replaces current data)."""
        with UnitOfWork() as uow:
            snap = uow.snapshots.get_by_id(snap_id)
            if snap is None:
                raise ValueError(f"Snapshot {snap_id} not found")

            state = json.loads(snap.snapshot_data)
            project_id = snap.project_id

            # Delete current templates (cascade deletes fields) and items
            for item in uow.items.get_by_project(project_id):
                uow.items.delete(item.id)
            for tmpl in uow.templates.get_by_project(project_id):
                uow.templates.delete(tmpl.id)
            uow.session.flush()  # Ensure deletes are applied before re-creating

            # Recreate templates with fields
            for td in state.get("templates", []):
                tmpl = uow.templates.create(project_id=project_id, name=td["name"], description=td.get("description", ""))
                # Override the generated id with the snapshot id
                tmpl.id = td["id"]
                tmpl.sort_order = td.get("sort_order", 0)
                uow.session.flush()
                for fd in td.get("fields", []):
                    field = uow.fields.create(
                        template_id=tmpl.id,
                        name=fd["name"],
                        field_type=fd["field_type"],
                        label=fd.get("label", ""),
                        required=fd.get("required", False),
                        default_val=fd.get("default_val", ""),
                        options=fd.get("options", []),
                        ref_tmpl_id=fd.get("ref_tmpl_id"),
                        multi_select=fd.get("multi_select", False),
                        sort_order=fd.get("sort_order", 0),
                    )
                    field.id = fd["id"]

            uow.session.flush()

            # Restore sub-template relationships
            for td in state.get("templates", []):
                for sub_id in td.get("sub_templates", []):
                    try:
                        uow.templates.add_sub_template(td["id"], sub_id)
                    except Exception:
                        pass  # sub-template may not exist if it belongs to another project

            # Recreate items
            for id_data in state.get("items", []):
                item = uow.items.create(
                    project_id=project_id,
                    template_id=id_data["template_id"],
                    title=id_data["title"],
                    field_values=id_data.get("field_values", {}),
                )
                item.id = id_data["id"]

            uow.commit()
            logger.info(f"[SnapshotService] Restored snapshot: {snap.name} ({snap.id})")
            return True

    def delete_snapshot(self, snap_id: str) -> bool:
        with UnitOfWork() as uow:
            ok = uow.snapshots.delete(snap_id)
            if ok:
                uow.commit()
                logger.info(f"[SnapshotService] Deleted snapshot: {snap_id}")
            return ok
