from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineListItem

KV = '''
<NoteItem>:
    size_hint_y: None
    height: "72dp"
    padding: "16dp"
    radius: "12dp"
    elevation: 1

    OneLineListItem:
        text: root.text
        _no_ripple: True

ScreenManager:
    MainScreen:
        name: "main"

<MainScreen>:
    MDFloatLayout:
        MDBoxLayout:
            orientation: "vertical"
            MDTopAppBar:
                title: "Мои Заметки"
                elevation: 4
                pos_hint: {"top": 1}

            Widget:

        MDFloatingActionButton:
            icon: "plus"
            pos_hint: {"right": 0.95, "bottom": 0.05}
            on_release: root.add_note()
'''

class NoteItem(MDCard):
    text = ""

class MainScreen(MDScreen):
    notes = ListProperty()

    def on_enter(self):
        self.update_notes()

    def update_notes(self):
        notes_list = self.ids.notes_list
        notes_list.clear_widgets()
        for note in self.notes:
            item = NoteItem()
            item.text = note
            notes_list.add_widget(item)

    def add_note(self):
        from datetime import datetime
        new_note = f"Заметка {datetime.now().strftime('%H:%M:%S')}"
        self.notes.append(new_note)
        self.update_notes()

class NotesApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        return Builder.load_string(KV)

if __name__ == "__main__":
    NotesApp().run()