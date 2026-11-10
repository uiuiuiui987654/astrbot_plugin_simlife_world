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

**修改的上游文件**

- `main.py`：加入生活模拟相关的指令、LLM 工具与事件钩子；非装饰器方法拆入 `core/mixins/`。
- `core/context_injection.py`：基础状态模块默认关闭；日程段落总是附带当前实际服装。
- `core/generator.py`：加入日程现实性校验（全天覆盖、睡眠时长、三餐、午休等）。
- `core/models.py`、`core/storage.py`、`core/proactive.py`、`core/message_generator.py`、`core/reply_delay.py`、`core/image_renderer.py`、`core/utils.py`：为新增子系统扩展数据字段与调用；主人睡觉时跳过主动消息；状态文件改为原子写入。
- `_conf_schema.json`、`metadata.yaml`、`README.md`、`templates/`：配置项、元数据、文档与渲染模板相应调整。

**新增的文件**

- `core/` 下的生活模拟子系统：`affection`、`books`、`camera_*`、`character_assets`、`chat_schedule`、`cooking`、`delivery`、`diary`、`environment`、`food`、`furniture_*`、`garage`、`goods`、`health_journal`、`home_decor`、`interaction`、`item_effects`、`money`、`mood_history`、`transport`、`travel`、`user_state`、`view_api`、`view_state`、`wardrobe`、`weekly`、`world_events` 等，以及 `core/life_state/`、`core/mixins/`、`core/jsonio.py`。
- `views/life/`：2D / 3D 生活面板前端（含 `src/` 源码片段）。
- `tools/`、`tests/astrbot_stub.py`、`tests/test_structure.py`、`tests/test_jsonio.py`、`.github/workflows/ci.yml`、`ARCHITECTURE.md`、`NOTICE.md`。

**测试**

- `tests/` 中的其余测试文件来自上游，做了以下调整：包名改为本插件；按本插件行为修改断言（基础状态默认关闭、日程需通过现实性校验、主人睡眠检查）；节日测试在未安装 `holidays` / `lunar_python` 时跳过。
