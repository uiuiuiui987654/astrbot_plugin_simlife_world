"""Weekly report, diary, books and affection."""

from __future__ import annotations

from datetime import timedelta


from .. import (
    affection,
    books,
    diary,
    view_state,
    weekly,
)

from .context import RouteContext


class JournalRoutes:
    """Mixin for LifeViewAPI; expects ``self.plugin`` and ``self.plans_path``."""

    def _get_weekly(self, ctx: RouteContext) -> dict:
        """GET weekly"""
        now = ctx.now
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        try:
            days = int(params.get("days") or 7)
        except (TypeError, ValueError):
            days = 7
        days = 365 if days >= 300 else 30 if days >= 28 else 7
        return {
            "ok": True,
            "report": weekly.build(
                self.plans_path.parent,
                target_persona,
                now=now,
                days=days,
            ),
            "previous": weekly.build(
                self.plans_path.parent,
                target_persona,
                now=now - timedelta(days=days),
                days=days,
            ),
        }

    def _get_diary(self, ctx: RouteContext) -> dict:
        """GET diary"""
        params = ctx.params
        target_persona = str(params.get("persona") or "").strip()
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        return {
            "ok": True,
            "persona": target_persona,
            "entries": diary.list_entries(
                self.plans_path.parent, target_persona, limit=20
            ),
        }

    def _get_book(self, ctx: RouteContext) -> dict:
        """GET book"""
        params = ctx.params
        payload = ctx.payload
        item = books.find_book(
            str(params.get("id") or params.get("name") or "")
        )
        if item is None:
            return {"ok": False, "error": "没有这本书"}
        raw_chapter = params.get("chapter")
        try:
            requested_chapter = int(raw_chapter or 0)
        except (TypeError, ValueError):
            requested_chapter = 0
        target_persona = str(
            params.get("persona") or payload.get("persona") or ""
        ).strip()
        progress = (
            books.get_progress(
                self.plans_path.parent,
                target_persona,
                str(item.get("id") or ""),
            )
            if target_persona
            else {}
        )
        total_chapters = max(1, len(item.get("chapters") or []))
        if requested_chapter > 0:
            chapter = min(requested_chapter, total_chapters)
        else:
            chapter = min(
                int(progress.get("chapter") or 1) or 1,
                total_chapters,
            )
        all_notes = list(progress.get("notes") or [])
        return {
            "ok": True,
            "id": item.get("id"),
            "title": item.get("title"),
            "author": item.get("author"),
            "genre": item.get("genre"),
            "chapter": chapter,
            "chapters": total_chapters,
            "chapter_titles": [
                str(chapter_item.get("title") or "")
                for chapter_item in (item.get("chapters") or [])
            ],
            "notes": len(all_notes),
            "note_items": [
                {**note, "index": index}
                for index, note in enumerate(all_notes)
            ],
            "content": books.render_book(item, chapter),
        }

    def _post_book_progress(self, ctx: RouteContext) -> dict:
        """POST book/progress"""
        payload = ctx.payload
        persona = ctx.persona
        target_persona = str(
            persona or payload.get("persona") or ""
        ).strip() or (view_state.active_persona(self.plans_path) or "")
        if not target_persona:
            return {"ok": False, "error": "缺少人格"}
        item = books.find_book(
            str(payload.get("id") or payload.get("book_id") or "")
        )
        if item is None:
            return {"ok": False, "error": "没有这本书"}
        try:
            read_chapter = int(payload.get("chapter") or 0)
        except (TypeError, ValueError):
            read_chapter = 0
        total = max(1, len(item.get("chapters") or []))
        result = books.record_reading(
            self.plans_path.parent,
            target_persona,
            str(item.get("id") or ""),
            read_chapter,
            total,
        )
        return {"ok": True, **result}

    def _post_affection_nickname(self, ctx: RouteContext) -> dict:
        """POST affection/nickname"""
        actual = ctx.actual
        now = ctx.now
        payload = ctx.payload
        return affection.set_nickname(
            self.plans_path.parent,
            actual["persona"],
            str(payload.get("nickname") or ""),
            now=now,
        )

    def _post_book_note(self, ctx: RouteContext) -> dict:
        """POST book/note"""
        actual = ctx.actual
        payload = ctx.payload
        try:
            note_chapter = int(payload.get("chapter") or 0)
        except (TypeError, ValueError):
            note_chapter = 0
        return books.add_note(
            self.plans_path.parent,
            actual["persona"],
            str(payload.get("id") or payload.get("book_id") or ""),
            str(payload.get("text") or ""),
            chapter=note_chapter,
        )

    def _post_book_note_delete(self, ctx: RouteContext) -> dict:
        """POST book/note/delete"""
        actual = ctx.actual
        payload = ctx.payload
        try:
            note_index = int(payload.get("index") or 0)
        except (TypeError, ValueError):
            note_index = -1
        return books.delete_note(
            self.plans_path.parent,
            actual["persona"],
            str(payload.get("id") or payload.get("book_id") or ""),
            note_index,
        )
