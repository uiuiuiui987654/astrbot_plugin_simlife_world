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

### 3D 脚本按需加载

`room-3d-models.js`、`room-3d-atmosphere.js`、`room-3d-outdoor.js`、`destination-3d.js`、`bedroom-3d.js` 在 `index.html` 里写成：

```html
<script type="text/x-lazy-3d" data-src="assets/bedroom-3d.js?v=…"></script>
```

浏览器不会执行这种标签。只有需要 3D 时，`src/app/05a-render-mode.js` 的 `ensure3DScripts()` 才按标签顺序注入真正的脚本，加载完成后调用 `wire3D()` 并重新渲染。改这几个文件时照常在这里更新 `?v=`；新增的 3D 脚本也用同样写法，放在 `bedroom-3d.js` 之前。

渲染代码判断 3D 时用 `use3D()`（想要 3D 且脚本已就绪），不要直接判断 `window.Room3D`。画面模式（自动 / 3D / 2D）保存在 `localStorage` 的 `vl-render`；自动模式在无 WebGL、省流量、内存 ≤ 4 GB、CPU ≤ 4 核或非本机 / 局域网访问时选 2D。

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
