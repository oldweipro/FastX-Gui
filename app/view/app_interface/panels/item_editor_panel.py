"""Item editor panel — dynamic form for editing an item's field values."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    SpinBox,
    StrongBodyLabel,
    TextEdit,
)

from app.common.signal_bus import signalBus
from app.service import item_service, template_service


class _MultiSelectWidget(QWidget):
    """A vertical list of check-boxes for multi-select fields.

    Each check-box carries a *label* (displayed) and a *value* (stored).
    Values are persisted as a comma-separated string.
    """

    def __init__(self, options: list[tuple[str, str]], parent=None):
        """*options* is a list of ``(label, value)`` tuples."""
        super().__init__(parent)
        self._checkboxes: list[tuple[CheckBox, str]] = []

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(4)
        for label, value in options:
            cb = CheckBox(label, inner)
            inner_layout.addWidget(cb)
            self._checkboxes.append((cb, value))
        inner_layout.addStretch()
        scroll.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def get_value(self) -> str:
        """Return comma-separated string of checked values."""
        return ",".join(val for cb, val in self._checkboxes if cb.isChecked())

    def set_value(self, csv: str):
        """Check boxes whose value appears in *csv* (comma-separated)."""
        selected = {v.strip() for v in csv.split(",") if v.strip()} if csv else set()
        for cb, val in self._checkboxes:
            cb.setChecked(val in selected)


class ItemEditorPanel(QWidget):
    """Dynamic form editor for a single item, rendered from its template fields."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._item_id = ""
        self._project_id = ""
        self._field_widgets: dict[str, QWidget] = {}  # field_name -> widget
        self._field_defs: list[dict] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.title_label = StrongBodyLabel("Edit Item", self)
        layout.addWidget(self.title_label)

        self.item_title_edit = LineEdit(self)
        self.item_title_edit.setPlaceholderText("Item title")
        title_row = QVBoxLayout()
        title_row.addWidget(BodyLabel("Title:", self))
        title_row.addWidget(self.item_title_edit)
        layout.addLayout(title_row)

        # Scrollable form area
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(8)
        self.scroll.setWidget(self.form_widget)
        layout.addWidget(self.scroll, 1)

    def load_item(self, item_id: str, project_id: str):
        self._item_id = item_id
        self._project_id = project_id
        self._field_widgets.clear()

        item = item_service.get_item(item_id)
        if item is None:
            return

        self.item_title_edit.setText(item.get("title", ""))

        # Get template fields
        tmpl = template_service.get_template(item["template_id"])
        self._field_defs = tmpl.get("fields", []) if tmpl else []

        field_values = item.get("field_values", {})

        # Rebuild form
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for fd in self._field_defs:
            widget = self._create_field_widget(fd, field_values.get(fd["name"]))
            self._field_widgets[fd["name"]] = widget
            label = f"{'* ' if fd.get('required') else ''}{fd.get('label') or fd['name']}"
            self.form_layout.addRow(label, widget)

        self.title_label.setText(f"Edit Item: {item.get('title', '')}")

    def _create_field_widget(self, field_def: dict, value) -> QWidget:
        ft = field_def.get("field_type", "text")
        multi = field_def.get("multi_select", False)

        if ft == "text":
            w = LineEdit(self)
            w.setText(str(value) if value else "")
            return w
        elif ft == "number":
            w = SpinBox(self)
            w.setRange(-999999, 999999)
            w.setValue(int(value) if value else 0)
            return w
        elif ft == "checkbox":
            w = CheckBox(self)
            w.setChecked(bool(value))
            return w
        elif ft == "select":
            options = field_def.get("options", [])
            if multi and options:
                pairs = [(opt, opt) for opt in options]
                w = _MultiSelectWidget(pairs, self)
                w.set_value(str(value) if value else "")
                return w
            w = ComboBox(self)
            w.addItems(options)
            if value and value in options:
                w.setCurrentText(str(value))
            return w
        elif ft == "textarea":
            w = TextEdit(self)
            w.setPlainText(str(value) if value else "")
            w.setMaximumHeight(120)
            return w
        elif ft == "date":
            w = LineEdit(self)
            w.setPlaceholderText("YYYY-MM-DD")
            w.setText(str(value) if value else "")
            return w
        elif ft == "template_item":
            ref_id = field_def.get("ref_tmpl_id")
            ref_items = []
            if ref_id:
                ref_items = item_service.list_items(self._project_id, template_id=ref_id)
            if multi and ref_items:
                pairs = [(ri["title"], ri["id"]) for ri in ref_items]
                w = _MultiSelectWidget(pairs, self)
                w.set_value(str(value) if value else "")
                return w
            w = ComboBox(self)
            for ri in ref_items:
                w.addItem(ri["title"], userData=ri["id"])
            if value:
                idx = w.findData(value)
                if idx >= 0:
                    w.setCurrentIndex(idx)
            return w
        else:
            w = LineEdit(self)
            w.setText(str(value) if value else "")
            return w

    def _collect_field_values(self) -> dict:
        values = {}
        for fd in self._field_defs:
            name = fd["name"]
            widget = self._field_widgets.get(name)
            if widget is None:
                continue
            if isinstance(widget, _MultiSelectWidget):
                values[name] = widget.get_value()
            elif isinstance(widget, CheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, SpinBox):
                values[name] = widget.value()
            elif isinstance(widget, TextEdit):
                values[name] = widget.toPlainText()
            elif isinstance(widget, ComboBox):
                ft = fd.get("field_type", "text")
                if ft == "template_item":
                    values[name] = widget.currentData() or ""
                else:
                    values[name] = widget.currentText()
            elif isinstance(widget, LineEdit):
                values[name] = widget.text()
            else:
                values[name] = ""
        return values

    def on_save(self):
        title = self.item_title_edit.text().strip()
        if not title:
            InfoBar.warning("Warning", "Item title cannot be empty", parent=self, position=InfoBarPosition.TOP)
            return
        field_values = self._collect_field_values()
        try:
            item_service.update_item(self._item_id, title=title, field_values=field_values)
            signalBus.dataChanged.emit()
            InfoBar.success("Saved", "Item updated", parent=self, position=InfoBarPosition.TOP)
        except Exception as e:
            InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
