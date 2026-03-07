from loguru import logger

from app.database.repository import UnitOfWork


class ProjectService:
    """Business logic for project management."""

    def list_projects(self, workspace_id: str) -> list[dict]:
        with UnitOfWork() as uow:
            rows = uow.projects.get_by_workspace(workspace_id)
            result = []
            for p in rows:
                stats = uow.projects.get_stats(p.id)
                result.append({
                    "id": p.id,
                    "workspace_id": p.workspace_id,
                    "name": p.name,
                    "description": p.description,
                    "sort_order": p.sort_order,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                    **stats,
                })
            return result

    def get_project(self, proj_id: str) -> dict | None:
        with UnitOfWork() as uow:
            p = uow.projects.get_by_id(proj_id)
            if p is None:
                return None
            stats = uow.projects.get_stats(p.id)
            return {
                "id": p.id,
                "workspace_id": p.workspace_id,
                "name": p.name,
                "description": p.description,
                "sort_order": p.sort_order,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                **stats,
            }

    def get_overview(self, proj_id: str) -> dict:
        with UnitOfWork() as uow:
            p = uow.projects.get_by_id(proj_id)
            if p is None:
                return {}
            stats = uow.projects.get_stats(proj_id)
            return {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                **stats,
            }

    def create_project(self, workspace_id: str, name: str, description: str = "") -> dict:
        name = name.strip()
        if not name:
            raise ValueError("Project name cannot be empty")
        with UnitOfWork() as uow:
            proj = uow.projects.create(workspace_id=workspace_id, name=name, description=description)
            uow.commit()
            logger.info(f"[ProjectService] Created project: {proj.name} ({proj.id})")
            return {"id": proj.id, "workspace_id": proj.workspace_id, "name": proj.name, "description": proj.description}

    def update_project(self, proj_id: str, **kwargs) -> dict | None:
        if "name" in kwargs:
            kwargs["name"] = kwargs["name"].strip()
            if not kwargs["name"]:
                raise ValueError("Project name cannot be empty")
        with UnitOfWork() as uow:
            proj = uow.projects.update(proj_id, **kwargs)
            if proj is None:
                return None
            uow.commit()
            logger.info(f"[ProjectService] Updated project: {proj.name} ({proj.id})")
            return {"id": proj.id, "name": proj.name, "description": proj.description}

    def delete_project(self, proj_id: str) -> bool:
        with UnitOfWork() as uow:
            ok = uow.projects.delete(proj_id)
            if ok:
                uow.commit()
                logger.info(f"[ProjectService] Deleted project: {proj_id}")
            return ok
