import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any


class Field:
    """字段类，定义表单字段"""
    def __init__(self, name: str, field_type: str, label: str, required: bool = False, default: Any = None, options: List[str] = None, template_id: str = None, multi_select: bool = False):
        self.id = str(uuid.uuid4())
        self.name = name
        self.field_type = field_type  # text, number, checkbox, select, date, textarea, template_item
        self.label = label
        self.required = required
        self.default = default
        self.options = options or []
        self.template_id = template_id  # 用于template_item类型，指定从中获取条目的模板ID
        self.multi_select = multi_select  # 用于template_item类型，是否允许多选

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "field_type": self.field_type,
            "label": self.label,
            "required": self.required,
            "default": self.default,
            "options": self.options,
            "template_id": self.template_id,
            "multi_select": self.multi_select
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Field':
        field = cls(
            name=data['name'],
            field_type=data['field_type'],
            label=data['label'],
            required=data.get('required', False),
            default=data.get('default'),
            options=data.get('options', []),
            template_id=data.get('template_id'),
            multi_select=data.get('multi_select', False)
        )
        field.id = data['id']
        return field


class Template:
    """模板类，包含字段定义和子模板"""
    def __init__(self, name: str, project_id: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.project_id = project_id  # 所属项目ID
        self.description = description
        self.fields: List[Field] = []
        self.sub_templates: List[str] = []  # 子模板ID列表
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def add_field(self, field: Field):
        self.fields.append(field)
        self.updated_at = datetime.now().isoformat()

    def remove_field(self, field_id: str):
        self.fields = [f for f in self.fields if f.id != field_id]
        self.updated_at = datetime.now().isoformat()

    def add_sub_template(self, template_id: str):
        if template_id not in self.sub_templates:
            self.sub_templates.append(template_id)
            self.updated_at = datetime.now().isoformat()

    def remove_sub_template(self, template_id: str):
        if template_id in self.sub_templates:
            self.sub_templates.remove(template_id)
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "sub_templates": self.sub_templates,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Template':
        # 为旧数据添加默认的project_id
        project_id = data.get('project_id', "")
        template = cls(
            name=data['name'],
            project_id=project_id,
            description=data.get('description', "")
        )
        template.id = data['id']
        template.fields = [Field.from_dict(f) for f in data.get('fields', [])]
        template.sub_templates = data.get('sub_templates', [])
        template.created_at = data.get('created_at', datetime.now().isoformat())
        template.updated_at = data.get('updated_at', datetime.now().isoformat())
        return template


class Project:
    """项目类，包含多个条目和模板集合"""
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.item_ids: List[str] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def add_item(self, item_id: str):
        if item_id not in self.item_ids:
            self.item_ids.append(item_id)
            self.updated_at = datetime.now().isoformat()

    def remove_item(self, item_id: str):
        if item_id in self.item_ids:
            self.item_ids.remove(item_id)
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_ids": self.item_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Project':
        project = cls(
            name=data['name'],
            description=data.get('description', "")
        )
        project.id = data['id']
        project.item_ids = data.get('item_ids', [])
        project.created_at = data.get('created_at', datetime.now().isoformat())
        project.updated_at = data.get('updated_at', datetime.now().isoformat())
        return project


class Item:
    """条目类，基于模板创建，包含字段值"""
    def __init__(self, template_id: str, project_id: str, title: str = ""):
        self.id = str(uuid.uuid4())
        self.template_id = template_id
        self.project_id = project_id
        self.title = title
        self.field_values: Dict[str, Any] = {}
        self.relationships: List[Dict] = []  # 关联关系
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def set_field_value(self, field_id: str, value: Any):
        self.field_values[field_id] = value
        self.updated_at = datetime.now().isoformat()

    def add_relationship(self, related_item_id: str, relationship_type: str):
        self.relationships.append({
            "related_item_id": related_item_id,
            "relationship_type": relationship_type
        })
        self.updated_at = datetime.now().isoformat()

    def remove_relationship(self, related_item_id: str):
        self.relationships = [r for r in self.relationships if r['related_item_id'] != related_item_id]
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "project_id": self.project_id,
            "title": self.title,
            "field_values": self.field_values,
            "relationships": self.relationships,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Item':
        item = cls(
            template_id=data['template_id'],
            project_id=data['project_id'],
            title=data.get('title', "")
        )
        item.id = data['id']
        item.field_values = data.get('field_values', {})
        item.relationships = data.get('relationships', [])
        item.created_at = data.get('created_at', datetime.now().isoformat())
        item.updated_at = data.get('updated_at', datetime.now().isoformat())
        return item


class FaultManager:
    """故障管理文档系统的核心类，管理所有数据"""
    def __init__(self, storage_path: str = "fault_manager_data.json"):
        self.storage_path = storage_path
        self.templates: Dict[str, Template] = {}
        self.projects: Dict[str, Project] = {}
        self.items: Dict[str, Item] = {}
        self.load_data()

    def save_data(self):
        """保存数据到JSON文件"""
        print(f"[FaultManager] 保存数据到 {self.storage_path}")
        data = {
            "templates": [t.to_dict() for t in self.templates.values()],
            "projects": [p.to_dict() for p in self.projects.values()],
            "items": [i.to_dict() for i in self.items.values()]
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[FaultManager] 数据保存成功")

    def load_data(self):
        """从JSON文件加载数据"""
        print(f"[FaultManager] 从 {self.storage_path} 加载数据")
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.templates = {t['id']: Template.from_dict(t) for t in data.get('templates', [])}
                self.projects = {p['id']: Project.from_dict(p) for p in data.get('projects', [])}
                self.items = {i['id']: Item.from_dict(i) for i in data.get('items', [])}
            print(f"[FaultManager] 数据加载成功: {len(self.templates)} 个模板, {len(self.projects)} 个项目, {len(self.items)} 个条目")
        except FileNotFoundError:
            # 文件不存在，初始化空数据
            print(f"[FaultManager] 文件不存在，初始化空数据")
            pass

    # 模板管理方法
    def create_template(self, name: str, project_id: str, description: str = "") -> Template:
        print(f"[FaultManager] 创建模板: {name}, 项目: {project_id}")
        template = Template(name, project_id, description)
        self.templates[template.id] = template
        self.save_data()
        print(f"[FaultManager] 模板创建成功: {template.id}")
        return template

    def get_template(self, template_id: str) -> Optional[Template]:
        template = self.templates.get(template_id)
        print(f"[FaultManager] 获取模板: {template_id} -> {'成功' if template else '失败'}")
        return template

    def update_template(self, template: Template):
        if template.id in self.templates:
            print(f"[FaultManager] 更新模板: {template.name}")
            self.templates[template.id] = template
            self.save_data()
            print(f"[FaultManager] 模板更新成功: {template.id}")

    def delete_template(self, template_id: str):
        if template_id in self.templates:
            template_name = self.templates[template_id].name
            print(f"[FaultManager] 删除模板: {template_name} ({template_id})")
            del self.templates[template_id]
            # 同时删除关联的子模板引用
            for t in self.templates.values():
                if template_id in t.sub_templates:
                    t.remove_sub_template(template_id)
            self.save_data()
            print(f"[FaultManager] 模板删除成功: {template_id}")

    # 项目管理方法
    def create_project(self, name: str, description: str = "") -> Project:
        print(f"[FaultManager] 创建项目: {name}")
        project = Project(name, description)
        self.projects[project.id] = project
        self.save_data()
        print(f"[FaultManager] 项目创建成功: {project.id}")
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        project = self.projects.get(project_id)
        print(f"[FaultManager] 获取项目: {project_id} -> {'成功' if project else '失败'}")
        return project

    def update_project(self, project: Project):
        if project.id in self.projects:
            print(f"[FaultManager] 更新项目: {project.name}")
            self.projects[project.id] = project
            self.save_data()
            print(f"[FaultManager] 项目更新成功: {project.id}")

    def delete_project(self, project_id: str):
        if project_id in self.projects:
            project_name = self.projects[project_id].name
            item_count = len(self.projects[project_id].item_ids)
            print(f"[FaultManager] 删除项目: {project_name} ({project_id}), 包含 {item_count} 个条目")
            # 删除项目关联的条目
            for item_id in self.projects[project_id].item_ids:
                if item_id in self.items:
                    del self.items[item_id]
            del self.projects[project_id]
            self.save_data()
            print(f"[FaultManager] 项目删除成功: {project_id}")

    # 项目模板管理方法
    def get_project_templates(self, project_id: str) -> List[Template]:
        """获取项目的所有模板"""
        templates = []
        for template in self.templates.values():
            if template.project_id == project_id:
                templates.append(template)
        print(f"[FaultManager] 获取项目模板: 项目={project_id}, 模板数量={len(templates)}")
        return templates

    # 条目管理方法
    def create_item(self, template_id: str, project_id: str, title: str = "") -> Item:
        print(f"[FaultManager] 创建条目: {title}, 模板: {template_id}, 项目: {project_id}")
        item = Item(template_id, project_id, title)
        self.items[item.id] = item
        # 添加到项目中
        if project_id in self.projects:
            self.projects[project_id].add_item(item.id)
        self.save_data()
        print(f"[FaultManager] 条目创建成功: {item.id}")
        return item

    def get_item(self, item_id: str) -> Optional[Item]:
        item = self.items.get(item_id)
        print(f"[FaultManager] 获取条目: {item_id} -> {'成功' if item else '失败'}")
        return item

    def update_item(self, item: Item):
        if item.id in self.items:
            print(f"[FaultManager] 更新条目: {item.title}")
            self.items[item.id] = item
            self.save_data()
            print(f"[FaultManager] 条目更新成功: {item.id}")

    def delete_item(self, item_id: str):
        if item_id in self.items:
            item = self.items[item_id]
            print(f"[FaultManager] 删除条目: {item.title} ({item_id})")
            # 从项目中移除
            if item.project_id in self.projects:
                self.projects[item.project_id].remove_item(item_id)
            # 移除其他条目中的关联
            for other_item in self.items.values():
                other_item.remove_relationship(item_id)
            del self.items[item_id]
            self.save_data()
            print(f"[FaultManager] 条目删除成功: {item_id}")

    # 批量操作方法
    def export_items(self, item_ids: List[str]) -> List[Dict]:
        """导出多个条目"""
        print(f"[FaultManager] 导出条目: {len(item_ids)} 个条目")
        exported_items = [self.items[item_id].to_dict() for item_id in item_ids if item_id in self.items]
        print(f"[FaultManager] 导出成功: {len(exported_items)} 个条目")
        return exported_items

    def import_items(self, items_data: List[Dict], project_id: str) -> List[Item]:
        """导入多个条目"""
        print(f"[FaultManager] 导入条目: {len(items_data)} 个条目到项目 {project_id}")
        imported_items = []
        for item_data in items_data:
            # 创建新条目，使用新ID
            item = Item(
                template_id=item_data['template_id'],
                project_id=project_id,
                title=item_data.get('title', "")
            )
            item.field_values = item_data.get('field_values', {})
            item.relationships = item_data.get('relationships', [])
            self.items[item.id] = item
            if project_id in self.projects:
                self.projects[project_id].add_item(item.id)
            imported_items.append(item)
        self.save_data()
        print(f"[FaultManager] 导入成功: {len(imported_items)} 个条目")
        return imported_items