# NOTICE

**模拟人生_世界**（`astrbot_plugin_simlife_world`）
Copyright (C) 2026 uiuiuiui8

本程序是自由软件，依据 GNU 通用公共许可证第 3 版（GPL-3.0）发布，不提供任何担保。完整条款见 [LICENSE](LICENSE)。

## 来源

本插件是以下项目的修改版本：

- 项目：[FloranceYeh/astrbot_plugin_virtual_life](https://github.com/FloranceYeh/astrbot_plugin_virtual_life)（虚拟人生）
- 作者：Florance
- 基于版本：v1.12.2（2026-08-14）
- 许可证：GPL-3.0

原项目的版权与许可声明保持不变。上游的更新历史原样保留在 [CHANGELOG.md](CHANGELOG.md) 末尾。

## 相对上游 v1.12.2 的修改

依照 GPL-3.0 第 5 条 a 款，下面说明本版本做过的修改。修改自 2026-11-09（v2.0.0）起，持续到当前版本；逐项变化见 [CHANGELOG.md](CHANGELOG.md)。

**改名与标识**

- 插件标识改为 `astrbot_plugin_simlife_world`，显示名改为“模拟人生_世界”；保留对旧标识 `astrbot_plugin_virtual_life` 数据目录的兼容读取。

**从上游继承、已重新编写的部分**

上游项目的程序已全部按“行为不变”的要求重新编写，不再沿用上游的实现代码：

- `core/models.py`、`core/utils.py`、`core/storage.py`、`core/persona.py`、`core/runtime.py`、`core/window_schedule.py`、`core/holiday_calendar.py`、`core/message_segmenter.py`、`core/proactive.py`、`core/context_injection.py`、`core/reply_delay.py`、`core/message_generator.py`（状态提示改为数据表 `core/state_hints.py`）、`core/long_term.py`、`core/image_renderer.py`、`core/generator.py` 的生成流程。
- `main.py` 的事件钩子与指令：指令实现移入 `core/mixins/admin_commands.py`，`main.py` 只保留注册（指令名、参数与 LLM 工具接口不变）；`core/mixins/` 中的调度、规划、主动消息、回复延迟、大时间表与人际关系联动逻辑。
- `templates/schedule.html` 卡片模板与 `_conf_schema.json` 中所有配置说明（配置键名与默认值保持不变，以兼容现有配置）。
- 上游的测试全部改写为新的测试。

重写过程中用差分测试（同一批随机输入分别交给旧实现和新实现，逐项比较输出）确认行为一致。为保持与现有配置、数据文件、指令和 LLM 工具的兼容，下列内容属于对外接口，按原样保留：配置键名与默认提示词、数据文件字段名、指令与工具名称及其说明文字、日志之外面向用户的提示语。

**新增的文件**

- `core/` 下的生活模拟子系统：`affection`、`books`、`camera_*`、`character_assets`、`chat_schedule`、`cooking`、`delivery`、`diary`、`environment`、`food`、`furniture_*`、`garage`、`goods`、`health_journal`、`home_decor`、`interaction`、`item_effects`、`money`、`mood_history`、`transport`、`travel`、`user_state`、`view_api`、`view_state`、`wardrobe`、`weekly`、`world_events` 等，以及 `core/life_state/`、`core/mixins/`、`core/jsonio.py`。
- `views/life/`：2D / 3D 生活面板前端（含 `src/` 源码片段）。
- `tools/`、`tests/astrbot_stub.py`、`tests/test_structure.py`、`tests/test_jsonio.py`、`.github/workflows/ci.yml`、`ARCHITECTURE.md`、`NOTICE.md`。

**测试**

- `tests/` 中的其余测试文件来自上游，做了以下调整：包名改为本插件；按本插件行为修改断言（基础状态默认关闭、日程需通过现实性校验、主人睡眠检查）；节日测试在未安装 `holidays` / `lunar_python` 时跳过。
