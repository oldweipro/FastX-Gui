import json

from loguru import logger

from app.database.repository import UnitOfWork


class ItemService:
    """Business logic for item (fault record) management."""

    def list_items(self, project_id: str, template_id: str | None = None) -> list[dict]:
        with UnitOfWork() as uow:
            if template_id:
                rows = uow.items.get_by_project_and_template(project_id, template_id)
            else:
                rows = uow.items.get_by_project(project_id)
            return [self._item_to_dict(item) for item in rows]

    def get_item(self, item_id: str) -> dict | None:
        with UnitOfWork() as uow:
            item = uow.items.get_by_id(item_id)
            if item is None:
                return None
            return self._item_to_dict(item)

    def create_item(
        self, project_id: str, template_id: str, title: str, field_values: dict | None = None
    ) -> dict:
        title = title.strip()
        if not title:
            raise ValueError("Item title cannot be empty")
        with UnitOfWork() as uow:
            item = uow.items.create(
                project_id=project_id,
                template_id=template_id,
                title=title,
                field_values=field_values,
            )
            uow.commit()
            logger.info(f"[ItemService] Created item: {item.title} ({item.id})")
            return self._item_to_dict(item)

    def update_item(self, item_id: str, **kwargs) -> dict | None:
        if "title" in kwargs:
            kwargs["title"] = kwargs["title"].strip()
            if not kwargs["title"]:
                raise ValueError("Item title cannot be empty")
        with UnitOfWork() as uow:
            item = uow.items.update(item_id, **kwargs)
            if item is None:
                return None
            uow.commit()
            logger.info(f"[ItemService] Updated item: {item.title} ({item.id})")
            return self._item_to_dict(item)

    def delete_item(self, item_id: str) -> bool:
        with UnitOfWork() as uow:
            ok = uow.items.delete(item_id)
            if ok:
                uow.commit()
                logger.info(f"[ItemService] Deleted item: {item_id}")
            return ok

    def bulk_create(self, items_data: list[dict]) -> list[dict]:
        with UnitOfWork() as uow:
            created = uow.items.bulk_create(items_data)
            uow.commit()
            logger.info(f"[ItemService] Bulk created {len(created)} items")
            return [self._item_to_dict(i) for i in created]

    # ── helpers ──

    @staticmethod
    def _item_to_dict(item) -> dict:
        fv = item.field_values
        if isinstance(fv, str):
            try:
                fv = json.loads(fv)
            except (json.JSONDecodeError, TypeError):
                fv = {}
        return {
            "id": item.id,
            "project_id": item.project_id,
            "template_id": item.template_id,
            "title": item.title,
            "field_values": fv,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
