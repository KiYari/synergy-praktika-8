from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder

import sqlite3
import json
import os
from datetime import datetime
from abc import ABC, abstractmethod

KV = '''
<NoteItem>:
    orientation: "vertical"
    size_hint_y: None
    height: "120dp"
    padding: "15dp"
    spacing: "8dp"
    md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == "Light" else app.theme_cls.bg_light
    elevation: 1

    MDBoxLayout:
        orientation: "vertical"
        spacing: "5dp"
        adaptive_height: True

        MDLabel:
            text: root.note_title
            theme_text_color: "Primary"
            font_style: "H6"
            size_hint_y: None
            height: self.texture_size[1]
            shorten: True
            shorten_from: "right"
            bold: True

        MDLabel:
            text: root.note_content
            theme_text_color: "Secondary"
            font_style: "Body1"
            size_hint_y: None
            height: self.texture_size[1]
            shorten: True
            shorten_from: "right"

<MainScreen>:
    name: "main"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: toolbar
            title: "Мои Заметки"
            elevation: 10
            left_action_items: [["menu", lambda x: root.show_menu(x)]]
            right_action_items: [["magnify", lambda x: root.toggle_search()]]

        MDBoxLayout:
            id: search_box
            orientation: "horizontal"
            adaptive_height: True
            padding: "10dp"
            spacing: "10dp"
            height: 0
            opacity: 0

            MDTextField:
                id: search_field
                hint_text: "Поиск по заголовку и содержанию..."
                mode: "round"
                size_hint_x: 0.8
                on_text: root.search_notes(self.text)

            MDFlatButton:
                text: "X"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                on_release: root.clear_search()

        MDScrollView:
            MDList:
                id: notes_list

        MDFloatingActionButton:
            icon: "plus"
            elevation: 12
            md_bg_color: app.theme_cls.primary_color
            pos_hint: {"right": 0.95, "bottom": 0.05}
            on_release: root.add_note()

<NoteDialogContent>:
    orientation: "vertical"
    spacing: "15dp"
    padding: "20dp"
    adaptive_height: True

    MDTextField:
        id: title_field
        hint_text: "Заголовок заметки"
        mode: "rectangle"
        size_hint_y: None
        height: "60dp"

    MDTextField:
        id: content_field
        hint_text: "Содержание заметки"
        mode: "rectangle"
        multiline: True
        size_hint_y: None
        height: "200dp"
'''

Builder.load_string(KV)

class Storage(ABC):
    @abstractmethod
    def load_notes(self):
        pass

    @abstractmethod
    def save_note(self, note):
        pass

    @abstractmethod
    def delete_note(self, note_id):
        pass

    @abstractmethod
    def search_notes(self, query):
        pass

class SQLiteStorage(Storage):
    def __init__(self, db_path="notes.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS notes
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           title
                           TEXT
                           NOT
                           NULL,
                           content
                           TEXT
                           NOT
                           NULL,
                           date
                           TEXT
                           NOT
                           NULL,
                           time
                           TEXT
                           NOT
                           NULL
                       )
                       ''')
        conn.commit()
        conn.close()

    def load_notes(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY date DESC, time DESC")
        notes = [{
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'date': row[3],
            'time': row[4]
        } for row in cursor.fetchall()]
        conn.close()
        return notes

    def save_note(self, note):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if note.get('id'):
            cursor.execute('''
                           UPDATE notes
                           SET title=?,
                               content=?
                           WHERE id = ?
                           ''', (note['title'], note['content'], note['id']))
        else:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")

            cursor.execute('''
                           INSERT INTO notes (title, content, date, time)
                           VALUES (?, ?, ?, ?)
                           ''', (note['title'], note['content'], current_date, current_time))
            note['id'] = cursor.lastrowid

        conn.commit()
        conn.close()

    def delete_note(self, note_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
        conn.close()

    def search_notes(self, query):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT *
                       FROM notes
                       WHERE title LIKE ?
                          OR content LIKE ?
                       ORDER BY date DESC, time DESC
                       ''', (f'%{query}%', f'%{query}%'))
        notes = [{
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'date': row[3],
            'time': row[4]
        } for row in cursor.fetchall()]
        conn.close()
        return notes

class FileStorage(Storage):
    def __init__(self, file_path="notes.json"):
        self.file_path = file_path
        self.init_storage()

    def init_storage(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def load_notes(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_note(self, note):
        notes = self.load_notes()

        if note.get('id'):
            for i, n in enumerate(notes):
                if n['id'] == note['id']:
                    notes[i]['title'] = note['title']
                    notes[i]['content'] = note['content']
                    break
        else:
            now = datetime.now()
            note['id'] = max([n['id'] for n in notes], default=0) + 1
            note['date'] = now.strftime("%Y-%m-%d")
            note['time'] = now.strftime("%H:%M")
            notes.append(note)

        with open(self.file_path, 'w') as f:
            json.dump(notes, f, indent=2)

    def delete_note(self, note_id):
        notes = self.load_notes()
        notes = [n for n in notes if n['id'] != note_id]
        with open(self.file_path, 'w') as f:
            json.dump(notes, f, indent=2)

    def search_notes(self, query):
        notes = self.load_notes()
        return [n for n in notes if query.lower() in n['title'].lower() or
                query.lower() in n['content'].lower()]

class NoteItem(MDCard):
    note_title = StringProperty("")
    note_content = StringProperty("")
    note_date = StringProperty("")
    note_time = StringProperty("")
    note_id = NumericProperty(0)
    note_data = ObjectProperty(None)

class NoteDialogContent(MDBoxLayout):
    pass

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = SQLiteStorage()
        self.selected_note = None
        self.menu = None
        self.dialog = None
        Clock.schedule_once(self.init_ui)

    def init_ui(self, dt):
        self.load_notes()
        self.create_menu()
        self.ids.search_box.height = 0
        self.ids.search_box.opacity = 0

    def create_menu(self):
        menu_items = [
            {
                "text": "SQLite хранилище",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.switch_storage("sqlite"),
            },
            {
                "text": "Файловое хранилище",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.switch_storage("file"),
            },
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    def show_menu(self, button):
        self.menu.caller = button
        self.menu.open()

    def switch_storage(self, storage_type):
        if storage_type == "sqlite":
            self.storage = SQLiteStorage()
        else:
            self.storage = FileStorage()
        self.load_notes()
        self.menu.dismiss()
        self.show_toast(f"Используется {storage_type} хранилище")

    def toggle_search(self):
        search_box = self.ids.search_box
        if search_box.height == 0:
            search_box.height = 80
            search_box.opacity = 1
            self.ids.search_field.focus = True
        else:
            self.clear_search()

    def load_notes(self):
        notes_list = self.ids.notes_list
        notes_list.clear_widgets()

        notes = self.storage.load_notes()
        for note in notes:
            item = NoteItem(
                note_title=note['title'],
                note_content=note['content'][:150] + "..." if len(note['content']) > 150 else note['content'],
                note_date=note['date'],
                note_time=note['time'],
                note_id=note['id'],
                note_data=note
            )
            item.bind(
                on_touch_down=lambda instance, touch, note_data=note: self.on_note_tap(instance, touch, note_data))
            notes_list.add_widget(item)

    def on_note_tap(self, instance, touch, note_data):
        if instance.collide_point(*touch.pos) and touch.button == 'left':
            self.selected_note = note_data
            self.show_action_dialog()
            return True

    def show_action_dialog(self):
        if not self.selected_note:
            return

        app = MDApp.get_running_app()
        primary_color = app.theme_cls.primary_color

        action_dialog = MDDialog(
            title=f"Действия с заметкой: {self.selected_note['title'][:30]}...",
            buttons=[
                MDFlatButton(
                    text="Редактировать",
                    theme_text_color="Custom",
                    text_color=primary_color,
                    on_release=lambda x: self.edit_note_action(action_dialog)
                ),
                MDFlatButton(
                    text="Удалить",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.error_color,
                    on_release=lambda x: self.delete_note_action(action_dialog)
                ),
                MDFlatButton(
                    text="Отмена",
                    theme_text_color="Custom",
                    text_color=primary_color,
                    on_release=lambda x: action_dialog.dismiss()
                ),
            ],
        )
        action_dialog.open()

    def edit_note_action(self, dialog):
        dialog.dismiss()
        self.show_note_dialog()

    def delete_note_action(self, dialog):
        dialog.dismiss()
        self.delete_note()

    def add_note(self):
        self.selected_note = None
        self.show_note_dialog()

    def edit_note(self):
        if not self.selected_note:
            self.show_toast("Сначала выберите заметку")
            return
        self.show_note_dialog()

    def show_note_dialog(self):
        content = NoteDialogContent()

        if self.selected_note:
            content.ids.title_field.text = self.selected_note['title']
            content.ids.content_field.text = self.selected_note['content']
        else:
            content.ids.title_field.text = ""
            content.ids.content_field.text = ""

        app = MDApp.get_running_app()
        primary_color = app.theme_cls.primary_color

        self.dialog = MDDialog(
            title="Редактировать заметку" if self.selected_note else "Новая заметка",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    theme_text_color="Custom",
                    text_color=primary_color,
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="СОХРАНИТЬ",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    md_bg_color=primary_color,
                    on_release=lambda x: self.save_note(content)
                ),
            ],
        )
        self.dialog.open()

    def save_note(self, content):
        title = content.ids.title_field.text.strip()
        content_text = content.ids.content_field.text.strip()

        if not title:
            self.show_toast("Введите заголовок заметки")
            return

        if not content_text:
            self.show_toast("Введите содержание заметки")
            return

        note_data = {
            'title': title,
            'content': content_text
        }

        if self.selected_note:
            note_data['id'] = self.selected_note['id']

        try:
            self.storage.save_note(note_data)
            self.dialog.dismiss()
            self.load_notes()
            self.show_toast("Заметка сохранена")
        except Exception as e:
            self.show_toast(f"Ошибка сохранения: {str(e)}")

    def delete_note(self):
        if not self.selected_note:
            self.show_toast("Сначала выберите заметку")
            return

        app = MDApp.get_running_app()
        primary_color = app.theme_cls.primary_color
        error_color = app.theme_cls.error_color

        confirm_dialog = MDDialog(
            title="Подтверждение удаления",
            text=f"Удалить заметку '{self.selected_note['title']}'?",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    theme_text_color="Custom",
                    text_color=primary_color,
                    on_release=lambda x: confirm_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="УДАЛИТЬ",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    md_bg_color=error_color,
                    on_release=lambda x: self.confirm_delete(confirm_dialog)
                ),
            ],
        )
        confirm_dialog.open()

    def confirm_delete(self, dialog):
        try:
            self.storage.delete_note(self.selected_note['id'])
            dialog.dismiss()
            self.selected_note = None
            self.load_notes()
            self.show_toast("Заметка удалена")
        except Exception as e:
            self.show_toast(f"Ошибка удаления: {str(e)}")

    def search_notes(self, query):
        if not query.strip():
            self.load_notes()
            return

        notes_list = self.ids.notes_list
        notes_list.clear_widgets()

        notes = self.storage.search_notes(query)
        for note in notes:
            item = NoteItem(
                note_title=note['title'],
                note_content=note['content'][:150] + "..." if len(note['content']) > 150 else note['content'],
                note_date=note['date'],
                note_time=note['time'],
                note_id=note['id'],
                note_data=note
            )
            item.bind(
                on_touch_down=lambda instance, touch, note_data=note: self.on_note_tap(instance, touch, note_data))
            notes_list.add_widget(item)

    def clear_search(self):
        self.ids.search_field.text = ""
        self.load_notes()
        self.ids.search_box.height = 0
        self.ids.search_box.opacity = 0

    def show_toast(self, text):
        toast_dialog = MDDialog(
            title=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=lambda x: toast_dialog.dismiss()
                ),
            ],
        )
        toast_dialog.open()

class NotesApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Notes App"

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"

        return MainScreen()

if __name__ == "__main__":
    NotesApp().run()