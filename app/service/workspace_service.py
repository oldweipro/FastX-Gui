from loguru import logger

from app.database.repository import UnitOfWork


class WorkspaceService:
    """Business logic for workspace management."""

    def list_workspaces(self) -> list[dict]:
        with UnitOfWork() as uow:
            rows = uow.workspaces.get_all()
            return [
                {
                    "id": ws.id,
                    "name": ws.name,
                    "description": ws.description,
                    "sort_order": ws.sort_order,
                    "created_at": ws.created_at,
                    "updated_at": ws.updated_at,
                }
                for ws in rows
            ]

    def get_workspace(self, ws_id: str) -> dict | None:
        with UnitOfWork() as uow:
            ws = uow.workspaces.get_by_id(ws_id)
            if ws is None:
                return None
            return {
                "id": ws.id,
                "name": ws.name,
                "description": ws.description,
                "sort_order": ws.sort_order,
                "created_at": ws.created_at,
                "updated_at": ws.updated_at,
            }

    def create_workspace(self, name: str, description: str = "") -> dict:
        name = name.strip()
        if not name:
            raise ValueError("Workspace name cannot be empty")
        with UnitOfWork() as uow:
            ws = uow.workspaces.create(name=name, description=description)
            uow.commit()
            logger.info(f"[WorkspaceService] Created workspace: {ws.name} ({ws.id})")
            return {"id": ws.id, "name": ws.name, "description": ws.description}

    def update_workspace(self, ws_id: str, **kwargs) -> dict | None:
        if "name" in kwargs:
            kwargs["name"] = kwargs["name"].strip()
            if not kwargs["name"]:
                raise ValueError("Workspace name cannot be empty")
        with UnitOfWork() as uow:
            ws = uow.workspaces.update(ws_id, **kwargs)
            if ws is None:
                return None
            uow.commit()
            logger.info(f"[WorkspaceService] Updated workspace: {ws.name} ({ws.id})")
            return {"id": ws.id, "name": ws.name, "description": ws.description}

    def delete_workspace(self, ws_id: str) -> bool:
        with UnitOfWork() as uow:
            ok = uow.workspaces.delete(ws_id)
            if ok:
                uow.commit()
                logger.info(f"[WorkspaceService] Deleted workspace: {ws_id}")
            return ok
