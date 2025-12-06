# web_element_editor_pyqt5.py
import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class WebElement:
    def __init__(self, tag, content="", attributes=None, children=None):
        self.tag = tag
        self.content = content
        self.attributes = attributes or {}
        self.children = children or []
    
    def to_dict(self):
        return {
            "tag": self.tag,
            "content": self.content,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children]
        }
    
    @staticmethod
    def from_dict(data):
        element = WebElement(
            data["tag"],
            data.get("content", ""),
            data.get("attributes", {})
        )
        element.children = [WebElement.from_dict(child) for child in data.get("children", [])]
        return element
    
    def to_html(self, indent=0):
        indent_str = "  " * indent
        attrs = " ".join([f'{k}="{v}"' for k, v in self.attributes.items()])
        attr_str = f" {attrs}" if attrs else ""
        
        if self.children:
            children_html = "\n".join([child.to_html(indent + 1) for child in self.children])
            return f"{indent_str}<{self.tag}{attr_str}>\n{children_html}\n{indent_str}</{self.tag}>"
        elif self.content:
            return f"{indent_str}<{self.tag}{attr_str}>{self.content}</{self.tag}>"
        else:
            return f"{indent_str}<{self.tag}{attr_str} />"

class ElementItem(QTreeWidgetItem):
    def __init__(self, element):
        super().__init__()
        self.element = element
        self.update_text()
    
    def update_text(self):
        attrs = ", ".join([f"{k}: {v}" for k, v in self.element.attributes.items()])
        text = f"<{self.element.tag}>"
        if attrs:
            text += f" ({attrs})"
        if self.element.content:
            text += f": {self.element.content[:30]}..."
        self.setText(0, text)

class WebElementEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_element = None
        self.elements = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("网页元素编辑器 - PyQt5")
        self.setGeometry(100, 100, 1200, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：元素树
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.element_tree = QTreeWidget()
        self.element_tree.setHeaderLabel("网页元素结构")
        self.element_tree.itemClicked.connect(self.on_element_selected)
        left_layout.addWidget(self.element_tree)
        
        # 元素树按钮
        tree_buttons = QWidget()
        tree_buttons_layout = QHBoxLayout(tree_buttons)
        
        self.add_element_btn = QPushButton("添加元素")
        self.add_element_btn.clicked.connect(self.add_element)
        tree_buttons_layout.addWidget(self.add_element_btn)
        
        self.delete_element_btn = QPushButton("删除元素")
        self.delete_element_btn.clicked.connect(self.delete_element)
        tree_buttons_layout.addWidget(self.delete_element_btn)
        
        left_layout.addWidget(tree_buttons)
        main_layout.addWidget(left_panel, 1)
        
        # 右侧：编辑面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 元素属性编辑
        self.attr_widget = QWidget()
        attr_layout = QFormLayout(self.attr_widget)
        
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("例如: div, p, h1, span")
        attr_layout.addRow("标签名:", self.tag_edit)
        
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(100)
        attr_layout.addRow("内容:", self.content_edit)
        
        right_layout.addWidget(QLabel("元素属性"))
        right_layout.addWidget(self.attr_widget)
        
        # 属性表格
        right_layout.addWidget(QLabel("HTML属性"))
        self.attr_table = QTableWidget(0, 2)
        self.attr_table.setHorizontalHeaderLabels(["属性名", "属性值"])
        self.attr_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.attr_table)
        
        # 属性按钮
        attr_buttons = QWidget()
        attr_buttons_layout = QHBoxLayout(attr_buttons)
        
        self.add_attr_btn = QPushButton("添加属性")
        self.add_attr_btn.clicked.connect(self.add_attribute)
        attr_buttons_layout.addWidget(self.add_attr_btn)
        
        self.remove_attr_btn = QPushButton("删除属性")
        self.remove_attr_btn.clicked.connect(self.remove_attribute)
        attr_buttons_layout.addWidget(self.remove_attr_btn)
        
        right_layout.addWidget(attr_buttons)
        
        # 更新按钮
        self.update_btn = QPushButton("更新元素")
        self.update_btn.clicked.connect(self.update_element)
        right_layout.addWidget(self.update_btn)
        
        # HTML预览
        right_layout.addWidget(QLabel("HTML预览"))
        self.html_preview = QTextEdit()
        self.html_preview.setReadOnly(True)
        self.html_preview.setFont(QFont("Courier", 10))
        right_layout.addWidget(self.html_preview, 2)
        
        main_layout.addWidget(right_panel, 2)
        
        # 底部：操作按钮
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        self.export_html_btn = QPushButton("导出HTML")
        self.export_html_btn.clicked.connect(self.export_html)
        bottom_layout.addWidget(self.export_html_btn)
        
        self.import_json_btn = QPushButton("导入JSON")
        self.import_json_btn.clicked.connect(self.import_json)
        bottom_layout.addWidget(self.import_json_btn)
        
        self.export_json_btn = QPushButton("导出JSON")
        self.export_json_btn.clicked.connect(self.export_json)
        bottom_layout.addWidget(self.export_json_btn)
        
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.clicked.connect(self.clear_all)
        bottom_layout.addWidget(self.clear_btn)
        
        right_layout.addWidget(bottom_widget)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 添加示例数据
        self.add_example_elements()
    
    def add_example_elements(self):
        """添加示例元素"""
        root = WebElement("div", attributes={"class": "container"})
        header = WebElement("h1", "欢迎使用网页编辑器")
        paragraph = WebElement("p", "这是一个示例段落。")
        link = WebElement("a", "点击这里", {"href": "https://example.com", "class": "link"})
        
        root.children = [header, paragraph, link]
        self.elements.append(root)
        self.refresh_tree()
    
    def refresh_tree(self):
        """刷新元素树"""
        self.element_tree.clear()
        for element in self.elements:
            item = ElementItem(element)
            self.element_tree.addTopLevelItem(item)
            self.add_children_to_tree(item, element.children)
        self.element_tree.expandAll()
        self.update_html_preview()
    
    def add_children_to_tree(self, parent_item, children):
        """添加子元素到树中"""
        for child in children:
            child_item = ElementItem(child)
            parent_item.addChild(child_item)
            self.add_children_to_tree(child_item, child.children)
    
    def on_element_selected(self, item):
        """元素被选中"""
        self.current_element = item.element
        self.tag_edit.setText(self.current_element.tag)
        self.content_edit.setText(self.current_element.content)
        
        # 更新属性表格
        self.attr_table.setRowCount(0)
        for key, value in self.current_element.attributes.items():
            row = self.attr_table.rowCount()
            self.attr_table.insertRow(row)
            self.attr_table.setItem(row, 0, QTableWidgetItem(key))
            self.attr_table.setItem(row, 1, QTableWidgetItem(value))
    
    def add_element(self):
        """添加新元素"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加新元素")
        layout = QFormLayout(dialog)
        
        tag_edit = QLineEdit()
        tag_edit.setPlaceholderText("div")
        layout.addRow("标签名:", tag_edit)
        
        content_edit = QLineEdit()
        layout.addRow("内容:", content_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            tag = tag_edit.text() or "div"
            element = WebElement(tag, content_edit.text())
            
            selected_items = self.element_tree.selectedItems()
            if selected_items:
                parent_item = selected_items[0]
                parent_element = parent_item.element
                parent_element.children.append(element)
                child_item = ElementItem(element)
                parent_item.addChild(child_item)
            else:
                self.elements.append(element)
                item = ElementItem(element)
                self.element_tree.addTopLevelItem(item)
            
            self.statusBar().showMessage(f"已添加 <{tag}> 元素")
            self.update_html_preview()
    
    def delete_element(self):
        """删除选中元素"""
        selected_items = self.element_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个元素")
            return
        
        item = selected_items[0]
        parent = item.parent()
        
        if parent:
            parent_element = parent.element
            parent_element.children.remove(item.element)
            parent.removeChild(item)
        else:
            self.elements.remove(item.element)
            self.element_tree.takeTopLevelItem(self.element_tree.indexOfTopLevelItem(item))
        
        self.statusBar().showMessage("元素已删除")
        self.update_html_preview()
    
    def add_attribute(self):
        """添加属性"""
        if not self.current_element:
            QMessageBox.warning(self, "警告", "请先选择一个元素")
            return
        
        key, ok1 = QInputDialog.getText(self, "添加属性", "属性名:")
        if not ok1 or not key:
            return
        
        value, ok2 = QInputDialog.getText(self, "添加属性", "属性值:")
        if not ok2:
            return
        
        self.current_element.attributes[key] = value
        self.refresh_tree()
        self.statusBar().showMessage(f"已添加属性 {key}=\"{value}\"")
    
    def remove_attribute(self):
        """删除属性"""
        if not self.current_element:
            return
        
        selected = self.attr_table.selectedItems()
        if selected:
            key = selected[0].text()
            if key in self.current_element.attributes:
                del self.current_element.attributes[key]
                self.refresh_tree()
                self.statusBar().showMessage(f"已删除属性 {key}")
    
    def update_element(self):
        """更新当前元素"""
        if not self.current_element:
            return
        
        self.current_element.tag = self.tag_edit.text()
        self.current_element.content = self.content_edit.toPlainText()
        
        # 更新属性
        self.current_element.attributes = {}
        for row in range(self.attr_table.rowCount()):
            key_item = self.attr_table.item(row, 0)
            value_item = self.attr_table.item(row, 1)
            if key_item and value_item:
                self.current_element.attributes[key_item.text()] = value_item.text()
        
        self.refresh_tree()
        self.statusBar().showMessage("元素已更新")
    
    def update_html_preview(self):
        """更新HTML预览"""
        html = "<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"UTF-8\">\n  <title>生成的网页</title>\n</head>\n<body>\n"
        for element in self.elements:
            html += element.to_html(1) + "\n"
        html += "</body>\n</html>"
        self.html_preview.setText(html)
    
    def export_html(self):
        """导出HTML文件"""
        filename, _ = QFileDialog.getSaveFileName(self, "导出HTML", "", "HTML文件 (*.html)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.html_preview.toPlainText())
            self.statusBar().showMessage(f"HTML已导出到 {filename}")
    
    def import_json(self):
        """导入JSON文件"""
        filename, _ = QFileDialog.getOpenFileName(self, "导入JSON", "", "JSON文件 (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.elements = [WebElement.from_dict(item) for item in data]
                self.refresh_tree()
                self.statusBar().showMessage(f"已从 {filename} 导入")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def export_json(self):
        """导出JSON文件"""
        filename, _ = QFileDialog.getSaveFileName(self, "导出JSON", "", "JSON文件 (*.json)")
        if filename:
            data = [element.to_dict() for element in self.elements]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f"JSON已导出到 {filename}")
    
    def clear_all(self):
        """清空所有元素"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有元素吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.elements.clear()
            self.refresh_tree()
            self.statusBar().showMessage("已清空所有元素")

def main():
    app = QApplication(sys.argv)
    editor = WebElementEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
