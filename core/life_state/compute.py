"""The main life-state computation (energy, fullness, cleanliness, mood, health flags)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import (
    RATES,
    _activity_kind,
    _activity_minutes,
    _clamp,
    _current_activity_kind,
    _history_mood_average,
    _is_weekend,
    _item_get,
    _label,
    _low_mood_streak,
    _minute,
    _mood_base,
    _timeline,
    _weekday,
)
from .body import (
    _brushed_in_window,
    _days_since_overwork,
    _exercise_yesterday,
    _has_brushed_teeth,
    _has_stretch,
    _plan_recovery_text,
    _recent_brushing_days,
    _recent_exercise_days,
    _recent_harmful_actions,
    _recent_long_commute_days,
    _recent_overtraining_days,
    _recent_overwork_days,
    _recent_recovery_actions,
    _recent_tooth_neglect_days,
    _recovery_light_movement,
    _stiff_neck_yesterday,
    _transit_minutes,
    _work_minutes,
    _yesterday_exercise_minutes,
)
from .habits import (
    _apply_furniture_effects,
    _late_movie_yesterday,
    _reading_minutes,
    _recent_aroma,
    _recent_audio_action,
    _recent_chore,
    _recent_fresh_clothes,
    _recent_instrument,
    _recent_popcorn,
    _recent_screen_time,
)
from .meals import (
    _apply_hydration_effects,
    _baking_minutes,
    _breakfast_eaten_by,
    _caffeine_crash,
    _cooking_minutes,
    _has_breakfast,
    _has_dinner,
    _has_heavy_food,
    _has_late_dinner,
    _has_late_meal,
    _has_light_diet,
    _has_lunch,
    _hydration_at,
    _late_baking,
    _late_caffeine,
    _light_diet_streak,
    _meal_end_minute,
    _meal_time_irregular,
    _plan_morning_coffee,
    _recent_baking_days,
    _recent_breakfast_skip_days,
    _recent_heavy_food_days,
    _recent_home_cooked_days,
    _recent_late_dinner_days,
    _recent_late_meal_days,
    _recent_lunch_skip_days,
    _recent_meal_regular_days,
    _recent_morning_coffee,
)
from .sleep import (
    _good_sleep_days,
    _good_sleep_streak,
    _late_night_streak,
    _main_sleep_window,
    _nap_minutes,
    _recent_late_nights,
    _sleep_debt,
    _sleep_regularity_minutes,
    _social_jetlag_minutes,
)
from .social import (
    _alcohol_current,
    _alcohol_last_night,
    _alcohol_last_night_severity,
    _completed_social_today,
    _days_since_social,
    _deep_social_yesterday,
    _hug_yesterday,
    _plan_has_alcohol,
    _plan_has_deep_social,
    _plan_has_hug,
    _recent_alcohol_days,
    _recent_social_days,
    _recent_solitude_minutes,
    _sober_days,
    _yesterday_social_minutes,
)
from .weather import (
    _consecutive_bad_weather,
    _consecutive_good_weather,
    _has_evening_walk,
    _heat_exposure_minutes,
    _heat_protection,
    _outfit_weather_protection,
    _recent_sun_days,
    _season_for_plan,
    _sunburn_yesterday,
    _sunlight_minutes,
    _temperature_swing,
    _weather_exposure_minutes,
    _weather_high_temp,
    _weather_is_bad,
    _weather_low_temp,
)


def compute(
    plan: Any,
    now: datetime | None = None,
    *,
    furniture_states: dict[str, Any] | None = None,
    history_plans: list[Any] | None = None,
    weak_constitution: bool = False,
    recent_illness_days: int = 0,
) -> dict[str, Any]:
    """Compute energy/fullness/cleanliness/mood from the day's timeline."""
    current = now or datetime.now()
    now_minute = current.hour * 60 + current.minute
    current_activity_kind = _current_activity_kind(plan, now_minute)
    afternoon_dip = bool(
        13 * 60 <= now_minute < 15 * 60
        and current_activity_kind not in ("sleep",)
    )
    evening_sleepiness = bool(
        22 * 60 <= now_minute < 24 * 60
        and current_activity_kind not in ("sleep",)
    )
    weather_bad = _weather_is_bad(plan)
    weather_exposure_minutes = _weather_exposure_minutes(plan, now_minute)
    warm_clothing, rain_gear, exposure_protection = _outfit_weather_protection(plan)
    heat_exposure_minutes = _heat_exposure_minutes(plan, now_minute)
    heat_protection = _heat_protection(plan)
    heat_penalty = min(
        4.0, heat_exposure_minutes * 0.05 * heat_protection
    )
    sunburn = bool(
        heat_exposure_minutes >= 60
        and heat_protection >= 1.0
        and _weather_high_temp(plan, 20) >= 32
    )
    sunburn_aftermath = bool(
        not sunburn and _sunburn_yesterday(history_plans, plan)
    )
    sunburn_repeat = bool(sunburn and _sunburn_yesterday(history_plans, plan))
    rainy_streak = _consecutive_bad_weather(plan, history_plans)
    sunny_streak = _consecutive_good_weather(plan, history_plans)
    season = _season_for_plan(plan)
    days_since_social = _days_since_social(history_plans, plan, now_minute=now_minute)
    social_days_7d = _recent_social_days(history_plans, plan, now_minute=now_minute)
    socially_satisfied = social_days_7d >= 3
    deep_social_today = _plan_has_deep_social(plan, now_minute)
    hugged_today = _plan_has_hug(plan, now_minute)
    hug_afterglow = _hug_yesterday(history_plans, plan)
    deep_social_afterglow = _deep_social_yesterday(history_plans, plan)
    yesterday_social_minutes = _yesterday_social_minutes(history_plans, plan)
    social_hangover_yesterday = yesterday_social_minutes >= 150
    social_minutes = _activity_minutes(plan, now_minute, "social")
    social_exhaustion_threshold = 120 if deep_social_today else 150
    social_exhaustion = social_minutes >= social_exhaustion_threshold
    need_solitude = social_exhaustion
    lonely = days_since_social >= 2
    chronic_lonely = days_since_social >= 5
    social_today = _completed_social_today(plan, now_minute)
    social_afterglow = bool(
        not social_today and 1 <= days_since_social <= 2
    )
    hangover = _alcohol_last_night(history_plans, plan)
    hangover_severity = _alcohol_last_night_severity(history_plans, plan)
    alcohol_today = _plan_has_alcohol(plan, now_minute)
    tipsy = _alcohol_current(plan, now_minute)
    alcohol_days_7d = _recent_alcohol_days(history_plans, plan, now_minute=now_minute)
    frequent_drinking = alcohol_days_7d >= 3
    sober_days = _sober_days(history_plans, plan, now_minute=now_minute)
    work_minutes = _work_minutes(plan, now_minute)
    nap_minutes_today = _nap_minutes(plan, now_minute)
    nap_inertia = 60 <= nap_minutes_today <= 180
    reading_minutes = _reading_minutes(plan, now_minute)
    cooking_minutes = _cooking_minutes(plan, now_minute)
    home_cooked = cooking_minutes >= 30
    baking_minutes = _baking_minutes(plan, now_minute)
    baking_today = baking_minutes >= 20
    baking_days_7d = _recent_baking_days(history_plans, plan, now_minute=now_minute)
    frequent_baking = baking_days_7d >= 3
    late_baking = _late_baking(plan, now_minute)
    brushed_teeth = _has_brushed_teeth(plan, now_minute)
    brushed_morning = _brushed_in_window(plan, 6 * 60, 11 * 60, now_minute)
    brushed_evening = _brushed_in_window(plan, 18 * 60, 24 * 60, now_minute)
    brushed_twice = bool(brushed_morning and brushed_evening)
    tooth_sensitivity = bool(
        (late_baking or frequent_baking) and not brushed_teeth
    )
    tooth_neglect_days_7d = _recent_tooth_neglect_days(history_plans, plan, now_minute=now_minute)
    frequent_tooth_neglect = tooth_neglect_days_7d >= 3
    brushing_days_7d = _recent_brushing_days(history_plans, plan, now_minute=now_minute)
    weekly_brushing_regular = brushing_days_7d >= 5
    home_cooked_days_7d = _recent_home_cooked_days(history_plans, plan, now_minute=now_minute)
    weekly_home_cooked = home_cooked_days_7d >= 3
    eye_strain = _recent_screen_time(furniture_states, current)
    instrument_practice = _recent_instrument(furniture_states, current)
    morning_coffee = bool(
        _recent_morning_coffee(furniture_states, current)
        or _plan_morning_coffee(plan, now_minute)
    )
    coffee_with_breakfast = bool(
        morning_coffee and _breakfast_eaten_by(plan, now_minute)
    )
    coffee_empty_stomach = bool(
        morning_coffee and not _breakfast_eaten_by(plan, now_minute)
    )
    popcorn_snack = _recent_popcorn(furniture_states, current)
    movie_night = bool(popcorn_snack and eye_strain)
    late_movie = bool(movie_night and now_minute >= 22 * 60)
    late_movie_yesterday = _late_movie_yesterday(history_plans, plan)
    movie_brush_relief = bool(late_movie and brushed_teeth)
    reading_relax = 20 <= reading_minutes < 120 and not eye_strain
    reading_fatigue = reading_minutes >= 120 and not eye_strain
    audio_action = _recent_audio_action(furniture_states, current)
    audio_relax = bool(audio_action)
    energetic_music = audio_relax and any(
        word in audio_action
        for word in ("摇滚", "快歌", "舞曲", "电音", "嗨", "迪斯科")
    )
    reading_audio_cozy = bool(
        reading_relax and audio_relax and not energetic_music
    )
    reading_audio_distracted = bool(reading_relax and energetic_music)
    transit_minutes = _transit_minutes(plan, now_minute)
    commute_fatigue = transit_minutes >= 60
    stiff_neck = bool(
        work_minutes >= 480
        and not _has_stretch(plan, now_minute)
        and _activity_minutes(plan, now_minute, "rest") < 30
    )
    overtraining = _activity_minutes(plan, now_minute, "exercise") >= 120
    pollen_allergy = bool(
        season == "spring"
        and _sunlight_minutes(plan, now_minute) >= 30
        and not weather_bad
    )
    overtraining_days_7d = _recent_overtraining_days(history_plans, plan, now_minute=now_minute)
    frequent_overtraining = overtraining_days_7d >= 2
    stiff_neck_yesterday = _stiff_neck_yesterday(history_plans, plan)
    weekend = _is_weekend(plan)
    weekday = _weekday(plan)
    monday_blues = bool(weekday == 0 and work_minutes > 0)
    good_sleep_streak = _good_sleep_streak(history_plans, plan, now_minute=now_minute)
    good_sleep_days_7d = _good_sleep_days(history_plans, plan, now_minute=now_minute)
    bad_weather_commute = bool(weather_bad and transit_minutes >= 30)
    long_commute_days_7d = _recent_long_commute_days(history_plans, plan)
    frequent_long_commute = long_commute_days_7d >= 3
    commute_penalty = (
        min(3.0, (long_commute_days_7d - 1) * 0.8)
        if frequent_long_commute
        else 0.0
    )
    muscle_soreness = _exercise_yesterday(history_plans, plan)
    yesterday_exercise_minutes = _yesterday_exercise_minutes(history_plans, plan)
    overtraining_yesterday = yesterday_exercise_minutes >= 120
    exercise_days_7d = _recent_exercise_days(history_plans, plan, now_minute=now_minute)
    regular_exercise = exercise_days_7d >= 3
    sedentary_week = exercise_days_7d == 0
    restart_soreness = muscle_soreness and 1 <= exercise_days_7d <= 2
    heavy_food_today = _has_heavy_food(plan, now_minute)
    late_meal = _has_late_meal(plan, now_minute)
    breakfast_skipped = now_minute >= 10 * 60 + 30 and not _has_breakfast(plan)
    lunch_skipped = now_minute >= 15 * 60 and not _has_lunch(plan)
    today_breakfast = _has_breakfast(plan)
    today_lunch = _has_lunch(plan)
    today_dinner = _has_dinner(plan)
    late_dinner = _has_late_dinner(plan, now_minute)
    late_dinner_walk = bool(late_dinner and _has_evening_walk(plan, now_minute))
    late_dinner_days_7d = _recent_late_dinner_days(history_plans, plan, now_minute=now_minute)
    frequent_late_dinner = late_dinner_days_7d >= 3
    late_dinner_penalty = (
        min(3.0, (late_dinner_days_7d - 1) * 0.8)
        if frequent_late_dinner
        else 0.0
    )
    meal_regular = bool(
        today_breakfast
        and today_lunch
        and today_dinner
        and not late_meal
        and now_minute >= _meal_end_minute(plan)
    )
    meal_regular_days_7d = _recent_meal_regular_days(history_plans, plan, now_minute=now_minute)
    weekly_meal_regular = meal_regular_days_7d >= 5
    weekly_meal_irregular = meal_regular_days_7d <= 2
    meal_time_irregular = _meal_time_irregular(history_plans, plan)
    lunch_skip_days_7d = _recent_lunch_skip_days(history_plans, plan, now_minute=now_minute)
    frequent_lunch_skip = lunch_skip_days_7d >= 3
    lunch_skip_penalty = (
        min(3.0, (lunch_skip_days_7d - 1) * 0.8)
        if frequent_lunch_skip
        else 0.0
    )
    breakfast_skip_days_7d = _recent_breakfast_skip_days(history_plans, plan, now_minute=now_minute)
    frequent_breakfast_skip = breakfast_skip_days_7d >= 3
    breakfast_skip_penalty = (
        min(3.0, (breakfast_skip_days_7d - 1) * 0.8)
        if frequent_breakfast_skip
        else 0.0
    )
    late_meal_days_7d = _recent_late_meal_days(history_plans, plan, now_minute=now_minute)
    frequent_late_meal = late_meal_days_7d >= 3
    late_meal_penalty = (
        min(3.0, (late_meal_days_7d - 1) * 0.8) if frequent_late_meal else 0.0
    )
    light_diet_today = _has_light_diet(plan, now_minute)
    light_diet_streak = _light_diet_streak(history_plans, plan, now_minute=now_minute)
    heavy_food_days_7d = _recent_heavy_food_days(history_plans, plan, now_minute=now_minute)
    frequent_heavy_food = heavy_food_days_7d >= 3
    stomach_discomfort = heavy_food_today
    heavy_food_penalty = (
        min(4.0, (heavy_food_days_7d - 1) * 1.0) if frequent_heavy_food else 0.0
    )
    raw_work_stress = 2 if 360 <= work_minutes < 480 else (4 if work_minutes >= 480 else 0)
    exercise_minutes = _activity_minutes(plan, now_minute, "exercise")
    rest_minutes = _activity_minutes(plan, now_minute, "rest")
    eye_strain = _recent_screen_time(furniture_states, current)
    audio_action = _recent_audio_action(furniture_states, current)
    audio_relax = bool(audio_action)
    chore_done = _recent_chore(furniture_states, current)
    energetic_music = audio_relax and any(
        word in audio_action
        for word in ("摇滚", "快歌", "舞曲", "电音", "嗨", "迪斯科")
    )
    stress_relief = (
        (1 if exercise_minutes >= 20 else 0)
        + (1 if rest_minutes >= 30 else 0)
        + (1 if social_today else 0)
        + (1 if eye_strain else 0)
        + (1 if audio_relax else 0)
        + (1 if instrument_practice else 0)
    )
    work_stress = max(0, raw_work_stress - stress_relief)
    lonely_work_penalty = 1 if lonely and raw_work_stress else 0
    work_stress = min(5, work_stress + lonely_work_penalty)
    overwork_days_7d = _recent_overwork_days(history_plans, plan, now_minute=now_minute)
    overwork = overwork_days_7d >= 3
    overwork_recent_14d = (
        _recent_overwork_days(history_plans, plan, days=14, now_minute=now_minute) > 0
    )
    days_since_overwork = _days_since_overwork(
        history_plans, plan, now_minute=now_minute
    )
    overwork_recovery = (
        overwork_recent_14d and overwork_days_7d == 0 and days_since_overwork >= 2
    )
    overwork_penalty = (
        min(5.0, (overwork_days_7d - 1) * 1.2) if overwork else 0.0
    )
    drinking_recovery = (
        _recent_alcohol_days(history_plans, plan, days=14, now_minute=now_minute) > 0
        and sober_days >= 3
    )
    late_caffeine = _late_caffeine(furniture_states, current)
    caffeine_crash = _caffeine_crash(furniture_states, current)
    temperature_swing = _temperature_swing(plan)
    harsh_room_temperature = bool(
        _weather_high_temp(plan, 20) >= 30
        or _weather_low_temp(plan, 20) <= 10
    )
    sunlight_minutes = _sunlight_minutes(plan, now_minute)
    sleep_regularity_minutes = _sleep_regularity_minutes(
        history_plans, plan, now_minute=now_minute
    )
    social_jetlag_minutes = _social_jetlag_minutes(
        history_plans, plan, now_minute=now_minute
    )
    late_night_streak = _late_night_streak(history_plans, plan, now_minute=now_minute)
    recent_late_nights = _recent_late_nights(
        history_plans, plan, now_minute=now_minute
    )
    recent_sun_days = _recent_sun_days(history_plans, plan, now_minute=now_minute)
    immunity_score = max(
        0,
        max(0, recent_late_nights - recent_sun_days)
        + alcohol_days_7d
        + (1 if overwork else 0)
        - (1 if socially_satisfied else 0),
    )
    sleep_irregular_penalty = (
        min(6.0, (sleep_regularity_minutes - 90) * 0.04)
        if sleep_regularity_minutes >= 90
        else 0.0
    )
    late_night_penalty = (
        min(5.0, (late_night_streak - 1) * 1.5)
        if late_night_streak >= 2
        else 0.0
    )
    social_jetlag_penalty = (
        min(5.0, (social_jetlag_minutes - 60) * 0.04)
        if social_jetlag_minutes >= 60
        else 0.0
    )
    temperature_penalty = (
        min(4.0, (temperature_swing - 8) * 0.5)
        if temperature_swing >= 10
        else 0.0
    )
    if weak_constitution:
        temperature_penalty *= 1.5
    debt_minutes = _sleep_debt(history_plans, plan, now=current)
    sleep_window = _main_sleep_window(plan)
    weekend_catchup = bool(
        weekend
        and sleep_window is not None
        and sleep_window[1] - sleep_window[0] >= 480
    )
    weekend_social_bonus = bool(weekend and social_today)
    weekend_outdoor_bonus = bool(
        weekend and sunlight_minutes >= 20 and not weather_bad
    )
    if weekend_catchup:
        debt_minutes = max(0, debt_minutes - 10)
    if late_caffeine:
        debt_minutes = min(300, debt_minutes + 30)
    if frequent_drinking:
        debt_minutes = min(300, debt_minutes + 30)
    if overwork:
        debt_minutes = min(300, debt_minutes + 20)
    energy = 44.0 - min(25.0, debt_minutes * 0.08)
    if late_night_streak >= 2:
        energy -= min(5.0, (late_night_streak - 1) * 1.5)
    satiety = 58.0
    hygiene = 72.0
    mood = float(_mood_base(plan, history_plans)) - min(12.0, debt_minutes * 0.03)
    if rainy_streak >= 2:
        mood -= min(8.0, rainy_streak * 1.5)
    if sunny_streak >= 2:
        mood += min(4.0, (sunny_streak - 1) * 0.8)
    if season == "winter":
        mood -= 2.0
    elif season == "summer":
        mood += 1.0
    if lonely:
        mood -= min(6.0, (days_since_social - 1) * 1.5)
    if chronic_lonely:
        mood -= min(4.0, (days_since_social - 4) * 1.0)
    if socially_satisfied:
        mood += 1.0
    if deep_social_today:
        mood += 1.0
    if hugged_today:
        mood += 1.0
        debt_minutes = max(0, debt_minutes - 5)
    if hug_afterglow:
        mood += 1.0
    if deep_social_afterglow:
        mood += 1.0
    if social_exhaustion:
        energy -= 1.0
        mood += 0.5
        debt_minutes += 5
    if social_hangover_yesterday:
        energy -= 1.0
        mood -= 0.5
    if social_today:
        mood += 2.0
    elif social_afterglow:
        mood += 1.0
    if hangover:
        mood -= 3.0 if hangover_severity == "severe" else 2.0
        energy -= 5.0 if hangover_severity == "severe" else 3.0
    if tipsy:
        mood += 2.0
    if drinking_recovery:
        mood += min(3.0, (sober_days - 2) * 0.8)
    if work_stress:
        mood -= work_stress
        energy -= work_stress * 0.8
    if overwork_recovery:
        mood += 1.5
    if caffeine_crash:
        energy -= 3.0
        mood -= 1.0
    if eye_strain:
        energy -= 2.0
        mood += 1.0
        debt_minutes += 10
    if sunburn:
        debt_minutes += 10
    audio_sleep_relief = (
        audio_relax and not eye_strain and not energetic_music
    )
    energetic_music_sleep = (
        audio_relax and energetic_music and not eye_strain
    )
    if audio_sleep_relief:
        debt_minutes = max(0, debt_minutes - 5)
        mood += 0.5
    if energetic_music_sleep:
        debt_minutes += 5
        mood += 1.0
    if late_meal:
        energy -= 0.5
        mood -= 0.5
    if breakfast_skipped:
        energy -= 2.0
        mood -= 0.5
    if lunch_skipped:
        energy -= 1.5
        mood -= 0.5
    if meal_regular:
        mood += 0.5
    if weekend and work_minutes == 0:
        mood += 1.0
    if weekend and work_minutes > 0:
        mood -= 1.0
    if good_sleep_streak:
        mood += 1.0
    if weekend_social_bonus:
        mood += 1.0
    if weekend_outdoor_bonus:
        mood += 0.5
    if monday_blues:
        mood -= 0.5
    if monday_blues and socially_satisfied:
        mood += 0.5
    if weekend_catchup:
        mood += 0.5
    if late_dinner:
        mood -= 0.5
    if late_dinner_walk:
        mood += 0.5
        debt_minutes = max(0, debt_minutes - 5)
    if meal_time_irregular:
        mood -= 0.5
    if afternoon_dip:
        energy -= 1.0
        mood -= 0.5
    if evening_sleepiness:
        energy -= 1.0
        mood -= 0.5
    if commute_fatigue:
        energy -= min(3.0, (transit_minutes - 60) / 60.0 * 1.5)
        mood -= 0.5
    if stiff_neck:
        energy -= 1.0
        mood -= 0.5
        debt_minutes += 5
    if overtraining:
        energy -= 2.0
        mood -= 0.5
    if pollen_allergy:
        energy -= 1.0
        mood -= 0.5
        debt_minutes += 5
    if stiff_neck_yesterday:
        energy -= 1.0
        mood -= 0.5
    if bad_weather_commute:
        energy -= 0.5
        mood -= 0.5
    if nap_inertia:
        energy -= 1.0
        mood -= 0.5
    if harsh_room_temperature:
        energy -= 0.5
        mood -= 0.5
    if chore_done:
        energy -= 1.0
        mood += 0.5
    if instrument_practice:
        energy -= 1.0
        mood += 1.0
    if morning_coffee:
        energy += 2.0
        mood += 0.5
    if coffee_with_breakfast:
        mood += 0.5
    if coffee_empty_stomach:
        mood -= 0.5
    if popcorn_snack:
        mood += 0.5
        satiety = _clamp(satiety + 2.0)
    if movie_night:
        mood += 0.5
    if late_movie:
        debt_minutes += 5
    if late_movie_yesterday:
        energy -= 1.0
        debt_minutes += 5
    if movie_brush_relief:
        mood += 0.5
    if reading_relax:
        energy -= 0.5
        mood += 0.8
        debt_minutes = max(0, debt_minutes - 5)
    if reading_fatigue:
        energy -= 1.0
        mood -= 0.5
    if home_cooked:
        energy -= 1.0
        mood += 1.0
        satiety = _clamp(satiety + 3.0)
    if baking_today:
        energy -= 0.5
        mood += 1.0
        satiety = _clamp(satiety + 2.0)
    if late_baking:
        debt_minutes += 5
        if brushed_teeth:
            mood += 0.5
        else:
            mood -= 0.5
    if tooth_sensitivity:
        mood -= 0.5
    if brushed_twice:
        mood += 0.5
    if reading_audio_cozy:
        mood += 0.5
    if reading_audio_distracted:
        mood -= 0.5
    if sunburn:
        energy -= 1.0
        mood -= 1.0
    if sunburn_aftermath:
        energy -= 1.0
        mood -= 0.5
        debt_minutes += 5
    morning_grogginess = bool(
        6 * 60 <= now_minute < 9 * 60
        and current_activity_kind != "sleep"
        and debt_minutes >= 120
    )
    if morning_grogginess:
        energy -= 1.0
        mood -= 0.5
    if stomach_discomfort:
        energy -= 0.5 if light_diet_today else 1.0
        mood -= 0.5 if light_diet_today else 1.0
    if muscle_soreness:
        if regular_exercise:
            energy -= 1.0
        elif restart_soreness:
            energy -= 3.0
            mood -= 1.5
        else:
            energy -= 2.0
            mood -= 1.0
    if overtraining_yesterday:
        energy -= 1.0
        mood -= 0.5
    if regular_exercise:
        energy += 2.0
        mood += 0.5
    if sedentary_week:
        energy -= 1.0
        mood -= 0.5
    if sleep_regularity_minutes >= 90:
        mood -= min(5.0, (sleep_regularity_minutes - 90) * 0.035)
    if social_jetlag_minutes >= 60:
        mood -= min(4.0, (social_jetlag_minutes - 60) * 0.03)
    if late_night_streak >= 2:
        mood -= min(4.0, late_night_streak * 1.2)
    if sunlight_minutes >= 20:
        mood += min(4.0, sunlight_minutes * 0.03)
    historical_mood = _history_mood_average(history_plans, plan)
    low_mood_streak = _low_mood_streak(history_plans, plan)
    sleeping_now = False
    last_meal_minute = -999
    last_bath_minute = -999

    items = sorted(
        _timeline(plan),
        key=lambda item: (_minute(_item_get(item, "start")), _minute(_item_get(item, "end"))),
    )
    for item in items:
        start = _minute(_item_get(item, "start"))
        end = _minute(_item_get(item, "end"))
        if end <= start or start >= now_minute:
            continue
        active_end = min(end, now_minute)
        duration = max(0, active_end - start)
        if duration <= 0:
            continue
        activity = str(_item_get(item, "activity", "") or "")
        state = str(_item_get(item, "state", "") or "")
        kind = _activity_kind(activity, state)
        baseline = RATES["sleep" if kind == "sleep" else "awake"]
        energy += baseline["energy"] * duration
        satiety += baseline["satiety"] * duration
        hygiene += baseline["hygiene"] * duration
        mood += baseline["mood"] * duration
        if kind == "sleep" and end > now_minute:
            sleeping_now = True
        if kind == "eat" and start - last_meal_minute >= 100:
            satiety += 18.0
            mood += 2.0
            last_meal_minute = start
        elif kind == "bath" and start - last_bath_minute >= 150:
            hygiene += 28.0
            mood += 2.0
            last_bath_minute = start
        elif kind == "exercise":
            energy -= 0.12 * duration
            hygiene -= 0.020 * duration
            mood += 0.050 * duration
        elif kind == "work":
            energy -= 0.020 * duration
            mood -= 0.008 * duration
        elif kind == "rest":
            energy += 0.020 * duration
            mood += 0.012 * duration
        elif kind == "social":
            mood += 0.020 * duration

    energy, satiety, hygiene, mood = _apply_furniture_effects(
        energy, satiety, hygiene, mood, furniture_states, current
    )
    recovery_actions = _recent_recovery_actions(furniture_states, current)
    harmful_actions = _recent_harmful_actions(furniture_states, current)
    rain_soaked = bool(
        weather_bad
        and weather_exposure_minutes >= 30
        and not (rain_gear or warm_clothing)
    )
    recovery_text = " ".join(recovery_actions)
    plan_recovery_text = _plan_recovery_text(plan, now_minute)
    recovery_all = f"{recovery_text} {plan_recovery_text}"
    eye_relief = bool(
        eye_strain
        and any(
            word in recovery_all
            for word in ("休息", "躺", "散步", "闭眼", "远眺")
        )
    )
    soreness_relief = bool(
        muscle_soreness
        and any(
            word in recovery_all
            for word in ("澡", "热敷", "热水澡", "热毛巾", "拉伸", "按摩", "休息", "躺")
        )
    )
    nap_relief = bool(
        nap_inertia
        and any(word in recovery_all for word in ("洗", "水", "茶"))
    )
    sunburn_relief = bool(
        sunburn
        and any(word in recovery_all for word in ("澡", "洗", "凉", "芦荟"))
    )
    reading_relief = bool(
        reading_fatigue
        and any(
            word in recovery_all
            for word in ("休息", "躺", "闭眼", "远眺", "睡")
        )
    )
    reading_tea_cozy = bool(
        reading_relax
        and any(
            word in recovery_all
            for word in ("茶", "热水", "热茶", "温水", "姜茶")
        )
    )
    stiff_relief = bool(
        (stiff_neck or stiff_neck_yesterday)
        and any(
            word in recovery_all
            for word in ("澡", "热敷", "热水澡", "热毛巾", "按摩", "拉伸")
        )
    )
    overtraining_relief = bool(
        overtraining
        and any(
            word in recovery_all
            for word in ("休息", "躺", "拉伸", "按摩", "澡")
        )
    )
    reading_aroma_cozy = bool(
        reading_relax and _recent_aroma(furniture_states, current)
    )
    cozy_triple = bool(
        reading_aroma_cozy
        and audio_relax
        and not energetic_music
        and reading_tea_cozy
    )
    solitude_relief = bool(
        social_exhaustion
        and any(
            word in recovery_all
            for word in ("休息", "躺", "安静", "独处", "听", "书")
        )
    )
    solitude_minutes = _recent_solitude_minutes(furniture_states, current)
    deep_solitude = bool(social_exhaustion and solitude_minutes >= 60)
    social_wind_down = bool(
        social_exhaustion
        and any(
            word in (recovery_text + " " + plan_recovery_text)
            for word in ("澡", "热茶", "音乐", "书", "呼吸", "冥想")
        )
    )
    pollen_relief = bool(
        pollen_allergy
        and any(word in recovery_all for word in ("洗", "澡", "水", "口罩"))
    )
    afternoon_nap_relief = bool(
        afternoon_dip and nap_minutes_today >= 20
    )
    afternoon_dip_relief = bool(
        afternoon_dip
        and (
            afternoon_nap_relief
            or any(
                word in (recovery_text + " " + plan_recovery_text)
                for word in ("茶", "咖啡", "水", "洗", "散步", "走动", "拉伸")
            )
        )
    )
    morning_grogginess_relief = bool(
        morning_grogginess
        and (
            _breakfast_eaten_by(plan, now_minute)
            or any(
                word in (recovery_text + " " + plan_recovery_text)
                for word in ("茶", "咖啡", "水", "洗", "早餐", "走动")
            )
        )
    )
    if eye_relief:
        energy += 1.0
        mood += 0.5
    if soreness_relief:
        energy += 1.0
        mood += 0.5
    if nap_relief:
        energy += 1.0
        mood += 0.5
    if sunburn_relief:
        energy += 1.0
        mood += 0.5
    if reading_relief:
        energy += 1.0
        mood += 0.5
    if reading_tea_cozy:
        mood += 0.5
    if stiff_relief:
        energy += 1.0
        mood += 0.5
    if overtraining_relief:
        energy += 1.0
        mood += 0.5
    if solitude_relief:
        energy += 1.0
        mood += 0.5
    if deep_solitude:
        energy += 1.0
        mood += 0.5
    if social_wind_down:
        mood += 0.5
        debt_minutes = max(0, debt_minutes - 5)
    if pollen_relief:
        mood += 0.5
    if afternoon_dip_relief:
        energy += 0.5
        mood += 0.5
    if morning_grogginess_relief:
        energy += 0.5
        mood += 0.5
    need_solitude = bool(social_exhaustion and not solitude_relief)
    if reading_aroma_cozy:
        mood += 0.5
    if cozy_triple:
        mood += 0.5
        debt_minutes = max(0, debt_minutes - 5)
    rain_relief = bool(
        rain_soaked
        and any(
            word in recovery_all
            for word in ("澡", "热水", "热茶", "姜茶", "汤")
        )
    )
    if rain_soaked:
        mood -= 2.0
    if rain_relief:
        mood += 1.0
        exposure_protection *= 0.7
    wet_clothes_penalty = 2.0 if rain_soaked and not rain_relief else 0.0
    hydration = _clamp(
        _apply_hydration_effects(
            _hydration_at(plan, now_minute),
            furniture_states,
            current,
        )
    )
    if hydration < 35:
        mood -= (35 - hydration) * 0.10
    if hydration < 25:
        energy -= (25 - hydration) * 0.15
    if heat_exposure_minutes:
        hydration = _clamp(
            hydration - min(15.0, heat_exposure_minutes * 0.1)
        )
    if popcorn_snack:
        hydration = _clamp(hydration - 4.0)
    dehydration_headache = hydration < 30
    body_odor = hygiene < (60 if exercise_minutes >= 30 else 55)
    body_odor_relief = bool(
        body_odor
        and _recent_fresh_clothes(
            furniture_states, plan, current, now_minute
        )
    )
    aroma_relax = _recent_aroma(furniture_states, current)
    if body_odor:
        mood -= 0.5
    if body_odor_relief:
        mood += 1.0
    if aroma_relax:
        mood += 0.5
        debt_minutes = max(0, debt_minutes - 5)
    if dehydration_headache:
        mood -= 1.5
        energy -= 1.0

    # Basic homeostatic mood pressure: being exhausted / hungry / grimy Grinds
    # mood down; a comfortable body slowly lifts it.
    if energy < 35:
        mood -= (35 - energy) * 0.22
    if satiety < 30:
        mood -= (30 - satiety) * 0.16
    if hygiene < 35:
        mood -= (35 - hygiene) * 0.12
    if energy >= 65 and satiety >= 50 and hygiene >= 55:
        mood += 2.0
    mood += (62 - mood) * 0.03

    energy = _clamp(energy)
    satiety = _clamp(satiety)
    hygiene = _clamp(hygiene)
    mood = _clamp(mood)
    if low_mood_streak >= 2:
        mood = _clamp(mood - min(8.0, low_mood_streak * 1.5))
    willingness = _clamp(
        0.45 * energy
        + 0.25 * mood
        + 0.20 * satiety
        + 0.10 * hygiene
        - min(18.0, debt_minutes * 0.04)
        - max(0, 30 - hydration) * 0.10
        - (3.0 if body_odor else 0.0)
        + (2.0 if body_odor_relief else 0.0)
    )
    hangover_relief = bool(
        hangover and hydration >= 50 and satiety >= 45
    )
    hangover_penalty = (
        1.0
        if hangover_relief
        else (4.0 if hangover_severity == "severe" else (2.0 if hangover else 0.0))
    )
    drinking_penalty = (
        min(5.0, (alcohol_days_7d - 1) * 1.2) if frequent_drinking else 0.0
    )
    if hangover_relief:
        mood = _clamp(mood + 1.0)
    health = _clamp(
        100.0
        - min(45.0, debt_minutes * 0.15)
        - max(0, 45 - energy) * 0.30
        - max(0, 35 - satiety) * 0.22
        - max(0, 35 - hygiene) * 0.18
        - max(0, 35 - hydration) * 0.20
        - hangover_penalty
        - drinking_penalty
        - overwork_penalty
        - wet_clothes_penalty
        - heat_penalty
        - (1.0 if sunburn_repeat else 0.0)
        - heavy_food_penalty
        - late_meal_penalty
        - breakfast_skip_penalty
        - lunch_skip_penalty
        - late_dinner_penalty
        - (1.0 if meal_time_irregular else 0.0)
        - commute_penalty
        - max(0, 45 - mood) * 0.20
        - min(12.0, low_mood_streak * 2.5)
        - (min(10.0, max(0, recent_illness_days) * 0.6) if weak_constitution else 0.0)
        - min(
            8.0,
            weather_exposure_minutes
            * 0.08
            * (1.5 if weak_constitution else 1.0)
            * exposure_protection,
        )
        - temperature_penalty
        - sleep_irregular_penalty
        + (1.0 if meal_regular else 0.0)
        + (1.0 if home_cooked and not heavy_food_today else 0.0)
        + (1.0 if weekly_home_cooked else 0.0)
        - (1.0 if frequent_baking else 0.0)
        - (1.0 if frequent_overtraining else 0.0)
        - (1.0 if frequent_tooth_neglect else 0.0)
        + (1.0 if weekly_brushing_regular else 0.0)
        + (1.0 if weekly_meal_regular else 0.0)
        - (1.0 if weekly_meal_irregular else 0.0)
        - social_jetlag_penalty
        - late_night_penalty
        + min(3.0, sunlight_minutes * 0.02)
    )
    lingering_illness = (
        health < 45 and debt_minutes >= 120 and low_mood_streak >= 2
    )
    low_immunity = (
        immunity_score >= 3
        or weak_constitution
        or overwork
        or frequent_overtraining
    )
    weather_illness_risk = bool(
        low_immunity and weather_exposure_minutes >= 60 and health < 60
    )
    wet_clothes_illness = bool(
        rain_soaked and not rain_relief and health < 60
    )
    heat_illness = bool(
        heat_exposure_minutes >= 90 and hydration < 35
    )
    sick = (
        health < 35
        or lingering_illness
        or weather_illness_risk
        or wet_clothes_illness
        or heat_illness
        or (low_immunity and health < 45 and debt_minutes >= 120)
    )
    sick_days = (low_mood_streak + 1) if sick else 0
    fever = bool(sick and (health < 30 or wet_clothes_illness))
    if fever:
        hydration = _clamp(hydration - 8)
    recovering = (
        not sick
        and health < 55
        and (low_mood_streak >= 2 or debt_minutes >= 120)
    )
    if sick:
        if health < 25 or debt_minutes >= 240 or energy < 20:
            illness_severity = "severe"
            illness_label = "病得比较重"
        elif health < 35:
            illness_severity = "moderate"
            illness_label = "生病中"
        else:
            illness_severity = "mild"
            illness_label = "有点不舒服"
    elif recovering:
        illness_severity = "recovering"
        illness_label = "恢复中"
    else:
        illness_severity = "healthy"
        illness_label = "健康"
    recovery_light_movement = _recovery_light_movement(
        recovering, exercise_minutes
    )
    if recovery_light_movement:
        energy += 0.5
        mood += 0.5
    appetite_low = bool((sick or recovering) and (fever or health < 55))
    appetite_penalty = 0
    if appetite_low:
        if light_diet_streak >= 2:
            appetite_penalty = 2
        elif light_diet_today:
            appetite_penalty = 4
        else:
            appetite_penalty = 10
        satiety = _clamp(satiety - appetite_penalty)
        if satiety < 30:
            energy -= 2.0
    symptoms: list[str] = []
    if sick or recovering:
        if fever:
            symptoms.append("有点发烧")
        if debt_minutes >= 120:
            symptoms.append("睡不好、头有点沉")
        if satiety < 35:
            symptoms.append("没什么胃口")
        if hygiene < 45:
            symptoms.append("有点着凉")
        if energy < 25:
            symptoms.append("浑身没力气")
        if mood < 40:
            symptoms.append("提不起精神")
        if weather_exposure_minutes >= 30:
            symptoms.append("有点受凉、鼻塞")
        if temperature_swing >= 12:
            symptoms.append("嗓子有点疼")
        symptoms = symptoms[:3]
    labels = {
        "energy": _label("energy", energy),
        "satiety": _label("satiety", satiety),
        "hygiene": _label("hygiene", hygiene),
        "hydration": _label("hydration", hydration),
        "mood": _label("mood", mood),
        "willingness": _label("willingness", willingness),
        "health": _label("health", health),
    }
    summary = (
        f"精力 {energy}/100（{labels['energy']}），"
        f"饱腹 {satiety}/100（{labels['satiety']}），"
        f"清洁 {hygiene}/100（{labels['hygiene']}），"
        f"水分 {hydration}/100（{labels['hydration']}），"
        f"心情 {mood}/100（{labels['mood']}），"
        f"意愿 {willingness}/100（{labels['willingness']}），"
        f"健康 {health}/100（{labels['health']}）"
    )
    details = []
    if satiety < 35:
        details.append("肚子有点空")
    if energy < 40:
        details.append("身体有点乏")
    if hygiene < 40:
        details.append("想洗漱一下")
    if body_odor:
        details.append("身上有点味道，想洗个澡")
    if body_odor_relief:
        details.append("换了身干净衣服，身上清爽一点")
    if aroma_relax:
        details.append("卧室有淡淡香气，人放松一点")
        if body_odor:
            details.append("香薰盖住一点味道，但还是想洗澡")
    if hydration < 35:
        details.append("有点口渴")
    if dehydration_headache:
        details.append("水喝太少了，头有点疼")
    elif hydration < 20:
        details.append("嘴巴很干，得喝水")
    if mood < 40:
        details.append("情绪有点低")
    if rainy_streak >= 2:
        details.append(f"已经连着 {rainy_streak} 天坏天气，心情有点闷")
    if sunny_streak >= 3:
        details.append(f"已经连着 {sunny_streak} 天天气不错，心情也亮了一点")
    if season == "winter":
        details.append("冬天日照短，情绪容易低一点")
    if lonely:
        if days_since_social >= 99:
            details.append("很久没和人好好说话了，有点闷")
        else:
            details.append(f"已经 {days_since_social} 天没怎么和人说话了，有点闷")
    if chronic_lonely:
        details.append("一个人待得有点久，情绪越来越闷")
    if socially_satisfied:
        details.append("最近和朋友见得挺多，心里踏实")
    if deep_social_today:
        details.append("和人聊了聊心事，心里轻一点")
    if hugged_today:
        details.append("今天被抱抱了，心里软软的")
        details.append("被抱抱后放松下来，晚上睡得踏实一点")
    if hug_afterglow:
        details.append("昨天被抱抱，今天想起来还开心")
    if deep_social_afterglow:
        details.append("昨天聊过心事，今天心里还暖")
    if social_exhaustion:
        details.append("聊了很久，有点累但心里松")
        details.append("聊得太兴奋，晚上有点难入睡")
        if deep_social_today:
            details.append("聊心事比普通聊天更耗神")
    if need_solitude:
        details.append("社交电量用完了，想一个人待会儿")
    if social_hangover_yesterday:
        details.append("昨天聊太久，今天还有点没缓过来")
    if solitude_relief:
        details.append("一个人安静待了会儿，缓过来一点")
    if deep_solitude:
        details.append("安静躺了一个多小时，缓过来不少")
    if social_wind_down:
        details.append("睡前洗了澡/听了会儿轻音乐，慢慢静下来")
    if pollen_relief:
        details.append("洗了把脸，鼻子舒服一点")
    if afternoon_nap_relief:
        details.append("午睡了一会儿，下午没那么困了")
    elif afternoon_dip_relief:
        details.append("缓了缓，没那么困了")
    if social_today:
        details.append("今天和人聊过天，心情松快一些")
    elif social_afterglow:
        details.append("昨天和人聊过天，今天心情还留着一点暖")
    if hangover:
        if hangover_relief:
            details.append("喝了水、吃了点东西，宿醉好受一些")
        elif hangover_severity == "severe":
            details.append("昨晚喝得有点多，今天头很沉")
        else:
            details.append("昨晚喝了点酒，今天有点没精神")
    if tipsy:
        details.append("有点微醺，话比平时多一点")
    if frequent_drinking:
        details.append(f"最近一周喝了 {alcohol_days_7d} 天酒，身体有点吃不消")
        if low_immunity:
            details.append("喝酒多，抵抗力也有点下降")
    if frequent_heavy_food:
        details.append(f"最近一周吃了 {heavy_food_days_7d} 天重口，肠胃有点累")
    if drinking_recovery:
        details.append(f"已经 {sober_days} 天没喝酒，精神和心情都在恢复")
    if work_stress >= 4:
        details.append("今天工作有点久，肩颈发紧，脑子也累了")
    elif work_stress >= 2:
        details.append("今天工作有点久，有点疲惫")
    if raw_work_stress and stress_relief:
        if social_today:
            details.append("下班后和人聊了聊，肩颈和心情都松了些")
        else:
            details.append("下班后活动或休息了一下，肩颈松了些")
    if lonely_work_penalty:
        details.append("工作很累，又没人说说话，心里更闷")
    if raw_work_stress and eye_strain:
        details.append("看了会儿轻松的内容，工作压力松了一点")
    if raw_work_stress and audio_relax:
        details.append("听了会儿音乐，心情松下来一点")
    if raw_work_stress and instrument_practice:
        details.append("弹了会儿琴，工作上的烦心事淡了点")
    if overwork:
        details.append(f"最近一周有 {overwork_days_7d} 天加班到很晚，身体有点透支")
        if low_immunity:
            details.append("长期加班，抵抗力也有点下降")
    if overwork_recovery:
        details.append(f"已经 {days_since_overwork} 天没怎么加班，身体缓过来一点")
    if late_caffeine:
        details.append("下午喝了咖啡，晚上可能睡不踏实")
    if caffeine_crash:
        details.append("咖啡劲过去了，有点犯困")
    if eye_strain:
        details.append("盯屏幕久了，眼睛有点酸")
        details.append("屏幕看久了，晚上可能睡得慢一点")
    if audio_sleep_relief:
        details.append("睡前听了会儿音乐，人放松一点")
    if energetic_music_sleep:
        details.append("睡前听了快歌，反而有点兴奋")
    if eye_relief:
        details.append("闭眼休息了一下，眼睛舒服一点")
    if stomach_discomfort:
        details.append("吃得太重口，胃里有点烧")
        if light_diet_today:
            details.append("喝了点清淡的，胃里好受一些")
    if late_meal:
        details.append("睡前吃夜宵，胃有点胀")
    if breakfast_skipped:
        details.append("没吃早饭，上午有点没力气")
    if lunch_skipped:
        details.append("没吃午饭，下午有点饿")
    if meal_regular:
        details.append("三餐都按时吃了，身体状态稳一点")
    if weekend and work_minutes == 0:
        details.append("周末没排工作，整个人松一点")
    if weekend_catchup:
        details.append("周末睡了个长觉，睡眠债还了一点")
    if good_sleep_streak:
        details.append("连续几天都睡得挺早，精神好一点")
    if weekend_social_bonus:
        details.append("周末和朋友聚了聚，心情特别好")
    if weekend_outdoor_bonus:
        details.append("周末出去晒了晒太阳，心情松一点")
    if monday_blues:
        details.append("周一又要上班，有点提不起劲")
    if monday_blues and socially_satisfied:
        details.append("有人陪着，周一也没那么难熬")
    if weekend and work_minutes > 0:
        details.append("周末还得工作，心里有点烦")
    if late_dinner:
        details.append("晚饭吃得太晚，胃还没消化")
    if meal_time_irregular:
        details.append("最近吃饭时间忽早忽晚，肠胃有点不适应")
        details.append("饭点太乱，晚上也睡不踏实")
    if late_dinner_walk:
        details.append("饭后走了走，胃里舒服一点")
    if frequent_late_dinner:
        details.append(f"最近一周有 {late_dinner_days_7d} 天晚饭吃很晚，肠胃有点累")
    if weekly_meal_regular:
        details.append("最近一周三餐挺规律，身体状态稳")
    if weekly_meal_irregular:
        details.append("最近一周吃饭不太规律，身体有点虚")
    if frequent_lunch_skip:
        details.append(f"最近一周有 {lunch_skip_days_7d} 天没吃午饭，下午总有点虚")
    if commute_fatigue:
        details.append(f"今天通勤约 {transit_minutes} 分钟，路上有点累")
    if afternoon_dip:
        details.append("午后有点犯困，效率不太高")
    if evening_sleepiness:
        details.append("这个点有点困了，想早点睡")
    if morning_grogginess:
        details.append("昨晚没睡够，早上有点懵")
    if morning_grogginess_relief:
        details.append("缓了缓，清醒一点")
    if stiff_neck:
        details.append("坐了太久没活动，肩颈有点发僵")
        details.append("肩颈发僵，晚上可能睡不安稳")
    if overtraining:
        details.append("今天运动量有点大，肌肉有点发酸")
    if pollen_allergy:
        details.append("春天花粉多，鼻子有点痒")
        details.append("鼻子痒，晚上可能睡不踏实")
    if frequent_overtraining:
        details.append(f"最近一周有 {overtraining_days_7d} 天运动过量，身体有点吃不消")
    if stiff_neck_yesterday:
        details.append("昨天久坐没活动，今天肩颈还紧")
    if bad_weather_commute:
        details.append("下雨天通勤更折腾，鞋也有点湿")
    if nap_inertia:
        details.append("午睡睡太久，起来有点懵")
    if sunburn:
        details.append("肩膀被晒得有点红，碰着疼")
    if sunburn_repeat:
        details.append("连着两天晒伤，皮肤更疼了")
    if sunburn_aftermath:
        details.append("昨天晒伤的地方今天还红着")
        details.append("晒伤还没退，衣服蹭着有点不舒服")
    if sunburn_relief:
        details.append("冲了个凉，晒伤的地方舒服一点")
    if nap_relief:
        details.append("洗了把脸喝了口水，人清醒一点")
    if frequent_long_commute:
        details.append(f"最近一周有 {long_commute_days_7d} 天通勤很久，身体有点疲")
    if frequent_breakfast_skip:
        details.append(f"最近一周有 {breakfast_skip_days_7d} 天没吃早饭，上午总有点虚")
    if frequent_late_meal:
        details.append(f"最近一周吃了 {late_meal_days_7d} 天夜宵，肠胃和睡眠都受影响")
    if muscle_soreness:
        details.append("昨天运动完，今天腿有点酸")
        if restart_soreness:
            details.append("太久没运动，这一练酸得有点厉害")
        if regular_exercise:
            details.append("最近有规律运动，酸痛轻一点")
        if soreness_relief:
            details.append("泡了热水澡/拉伸了一下，腿没那么酸")
    if overtraining_yesterday:
        details.append("昨天练得太狠，今天浑身发酸")
    elif regular_exercise:
        details.append("最近有规律运动，体力好一些")
    if sedentary_week:
        details.append("最近一周都没怎么运动，身体有点发懒")
    if low_mood_streak >= 2:
        details.append(f"最近连续 {low_mood_streak} 天情绪偏低")
    elif historical_mood is not None and historical_mood < 48 and mood < 60:
        details.append("最近心情一直不太高")
    if willingness < 30:
        details.append("提不起劲，不太想出门或做费力的事")
    if health < 55:
        details.append("身体有点不舒服")
    if weak_constitution:
        details.append("最近反复生病，身体底子偏虚")
    if weather_bad and weather_exposure_minutes >= 30:
        details.append(
            f"在坏天气里待了约 {weather_exposure_minutes} 分钟，有点受凉"
        )
        if rain_gear or warm_clothing:
            details.append("还好带了伞或穿了外套，受凉轻一些")
    if rain_soaked:
        details.append("淋了雨，衣服有点湿，心情也down了一点")
    if wet_clothes_penalty:
        details.append("湿衣服还没换，身上有点发冷")
    if rain_relief:
        details.append("洗了热水澡/喝了热茶，暖和过来了")
    if sunlight_minutes >= 30:
        details.append(f"今天晒了约 {sunlight_minutes} 分钟太阳，心情松快一些")
    if temperature_swing >= 10:
        details.append(f"今天温差约 {temperature_swing} 度，嗓子有点干")
    if harsh_room_temperature:
        details.append("晚上温度不太舒服，睡得不沉")
    if chore_done:
        details.append("做了点家务，有点累但看着清爽")
    if instrument_practice:
        details.append("弹了会儿琴，心情好一点")
    if morning_coffee:
        details.append("早上喝了杯咖啡，人清醒一点")
    if coffee_with_breakfast:
        details.append("咖啡配早餐，胃里舒服一点")
    if coffee_empty_stomach:
        details.append("空腹喝咖啡，胃有点不舒服")
    if popcorn_snack:
        details.append("弄了点爆米花，像在家里看电影")
        details.append("爆米花有点咸，嘴里发渴")
    if movie_night:
        details.append("边吃爆米花边看电影，很放松")
    if late_movie:
        details.append("电影看得有点晚，睡意被拖后了")
    if movie_brush_relief:
        details.append("看完电影刷了牙，清爽去睡")
    if late_movie_yesterday:
        details.append("昨晚电影看太晚，今天有点困")
    if reading_relax:
        details.append("看了会儿书，心静下来一点")
    if reading_fatigue:
        details.append("看书看太久，眼睛有点酸")
    if home_cooked:
        details.append("自己做了顿饭，挺有成就感")
        if not heavy_food_today:
            details.append("自己做饭，油盐比外卖可控一些")
    if baking_today:
        details.append("烤了点甜点，满屋香味")
    if late_baking:
        details.append("晚上吃甜点，血糖有点起伏")
        if brushed_teeth:
            details.append("刷了牙，嘴里清爽一点")
        else:
            details.append("吃完甜点没刷牙，嘴里有点黏")
    if tooth_sensitivity:
        details.append("甜食吃多了，牙有点酸")
    if brushed_twice:
        details.append("早晚都刷了牙，嘴里清爽")
    if frequent_tooth_neglect:
        details.append(f"最近一周有 {tooth_neglect_days_7d} 天吃甜食没刷牙，牙齿有点吃不消")
    if weekly_brushing_regular:
        details.append("最近一周刷牙挺规律，牙齿状态稳一点")
    if frequent_baking:
        details.append(f"最近一周做了 {baking_days_7d} 次甜点，糖分有点多")
    if weekly_home_cooked:
        details.append("最近一周常自己做饭，吃得比外卖健康")
    if reading_relief:
        details.append("合上书闭眼歇了会儿，眼睛舒服一点")
    if reading_audio_cozy:
        details.append("边看书边听轻音乐，很放松")
    if reading_audio_distracted:
        details.append("快歌有点分心，书没看进去")
    if reading_tea_cozy:
        details.append("边看书边喝点热饮，很惬意")
    if stiff_relief:
        details.append("缓了缓，肩颈松一点")
    if overtraining_relief:
        details.append("练完拉伸/休息了一下，肌肉没那么紧")
    if reading_aroma_cozy:
        details.append("香薰配着书，很舒服")
    if cozy_triple:
        details.append("香薰、轻音乐和热饮，整个人都松下来")
        details.append("这套组合太舒服，睡意来得更快")
    if heat_exposure_minutes >= 30:
        details.append(f"太阳有点毒，晒了约 {heat_exposure_minutes} 分钟，头有点晕")
    if sleep_regularity_minutes >= 120:
        details.append(f"最近作息有点乱，睡眠时间前后差了 {sleep_regularity_minutes // 60} 小时多")
    if social_jetlag_minutes >= 90:
        details.append(f"周末和工作日起居差了 {social_jetlag_minutes // 60} 小时多，像在倒时差")
    if late_night_streak >= 3:
        details.append(f"已经连续 {late_night_streak} 天凌晨才睡，抵抗力有点差")
    elif recent_late_nights >= 3:
        details.append("最近熬夜有点多，抵抗力还没完全恢复")
    if recent_sun_days and recent_late_nights >= 3 and not low_immunity:
        details.append("最近晒了太阳，抵抗力在慢慢恢复")
    elif low_immunity and not sick and not frequent_drinking and not overwork:
        details.append("最近抵抗力有点差，别着凉")
    if frequent_overtraining:
        details.append("最近练太猛，抵抗力有点下降")
    if socially_satisfied and immunity_score <= 1:
        details.append("最近有人陪着说说话，抵抗力稳一点")
    if weather_illness_risk:
        details.append("在坏天气里冻着了，抵抗力没扛住")
    if appetite_low:
        details.append("没什么胃口，吃几口就饱了")
        if light_diet_streak >= 2:
            details.append("连续吃了几天清淡的，胃口回来一点")
        elif light_diet_today:
            details.append("喝了点粥汤，胃口稍微好一点")
    if recovery_light_movement:
        details.append("恢复期出去走了走，身体松一点")
    if wet_clothes_illness:
        details.append("湿衣服穿久了，真的着凉了")
    if heat_illness:
        details.append("晒太久又没喝水，有点中暑了")
    if sick and health < 30:
        details.append("额头有点烫，可能发烧了")
        details.append("发烧让水分掉得快，得多喝水")
    if health < 35:
        details.append("今天最好多休息")
    if sick:
        details.append(
            "还没完全恢复，需要继续休息"
            if health >= 35
            else "生病了，需要好好休息"
        )
    elif recovering:
        details.append("还在恢复期，别太累")
    if symptoms:
        details.append("症状：" + "、".join(symptoms))
    if sleeping_now:
        details.append("正在睡觉")
    if debt_minutes >= 45:
        details.append(f"带着约 {debt_minutes // 60} 小时睡眠债")
    discomfort_count = sum(
        1
        for flag in (
            eye_strain and not eye_relief,
            muscle_soreness and not soreness_relief,
            nap_inertia and not nap_relief,
            stomach_discomfort,
            late_meal,
            breakfast_skipped,
            lunch_skipped,
            commute_fatigue,
            bad_weather_commute,
            dehydration_headache,
            body_odor,
            stiff_neck and not stiff_relief,
            overtraining,
            overtraining_yesterday,
            pollen_allergy,
            coffee_empty_stomach,
            sunburn,
            sunburn_aftermath,
            sunburn_repeat,
            reading_fatigue and not reading_relief,
            tooth_sensitivity,
            frequent_breakfast_skip,
            frequent_late_meal,
            frequent_long_commute,
        )
        if flag
    )
    return {
        "energy": energy,
        "discomfort_count": discomfort_count,
        "satiety": satiety,
        "hygiene": hygiene,
        "hydration": hydration,
        "dehydration_headache": dehydration_headache,
        "body_odor": body_odor,
        "body_odor_relief": body_odor_relief,
        "aroma_relax": aroma_relax,
        "mood": mood,
        "willingness": willingness,
        "health": health,
        "sick": sick,
        "sick_days": sick_days,
        "recovering": recovering,
        "recovery_light_movement": recovery_light_movement,
        "illness_severity": illness_severity,
        "illness_label": illness_label,
        "appetite_low": appetite_low,
        "appetite_penalty": appetite_penalty,
        "symptoms": symptoms,
        "fever": fever,
        "recovery_actions": recovery_actions,
        "harmful_actions": harmful_actions,
        "recent_illness_days": recent_illness_days,
        "weak_constitution": weak_constitution,
        "weather_bad": weather_bad,
        "weather_exposure_minutes": weather_exposure_minutes,
        "warm_clothing": warm_clothing,
        "rain_gear": rain_gear,
        "heat_exposure_minutes": heat_exposure_minutes,
        "sunburn": sunburn,
        "sunburn_repeat": sunburn_repeat,
        "sunburn_aftermath": sunburn_aftermath,
        "sunburn_relief": sunburn_relief,
        "rain_soaked": rain_soaked,
        "rain_relief": rain_relief,
        "wet_clothes_penalty": wet_clothes_penalty,
        "wet_clothes_illness": wet_clothes_illness,
        "heat_illness": heat_illness,
        "rainy_streak": rainy_streak,
        "sunny_streak": sunny_streak,
        "season": season,
        "days_since_social": days_since_social,
        "social_days_7d": social_days_7d,
        "socially_satisfied": socially_satisfied,
        "deep_social_today": deep_social_today,
        "hugged_today": hugged_today,
        "hug_afterglow": hug_afterglow,
        "deep_social_afterglow": deep_social_afterglow,
        "social_minutes": social_minutes,
        "social_exhaustion": social_exhaustion,
        "social_exhaustion_threshold": social_exhaustion_threshold,
        "need_solitude": need_solitude,
        "yesterday_social_minutes": yesterday_social_minutes,
        "social_hangover_yesterday": social_hangover_yesterday,
        "solitude_relief": solitude_relief,
        "solitude_minutes": solitude_minutes,
        "deep_solitude": deep_solitude,
        "social_wind_down": social_wind_down,
        "lonely": lonely,
        "chronic_lonely": chronic_lonely,
        "social_today": social_today,
        "social_afterglow": social_afterglow,
        "hangover": hangover,
        "hangover_severity": hangover_severity,
        "alcohol_today": alcohol_today,
        "tipsy": tipsy,
        "alcohol_days_7d": alcohol_days_7d,
        "frequent_drinking": frequent_drinking,
        "sober_days": sober_days,
        "drinking_recovery": drinking_recovery,
        "work_minutes": work_minutes,
        "heavy_food_today": heavy_food_today,
        "heavy_food_days_7d": heavy_food_days_7d,
        "frequent_heavy_food": frequent_heavy_food,
        "stomach_discomfort": stomach_discomfort,
        "late_meal": late_meal,
        "breakfast_skipped": breakfast_skipped,
        "lunch_skipped": lunch_skipped,
        "lunch_skip_days_7d": lunch_skip_days_7d,
        "frequent_lunch_skip": frequent_lunch_skip,
        "meal_regular": meal_regular,
        "late_dinner": late_dinner,
        "late_dinner_walk": late_dinner_walk,
        "late_dinner_days_7d": late_dinner_days_7d,
        "frequent_late_dinner": frequent_late_dinner,
        "meal_regular_days_7d": meal_regular_days_7d,
        "weekly_meal_regular": weekly_meal_regular,
        "weekly_meal_irregular": weekly_meal_irregular,
        "meal_time_irregular": meal_time_irregular,
        "transit_minutes": transit_minutes,
        "commute_fatigue": commute_fatigue,
        "afternoon_dip": afternoon_dip,
        "evening_sleepiness": evening_sleepiness,
        "morning_grogginess": morning_grogginess,
        "morning_grogginess_relief": morning_grogginess_relief,
        "afternoon_dip_relief": afternoon_dip_relief,
        "afternoon_nap_relief": afternoon_nap_relief,
        "stiff_neck": stiff_neck,
        "overtraining": overtraining,
        "pollen_allergy": pollen_allergy,
        "pollen_relief": pollen_relief,
        "overtraining_yesterday": overtraining_yesterday,
        "frequent_overtraining": frequent_overtraining,
        "overtraining_days_7d": overtraining_days_7d,
        "stiff_neck_yesterday": stiff_neck_yesterday,
        "stiff_relief": stiff_relief,
        "overtraining_relief": overtraining_relief,
        "weekend": weekend,
        "weekend_catchup": weekend_catchup,
        "good_sleep_streak": good_sleep_streak,
        "weekend_social_bonus": weekend_social_bonus,
        "weekend_outdoor_bonus": weekend_outdoor_bonus,
        "weekday": weekday,
        "monday_blues": monday_blues,
        "good_sleep_days_7d": good_sleep_days_7d,
        "bad_weather_commute": bad_weather_commute,
        "nap_minutes_today": nap_minutes_today,
        "nap_inertia": nap_inertia,
        "nap_relief": nap_relief,
        "long_commute_days_7d": long_commute_days_7d,
        "frequent_long_commute": frequent_long_commute,
        "breakfast_skip_days_7d": breakfast_skip_days_7d,
        "frequent_breakfast_skip": frequent_breakfast_skip,
        "late_meal_days_7d": late_meal_days_7d,
        "frequent_late_meal": frequent_late_meal,
        "light_diet_today": light_diet_today,
        "light_diet_streak": light_diet_streak,
        "work_stress": work_stress,
        "exercise_minutes": exercise_minutes,
        "rest_minutes": rest_minutes,
        "overwork_days_7d": overwork_days_7d,
        "overwork": overwork,
        "overwork_recovery": overwork_recovery,
        "days_since_overwork": days_since_overwork,
        "hangover_relief": hangover_relief,
        "late_caffeine": late_caffeine,
        "caffeine_crash": caffeine_crash,
        "eye_strain": eye_strain,
        "audio_relax": audio_relax,
        "energetic_music": energetic_music,
        "audio_sleep_relief": audio_sleep_relief,
        "energetic_music_sleep": energetic_music_sleep,
        "eye_relief": eye_relief,
        "muscle_soreness": muscle_soreness,
        "exercise_days_7d": exercise_days_7d,
        "regular_exercise": regular_exercise,
        "sedentary_week": sedentary_week,
        "restart_soreness": restart_soreness,
        "soreness_relief": soreness_relief,
        "temperature_swing": temperature_swing,
        "harsh_room_temperature": harsh_room_temperature,
        "chore_done": chore_done,
        "instrument_practice": instrument_practice,
        "morning_coffee": morning_coffee,
        "coffee_with_breakfast": coffee_with_breakfast,
        "coffee_empty_stomach": coffee_empty_stomach,
        "popcorn_snack": popcorn_snack,
        "movie_night": movie_night,
        "late_movie": late_movie,
        "late_movie_yesterday": late_movie_yesterday,
        "movie_brush_relief": movie_brush_relief,
        "reading_minutes": reading_minutes,
        "cooking_minutes": cooking_minutes,
        "home_cooked": home_cooked,
        "baking_minutes": baking_minutes,
        "baking_today": baking_today,
        "late_baking": late_baking,
        "brushed_teeth": brushed_teeth,
        "brushed_twice": brushed_twice,
        "tooth_sensitivity": tooth_sensitivity,
        "baking_days_7d": baking_days_7d,
        "frequent_baking": frequent_baking,
        "tooth_neglect_days_7d": tooth_neglect_days_7d,
        "frequent_tooth_neglect": frequent_tooth_neglect,
        "brushing_days_7d": brushing_days_7d,
        "weekly_brushing_regular": weekly_brushing_regular,
        "home_cooked_days_7d": home_cooked_days_7d,
        "weekly_home_cooked": weekly_home_cooked,
        "reading_relax": reading_relax,
        "reading_fatigue": reading_fatigue,
        "reading_relief": reading_relief,
        "reading_audio_cozy": reading_audio_cozy,
        "reading_audio_distracted": reading_audio_distracted,
        "reading_tea_cozy": reading_tea_cozy,
        "reading_aroma_cozy": reading_aroma_cozy,
        "cozy_triple": cozy_triple,
        "sunlight_minutes": sunlight_minutes,
        "sleep_regularity_minutes": sleep_regularity_minutes,
        "social_jetlag_minutes": social_jetlag_minutes,
        "late_night_streak": late_night_streak,
        "recent_late_nights": recent_late_nights,
        "recent_sun_days": recent_sun_days,
        "immunity_score": immunity_score,
        "low_immunity": low_immunity,
        "weather_illness_risk": weather_illness_risk,
        "labels": labels,
        "summary": summary
        + (f"；睡眠债约 {debt_minutes // 60} 小时" if debt_minutes >= 60 else "")
        + (
            ("；生病中" if sick else ("；恢复期" if recovering else ""))
        )
        + (("；症状：" + "、".join(symptoms)) if symptoms else "")
        + (
            "；有点口渴"
            if hydration < 35
            else ""
        )
        + (
            "；水喝太少了，头有点疼"
            if dehydration_headache
            else ""
        )
        + (
            "；嘴巴很干，得喝水"
            if hydration < 20 and not dehydration_headache
            else ""
        )
        + ("；身上有点味道，想洗个澡" if body_odor else "")
        + ("；换了身干净衣服，身上清爽一点" if body_odor_relief else "")
        + ("；卧室有淡淡香气，人放松一点" if aroma_relax else "")
        + (
            "；香薰盖住一点味道，但还是想洗澡"
            if aroma_relax and body_odor
            else ""
        )
        + (
            "；太阳有点毒，晒得头有点晕"
            if heat_exposure_minutes >= 30
            else ""
        )
        + (
            "；晚上温度不太舒服，睡得不沉"
            if harsh_room_temperature
            else ""
        )
        + ("；做了点家务，有点累但看着清爽" if chore_done else "")
        + ("；弹了会儿琴，心情好一点" if instrument_practice else "")
        + ("；早上喝了杯咖啡，人清醒一点" if morning_coffee else "")
        + ("；咖啡配早餐，胃里舒服一点" if coffee_with_breakfast else "")
        + ("；空腹喝咖啡，胃有点不舒服" if coffee_empty_stomach else "")
        + ("；弄了点爆米花，像在家里看电影" if popcorn_snack else "")
        + ("；边吃爆米花边看电影，很放松" if movie_night else "")
        + ("；电影看得有点晚，睡意被拖后了" if late_movie else "")
        + ("；看完电影刷了牙，清爽去睡" if movie_brush_relief else "")
        + ("；看了会儿书，心静下来一点" if reading_relax else "")
        + ("；看书看太久，眼睛有点酸" if reading_fatigue else "")
        + ("；自己做了顿饭，挺有成就感" if home_cooked else "")
        + ("；烤了点甜点，满屋香味" if baking_today else "")
        + ("；晚上吃甜点，血糖有点起伏" if late_baking else "")
        + (
            "；刷了牙，嘴里清爽一点"
            if late_baking and brushed_teeth
            else ("；吃完甜点没刷牙，嘴里有点黏" if late_baking else "")
        )
        + (
            f"；最近一周做了 {baking_days_7d} 次甜点，糖分有点多"
            if frequent_baking
            else ""
        )
        + (
            f"；最近一周有 {tooth_neglect_days_7d} 天吃甜食没刷牙，牙齿有点吃不消"
            if frequent_tooth_neglect
            else ""
        )
        + ("；最近一周刷牙挺规律，牙齿状态稳一点" if weekly_brushing_regular else "")
        + ("；最近一周常自己做饭，吃得比外卖健康" if weekly_home_cooked else "")
        + (
            "；自己做饭，油盐比外卖可控一些"
            if home_cooked and not heavy_food_today
            else ""
        )
        + ("；合上书闭眼歇了会儿，眼睛舒服一点" if reading_relief else "")
        + ("；边看书边听轻音乐，很放松" if reading_audio_cozy else "")
        + ("；快歌有点分心，书没看进去" if reading_audio_distracted else "")
        + ("；边看书边喝点热饮，很惬意" if reading_tea_cozy else "")
        + ("；香薰配着书，很舒服" if reading_aroma_cozy else "")
        + ("；香薰、轻音乐和热饮，整个人都松下来" if cozy_triple else "")
        + ("；这套组合太舒服，睡意来得更快" if cozy_triple else "")
        + (
            "；在坏天气里待了较久，有点受凉"
            if weather_bad and weather_exposure_minutes >= 30
            else ""
        )
        + (
            "；没带伞，淋得有点狼狈"
            if weather_bad
            and weather_exposure_minutes >= 30
            and not (rain_gear or warm_clothing)
            else ""
        )
        + (
            "；还好带了伞或穿了外套"
            if weather_bad
            and weather_exposure_minutes >= 30
            and (rain_gear or warm_clothing)
            else ""
        )
        + ("；湿衣服还没换，身上有点发冷" if wet_clothes_penalty else "")
        + ("；洗了热水澡，暖和过来了" if rain_relief else "")
        + (
            f"；已经连着 {rainy_streak} 天坏天气"
            if rainy_streak >= 2
            else ""
        )
        + (
            f"；已经连着 {sunny_streak} 天天气不错"
            if sunny_streak >= 3
            else ""
        )
        + ("；冬天日照短，情绪容易低一点" if season == "winter" else "")
        + (
            "；很久没和人好好说话了，有点闷"
            if lonely and days_since_social >= 99
            else (
                f"；已经 {days_since_social} 天没怎么和人说话了，有点闷"
                if lonely
                else ""
            )
        )
        + ("；今天和人聊过天，心情松快一些" if social_today else "")
        + ("；昨天和人聊过天，今天心情还留着一点暖" if social_afterglow else "")
        + ("；一个人待得有点久，情绪越来越闷" if chronic_lonely else "")
        + ("；最近和朋友见得挺多，心里踏实" if socially_satisfied else "")
        + ("；和人聊了聊心事，心里轻一点" if deep_social_today else "")
        + ("；今天被抱抱了，心里软软的" if hugged_today else "")
        + ("；被抱抱后放松下来，晚上睡得踏实一点" if hugged_today else "")
        + ("；昨天被抱抱，今天想起来还开心" if hug_afterglow else "")
        + ("；昨天聊过心事，今天心里还暖" if deep_social_afterglow else "")
        + ("；聊了很久，有点累但心里松" if social_exhaustion else "")
        + ("；聊得太兴奋，晚上有点难入睡" if social_exhaustion else "")
        + ("；社交电量用完了，想一个人待会儿" if need_solitude else "")
        + ("；昨天聊太久，今天还有点没缓过来" if social_hangover_yesterday else "")
        + ("；一个人安静待了会儿，缓过来一点" if solitude_relief else "")
        + ("；安静躺了一个多小时，缓过来不少" if deep_solitude else "")
        + (
            "；睡前洗了澡/听了会儿轻音乐，慢慢静下来"
            if social_wind_down
            else ""
        )
        + (
            "；昨晚喝了酒，今天头有点沉"
            if hangover and not hangover_relief and hangover_severity != "severe"
            else ""
        )
        + (
            "；昨晚喝得有点多，今天头很沉"
            if hangover and not hangover_relief and hangover_severity == "severe"
            else ""
        )
        + ("；喝了水、吃了点东西，宿醉好受一些" if hangover_relief else "")
        + ("；下午喝了咖啡，晚上可能睡不踏实" if late_caffeine else "")
        + ("；咖啡劲过去了，有点犯困" if caffeine_crash else "")
        + ("；盯屏幕久了，眼睛有点酸" if eye_strain else "")
        + ("；屏幕看久了，晚上可能睡得慢一点" if eye_strain else "")
        + ("；睡前听了会儿音乐，人放松一点" if audio_sleep_relief else "")
        + ("；睡前听了快歌，反而有点兴奋" if energetic_music_sleep else "")
        + ("；闭眼休息了一下，眼睛舒服一点" if eye_relief else "")
        + ("；昨天运动完，今天腿有点酸" if muscle_soreness else "")
        + ("；太久没运动，这一练酸得有点厉害" if restart_soreness else "")
        + ("；最近有规律运动，酸痛轻一点" if muscle_soreness and regular_exercise else "")
        + ("；泡了热水澡/拉伸了一下，腿没那么酸" if soreness_relief else "")
        + ("；最近有规律运动，体力好一些" if regular_exercise and not muscle_soreness else "")
        + ("；最近一周都没怎么运动，身体有点发懒" if sedentary_week else "")
        + ("；发烧中，水分掉得快，要多喝水" if fever else "")
        + ("；没什么胃口，吃几口就饱了" if appetite_low else "")
        + (
            "；喝了点粥汤，胃口稍微好一点"
            if appetite_low and light_diet_today and light_diet_streak < 2
            else ""
        )
        + (
            "；恢复期出去走了走，身体松一点"
            if recovery_light_movement
            else ""
        )
        + ("；有点微醺，话比平时多一点" if tipsy else "")
        + (
            f"；最近一周喝了 {alcohol_days_7d} 天酒，身体有点吃不消"
            if frequent_drinking
            else ""
        )
        + (
            f"；最近一周吃了 {heavy_food_days_7d} 天重口，肠胃有点累"
            if frequent_heavy_food
            else ""
        )
        + ("；吃得太重口，胃里有点烧" if stomach_discomfort else "")
        + ("；睡前吃夜宵，胃有点胀" if late_meal else "")
        + ("；没吃早饭，上午有点没力气" if breakfast_skipped else "")
        + ("；没吃午饭，下午有点饿" if lunch_skipped else "")
        + ("；三餐都按时吃了，身体状态稳一点" if meal_regular else "")
        + ("；周末没排工作，整个人松一点" if weekend and work_minutes == 0 else "")
        + ("；周末睡了个长觉，睡眠债还了一点" if weekend_catchup else "")
        + ("；连续几天都睡得挺早，精神好一点" if good_sleep_streak else "")
        + ("；周末和朋友聚了聚，心情特别好" if weekend_social_bonus else "")
        + ("；周末出去晒了晒太阳，心情松一点" if weekend_outdoor_bonus else "")
        + ("；周一又要上班，有点提不起劲" if monday_blues else "")
        + ("；有人陪着，周一也没那么难熬" if monday_blues and socially_satisfied else "")
        + ("；周末还得工作，心里有点烦" if weekend and work_minutes > 0 else "")
        + ("；晚饭吃得太晚，胃还没消化" if late_dinner else "")
        + ("；饭后走了走，胃里舒服一点" if late_dinner_walk else "")
        + (
            f"；最近一周有 {late_dinner_days_7d} 天晚饭吃很晚，肠胃有点累"
            if frequent_late_dinner
            else ""
        )
        + ("；最近一周三餐挺规律，身体状态稳" if weekly_meal_regular else "")
        + ("；最近一周吃饭不太规律，身体有点虚" if weekly_meal_irregular else "")
        + ("；最近吃饭时间忽早忽晚，肠胃有点不适应" if meal_time_irregular else "")
        + ("；饭点太乱，晚上也睡不踏实" if meal_time_irregular else "")
        + (
            f"；最近一周有 {lunch_skip_days_7d} 天没吃午饭，下午总有点虚"
            if frequent_lunch_skip
            else ""
        )
        + (
            f"；今天通勤约 {transit_minutes} 分钟，路上有点累"
            if commute_fatigue
            else ""
        )
        + ("；午后有点犯困，效率不太高" if afternoon_dip else "")
        + ("；这个点有点困了，想早点睡" if evening_sleepiness else "")
        + ("；昨晚没睡够，早上有点懵" if morning_grogginess else "")
        + (
            "；缓了缓，清醒一点"
            if morning_grogginess_relief
            else ""
        )
        + ("；午睡了一会儿，下午没那么困了" if afternoon_nap_relief else "")
        + (
            "；缓了缓，没那么困了"
            if afternoon_dip_relief and not afternoon_nap_relief
            else ""
        )
        + ("；坐了太久没活动，肩颈有点发僵" if stiff_neck else "")
        + ("；今天运动量有点大，肌肉有点发酸" if overtraining else "")
        + ("；春天花粉多，鼻子有点痒" if pollen_allergy else "")
        + ("；鼻子痒，晚上可能睡不踏实" if pollen_allergy else "")
        + ("；洗了把脸，鼻子舒服一点" if pollen_relief else "")
        + (
            f"；最近一周有 {overtraining_days_7d} 天运动过量，身体有点吃不消"
            if frequent_overtraining
            else ""
        )
        + ("；最近练太猛，抵抗力有点下降" if frequent_overtraining else "")
        + ("；昨天练得太狠，今天浑身发酸" if overtraining_yesterday else "")
        + ("；昨天久坐没活动，今天肩颈还紧" if stiff_neck_yesterday else "")
        + (
            "；缓了缓，肩颈松一点"
            if stiff_relief
            else ""
        )
        + (
            "；练完拉伸/休息了一下，肌肉没那么紧"
            if overtraining_relief
            else ""
        )
        + ("；肩颈发僵，晚上可能睡不安稳" if stiff_neck else "")
        + ("；下雨天通勤更折腾，鞋也有点湿" if bad_weather_commute else "")
        + ("；午睡睡太久，起来有点懵" if nap_inertia else "")
        + ("；肩膀被晒得有点红，碰着疼" if sunburn else "")
        + ("；连着两天晒伤，皮肤更疼了" if sunburn_repeat else "")
        + ("；昨天晒伤的地方今天还红着" if sunburn_aftermath else "")
        + ("；晒伤还没退，衣服蹭着有点不舒服" if sunburn_aftermath else "")
        + ("；冲了个凉，晒伤的地方舒服一点" if sunburn_relief else "")
        + ("；洗了把脸喝了口水，人清醒一点" if nap_relief else "")
        + (
            f"；身上有 {discomfort_count} 处不舒服"
            if discomfort_count >= 2
            else ""
        )
        + (
            f"；最近一周有 {long_commute_days_7d} 天通勤很久，身体有点疲"
            if frequent_long_commute
            else ""
        )
        + (
            f"；最近一周有 {breakfast_skip_days_7d} 天没吃早饭，上午总有点虚"
            if frequent_breakfast_skip
            else ""
        )
        + (
            f"；最近一周吃了 {late_meal_days_7d} 天夜宵，肠胃和睡眠都受影响"
            if frequent_late_meal
            else ""
        )
        + (
            f"；已经 {sober_days} 天没喝酒，状态在恢复"
            if drinking_recovery
            else ""
        )
        + ("；今天工作有点久，有点疲惫" if work_stress >= 2 else "")
        + (
            "；下班后和人聊了聊，肩颈和心情都松了些"
            if raw_work_stress and social_today
            else (
                "；下班后活动或休息了一下，肩颈松了些"
                if raw_work_stress and stress_relief
                else ""
            )
        )
        + (
            "；工作很累，又没人说说话，心里更闷"
            if lonely_work_penalty
            else ""
        )
        + (
            "；看了会儿轻松的内容，工作压力松了一点"
            if raw_work_stress and eye_strain
            else ""
        )
        + (
            "；听了会儿音乐，心情松下来一点"
            if raw_work_stress and audio_relax
            else ""
        )
        + (
            "；弹了会儿琴，工作上的烦心事淡了点"
            if raw_work_stress and instrument_practice
            else ""
        )
        + (
            f"；最近一周有 {overwork_days_7d} 天加班到很晚，身体有点透支"
            if overwork
            else ""
        )
        + (
            f"；已经 {days_since_overwork} 天没怎么加班，身体缓过来一点"
            if overwork_recovery
            else ""
        )
        + (
            "；最近作息有点乱"
            if sleep_regularity_minutes >= 120
            else ""
        )
        + (
            "；周末和工作日起居差得有点多"
            if social_jetlag_minutes >= 90
            else ""
        )
        + (
            "；今天晒了太阳，心情松快一些"
            if sunlight_minutes >= 30
            else ""
        )
        + (
            "；最近连续晚睡，抵抗力有点差"
            if late_night_streak >= 3
            else ""
        )
        + (
            "；最近熬夜有点多，抵抗力还没恢复"
            if recent_late_nights >= 3 and late_night_streak < 3
            else ""
        )
        + (
            "；最近晒了太阳，抵抗力在恢复"
            if recent_sun_days and recent_late_nights >= 3 and not low_immunity
            else ""
        )
        + (
            "；最近抵抗力有点差"
            if low_immunity and late_night_streak < 3
            else ""
        ),
        "details": "；".join(details),
        "sleeping": sleeping_now,
        "sleep_debt_minutes": debt_minutes,
        "historical_mood": historical_mood,
        "low_mood_streak": low_mood_streak,
    }
