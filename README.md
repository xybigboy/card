# 动漫卡牌对战游戏

一款基于 FastAPI + Vue 3 + Vant 4 + SQLite/MySQL + WebSocket 的实时 H5 卡牌对战游戏，支持移动端和桌面端。

线上地址：https://card.jiiii.cn

## 当前项目状态

**版本**：开发中（持续迭代）  
**最新提交**：`711511d` fix: battle HP real-time, multi-skill ordering, skin system, home icon  
**部署状态**：运行中 @ 124.221.113.25:28888（Docker 容器 `card-game`）

### 未完成的功能和bug：
1.界面图片  加载压缩的web格式的图片
2.工会成员 没有信息 是没有工会功能类不全还是数据没有渲染还是表没得
3.实时匹配有问题 匹配不到人 然后实时匹配 的实时掉血效果应该是应用全部战斗模式 大乱斗 指定玩家战斗 等 作为基础效果
4.我的 战绩 记录看不到对手名称全是显示未知
5.玩家卡片点击放大这个会导致界面 上下滑动实效 点击放大这个 直接做成和管理后台点击放大那种效果或者就不要 
6.战斗只要点了大乱斗 进入无限挂机自动匹配 就会一直打 我点退出 也没用 导致 我的卡金数据和对战场次一直增加
7.能不能优化一下战斗界面排版 缩小一点 战斗效果像次元乱斗那种？
8在对战里面界面增加一个boss模式
9.指定对战如果打不赢可不可以支持组队拉玩家进来一起打对方？ 所以就引入了组队多打一 
代码实现原则 模块化 前后端 功能 解藕设计原则

### 已完成功能

**核心玩法**

- 抽卡系统（普通/高级/史诗/典藏四种稀有度，单抽+十连抽）
- 卡片升级与兑换（消耗卡金提升全属性，多余卡片兑换卡金）
- 重复卡片分组展示与融合系统（消耗同名卡片获属性加成，按稀有度 5%~40%）
- 多技能系统（卡片支持多个技能，`skills_json` JSON 数组存储，向后兼容单技能字段；6 种触发类型：被动/每回合/每N回合/特定回合/低血量/死亡时）
- 卡片皮肤系统（`CardImage` 模型，后台管理上传/管理皮肤，玩家在仓库选择皮肤切换外观）

**对战系统**

- 实时 PVP 对战（WebSocket 匹配，完整回合制战斗，战斗日志回放）
- 战斗 HP 实时显示（后端结构化 HP 字段：defender_hp/card_hp/attacker_hp，前端实时更新血条）
- AI 对战（等待 15s 后可挑战 AI 训练师，奖励减半，不影响积分）
- 指名挑战（输入用户名直接挑战指定玩家）
- 乱斗模式（随机匹配对战）
- 掠夺机制（胜利有概率掠夺对方低星卡片）
- 麻痹免疫（被麻痹后获得 2 回合麻痹免疫）
- ELO 积分排名系统
- 对战记录列表与详情（支持战斗日志逐条回放）

**社交与经济**

- 工会系统（创建/加入/退出工会，工会信息管理）
- 商店系统（购买抽卡次数）
- 图鉴系统（查看所有已收录卡片，含多技能信息展示）
- 排行榜系统

**管理后台**

- 管理员登录、密码修改
- 卡片模板 CRUD（含多技能编辑器：主技能 + 额外技能，支持触发类型/参数/描述）
- 卡片皮肤管理（上传/删除皮肤图片，按模板管理）
- AI 批量生成卡片（通过 OpenAI 兼容 API，支持分类/主题指定）
- AI 图片生成（支持风格选择：默认/真人/日漫/自定义，图片带文字开关）
- AI 提供商管理（数据库存储，text/image 类型区分，管理后台动态增删改）
- 管理员奖励发放（给指定用户发送卡金/抽卡次数）
- 数据库 SQLite/MySQL 动态切换（管理后台配置 + 数据迁移）

**基础设施**

- 后端模块化架构（15 个路由模块 + WebSocket 模块）
- Docker 容器化部署（多阶段构建，volume 数据持久化，CST 时区）
- 数据库自动迁移（`_migrate_add_columns` 自动检测并添加新列）

### 技术栈

后端：FastAPI、SQLAlchemy、SQLite/MySQL、WebSocket、uvicorn  
前端：Vue 3 (Composition API)、Vant 4、Vue Router 4、Pinia、Vite 4、Axios、unplugin-icons (Tabler)  
部署：Docker（多阶段构建：Node 20 构建前端 → Python 3.12 运行后端）

## Docker 手动部署

### 前置条件

- 服务器已安装 Docker 和 Docker Compose
- 服务器已安装 Git
- 能访问 GitHub/Gitee 拉取代码（或能通过 scp 上传代码）

### 步骤一：拉取代码

```bash
# 克隆仓库到服务器
cd /tmp
git clone https://gitee.com/xy2654106757_1/card.git card
cd card
```

如果使用 Gitee 私有仓库需要认证，可以使用带用户名密码的 URL：

```bash
git clone https://<username>:<password>@gitee.com/xy2654106757_1/card.git card
```

### 步骤二：构建 Docker 镜像

```bash
cd /tmp/card
docker build -t card-game .
```

构建过程是多阶段的：第一阶段用 `node:20-alpine` 安装前端依赖并执行 `vite build`，第二阶段用 `python:3.12-slim` 安装后端依赖并复制前端产物。构建完成后镜像约 400MB。

### 步骤三：创建数据目录

```bash
# 创建数据持久化目录（数据库文件将存储在这里）
mkdir -p /tmp/card/data
```

### 步骤四：启动容器

```bash
docker run -d \
  --name card-game \
  -p 28888:8000 \
  -v /tmp/card/data:/app/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  card-game
```

参数说明：

- `-d`：后台运行
- `--name card-game`：容器名称
- `-p 28888:8000`：端口映射（宿主机 28888 → 容器 8000）
- `-v /tmp/card/data:/app/data`：挂载数据目录，数据库文件持久化到宿主机
- `-e TZ=Asia/Shanghai`：设置时区为 CST（中国标准时间 UTC+8）
- `--restart unless-stopped`：容器异常退出时自动重启

### 步骤五：验证部署

```bash
# 检查容器状态
docker ps --filter name=card-game

# 查看启动日志
docker logs card-game

# 测试访问
curl http://localhost:28888/
```

正常启动后日志应显示：

```
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 使用 Docker Compose 部署

项目根目录已包含 `docker-compose.yml`：

```bash
cd /tmp/card
docker compose up -d --build
```

Docker Compose 会自动构建镜像并启动容器，数据持久化在 `./data` 目录下。

### 更新部署

当代码有更新时，重新部署的流程：

```bash
cd /tmp/card

# 1. 拉取最新代码
git pull origin master

# 2. 停止并删除旧容器
docker stop card-game
docker rm card-game

# 3. 重新构建镜像
docker build -t card-game .

# 4. 启动新容器（数据不会丢失，因为挂载在 volume 上）
docker run -d \
  --name card-game \
  -p 28888:8000 \
  -v /tmp/card/data:/app/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  card-game
```

也可以使用项目自带的远程部署脚本（通过 Paramiko SSH）：

```bash
# 在本地执行
python scripts/remote_deploy.py --host 124.221.113.25 --password "your_password"
```

### 数据库管理

- 默认使用 SQLite，数据库文件位于 `/app/data/game.db`（宿主机 `/tmp/card/data/game.db`）
- 配置数据库位于 `/app/data/config.db`，存储数据库连接配置（始终使用 SQLite）
- 可在管理后台切换为 MySQL（需要提供 MySQL 连接信息，支持数据迁移）
- 数据库文件在 Docker volume 上，重新部署不会丢失

### 默认账号

- 管理员：`admin` / `admin123`（首次启动自动创建，建议登录后修改密码）
- 普通用户：通过注册页面自行注册，新用户赠送 10 次免费抽卡

## 本地开发

### 环境要求

- Python 3.10+
- Node.js 20+（unplugin-icons 要求 Node >= 20.19）
- npm

### 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 启动开发服务器

```bash
# 终端1 - 后端（端口 8000）
cd backend
python main.py

# 终端2 - 前端开发服务器（端口 5173）
cd frontend
npm run dev
```

前端开发模式下访问 http://localhost:5173，API 请求会代理到后端 8000 端口。

### 构建前端

```bash
cd frontend
npm run build
# 产物输出到 frontend/dist/，可复制到 backend/static/ 由后端直接服务
```

## 项目结构

```
card/
├── backend/
│   ├── main.py                 # FastAPI 主入口（~130行，仅注册路由+中间件）
│   ├── database.py             # SQLAlchemy 引擎管理（SQLite/MySQL 动态切换）
│   ├── config_db.py            # 配置数据库（始终 SQLite，存储 DB 连接配置）
│   ├── models.py               # 数据模型（User, UserCard, CardTemplate, BattleRecord, AdminUser, AIProvider, CardImage）
│   ├── schemas.py              # Pydantic 请求/响应模型（含 CardResponse: skills_json, selected_image）
│   ├── utils.py                # 共享工具函数（token 验证、card_to_response 含 effective image）
│   ├── game_logic.py           # 游戏核心逻辑（抽卡、战斗模拟、升级、融合、多技能解析）
│   ├── card_data.py            # 卡片模板种子数据（20+ 动漫角色）
│   ├── routers/                # API 路由模块
│   │   ├── auth.py             # 用户注册/登录
│   │   ├── gacha.py            # 抽卡
│   │   ├── cards.py            # 仓库/升级/兑换/融合/出战/图鉴
│   │   ├── battle.py           # 对战记录列表与详情
│   │   ├── shop.py             # 商店
│   │   ├── ranking.py          # 排行榜
│   │   ├── matchmaking.py      # 匹配队列状态
│   │   ├── challenge.py        # 指名挑战（按用户名挑战）
│   │   ├── guild.py            # 工会系统（创建/加入/退出）
│   │   ├── skins.py            # 卡片皮肤（玩家选择/后台管理上传删除）
│   │   ├── admin_auth.py       # 管理员登录/登出/改密
│   │   ├── admin_cards.py      # 卡片模板 CRUD + 皮肤管理
│   │   ├── admin_ai.py         # AI 批量生成卡片 + 图片生成
│   │   ├── admin_db.py         # 数据库配置管理/切换/迁移
│   │   └── admin_rewards.py    # 管理员奖励发放
│   ├── ws/
│   │   └── pvp.py              # WebSocket PVP 对战 + AI 对战
│   ├── sql/
│   │   ├── init_sqlite.sql     # SQLite 初始化脚本
│   │   └── init_mysql.sql      # MySQL 初始化脚本
│   ├── requirements.txt
│   └── static/                 # 前端构建产物（自动生成）
├── frontend/
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Login.vue / Register.vue
│   │   │   ├── Home.vue              # 首页（统计 + 快速入口）
│   │   │   ├── Gacha.vue             # 抽卡
│   │   │   ├── Warehouse.vue         # 仓库（卡片管理/升级/兑换/融合/皮肤选择/多技能展示）
│   │   │   ├── Battle.vue            # 对战（PVP 匹配 + AI 对战 + 指名挑战）
│   │   │   ├── BattleHistory.vue     # 对战记录
│   │   │   ├── Guild.vue             # 工会系统
│   │   │   ├── Brawl.vue             # 乱斗模式
│   │   │   ├── Shop.vue / Ranking.vue
│   │   │   ├── Collection.vue        # 图鉴（多技能信息展示）
│   │   │   ├── AdminLogin.vue
│   │   │   ├── AdminCards.vue        # 卡片模板管理 + AI 生成 + 图片生成 + 皮肤管理
│   │   │   └── AdminSettings.vue     # 管理员设置 + 数据库配置 + AI 提供商管理
│   │   ├── components/
│   │   │   ├── CardIcon.vue          # 卡牌图标（渐变色 + 角色首字，支持 AI 卡片）
│   │   │   ├── BattleDetail.vue      # 对战详情弹窗
│   │   │   └── BattleLogEntry.vue    # 战斗日志条目
│   │   ├── utils/
│   │   │   ├── api.js                # 统一 API 客户端（401 拦截 + token 注入）
│   │   │   └── icons.js              # 图标映射表（预定义 + AI 卡片 fallback）
│   │   ├── store/user.js             # Pinia 状态管理
│   │   ├── router/index.js
│   │   ├── App.vue                   # 根组件（Vant Tabbar 导航）
│   │   ├── main.js
│   │   └── style.css                 # 全局样式（Vant 暗色主题）
│   ├── package.json                  # 注意: 必须含 "type": "module"
│   └── vite.config.js
├── scripts/
│   └── remote_deploy.py              # 远程部署脚本（Paramiko SSH）
├── Dockerfile                        # 多阶段构建（Node 20 + Python 3.12）
├── docker-compose.yml
├── sql/                              # 初始化 SQL 脚本
└── README.md
```

## 游戏规则

### 抽卡概率

| 稀有度 | 概率 | 基础星级 |
|--------|------|----------|
| 普通 | 60% | 1-2 星 |
| 高级 | 25% | 2-3 星 |
| 史诗 | 12% | 3-4 星 |
| 典藏 | 3% | 4-5 星 |

星级在基础上随机浮动（+0 ~ +3 星），每星提升 12% 属性。

### 属性计算公式

`atk/def/hp/spd = base × (1 + (stars-1) × 0.12) × (1 + (level-1) × 0.05)`

### 战斗规则

- 回合制，速度快的先手攻击
- 速度差影响闪避率（最高 15%）
- 伤害 = 攻击力 - 防御力 × 0.5（受技能修正）
- 最大 30 回合，超时按剩余血量判定
- 技能在特定条件下自动触发（被动/每回合/特定回合/低血量等）

### 融合系统

消耗同名卡片获得属性加成，按稀有度不同加成比例不同：

| 稀有度 | 每张加成 | 每级额外 |
|--------|----------|----------|
| 普通 | 5% | +2% |
| 高级 | 10% | +2% |
| 史诗 | 20% | +2% |
| 典藏 | 40% | +2% |

### AI 对战

- 等待 15 秒后可挑战 AI 训练师
- AI 属性为玩家出战卡片的 70%~90%
- 奖励减半（胜 30 卡金 / 负 10 卡金 / 平 15 卡金）
- 不影响积分

### 奖励机制

- PVP 胜利：基础 50 卡金 + 星级 × 10 + 积分差加成
- PVP 失败：胜利奖励的 50%
- 掠夺：2 星及以下卡片，对手持有 3 张以上时 30% 概率被掠夺

### 升级费用

第 N 级升级费用 = `50 × 1.15^(N-1)` 卡金，每级提升 5% 全属性。

## 卡片角色

包含 21 张动漫角色卡片，覆盖 7 个系列：

- 龙珠：卡卡罗特、贝吉塔、弗利沙、孙悟饭、克林
- 火影：漩涡鸣人、宇智波佐助、旗木卡卡西、我爱罗、春野樱
- 奥特曼：迪迦、赛罗、泽塔、初代
- 海贼王：路飞、索隆
- 鬼灭：炭治郎、祢豆子
- 名侦探柯南：柯南
- 宝可梦：皮卡丘、喷火龙

管理后台支持通过 AI 批量生成新卡片，AI 会根据指定的动漫系列和主题生成平衡的卡片数据。

## API 接口

### 用户系统

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/register` | 注册 |
| POST | `/api/login` | 登录 |
| GET | `/api/user` | 获取用户信息 |

### 卡片系统

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/draw` | 抽卡 |
| GET | `/api/warehouse` | 获取仓库卡片 |
| POST | `/api/cards/{id}/set-battle` | 设置出战卡片 |
| GET | `/api/battle-card` | 获取出战卡片 |
| POST | `/api/cards/{id}/sell` | 兑换卡片 |
| POST | `/api/cards/{id}/upgrade` | 升级卡片 |
| POST | `/api/cards/{id}/consume` | 融合消耗同名卡片 |
| GET | `/api/collection` | 图鉴（已收录卡片） |

### 战斗系统

| 方法 | 路径 | 说明 |
|------|------|------|
| WebSocket | `/ws/pvp` | PVP 实时匹配 + AI 对战 |
| GET | `/api/battle/history` | 对战记录列表 |
| GET | `/api/battle/{id}` | 对战详情（含战斗日志） |
| GET | `/api/matchmaking/queue-size` | 匹配队列人数 |

### 商店与排行

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shop/info` | 商店信息 |
| POST | `/api/shop/buy-draws` | 购买抽卡次数 |
| GET | `/api/ranking` | 排行榜 |

### 卡片皮肤

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cards/{card_id}/skins` | 获取卡片的可用皮肤列表 |
| PUT | `/api/cards/{card_id}/skin` | 选择皮肤（设置 selected_image） |

### 社交系统

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/guilds` | 创建工会 |
| GET | `/api/guilds/my` | 获取我的工会信息 |
| POST | `/api/guilds/{guild_id}/join` | 加入工会 |
| POST | `/api/guilds/leave` | 退出工会 |
| GET | `/api/guilds` | 工会列表 |
| POST | `/api/challenge/by-name` | 指名挑战（按用户名） |

### 后台管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/login` | 管理员登录 |
| POST | `/api/admin/logout` | 管理员登出 |
| GET | `/api/admin/profile` | 管理员信息 |
| POST | `/api/admin/change-password` | 修改管理员密码 |
| GET | `/api/admin/card-templates` | 获取卡片模板列表 |
| POST | `/api/admin/card-templates` | 创建卡片模板 |
| PUT | `/api/admin/card-templates/{id}` | 更新卡片模板 |
| DELETE | `/api/admin/card-templates/{id}` | 删除卡片模板 |
| POST | `/api/admin/ai-generate-cards` | AI 批量生成卡片 |
| POST | `/api/admin/ai-generate-image` | AI 生成单张图片 |
| POST | `/api/admin/ai-generate-card-images` | AI 批量生成卡片图片 |
| GET | `/api/admin/ai-providers` | 获取 AI 提供商列表 |
| POST | `/api/admin/ai-providers` | 添加 AI 提供商 |
| PUT | `/api/admin/ai-providers/{id}` | 更新 AI 提供商 |
| DELETE | `/api/admin/ai-providers/{id}` | 删除 AI 提供商 |
| GET | `/api/admin/templates/{template_id}/skins` | 获取模板的皮肤列表 |
| POST | `/api/admin/templates/{template_id}/skins` | 上传皮肤图片 |
| DELETE | `/api/admin/skins/{skin_id}` | 删除皮肤 |
| GET | `/api/admin/users` | 获取用户列表 |
| POST | `/api/admin/send-reward` | 发放奖励（卡金/抽卡次数） |
| GET | `/api/admin/db/configs` | 获取数据库配置列表 |
| POST | `/api/admin/db/configs` | 添加数据库配置 |
| PUT | `/api/admin/db/configs/{id}` | 更新数据库配置 |
| POST | `/api/admin/db/switch` | 切换数据库 |
| POST | `/api/admin/db/test-connection` | 测试数据库连接 |
| POST | `/api/admin/db/migrate` | 数据迁移 |

## 注意事项

- `package.json` 必须包含 `"type": "module"`，否则 Vant 4 + unplugin-icons 的 ESM 构建会失败
- Dockerfile 必须使用 `node:20-alpine`（不能用 Node 18，unplugin 要求 Node >= 20.19）
- 数据目录通过 `DATA_DIR` 环境变量指定，Docker 中为 `/app/data`，本地开发默认为 `backend/data/`
- `config_db.py` 的默认 SQLite 路径必须与 `database.py` 的 `DB_PATH` 一致，否则迁移函数会连到不同数据库文件
- WebSocket 对战中一方断线不会导致双方崩溃（使用 `safe_send` 包装 + 独立 db session 计算奖励）
- Vant 4 暗色主题下 `plain` 按钮需要显式设置背景色，否则白底白字不可见
- FastAPI SPA fallback 使用 `BaseHTTPMiddleware` 而非 catch-all 路由，避免拦截静态资源
- 多技能系统 `skills_json` 第一个元素是主技能，前端编辑额外技能时需 `slice(1)` 跳过主技能，否则保存时会重复
- 战斗日志 HP 实时更新：后端返回结构化 HP 字段（defender_hp/card_hp/attacker_hp），前端必须先 `JSON.parse` 再处理，原始字符串会导致 `logObj={}` 跳过所有 HP 分支
- `card_to_response` 返回的 `image` 字段是 effective image（`selected_image or template.image`），前端直接使用即可
- 稀有度颜色标准（所有页面统一）：普通=default(gray)、高级=success(green)、史诗=primary(blue)、典藏=warning(gold)
- 后端 API 返回 "未找到" 时使用 HTTP 200 + null 字段（如 `/guilds/my` 返回 `{guild:null}`），前端必须检查响应体字段而非状态码
- `python-multipart` 必须安装以支持 FastAPI 文件上传（皮肤图片上传）
- Dockerfile 需使用 Debian 12 slim，且需 `rm -f /etc/apt/sources.list.d/*.sources` 再写 apt 镜像源
