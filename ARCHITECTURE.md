# 代码结构说明

这份文档说明插件各部分代码放在哪里、修改时要注意什么。功能说明见 [README](README.md)。

## 总览

```text
astrbot_plugin_simlife_world/
├─ main.py                  插件入口：生命周期 + 所有指令 / LLM 工具 / 事件钩子
├─ core/
│  ├─ mixins/               插件类的辅助方法，按功能拆成 Mixin
│  ├─ life_state/           身体与心情状态计算（精力、饱腹、清洁、心情、健康标记）
│  ├─ view_api.py           面板 HTTP 接口
│  ├─ view_state.py         面板状态数据
│  ├─ generator.py          每日日程生成
│  └─ …                     日程、人格、厨房、相机、出行、金钱等业务模块
├─ templates/               图片渲染模板
├─ views/life/              生活面板（前端）
│  ├─ index.html
│  ├─ app.js                ← 生成文件
│  ├─ style.css             ← 生成文件
│  ├─ assets/               2D / 3D 绘制脚本与素材
│  │  ├─ destination-3d.js  ← 生成文件
│  │  └─ room-3d-models.js  ← 生成文件
│  └─ src/                  上面四个生成文件的源码片段
└─ tools/
   ├─ build_frontend.py     由片段生成前端文件
   └─ plugin_snapshot.py    重构用：导出处理器注册表与方法指纹
```

## 后端

### main.py：只放带装饰器的处理器

AstrBot 按**定义所在的模块**绑定指令、LLM 工具和事件钩子，所以下面这些必须留在 `main.py` 的插件类里：

- `@filter.command` / `@filter.command_group` 以及组内子指令
- `@filter.llm_tool`
- `@filter.on_llm_request`、`@filter.after_message_sent`、`@filter.event_message_type` 等事件钩子
- `__init__`、`initialize`、`terminate`

其余不带装饰器的辅助方法都放在 `core/mixins/` 里，插件类通过多重继承组合它们：

| 模块 | Mixin | 负责 |
| --- | --- | --- |
| `runtime_state.py` | `RuntimeStateMixin` | 后台循环、会话活跃度、Agent 忙碌状态 |
| `personal_network.py` | `PersonalNetworkMixin` | 与人际网络插件的联动 |
| `planning.py` | `PlanningMixin` | 每日日程生成、日程要求、旅行指令 |
| `scheduling.py` | `SchedulingMixin` | 主动消息窗口、睡眠 / 空闲任务、重试 |
| `proactive.py` | `ProactiveMixin` | 自主发言机会与消息投递 |
| `interactions.py` | `InteractionsMixin` | 观察窗互动、用户状态 |
| `long_term.py` | `LongTermMixin` | 大时间表续期与草稿 |
| `reply_delay.py` | `ReplyDelayMixin` | 回复延迟批次 |
| `incoming.py` | `IncomingMixin` | 收到消息的分流、递东西请求 |
| `group_chat.py` | `GroupChatMixin` | 群聊隐私过滤与回复润色 |
| `life_context.py` | `LifeContextMixin` | 注入给 LLM 的生活状态、聊天回顾 |
| `chat_activity.py` | `ChatActivityMixin` | 从聊天中识别活动并补写日程 |
| `life_events.py` | `LifeEventsMixin` | 金钱、快递、日记、纪念日、车辆归还 |
| `common.py` | — | 模块级常量与函数（群聊词表、版本号读取、旧数据迁移） |

新增功能时：

- 新指令、新 LLM 工具、新事件钩子 → 写在 `main.py`，方法体尽量短，调用 Mixin 里的辅助方法。
- 新辅助方法 → 放进最贴近的 Mixin；没有合适的就新建 `core/mixins/xxx.py`，并在 `main.py` 的类定义里加入基类列表。
- 方法名在所有 Mixin 中必须唯一，否则会按继承顺序互相覆盖。

### core/life_state/：状态计算

原来的 `life_state.py` 拆成一个包，对外只暴露 `life_state.compute()`：

| 模块 | 内容 |
| --- | --- |
| `base.py` | 常量、时间轴读取、心情基线等基础函数 |
| `sleep.py` | 睡眠债、作息规律、熬夜 |
| `meals.py` | 三餐、咖啡因、饮水 |
| `body.py` | 运动、恢复、工作负荷、刷牙 |
| `weather.py` | 天气、日晒、高温暴露 |
| `social.py` | 社交、独处、饮酒 |
| `habits.py` | 香薰、家务、音乐、屏幕时间、读书、家具效果 |
| `compute.py` | `compute()` 主函数 |

模块之间只允许单向依赖：`base` ← 主题模块 ← `compute`，避免循环导入。

## 面板接口：core/view_api.py 与 core/view_routes/

`VirtualLifeViewAPI.dispatch` 只做两件事：按原顺序执行共用的检查（时间预览不能互动、POST 前要有今天的日程、家具和动作是否合法、角色在不在家），再把请求交给对应的处理函数。处理函数按领域放在 `core/view_routes/` 的 mixin 里：

| 文件 | 内容 |
| --- | --- |
| `system.py` | 状态快照、旅行、备份 / 恢复、诊断、最近活动 |
| `home.py` | 家具、装修、冰箱、做饭、心愿、礼物、家具互动 |
| `money.py` | 钱包、存款目标、商店、车库 |
| `journal.py` | 周报、日记、读书、好感称呼 |

处理函数签名统一为 `_get_<名称>(self, ctx)` / `_post_<名称>(self, ctx)`，`ctx` 是 `view_routes/context.py` 的 `RouteContext`（请求参数，加上 dispatch 里已经算好的 `actual`、`item` 等）。新增接口时，在对应文件加处理函数，并在 `dispatch` 的相应位置加一行分发。

相机同理：`core/camera_prompt.py` 只负责拼提示词（纯函数），`core/camera_photo.py` 负责调用绘图接口。

## 数据版本与迁移

数据目录里的每个状态 JSON 都有顶层 `schema_version`。`core/migrations.py` 的 `SCHEMAS` 记录每个文件当前代码写出的版本，以及把旧格式逐级升级的函数；插件启动时（`initialize` 最开始）调用 `migrate_all`：

- 已是最新的文件不会被重写；
- 旧文件先复制到数据目录的 `backups/`（每个文件保留最近 5 份），再逐级升级；
- 由更新版插件写出的文件不做改动，只在日志里警告；
- 结果写入 `data_manifest.json`，`/虚拟人生 自检` 会显示摘要。

改数据格式时：在写文件的模块和 `SCHEMAS` 里同时把版本加一，在 `steps[旧版本]` 注册升级函数，并在 `tests/test_migrations.py` 里用一份真实的旧数据做测试。`test_registered_versions_match_what_the_code_writes` 会提醒两边版本不一致。

## 前端

### 生成文件与片段

面板仍然只加载 `app.js`、`style.css`、`assets/destination-3d.js`、`assets/room-3d-models.js` 这几个文件，但它们的源码在 `views/life/src/` 下按功能拆成片段：

| 生成文件 | 片段目录 | 片段数 |
| --- | --- | --- |
| `app.js` | `src/app/` | 20（核心、数据、物品、互动、状态、平面图、场景、做饭、相机、小游戏、物品栏、读书、商店钱包、车库、系统、关系周报、日记回忆、初始化） |
| `style.css` | `src/style/` | 14 |
| `assets/destination-3d.js` | `src/destination-3d/` | 10 |
| `assets/room-3d-models.js` | `src/room-3d-models/` | 6 |

`app.js` 和两个 3D 脚本都包在一个立即执行函数里，片段之间共享同一作用域，所以单个片段不是完整的 JS 文件，必须拼接后使用。

**修改流程**

1. 改 `views/life/src/<目录>/` 下的片段，不要直接改生成文件（生成文件第一行有提示）。
2. 运行：

   ```bash
   python tools/build_frontend.py
   ```

3. 更新 `views/life/index.html` 中对应资源的 `?v=` 版本号；改了 `app.js` 时同步改 `src/app/00-core.js` 里的 `__VIRTUAL_LIFE_UI_VERSION`。
4. 提交前可以用 `python tools/build_frontend.py --check` 确认生成文件是最新的。

片段按文件名顺序拼接；新增片段时用编号前缀放到正确位置。CSS 的顺序就是层叠顺序，不要随意调整。

### 其他前端脚本

`views/life/assets/` 里其余脚本保持一个文件一个模块，由 `index.html` 按顺序加载：

- `scene-studio.js`：2D 平面图与房间近景
- `room-model.js`：房间家具坐标、门窗、锚点（2D / 3D 共用）
- `room-perspective.js`：2D 近景透视绘制
- `bedroom-3d.js`：3D 房间引擎；`room-3d-outdoor.js`、`room-3d-atmosphere.js`：户外与光照

### 本地预览面板

`python tools/panel_server.py` 会在 http://127.0.0.1:8770/ 打开生活面板：静态文件来自 `views/life/`，接口直接调用插件的 `VirtualLifeViewAPI.dispatch`，数据放在临时目录里并预置一天示例日程（`--data-dir` 可指定目录）。`tests/test_panel_smoke.py` 也用它跑无头浏览器测试。

### 3D 脚本按需加载

3D 场景脚本在 `index.html` 里写成占位标签，浏览器不会执行：

```html
<script type="text/x-lazy-3d" data-src="assets/bedroom-3d.js?v=…"></script>
<script type="text/x-lazy-3d" data-group="world" data-src="assets/destination-3d.js?v=…"></script>
```

`src/app/05a-render-mode.js` 分两组按标签顺序注入：

| 组 | 脚本 | 何时加载 |
| --- | --- | --- |
| `core`（默认） | `room-3d-models.js`、`room-3d-atmosphere.js`、`bedroom-3d.js`，以及它动态引入的 `vendor/three.*.js` | 需要 3D 时（家里的房间） |
| `world` | `room-3d-outdoor.js`、`destination-3d.js` | 第一次显示户外目的地、车库、阳台 / 露台时 |

渲染代码判断 3D 时用 `use3D()`（家里房间）或 `use3DWorld()`（户外、车库、阳台 / 露台），不要直接判断 `window.Room3D`；两组加载完成后都会重画场景。改这些文件时照常更新标签上的 `?v=`；新增的 3D 脚本按用途放进对应的组。

画面模式（自动 / 3D / 2D）保存在 `localStorage` 的 `vl-render`；自动模式在无 WebGL、省流量、内存 ≤ 4 GB、CPU ≤ 4 核或非本机 / 局域网访问时选 2D。

3D 画质分 `high` / `balanced` / `low` 三档，由 `quality3D()` 按 CPU 核数和内存选择并写入 `window.__VL_3D_QUALITY`，`bedroom-3d.js` 据此调整像素比、抗锯齿和阴影；可用 `localStorage` 的 `vl-3d-quality` 手动指定。

`vendor/three.core.js`、`vendor/three.module.js` 是 three.js r180 的压缩版（esbuild `--minify --legal-comments=inline`，共约 0.7 MB，原版约 2 MB）。升级 three.js 时同样换成压缩版。

## 重构校验

`tools/plugin_snapshot.py` 用桩模块导入插件（不需要安装 AstrBot），导出：

- 所有指令 / 工具 / 事件钩子的注册列表；
- 插件类每个方法的 AST 指纹。

重构前后各导出一次并对比，两者一致即说明只移动了代码、没有改动行为：

```bash
python tools/plugin_snapshot.py . before.json
# ……重构……
python tools/plugin_snapshot.py . after.json
```
