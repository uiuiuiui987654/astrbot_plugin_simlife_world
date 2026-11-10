from __future__ import annotations

import json
import random
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from .jsonio import atomic_write_json


MEAL_ORDER = ("早餐", "午餐", "晚餐", "加餐")
MAIN_MEALS = ("早餐", "午餐", "晚餐")
CONDIMENT_CATEGORY = "调味杂货"
DEFAULT_SHOPPING_SCENES = ("超市", "杂货铺", "菜市场")
BUY_WORDS = ("买", "采购", "补货", "采买", "补", "添", "囤")
OUT_LOCATION_WORDS = ("食堂", "外卖", "餐厅", "馆子", "咖啡", "公司", "学校", "单位")
COOKING_WORDS = (
    "做",
    "煮",
    "煎",
    "炒",
    "烤",
    "蒸",
    "炖",
    "拌",
    "熬",
    "焖",
    "包",
    "炸",
    "焯",
    "捏",
    "爆",
    "打",
)

# Ingredients that can stand in for one another when checking stock. The first
# name is what the recipe calls for; the rest are pantry names that satisfy it.
INGREDIENT_ALIASES: dict[str, tuple[str, ...]] = {
    "肉末": ("猪肉", "牛肉"),
    "肉片": ("猪肉", "牛肉"),
    "鸡肉": ("鸡腿", "鸡胸"),
    "玉米粒": ("玉米",),
    "面包": ("吐司",),
    "鱼片": ("鲈鱼", "三文鱼"),
    "青菜": ("青菜", "生菜", "菠菜"),
    "辣椒": ("辣椒", "韩式辣酱", "豆瓣酱"),
}

# Common shopping-list spellings that map back to catalog ingredient names.
INGREDIENT_SYNONYMS: dict[str, str] = {
    "西红柿": "番茄",
    "马铃薯": "土豆",
    "洋芋": "土豆",
    "红椒": "青椒",
    "彩椒": "青椒",
    "鸡翅": "鸡腿",
    "鸡胸肉": "鸡胸",
    "牛里脊": "牛肉",
    "猪里脊": "猪肉",
    "五花肉片": "五花肉",
    "葱段": "葱",
    "香葱": "葱",
    "蒜瓣": "蒜",
    "姜片": "姜",
}

PROTEIN_GROUPS: dict[str, str] = {
    "鸡腿": "鸡肉",
    "鸡胸": "鸡肉",
    "鸡肉": "鸡肉",
    "猪肉": "猪肉",
    "肉末": "猪肉",
    "五花肉": "猪肉",
    "排骨": "猪肉",
    "腊肠": "猪肉",
    "午餐肉": "猪肉",
    "火腿": "猪肉",
    "瘦肉": "猪肉",
    "牛肉": "牛肉",
    "牛腩": "牛肉",
    "虾仁": "虾",
    "鲈鱼": "鱼虾",
    "三文鱼": "鱼虾",
    "鱼头": "鱼虾",
    "鱼片": "鱼虾",
    "扇贝": "鱼虾",
    "鸡蛋": "鸡蛋",
    "皮蛋": "鸡蛋",
    "咸鸭蛋": "鸡蛋",
    "豆腐": "豆腐",
}

STAPLE_GROUPS: dict[str, str] = {
    "米饭": "米饭",
    "大米": "米饭",
    "面条": "面食",
    "意面": "面食",
    "面粉": "面食",
    "吐司": "面包",
    "面包": "面包",
    "可颂": "面包",
    "燕麦": "燕麦",
    "麦片": "燕麦",
    "小米": "杂粮",
    "红薯": "杂粮",
    "紫薯": "杂粮",
    "玉米": "杂粮",
    "玉米粒": "杂粮",
}

SPICY_INGREDIENTS = {"辣椒", "豆瓣酱", "韩式辣酱"}
SEAFOOD_INGREDIENTS = {
    "虾仁",
    "鲈鱼",
    "三文鱼",
    "鱼头",
    "鱼片",
    "扇贝",
    "海参",
    "蟹",
    "蛤蜊",
}
DAIRY_INGREDIENTS = {"牛奶", "酸奶", "芝士", "黄油", "奶油"}
PORK_INGREDIENTS = {"猪肉", "肉末", "五花肉", "排骨", "腊肠", "午餐肉", "火腿"}
BEEF_INGREDIENTS = {"牛肉", "牛腩"}
EGG_INGREDIENTS = {"鸡蛋", "皮蛋", "咸鸭蛋"}
AROMATIC_INGREDIENTS = {"葱", "姜", "蒜", "辣椒"}

MEAT_CATEGORIES = ("肉蛋水产",)
BULK_UNITS = {"袋", "瓶", "罐"}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _integer(value: Any, default: int, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, payload)


def _round_quantity(value: float) -> float:
    return round(max(0.0, value), 2)


def _label(item: dict) -> str:
    name = str(item.get("name") or "")
    quantity = _number(item.get("quantity"))
    unit = str(item.get("unit") or "")
    if quantity <= 0:
        return name + "（已用完）"
    if quantity == int(quantity):
        quantity_text = str(int(quantity))
    else:
        quantity_text = f"{quantity:g}"
    return f"{name}×{quantity_text}{unit}"


@dataclass(frozen=True)
class DietRules:
    vegetarian: bool = False
    vegan: bool = False
    no_spicy: bool = False
    no_seafood: bool = False
    no_dairy: bool = False
    no_pork: bool = False
    no_beef: bool = False
    no_egg: bool = False
    notes: tuple[str, ...] = ()

    def allows(self, dish: dict, category_of: dict[str, str]) -> bool:
        ingredients = [str(item) for item in dish.get("ingredients", [])]
        tags = {str(item) for item in dish.get("tags", [])}
        if self.no_spicy and ("辣" in tags or SPICY_INGREDIENTS & set(ingredients)):
            return False
        if self.no_seafood and SEAFOOD_INGREDIENTS & set(ingredients):
            return False
        if self.no_dairy and DAIRY_INGREDIENTS & set(ingredients):
            return False
        if self.no_pork and PORK_INGREDIENTS & set(ingredients):
            return False
        if self.no_beef and BEEF_INGREDIENTS & set(ingredients):
            return False
        if self.no_egg and EGG_INGREDIENTS & set(ingredients):
            return False
        if self.vegan and self._has_animal_product(ingredients, category_of):
            return False
        if self.vegetarian and self._has_meat_or_fish(ingredients, category_of):
            return False
        return True

    @staticmethod
    def _has_meat_or_fish(ingredients: list[str], category_of: dict[str, str]) -> bool:
        for ingredient in ingredients:
            if category_of.get(ingredient) in MEAT_CATEGORIES:
                if ingredient in EGG_INGREDIENTS:
                    continue
                return True
        return False

    @classmethod
    def _has_animal_product(cls, ingredients: list[str], category_of: dict[str, str]) -> bool:
        if cls._has_meat_or_fish(ingredients, category_of):
            return True
        return bool(EGG_INGREDIENTS & set(ingredients) or DAIRY_INGREDIENTS & set(ingredients))


def detect_diet(persona_prompt: str) -> DietRules:
    text = str(persona_prompt or "")
    notes: list[str] = []

    def hit(*keywords: str) -> bool:
        return any(keyword in text for keyword in keywords)

    vegetarian = hit(
        "素食", "吃素", "全素", "纯素", "不吃肉", "不吃荤", "vegetarian", "no meat"
    )
    vegan = hit("纯素", "全素", "严格素食", "vegan")
    no_spicy = hit(
        "不吃辣",
        "不喜欢辣",
        "不爱吃辣",
        "忌辣",
        "不能吃辣",
        "怕辣",
        "no spicy",
        "not spicy",
        "can't eat spicy",
    )
    no_seafood = hit(
        "海鲜过敏",
        "不吃海鲜",
        "贝类过敏",
        "对海鲜过敏",
        "不吃鱼虾",
        "seafood allergy",
        "no seafood",
    )
    no_dairy = hit(
        "乳糖不耐",
        "不喝牛奶",
        "不喝奶",
        "不吃奶制品",
        "牛奶过敏",
        "lactose",
        "no dairy",
    )
    no_pork = hit("不吃猪肉", "清真", "穆斯林", "不碰猪肉", "no pork", "halal")
    no_beef = hit("不吃牛", "不吃牛肉", "no beef")
    no_egg = hit("不吃鸡蛋", "不吃蛋", "鸡蛋过敏", "no egg") or vegan

    labels = []
    if vegan:
        labels.append("纯素")
    elif vegetarian:
        labels.append("素食")
    if no_spicy:
        labels.append("不吃辣")
    if no_seafood:
        labels.append("不吃海鲜")
    if no_dairy:
        labels.append("不吃乳制品")
    if no_pork:
        labels.append("不吃猪肉")
    if no_beef:
        labels.append("不吃牛肉")
    if no_egg and not vegan:
        labels.append("不吃蛋")
    if labels:
        notes.append("、".join(labels))

    return DietRules(
        vegetarian=vegetarian or vegan,
        vegan=vegan,
        no_spicy=no_spicy,
        no_seafood=no_seafood,
        no_dairy=no_dairy,
        no_pork=no_pork,
        no_beef=no_beef,
        no_egg=no_egg,
        notes=tuple(notes),
    )


def recent_dishes(state: dict, target: date, days: int) -> set[str]:
    if days <= 0:
        return set()
    cutoff = target - timedelta(days=days)
    names: set[str] = set()
    for entry in state.get("log", []):
        if not isinstance(entry, dict):
            continue
        dish = str(entry.get("dish") or "").strip()
        raw_date = str(entry.get("date") or "").strip()
        if not dish or not raw_date:
            continue
        try:
            entry_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if cutoff <= entry_date < target:
            names.add(dish)
    return names


class FoodSystem:
    """Menu planning and a pantry that changes with cooking and shopping."""

    _lock = threading.RLock()

    def __init__(self, data_dir: Path | None, catalog_path: Path):
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.catalog_path = Path(catalog_path)

    def load_catalog(self) -> dict:
        payload = _read_json(self.catalog_path, {})
        return payload if isinstance(payload, dict) else {}

    def inventory_path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "fridge_inventory.json"

    def state_path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "food_state.json"

    def load_inventory(self) -> dict[str, dict]:
        path = self.inventory_path()
        if path is None:
            return {}
        if not path.exists():
            starter = self.load_catalog().get("starter_inventory")
            if isinstance(starter, list) and starter:
                inventory = self._normalize_inventory({"ingredients": starter})
                self.save_inventory(inventory, date.today())
                return inventory
        payload = _read_json(path, {})
        return self._normalize_inventory(payload)

    def save_inventory(self, inventory: dict[str, dict], target: date) -> None:
        path = self.inventory_path()
        if path is None:
            return
        payload = {
            "schema_version": 2,
            "updated_at": target.isoformat(),
            "ingredients": list(inventory.values()),
        }
        _write_json(path, payload)

    def load_state(self) -> dict:
        path = self.state_path()
        if path is None:
            return self._empty_state()
        payload = _read_json(path, {})
        if not isinstance(payload, dict):
            return self._empty_state()
        state = self._empty_state()
        for key in ("menus", "applied"):
            value = payload.get(key)
            if isinstance(value, dict):
                state[key] = value
        for key in ("log", "shopping"):
            value = payload.get(key)
            if isinstance(value, list):
                state[key] = [item for item in value if isinstance(item, dict)]
        state["updated_at"] = str(payload.get("updated_at") or "")
        return state

    def save_state(self, state: dict) -> None:
        path = self.state_path()
        if path is None:
            return
        self._trim_state(state)
        payload = {
            "schema_version": 1,
            "updated_at": state.get("updated_at", ""),
            "menus": state.get("menus", {}),
            "applied": state.get("applied", {}),
            "log": state.get("log", []),
            "shopping": state.get("shopping", []),
        }
        _write_json(path, payload)

    @staticmethod
    def _empty_state() -> dict:
        return {
            "schema_version": 1,
            "updated_at": "",
            "menus": {},
            "applied": {},
            "log": [],
            "shopping": [],
        }

    @staticmethod
    def _normalize_inventory(payload: Any) -> dict[str, dict]:
        raw = payload.get("ingredients", []) if isinstance(payload, dict) else []
        inventory: dict[str, dict] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            inventory[name] = {
                "name": name,
                "quantity": _round_quantity(_number(item.get("quantity"))),
                "unit": str(item.get("unit") or "").strip(),
                "category": str(item.get("category") or "其他").strip() or "其他",
            }
        return inventory

    @staticmethod
    def _trim_state(state: dict) -> None:
        menus = state.get("menus")
        if isinstance(menus, dict) and len(menus) > 30:
            keep = sorted(menus)[-30:]
            state["menus"] = {key: menus[key] for key in keep}
        applied = state.get("applied")
        if isinstance(applied, dict) and len(applied) > 60:
            keep = sorted(applied)[-60:]
            state["applied"] = {key: applied[key] for key in keep}
        log = state.get("log")
        if isinstance(log, list) and len(log) > 500:
            state["log"] = log[-500:]
        shopping = state.get("shopping")
        if isinstance(shopping, list) and len(shopping) > 160:
            state["shopping"] = shopping[-160:]

    def plan_day(
        self,
        target: date,
        persona_id: str,
        persona_prompt: str,
        settings: dict | None = None,
        rhythm: dict | None = None,
    ) -> dict:
        settings = settings or {}
        rhythm = rhythm or {}
        catalog = self.load_catalog()
        meals_catalog = catalog.get("meals") or {}
        if not isinstance(meals_catalog, dict) or not meals_catalog:
            return {}

        inventory = self.load_inventory()
        state = self.load_state()
        category_of = self._category_map(catalog)
        diet = detect_diet(persona_prompt)
        variety_days = _integer(settings.get("dish_variety_days"), 3, 0, 30)
        recent = recent_dishes(state, target, variety_days)
        max_missing = _integer(settings.get("max_missing_ingredients"), 1, 0, 4)
        alternatives_count = _integer(settings.get("menu_alternatives"), 2, 0, 4)
        rng = random.Random(f"{target.isoformat()}::{persona_id}::menu-v2")
        sources = self._meal_sources(settings, rng)
        scenes = catalog.get("shopping_scenes")
        if not isinstance(scenes, list) or not scenes:
            scenes = list(DEFAULT_SHOPPING_SCENES)
        scene = rng.choice([str(item) for item in scenes])

        planned_meals: list[dict] = []
        used_proteins: set[str] = set()
        used_staples: set[str] = set()
        used_dishes: set[str] = set()

        for meal_name in MAIN_MEALS:
            source = sources.get(meal_name, "simple")
            if source == "simple":
                planned_meals.append(
                    {
                        "meal": meal_name,
                        "source": "simple",
                        "dish": "",
                        "ingredients": [],
                        "method": "",
                        "missing": [],
                        "alternatives": [],
                    }
                )
                continue
            if source == "out":
                dish = self._pick_takeout(catalog, meal_name, diet, rng, used_dishes)
                if dish is None:
                    planned_meals.append(
                        {
                            "meal": meal_name,
                            "source": "simple",
                            "dish": "",
                            "ingredients": [],
                            "method": "",
                            "missing": [],
                            "alternatives": [],
                        }
                    )
                    continue
                used_dishes.add(str(dish.get("name") or ""))
                planned_meals.append(
                    {
                        "meal": meal_name,
                        "source": "out",
                        "dish": str(dish.get("name") or ""),
                        "ingredients": [],
                        "method": "",
                        "missing": [],
                        "alternatives": [],
                    }
                )
                continue

            dishes = meals_catalog.get(meal_name)
            if not isinstance(dishes, list):
                dishes = self._all_dishes(meals_catalog)
            dish, alternatives = self._pick_dish(
                dishes,
                inventory,
                recent | used_dishes,
                diet,
                category_of,
                rng,
                used_proteins,
                used_staples,
                max_missing,
                alternatives_count,
                target,
            )
            if dish is None:
                planned_meals.append(
                    {
                        "meal": meal_name,
                        "source": "simple",
                        "dish": "",
                        "ingredients": [],
                        "method": "",
                        "missing": [],
                        "alternatives": [],
                    }
                )
                continue
            ingredients = [str(item) for item in dish.get("ingredients", [])]
            missing = self._missing_ingredients(dish, inventory)
            used_dishes.add(str(dish.get("name") or ""))
            protein = self._main_protein(ingredients)
            staple = self._main_staple(ingredients)
            if protein:
                used_proteins.add(protein)
            if staple:
                used_staples.add(staple)
            planned_meals.append(
                {
                    "meal": meal_name,
                    "source": "home",
                    "dish": str(dish.get("name") or ""),
                    "ingredients": ingredients,
                    "method": str(dish.get("method") or ""),
                    "missing": missing,
                    "alternatives": [
                        {
                            "name": str(item.get("name") or ""),
                            "missing": self._missing_ingredients(item, inventory),
                        }
                        for item in alternatives
                    ],
                }
            )

        shopping = sorted(
            {
                ingredient
                for meal in planned_meals
                for ingredient in meal.get("missing", [])
            }
        )
        low_stock = self._low_stock(inventory)
        return {
            "date": target.isoformat(),
            "persona_id": persona_id,
            "generated_at": date.today().isoformat(),
            "meals": planned_meals,
            "shopping": shopping,
            "shopping_scene": scene,
            "low_stock": low_stock,
            "diet": list(diet.notes),
            "windows": {
                "早餐": str(rhythm.get("breakfast_window") or "").strip(),
                "午餐": str(rhythm.get("lunch_window") or "").strip(),
                "晚餐": str(rhythm.get("dinner_window") or "").strip(),
            },
        }

    def _meal_sources(self, settings: dict, rng: random.Random) -> dict[str, str]:
        home_min = _integer(settings.get("home_cooked_min_per_day"), 1, 0, 3)
        home_max = _integer(settings.get("home_cooked_max_per_day"), 2, 0, 3)
        if home_max < home_min:
            home_min, home_max = home_max, home_min
        takeout_max = _integer(settings.get("takeout_max_per_day"), 1, 0, 3)
        home_count = rng.randint(home_min, home_max)
        sources = {meal: "simple" for meal in MAIN_MEALS}

        # Breakfast and dinner are the most natural home-cooked meals.
        for meal in ("早餐", "晚餐", "午餐"):
            if home_count <= 0:
                break
            sources[meal] = "home"
            home_count -= 1

        out_count = 0
        remaining = sum(1 for value in sources.values() if value == "simple")
        if takeout_max > 0 and remaining > 0:
            out_count = 1 if rng.random() < 0.7 else 0
            if not any(value != "simple" for value in sources.values()):
                out_count = min(takeout_max, 1)
        concrete = sum(1 for value in sources.values() if value != "simple")
        if concrete < 2 and takeout_max > 0 and not any(
            value == "out" for value in sources.values()
        ):
            out_count = max(out_count, 1)
        elif concrete < 2 and sum(
            1 for value in sources.values() if value == "home"
        ) < home_max:
            for meal in ("晚餐", "午餐", "早餐"):
                if sources[meal] == "simple":
                    sources[meal] = "home"
                    break
        for meal in ("午餐", "早餐", "晚餐"):
            if out_count <= 0:
                break
            if sources[meal] == "simple":
                sources[meal] = "out"
                out_count -= 1
        return sources

    def _pick_dish(
        self,
        dishes: list,
        inventory: dict[str, dict],
        recent: set[str],
        diet: DietRules,
        category_of: dict[str, str],
        rng: random.Random,
        used_proteins: set[str],
        used_staples: set[str],
        max_missing: int,
        alternatives_count: int,
        target: date,
    ) -> tuple[dict | None, list[dict]]:
        evaluated: list[tuple[list[str], dict]] = []
        for dish in dishes:
            if not isinstance(dish, dict):
                continue
            name = str(dish.get("name") or "").strip()
            if not name or not diet.allows(dish, category_of):
                continue
            evaluated.append((self._missing_ingredients(dish, inventory), dish))
        if not evaluated:
            return None, []

        pool: list[tuple[list[str], dict]] = []
        for limit in range(max_missing, 5):
            pool = [item for item in evaluated if len(item[0]) <= limit]
            if pool:
                break
        if not pool:
            pool = sorted(evaluated, key=lambda item: len(item[0]))[:8]

        scored: list[tuple[float, list[str], dict]] = []
        for missing, dish in pool:
            name = str(dish.get("name") or "")
            ingredients = [str(item) for item in dish.get("ingredients", [])]
            score = 6.0 - 3.0 * len(missing) + rng.random() * 2.0
            if name in recent:
                score -= 8.0
            protein = self._main_protein(ingredients)
            staple = self._main_staple(ingredients)
            if protein and protein in used_proteins:
                score -= 4.0
            if staple and staple in used_staples:
                score -= 2.0
            score += self._season_bonus(dish, target)
            scored.append((score, missing, dish))
        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[0]
        alternatives = [item[2] for item in scored[1 : 1 + alternatives_count]]
        return best[2], alternatives

    def _pick_takeout(
        self,
        catalog: dict,
        meal_name: str,
        diet: DietRules,
        rng: random.Random,
        used_dishes: set[str],
    ) -> dict | None:
        raw = catalog.get("takeout")
        if not isinstance(raw, list):
            return None
        category_of = self._category_map(catalog)
        choices = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name or name in used_dishes:
                continue
            meals = item.get("meals")
            if isinstance(meals, list) and meals and meal_name not in meals:
                continue
            if diet.allows(item, category_of):
                choices.append(item)
        if not choices:
            return None
        return rng.choice(choices)

    @staticmethod
    def _all_dishes(meals: dict) -> list:
        dishes: list = []
        for value in meals.values():
            if isinstance(value, list):
                dishes.extend(value)
        return dishes

    # ------------------------------------------------------------------
    # Stock helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _category_map(catalog: dict) -> dict[str, str]:
        mapping: dict[str, str] = {}
        raw = catalog.get("ingredients")
        if not isinstance(raw, dict):
            return mapping
        for category, names in raw.items():
            if not isinstance(names, list):
                continue
            for name in names:
                text = str(name).strip()
                if text:
                    mapping[text] = str(category)
        return mapping

    @staticmethod
    def _stock_for(ingredient: str, inventory: dict[str, dict]) -> dict | None:
        direct = inventory.get(ingredient)
        if direct and _number(direct.get("quantity")) > 0:
            return direct
        for alias in INGREDIENT_ALIASES.get(ingredient, ()):
            item = inventory.get(alias)
            if item and _number(item.get("quantity")) > 0:
                return item
        return None

    def _missing_ingredients(self, dish: dict, inventory: dict[str, dict]) -> list[str]:
        missing: list[str] = []
        for ingredient in dish.get("ingredients", []):
            name = str(ingredient).strip()
            if name and self._stock_for(name, inventory) is None:
                missing.append(name)
        return missing

    @staticmethod
    def _main_protein(ingredients: list[str]) -> str:
        for ingredient in ingredients:
            group = PROTEIN_GROUPS.get(ingredient)
            if group:
                return group
        return ""

    @staticmethod
    def _main_staple(ingredients: list[str]) -> str:
        for ingredient in ingredients:
            group = STAPLE_GROUPS.get(ingredient)
            if group:
                return group
        return ""

    @staticmethod
    def _season_bonus(dish: dict, target: date) -> float:
        text = " ".join(
            [str(dish.get("name") or ""), str(dish.get("method") or "")]
            + [str(item) for item in dish.get("tags", [])]
        )
        month = target.month
        if month in (11, 12, 1, 2) and any(
            word in text for word in ("暖胃", "炖", "汤", "粥", "锅", "焖")
        ):
            return 1.2
        if month in (6, 7, 8) and any(
            word in text for word in ("清爽", "凉", "拌", "沙拉", "水果")
        ):
            return 1.2
        return 0.0

    def _low_stock(self, inventory: dict[str, dict]) -> list[str]:
        low: list[str] = []
        for item in inventory.values():
            name = str(item.get("name") or "")
            category = str(item.get("category") or "")
            unit = str(item.get("unit") or "")
            quantity = _number(item.get("quantity"))
            if not name or category == CONDIMENT_CATEGORY:
                continue
            if name in AROMATIC_INGREDIENTS:
                continue
            if category == "主食" and unit in BULK_UNITS:
                continue
            if quantity <= 0:
                low.append(name)
                continue
            if unit == "克":
                if quantity <= 150 and category in MEAT_CATEGORIES:
                    low.append(name)
                continue
            if quantity <= 1 and category in (
                "肉蛋水产",
                "主食",
                "乳品豆制品",
                "水果",
            ):
                low.append(name)
        return low

    # ------------------------------------------------------------------
    # Prompt formatting
    # ------------------------------------------------------------------
    def format_day_prompt(self, menu: dict, settings: dict | None = None) -> str:
        if not menu:
            return ""
        settings = settings or {}
        include_ingredients = bool(settings.get("include_ingredients", True))
        include_method = bool(settings.get("include_cooking_method", True))
        include_shopping = bool(settings.get("include_shopping_list", True))
        windows = menu.get("windows") or {}

        lines = ["【今日菜单（生活系统已按冰箱库存排好）】"]
        for meal in menu.get("meals", []):
            name = str(meal.get("meal") or "")
            source = str(meal.get("source") or "simple")
            dish = str(meal.get("dish") or "")
            window = str(windows.get(name) or "").strip()
            prefix = f"- {name}" + (f"（{window}）" if window else "") + "："
            if source == "home" and dish:
                details = []
                if include_ingredients:
                    ingredients = [
                        str(item)
                        for item in meal.get("ingredients", [])
                        if str(item).strip()
                    ]
                    if ingredients:
                        details.append("食材：" + "、".join(ingredients))
                if include_method and meal.get("method"):
                    details.append("做法：" + str(meal.get("method")))
                suffix = "（" + "；".join(details) + "）" if details else ""
                lines.append(prefix + "在家做：" + dish + suffix)
            elif source == "out" and dish:
                lines.append(prefix + "外食：" + dish)
            else:
                lines.append(prefix + "简单解决（剩菜、加餐或自行安排）")

        if include_shopping and menu.get("shopping"):
            scene = str(menu.get("shopping_scene") or "超市")
            items = "、".join(str(item) for item in menu["shopping"])
            lines.append(
                f"- 采购：去{scene}买{items}；采购活动写成“去{scene}采购（买：{items}）”。"
            )
        elif include_shopping and menu.get("low_stock"):
            items = "、".join(str(item) for item in menu["low_stock"][:8])
            scene = str(menu.get("shopping_scene") or "超市")
            lines.append(f"- 库存偏低：{items}；可顺路去{scene}补一点。")

        alternatives = []
        for meal in menu.get("meals", []):
            names = [
                str(item.get("name") or "")
                for item in meal.get("alternatives", [])
                if str(item.get("name") or "").strip()
            ]
            if names:
                alternatives.append(f"{meal.get('meal')} → " + "、".join(names))
        if alternatives:
            lines.append("- 可替换：" + "；".join(alternatives))

        if menu.get("diet"):
            lines.append(
                "- 饮食限制："
                + "、".join(str(item) for item in menu["diet"])
                + "（菜单已避开）"
            )

        lines.extend(
            [
                "【今日菜单规则】",
                "- 上面的菜名、食材和做法由生活系统按现有库存排好，请直接写进时间线，不要改成别的菜。",
                "- 在家做饭写成“做菜名（食材：…；做法：…）”，吃饭写成“吃菜名”；外食写成“在食堂/餐厅吃菜名”。",
                "- 在家做的菜会消耗冰箱库存；外食和“简单解决”不消耗。",
                "- 不要凭空补满冰箱；缺的食材写进采购清单，采购后库存才会增加。",
            ]
        )
        pantry = self._pantry_lines()
        if pantry:
            lines.append("")
            lines.extend(pantry)
        return "\n".join(lines)

    def _pantry_lines(self) -> list[str]:
        inventory = self.load_inventory()
        if not inventory:
            return ["【冰箱库存】", "- 冰箱里暂时没有食材；今天适合安排一次采购。"]
        grouped: dict[str, list[str]] = {}
        for item in inventory.values():
            category = str(item.get("category") or "其他")
            grouped.setdefault(category, []).append(_label(item))
        lines = ["【冰箱库存（会随做饭和采购变化）】"]
        for category, labels in grouped.items():
            if category == CONDIMENT_CATEGORY:
                names = [
                    str(item.get("name") or "")
                    for item in inventory.values()
                    if item.get("category") == category
                ]
                lines.append(
                    f"- {category}："
                    + "、".join(name for name in names if name)
                    + "（常备）"
                )
                continue
            lines.append(f"- {category}：" + "、".join(labels))
        return lines

    def latest_menu(self, target: date, persona_id: str) -> dict:
        state = self.load_state()
        menus = state.get("menus")
        if not isinstance(menus, dict):
            return {}
        menu = menus.get(f"{target.isoformat()}::{persona_id}")
        return menu if isinstance(menu, dict) else {}

    def format_menu_text(self, menu: dict) -> str:
        if not menu:
            return ""
        labels = {"home": "在家做", "out": "外食", "simple": "简单解决"}
        lines = [f"【{menu.get('date', '')} 菜单】"]
        for meal in menu.get("meals", []):
            dish = str(meal.get("dish") or "")
            source = str(meal.get("source") or "simple")
            if source == "simple" or not dish:
                lines.append(f"- {meal.get('meal')}：剩菜、加餐或自行安排")
                continue
            detail_parts = [labels.get(source, source)]
            if source == "home":
                ingredients = [
                    str(item)
                    for item in meal.get("ingredients", [])
                    if str(item).strip()
                ]
                if ingredients:
                    detail_parts.append("食材：" + "、".join(ingredients))
                if meal.get("method"):
                    detail_parts.append("做法：" + str(meal.get("method")))
            lines.append(
                f"- {meal.get('meal')}：{dish}（" + "；".join(detail_parts) + "）"
            )
        if menu.get("shopping"):
            lines.append(
                "- 待采购：" + "、".join(str(item) for item in menu["shopping"])
            )
        if menu.get("low_stock"):
            lines.append(
                "- 库存偏低："
                + "、".join(str(item) for item in menu["low_stock"][:8])
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Applying a generated plan
    # ------------------------------------------------------------------
    def apply_plan(
        self,
        plan: Any,
        persona_id: str,
        menu: dict,
        settings: dict | None = None,
    ) -> dict:
        settings = settings or {}
        if self.data_dir is None or not menu:
            return {"status": "skipped", "reason": "no_data_dir"}
        consume_enabled = bool(settings.get("consume_inventory", True))
        restock_enabled = bool(settings.get("restock_from_shopping", True))
        if not consume_enabled and not restock_enabled:
            return {"status": "skipped", "reason": "disabled"}
        if not getattr(plan, "has_schedule", False):
            return {"status": "skipped", "reason": "no_schedule"}

        target = date.fromisoformat(str(plan.date))
        key = f"{plan.date}::{persona_id}"
        with self._lock:
            state = self.load_state()
            applied = state.setdefault("applied", {})
            if key in applied:
                return {"status": "skipped", "reason": "already_applied"}
            log = state.setdefault("log", [])
            if any(
                str(entry.get("date")) == plan.date
                and str(entry.get("persona_id")) == persona_id
                for entry in log
            ):
                applied[key] = str(getattr(plan, "revision", ""))
                state["updated_at"] = target.isoformat()
                self.save_state(state)
                return {"status": "skipped", "reason": "already_logged_today"}

            inventory = self.load_inventory()
            catalog = self.load_catalog()
            scenes = catalog.get("shopping_scenes")
            if not isinstance(scenes, list) or not scenes:
                scenes = list(DEFAULT_SHOPPING_SCENES)
            scene_names = [str(item) for item in scenes]

            consumed: list[str] = []
            purchased: list[str] = []
            eaten_out: list[str] = []
            recorded_meals: set[str] = set()
            timeline = sorted(
                getattr(plan, "timeline", ()), key=lambda item: item.start
            )
            for item in timeline:
                text = f"{item.activity} {item.location}"
                if self._is_shopping(text, scene_names):
                    if restock_enabled:
                        names = self._extract_ingredients(text, catalog, inventory)
                        for name in names:
                            self._add_stock(
                                inventory, name, self._category_map(catalog)
                            )
                        if names:
                            purchased.extend(names)
                            state.setdefault("shopping", []).append(
                                {
                                    "date": plan.date,
                                    "persona_id": persona_id,
                                    "scene": item.location or "",
                                    "items": names,
                                    "activity": item.activity,
                                }
                            )
                    continue

                meal = self._match_menu_meal(text, menu, recorded_meals)
                if meal is None:
                    continue
                meal_name = str(meal.get("meal") or "")
                if meal_name in recorded_meals:
                    continue
                recorded_meals.add(meal_name)
                dish = str(meal.get("dish") or "")
                source = str(meal.get("source") or "home")
                log.append(
                    {
                        "date": plan.date,
                        "persona_id": persona_id,
                        "meal": meal_name,
                        "dish": dish,
                        "method": str(meal.get("method") or ""),
                        "source": source,
                        "ingredients": list(meal.get("ingredients", [])),
                    }
                )
                if source == "home" and consume_enabled:
                    if self._consume_dish(inventory, meal):
                        consumed.append(dish)
                elif source == "out":
                    eaten_out.append(dish)

            applied[key] = str(getattr(plan, "revision", ""))
            state["updated_at"] = target.isoformat()
            state.setdefault("menus", {})[key] = menu
            if consume_enabled or restock_enabled:
                self.save_inventory(inventory, target)
            self.save_state(state)
        return {
            "status": "applied",
            "consumed": consumed,
            "purchased": sorted(set(purchased)),
            "eaten_out": eaten_out,
        }

    @staticmethod
    def _is_shopping(text: str, scenes: list[str]) -> bool:
        if not any(scene in text for scene in scenes):
            return False
        return any(word in text for word in BUY_WORDS)

    def _match_menu_meal(
        self, text: str, menu: dict, recorded: set[str]
    ) -> dict | None:
        meals = [
            item
            for item in menu.get("meals", [])
            if isinstance(item, dict) and item.get("meal") not in recorded
        ]
        looks_out = any(word in text for word in OUT_LOCATION_WORDS)
        # Exact dish names are the strongest signal. Prefer the meal whose
        # source matches the activity, since some dishes exist both at home
        # and as takeout options.
        for meal in meals:
            dish = str(meal.get("dish") or "")
            if dish and dish in text:
                source = str(meal.get("source") or "")
                if (looks_out and source == "out") or (
                    not looks_out and source == "home"
                ):
                    return meal
        for meal in meals:
            dish = str(meal.get("dish") or "")
            if dish and dish in text:
                return meal
        # A meal slot with cooking or eating wording is enough when the model
        # paraphrased the dish name but kept the activity at home.
        for meal in meals:
            if str(meal.get("source")) != "home":
                continue
            meal_name = str(meal.get("meal") or "")
            if meal_name in text and not looks_out and any(
                word in text for word in COOKING_WORDS + ("吃",)
            ):
                return meal
        for meal in meals:
            if str(meal.get("source")) != "out":
                continue
            meal_name = str(meal.get("meal") or "")
            if meal_name in text and looks_out:
                return meal
        return None

    def _consume_dish(self, inventory: dict[str, dict], meal: dict) -> bool:
        changed = False
        for ingredient in meal.get("ingredients", []):
            name = str(ingredient).strip()
            if not name:
                continue
            item = self._stock_for(name, inventory)
            if item is None or not self._should_consume(item):
                continue
            amount = self._consume_amount(item, name)
            current = _number(item.get("quantity"))
            item["quantity"] = _round_quantity(current - amount)
            changed = True
        return changed

    @staticmethod
    def _should_consume(item: dict) -> bool:
        category = str(item.get("category") or "")
        unit = str(item.get("unit") or "")
        if category == CONDIMENT_CATEGORY:
            return False
        if category == "主食" and unit in BULK_UNITS:
            return False
        return True

    @staticmethod
    def _consume_amount(item: dict, ingredient: str) -> float:
        name = str(item.get("name") or ingredient)
        unit = str(item.get("unit") or "")
        category = str(item.get("category") or "")
        if unit == "克":
            return 150.0 if category in MEAT_CATEGORIES else 100.0
        if unit == "毫升":
            return 200.0
        if name == "鸡蛋":
            return 2.0
        return 1.0

    def _add_stock(
        self, inventory: dict[str, dict], name: str, category_of: dict[str, str]
    ) -> None:
        if not name:
            return
        item = inventory.get(name)
        if item is None:
            category = category_of.get(name, "其他")
            item = {
                "name": name,
                "quantity": 0.0,
                "unit": self._guess_unit(name, category),
                "category": category,
            }
            inventory[name] = item
        amount = self._restock_amount(item)
        item["quantity"] = _round_quantity(
            min(999.0, _number(item.get("quantity")) + amount)
        )

    @staticmethod
    def _guess_unit(name: str, category: str) -> str:
        if name in {"鸡蛋", "皮蛋", "咸鸭蛋"}:
            return "个"
        if name in {"牛奶", "酸奶", "豆腐", "午餐肉", "泡菜", "豆瓣酱", "咖喱"}:
            return "盒"
        if category == "肉蛋水产":
            return "克"
        if category == "蔬菜":
            return "把" if name in {"青菜", "菠菜", "韭菜", "葱", "香菜"} else "个"
        if category == "主食":
            if name in {"大米", "面粉", "燕麦", "小米", "意面", "粉丝", "红薯粉"}:
                return "袋"
            return "份"
        if category == "乳品豆制品":
            return "盒"
        if category == "水果":
            return "个"
        if category == CONDIMENT_CATEGORY:
            return "瓶"
        return "份"

    @staticmethod
    def _restock_amount(item: dict) -> float:
        unit = str(item.get("unit") or "")
        category = str(item.get("category") or "")
        name = str(item.get("name") or "")
        if unit == "克":
            return 300.0 if category in MEAT_CATEGORIES else 200.0
        if unit == "毫升":
            return 500.0
        if name == "鸡蛋":
            return 6.0
        if category == "乳品豆制品" and unit in {"盒", "杯"}:
            return 3.0
        if unit in BULK_UNITS:
            return 1.0
        return 2.0

    @staticmethod
    def _extract_ingredients(
        text: str, catalog: dict, inventory: dict[str, dict]
    ) -> list[str]:
        names: set[str] = set()
        raw = catalog.get("ingredients")
        if isinstance(raw, dict):
            for values in raw.values():
                if not isinstance(values, list):
                    continue
                for value in values:
                    name = str(value).strip()
                    if name:
                        names.add(name)
        names.update(inventory.keys())
        for synonym, canonical in INGREDIENT_SYNONYMS.items():
            if synonym in text and canonical not in text:
                text = text.replace(synonym, canonical)
        found = [
            name for name in sorted(names, key=len, reverse=True) if name in text
        ]
        return list(dict.fromkeys(found))[:12]
