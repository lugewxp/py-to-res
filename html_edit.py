# html_editor_direct.py
import sys
import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class WebElement:
    def __init__(self, tag="", content="", attributes=None, children=None):
        self.tag = tag
        self.content = content
        self.attributes = attributes or {}
        self.children = children or []
    
    def to_html(self, indent=0):
        indent_str = "  " * indent
        attrs = " ".join([f'{k}="{v}"' for k, v in self.attributes.items()])
        attr_str = f" {attrs}" if attrs else ""
        
        if self.tag == "text":
            return indent_str + self.content
        
        if self.children:
            children_html = "\n".join([child.to_html(indent + 1) for child in self.children])
            return f"{indent_str}<{self.tag}{attr_str}>\n{children_html}\n{indent_str}</{self.tag}>"
        elif self.content:
            return f"{indent_str}<{self.tag}{attr_str}>{self.content}</{self.tag}>"
        else:
            return f"{indent_str}<{self.tag}{attr_str} />"

class HTMLParser:
    def __init__(self):
        self.current_index = 0
        self.html = ""
    
    def parse(self, html_content):
        """解析HTML字符串为元素树"""
        self.html = html_content
        self.current_index = 0
        elements = []
        
        while self.current_index < len(self.html):
            # 跳过空白字符
            if self.html[self.current_index].isspace():
                self.current_index += 1
                continue
            
            # 检查是否是注释
            if self.html.startswith("<!--", self.current_index):
                end_index = self.html.find("-->", self.current_index)
                if end_index != -1:
                    self.current_index = end_index + 3
                continue
            
            # 检查是否是标签
            if self.html[self.current_index] == '<':
                element = self.parse_element()
                if element:
                    elements.append(element)
            else:
                # 文本节点
                text = self.parse_text()
                if text.strip():
                    text_element = WebElement("text", text.strip())
                    elements.append(text_element)
        
        return elements
    
    def parse_element(self):
        """解析单个HTML元素"""
        if self.current_index >= len(self.html) or self.html[self.current_index] != '<':
            return None
        
        # 检查是否是结束标签
        if self.html[self.current_index + 1] == '/':
            # 跳过结束标签
            end_bracket = self.html.find('>', self.current_index)
            if end_bracket != -1:
                self.current_index = end_bracket + 1
            return None
        
        # 解析开始标签
        self.current_index += 1  # 跳过 '<'
        
        # 获取标签名
        tag_end = self.current_index
        while tag_end < len(self.html) and not self.html[tag_end].isspace() and self.html[tag_end] != '>' and self.html[tag_end] != '/':
            tag_end += 1
        
        tag = self.html[self.current_index:tag_end]
        self.current_index = tag_end
        
        # 解析属性
        attributes = {}
        while self.current_index < len(self.html) and self.html[self.current_index] != '>' and self.html[self.current_index] != '/':
            # 跳过空白
            if self.html[self.current_index].isspace():
                self.current_index += 1
                continue
            
            # 解析属性名
            attr_start = self.current_index
            while (self.current_index < len(self.html) and 
                   not self.html[self.current_index].isspace() and 
                   self.html[self.current_index] != '=' and 
                   self.html[self.current_index] != '>' and 
                   self.html[self.current_index] != '/'):
                self.current_index += 1
            
            attr_name = self.html[attr_start:self.current_index]
            
            if self.current_index < len(self.html) and self.html[self.current_index] == '=':
                self.current_index += 1  # 跳过 '='
                
                # 跳过空白
                while self.current_index < len(self.html) and self.html[self.current_index].isspace():
                    self.current_index += 1
                
                # 解析属性值
                quote_char = self.html[self.current_index] if self.html[self.current_index] in ('"', "'") else None
                if quote_char:
                    self.current_index += 1  # 跳过引号
                    attr_start = self.current_index
                    while (self.current_index < len(self.html) and 
                           self.html[self.current_index] != quote_char):
                        self.current_index += 1
                    attr_value = self.html[attr_start:self.current_index]
                    self.current_index += 1  # 跳过结束引号
                else:
                    # 没有引号的属性值
                    attr_start = self.current_index
                    while (self.current_index < len(self.html) and 
                           not self.html[self.current_index].isspace() and 
                           self.html[self.current_index] != '>' and 
                           self.html[self.current_index] != '/'):
                        self.current_index += 1
                    attr_value = self.html[attr_start:self.current_index]
                
                attributes[attr_name] = attr_value
        
        # 检查是否是自闭合标签
        is_self_closing = False
        if self.current_index < len(self.html) and self.html[self.current_index] == '/':
            is_self_closing = True
            self.current_index += 1
        
        # 跳过 '>'
        if self.current_index < len(self.html) and self.html[self.current_index] == '>':
            self.current_index += 1
        
        element = WebElement(tag, "", attributes)
        
        # 如果不是自闭合标签，解析子元素
        if not is_self_closing and tag.lower() not in ["br", "hr", "img", "input", "meta", "link"]:
            # 解析内容直到遇到结束标签
            children = []
            
            while self.current_index < len(self.html):
                # 检查是否是结束标签
                if (self.current_index + 1 < len(self.html) and 
                    self.html[self.current_index] == '<' and 
                    self.html[self.current_index + 1] == '/'):
                    
                    # 检查是否是我们当前标签的结束标签
                    end_tag_start = self.current_index + 2
                    end_tag_end = self.html.find('>', end_tag_start)
                    if end_tag_end != -1:
                        end_tag = self.html[end_tag_start:end_tag_end].strip()
                        if end_tag.lower() == tag.lower():
                            self.current_index = end_tag_end + 1  # 跳过结束标签
                            break
                
                # 解析子元素
                if self.html[self.current_index] == '<':
                    child = self.parse_element()
                    if child:
                        children.append(child)
                else:
                    text = self.parse_text()
                    if text.strip():
                        text_element = WebElement("text", text.strip())
                        children.append(text_element)
            
            element.children = children
        
        return element
    
    def parse_text(self):
        """解析文本内容"""
        start_index = self.current_index
        while (self.current_index < len(self.html) and 
               self.html[self.current_index] != '<'):
            self.current_index += 1
        
        return self.html[start_index:self.current_index]

class ElementItem(QTreeWidgetItem):
    def __init__(self, element):
        super().__init__()
        self.element = element
        self.update_text()
    
    def update_text(self):
        if self.element.tag == "text":
            text = f"[文本]: {self.element.content[:50]}..."
            if len(self.element.content) > 50:
                text += "..."
        else:
            attrs = ", ".join([f"{k}: {v}" for k, v in self.element.attributes.items()])
            text = f"<{self.element.tag}>"
            if attrs:
                text += f" ({attrs})"
            if self.element.content:
                text += f": {self.element.content[:30]}..."
        self.setText(0, text)

class HTMLEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_element = None
        self.elements = []
        self.html_file = "html.txt"  # 要读取的文件名
        self.init_ui()
        self.load_html_file()  # 初始化时读取文件
    
    def init_ui(self):
        self.setWindowTitle("HTML文件编辑器")
        self.setGeometry(100, 100, 1200, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：元素树
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.element_tree = QTreeWidget()
        self.element_tree.setHeaderLabel("HTML元素结构")
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
        
        self.save_btn = QPushButton("保存到html.txt")
        self.save_btn.clicked.connect(self.save_html_file)
        bottom_layout.addWidget(self.save_btn)
        
        self.reload_btn = QPushButton("重新加载")
        self.reload_btn.clicked.connect(self.reload_html_file)
        bottom_layout.addWidget(self.reload_btn)
        
        self.export_btn = QPushButton("导出HTML")
        self.export_btn.clicked.connect(self.export_html)
        bottom_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.clicked.connect(self.clear_all)
        bottom_layout.addWidget(self.clear_btn)
        
        right_layout.addWidget(bottom_widget)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_default_html(self):
        """创建默认HTML内容"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>新建网页</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }
        h1 { color: #333; }
        p { line-height: 1.6; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>欢迎使用HTML编辑器</h1>
        <p>这是一个新建的HTML文件。</p>
        <p>您可以在此编辑HTML代码。</p>
        <p>示例链接: <a href="https://example.com">点击这里</a></p>
    </div>
</body>
</html>"""
    
    def load_html_file(self):
        """读取html.txt文件并解析HTML内容"""
        try:
            if os.path.exists(self.html_file):
                with open(self.html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.statusBar().showMessage(f"已从 {self.html_file} 加载HTML文件")
            else:
                # 文件不存在，创建默认HTML
                html_content = self.create_default_html()
                with open(self.html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.statusBar().showMessage(f"已创建 {self.html_file} 并加载默认HTML")
            
            # 解析HTML
            parser = HTMLParser()
            self.elements = parser.parse(html_content)
            
            # 刷新显示
            self.refresh_tree()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取/解析文件失败: {str(e)}")
            # 创建默认元素
            self.elements = []
            self.refresh_tree()
    
    def reload_html_file(self):
        """重新加载html.txt文件"""
        reply = QMessageBox.question(self, "确认", "重新加载会丢失未保存的更改，确定要继续吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.load_html_file()
    
    def save_html_file(self):
        """保存当前编辑的内容到html.txt"""
        try:
            html_content = self.generate_html()
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.statusBar().showMessage(f"已保存到 {self.html_file}")
            QMessageBox.information(self, "保存成功", f"文件已保存到 {self.html_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
    
    def generate_html(self):
        """从元素树生成完整的HTML"""
        html_parts = []
        
        for element in self.elements:
            html_parts.append(element.to_html())
        
        # 如果只有文本元素，包装在body中
        if all(e.tag == "text" for e in self.elements):
            body_content = "\n".join([e.to_html() for e in self.elements])
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>生成的网页</title>
</head>
<body>
{body_content}
</body>
</html>"""
        
        return "\n".join(html_parts)
    
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
        
        if self.current_element.tag == "text":
            # 文本节点
            self.tag_edit.setText("text")
            self.tag_edit.setEnabled(False)
            self.content_edit.setText(self.current_element.content)
            self.attr_table.setRowCount(0)
        else:
            # HTML元素节点
            self.tag_edit.setText(self.current_element.tag)
            self.tag_edit.setEnabled(True)
            self.content_edit.setText(self.current_element.content)
            
            # 更新属性表格
            self.attr_table.setRowCount(0)
            for key, value in self.current_element.attributes.items():
                row = self.attr_table.rowCount()
                self.attr_table.insertRow(row)
                self.attr_table.setItem(row, 0, QTableWidgetItem(key))
                self.attr_table.setItem(row, 1, QTableWidgetItem(str(value)))
    
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
        if not self.current_element or self.current_element.tag == "text":
            QMessageBox.warning(self, "警告", "请先选择一个HTML元素（文本节点不能添加属性）")
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
        if not self.current_element or self.current_element.tag == "text":
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
        
        if self.current_element.tag == "text":
            # 更新文本内容
            self.current_element.content = self.content_edit.toPlainText()
        else:
            # 更新HTML元素
            new_tag = self.tag_edit.text()
            if new_tag and new_tag != self.current_element.tag:
                self.current_element.tag = new_tag
            
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
        html = self.generate_html()
        self.html_preview.setText(html)
    
    def export_html(self):
        """导出为单独的HTML文件"""
        filename, _ = QFileDialog.getSaveFileName(self, "导出HTML", "", "HTML文件 (*.html)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.generate_html())
                self.statusBar().showMessage(f"HTML已导出到 {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
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
    editor = HTMLEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
