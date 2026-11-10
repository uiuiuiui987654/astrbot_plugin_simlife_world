"""Home decor overrides, book catalog and reading progress."""

import tempfile
import unittest
from pathlib import Path

from astrbot_plugin_simlife_world.core import books, goods, home_decor


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


BASE = [
    {"id": "sofa", "room": "客厅", "place": {"x": 0.5, "y": 0.5}},
    {"id": "bed", "room": "卧室"},
    {"id": "lamp", "room": "卧室"},
]


class HomeDecorTests(StoreTestCase):
    def test_place_clamps_and_validates(self):
        result = home_decor.place(self.data_dir, "p", "sofa", "书房", 1.4, "0.2", facing="West")
        self.assertEqual(result["place"], {"x": 0.95, "y": 0.2, "facing": "W"})
        self.assertFalse(home_decor.place(self.data_dir, "p", "", "书房", 0, 0)["ok"])
        self.assertFalse(home_decor.place(self.data_dir, "p", "sofa", "书房", "左边", 0)["ok"])

    def test_apply_moves_and_hides(self):
        home_decor.place(self.data_dir, "p", "sofa", "书房", 0.3, 0.4)
        home_decor.store(self.data_dir, "p", "bed")
        items = home_decor.apply_items(BASE, self.data_dir, "p")
        self.assertEqual([item["id"] for item in items], ["sofa", "lamp"])
        self.assertEqual((items[0]["room"], items[0]["custom_place"]), ("书房", True))
        self.assertEqual(BASE[0]["room"], "客厅", "input must not be mutated")
        self.assertEqual(home_decor.apply_items(BASE, self.data_dir, ""), BASE)

        described = {item["id"]: item for item in home_decor.describe(BASE, self.data_dir, "p")}
        self.assertTrue(described["bed"]["stored"])
        self.assertEqual(described["sofa"]["override_room"], "书房")
        self.assertFalse(described["lamp"]["custom_place"])

    def test_reset_one_or_all(self):
        home_decor.place(self.data_dir, "p", "sofa", "书房", 0.3, 0.4)
        home_decor.store(self.data_dir, "p", "bed")
        home_decor.reset(self.data_dir, "p", "bed")
        self.assertEqual(set(home_decor.overrides(self.data_dir, "p")), {"sofa"})
        home_decor.reset(self.data_dir, "p")
        self.assertEqual(home_decor.overrides(self.data_dir, "p"), {})

    def test_overrides_are_per_persona(self):
        home_decor.store(self.data_dir, "a", "bed")
        self.assertEqual(len(home_decor.apply_items(BASE, self.data_dir, "b")), 3)


class BookCatalogTests(unittest.TestCase):
    def test_catalog_books_are_readable(self):
        catalog = books.load_books()
        self.assertTrue(catalog)
        for book in catalog:
            with self.subTest(book=book.get("id")):
                self.assertTrue(book.get("id") and book.get("title"))
                text = books.render_book(book, 999)
                self.assertIn(f"《{book['title']}》", text)

    def test_every_book_in_goods_catalog_exists(self):
        book_ids = {book["id"] for book in books.load_books()}
        for item in goods.load_goods():
            if item.get("book_id"):
                self.assertIn(item["book_id"], book_ids, item["id"])

    def test_find_book(self):
        first = books.load_books()[0]
        self.assertEqual(books.find_book(first["title"])["id"], first["id"])
        self.assertIsNone(books.find_book(""))

    def test_txt_chapter_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "books_txt").mkdir()
            (root / "catalog.json").write_text('{"books": [{"id": "b1", "title": "测试书"}, {"id": "b2"}]}', encoding="utf-8")
            (root / "books_txt" / "b1.txt").write_text(
                "封面信息\n正文\n第一章 开始\n第一段\n\n\n\n第二段\n第二章 结束\n终章内容\n", encoding="utf-8"
            )
            loaded = books.load_books(root / "catalog.json")
        chapters = loaded[0]["chapters"]
        self.assertEqual([chapter["title"] for chapter in chapters], ["第一章 开始", "第二章 结束"])
        self.assertEqual(chapters[0]["content"], "第一段\n\n第二段")
        self.assertNotIn("chapters", loaded[1])


class ReadingProgressTests(StoreTestCase):
    def test_progress_only_moves_forward(self):
        self.assertEqual(books.get_progress(self.data_dir, "p", "b"), {"chapter": 0, "finished": False, "notes": []})
        books.record_reading(self.data_dir, "p", "b", 3, 5)
        self.assertEqual(books.record_reading(self.data_dir, "p", "b", 1, 5), {"chapter": 3, "finished": False})
        self.assertTrue(books.record_reading(self.data_dir, "p", "b", 5, 5)["finished"])

    def test_notes(self):
        self.assertFalse(books.add_note(self.data_dir, "p", "b", "  ")["ok"])
        for index in range(32):
            books.add_note(self.data_dir, "p", "b", f"笔记{index}", chapter=-3)
        notes = books.get_progress(self.data_dir, "p", "b")["notes"]
        self.assertEqual((len(notes), notes[0]["text"], notes[0]["chapter"]), (30, "笔记2", 0))
        self.assertEqual(len(books.delete_note(self.data_dir, "p", "b", 0)["notes"]), 29)
        self.assertFalse(books.delete_note(self.data_dir, "p", "b", 99)["ok"])

    def test_reading_context(self):
        self.assertEqual(books.reading_context("做饭", []), "")
        book = books.load_books()[0]
        books.record_reading(self.data_dir, "p", book["id"], 1, 99)
        books.add_note(self.data_dir, "p", book["id"], "主角好可怜")
        text = books.reading_context("窝在沙发看书", [{"book_id": book["id"]}], data_dir=self.data_dir, persona="p")
        self.assertIn(f"《{book['title']}》", text)
        self.assertIn("已读到第 1 章", text)
        self.assertIn("主角好可怜", text)


if __name__ == "__main__":
    unittest.main()
