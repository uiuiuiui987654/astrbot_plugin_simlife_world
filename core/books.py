from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

CORE_DIR = Path(__file__).resolve().parent
BOOKS_PATH = CORE_DIR / "books_catalog.json"
BOOKS_TXT_DIR = CORE_DIR / "books_txt"
CHAPTER_HEADING = re.compile(
    r"^第[一二三四五六七八九十百零〇两0-9]+章[\s　].*$"
)
STATE_LOCK = threading.RLock()


def _state_path(data_dir: Path) -> Path:
    return Path(data_dir) / "books_state.json"


def _load_state(data_dir: Path) -> dict[str, Any]:
    path = _state_path(data_dir)
    if not path.exists():
        return {"schema_version": 1, "personas": {}}
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "personas": {}}
    if not isinstance(content, dict):
        return {"schema_version": 1, "personas": {}}
    content.setdefault("personas", {})
    return content


def _save_state(data_dir: Path, content: dict[str, Any]) -> None:
    path = _state_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _persona_state(content: dict[str, Any], persona: str) -> dict[str, Any]:
    personas = content.setdefault("personas", {})
    state = personas.setdefault(str(persona), {"books": {}})
    state.setdefault("books", {})
    return state


def get_progress(data_dir: Path, persona: str, book_id: str) -> dict[str, Any]:
    with STATE_LOCK:
        state = _persona_state(_load_state(data_dir), persona)
        entry = state["books"].get(str(book_id))
        if not isinstance(entry, dict):
            return {
                "chapter": 0,
                "finished": False,
                "notes": [],
            }
        return {
            "chapter": int(entry.get("chapter") or 0),
            "finished": bool(entry.get("finished")),
            "notes": list(entry.get("notes") or []),
        }


def record_reading(
    data_dir: Path,
    persona: str,
    book_id: str,
    chapter: int,
    total: int,
) -> dict[str, Any]:
    with STATE_LOCK:
        content = _load_state(data_dir)
        state = _persona_state(content, persona)
        entry = state["books"].setdefault(str(book_id), {})
        current = int(entry.get("chapter") or 0)
        entry["chapter"] = max(current, int(chapter or 0))
        entry["finished"] = bool(
            int(entry.get("chapter") or 0) >= max(1, int(total or 1))
        )
        entry["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _save_state(data_dir, content)
        return {
            "chapter": entry["chapter"],
            "finished": entry["finished"],
        }


def add_note(
    data_dir: Path,
    persona: str,
    book_id: str,
    text: str,
    *,
    chapter: int | None = None,
) -> dict[str, Any]:
    note = str(text or "").strip()[:300]
    if not note:
        return {"ok": False, "error": "笔记不能为空"}
    with STATE_LOCK:
        content = _load_state(data_dir)
        state = _persona_state(content, persona)
        entry = state["books"].setdefault(str(book_id), {})
        notes = entry.get("notes") or []
        notes.append(
            {
                "text": note,
                "at": datetime.now().isoformat(timespec="seconds"),
                "chapter": max(0, int(chapter or 0)),
            }
        )
        entry["notes"] = notes[-30:]
        _save_state(data_dir, content)
        return {"ok": True, "notes": entry["notes"]}


def delete_note(
    data_dir: Path,
    persona: str,
    book_id: str,
    index: int,
) -> dict[str, Any]:
    with STATE_LOCK:
        content = _load_state(data_dir)
        state = _persona_state(content, persona)
        entry = state["books"].get(str(book_id)) or {}
        notes = list(entry.get("notes") or [])
        if index < 0 or index >= len(notes):
            return {"ok": False, "error": "没有这条笔记"}
        notes.pop(index)
        entry["notes"] = notes
        state["books"][str(book_id)] = entry
        _save_state(data_dir, content)
        return {"ok": True, "notes": notes}


def _parse_txt_chapters(path: Path) -> list[dict[str, str]]:
    """Read one plain-text book and split it by chapter headings."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    chapters: list[dict[str, str]] = []
    current: dict[str, Any] | None = None
    in_body = False
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if stripped == "正文":
            in_body = True
            continue
        if not in_body:
            continue
        if CHAPTER_HEADING.match(stripped):
            if current is not None:
                content = "\n".join(current.pop("_lines")).strip()
                content = re.sub(r"\n{3,}", "\n\n", content)
                if content:
                    current["content"] = content
                    chapters.append(current)
            current = {"title": stripped, "_lines": []}
        elif current is not None:
            current["_lines"].append(line)
    if current is not None:
        content = "\n".join(current.pop("_lines")).strip()
        content = re.sub(r"\n{3,}", "\n\n", content)
        if content:
            current["content"] = content
            chapters.append(current)
    return chapters


def _apply_text_books(
    books: list[dict[str, Any]], txt_dir: Path
) -> list[dict[str, Any]]:
    for book in books:
        book_id = str(book.get("id") or "").strip()
        if not book_id:
            continue
        path = txt_dir / f"{book_id}.txt"
        if not path.is_file():
            continue
        chapters = _parse_txt_chapters(path)
        if chapters:
            book["chapters"] = chapters
            book["text_file"] = f"books_txt/{book_id}.txt"
    return books


def load_books(path: Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else BOOKS_PATH
    try:
        content = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    books = content.get("books") if isinstance(content, dict) else content
    if not isinstance(books, list):
        return []
    valid = [book for book in books if isinstance(book, dict)]
    return _apply_text_books(valid, target.parent / "books_txt")


def list_books(genre: str = "") -> list[dict[str, Any]]:
    books = load_books()
    genre = str(genre or "").strip()
    if genre:
        books = [
            book for book in books if genre in str(book.get("genre") or "")
        ]
    return books


def find_book(query: str) -> dict[str, Any] | None:
    text = str(query or "").strip().casefold()
    if not text:
        return None
    books = load_books()
    for book in books:
        if text in (
            str(book.get("id") or "").casefold(),
            str(book.get("title") or "").casefold(),
        ):
            return book
    for book in books:
        fields = " ".join(
            str(book.get(key) or "")
            for key in ("title", "author", "genre", "summary")
        ).casefold()
        if text in fields:
            return book
    return None


def render_book(book: dict[str, Any], chapter: int = 1) -> str:
    chapters = book.get("chapters") or []
    if not isinstance(chapters, list) or not chapters:
        return (
            f"《{book.get('title')}》\n"
            f"作者：{book.get('author')}\n"
            f"简介：{book.get('summary')}"
        )
    index = max(1, min(int(chapter or 1), len(chapters))) - 1
    item = chapters[index]
    return (
        f"《{book.get('title')}》\n"
        f"作者：{book.get('author')} · {book.get('genre')}\n"
        f"简介：{book.get('summary')}\n\n"
        f"{item.get('title')}\n{item.get('content')}"
    )


def teaser(book: dict[str, Any]) -> str:
    chapters = book.get("chapters") or []
    first = chapters[0] if chapters else {}
    return (
        f"《{book.get('title')}》（{book.get('genre')}）"
        f"{book.get('price', '')} 元\n"
        f"  {book.get('summary')}\n"
        f"  试读：{str(first.get('content') or '')[:90]}…"
    )


def reading_context(
    activity: str,
    possessions: list[dict[str, Any]],
    *,
    data_dir: Path | None = None,
    persona: str = "",
) -> str:
    text = str(activity or "")
    if not any(word in text for word in ("看", "读", "翻", "书")):
        return ""
    owned = [
        book
        for item in possessions or []
        for book in [find_book(str(item.get("book_id") or item.get("name") or ""))]
        if book is not None
    ]
    book = owned[0] if owned else (load_books() or [None])[0]
    if not book:
        return ""
    chapters = book.get("chapters") or []
    total = len(chapters)
    progress = (
        get_progress(data_dir, persona, str(book.get("id") or ""))
        if data_dir is not None and persona
        else {"chapter": 0, "finished": False, "notes": []}
    )
    if progress.get("finished"):
        index = max(0, total - 1)
    else:
        index = min(max(0, int(progress.get("chapter") or 0)), max(0, total - 1))
    chapter = chapters[index] if chapters else {}
    content = str(chapter.get("content") or "")[:220]
    prefix = (
        f"【你正在看的书】《{book.get('title')}》· {book.get('genre')}。"
        f"当前是「{chapter.get('title') or '开头'}」"
    )
    if progress.get("finished"):
        prefix += "（这本已经读完了，可以想起里面的内容）"
    elif progress.get("chapter"):
        prefix += f"（已读到第 {progress['chapter']} 章）"
    notes = progress.get("notes") or []
    note_text = (
        f" 你之前写的笔记：{notes[-1].get('text')}" if notes else ""
    )
    return f"{prefix}：{content}{note_text}"
