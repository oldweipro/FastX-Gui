from app.service.import_export_service import ImportExportService
from app.service.item_service import ItemService
from app.service.project_service import ProjectService
from app.service.snapshot_service import SnapshotService
from app.service.template_service import TemplateService
from app.service.workspace_service import WorkspaceService

# Module-level singleton instances
workspace_service = WorkspaceService()
project_service = ProjectService()
template_service = TemplateService()
item_service = ItemService()
snapshot_service = SnapshotService()
import_export_service = ImportExportService()

__all__ = [
    "workspace_service",
    "project_service",
    "template_service",
    "item_service",
    "snapshot_service",
    "import_export_service",
]
