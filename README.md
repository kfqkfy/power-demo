# 电力行业自然语言查数 Demo

这是一个可演示的最小可用 Demo，用来说明：

1. 用户先用自然语言提问
2. 系统先做问题分析（主题、指标、时间范围、查询类型）
3. 再路由到少量相关表
4. 程序生成 SQL 并查询 MySQL
5. 返回结果并生成简要回答

## 适合汇报的核心思路

这个 Demo 故意没有做“让大模型直接查几百张表”，而是采用更稳妥的架构：

- **问题分析层**：识别用户问题属于电量、负荷还是线损
- **语义映射层**：把“昨天 / 最近7天 / 本月 / 最大负荷 / 电量 / 线损率 / 同比”等业务词转成结构化字段
- **主题路由层**：只路由到少量候选表
- **查询执行层**：后端程序自己拼 SQL，而不是让模型自由执行 SQL

---

## 一、Demo 包含什么

- `app/`：FastAPI 后端
- `sql/init.sql`：MySQL 初始化脚本和演示数据
- `docker-compose.yml`：一键启动 MySQL + API

当前 Demo 演示三个主题：
- 电量（`energy_daily`）
- 负荷（`load_daily`）
- 线损（`line_loss_daily`）

并支持一张维表：
- 台区维表（`dim_station_area`），包含台区、供电所、线路、区域关系

并新增两个汇报友好能力：
- `/metadata`：展示表、字段、join、指标定义
- compare 查询：支持真实同比/环比 SQL 计算（当前为演示版）
- 非枚举式原型链路：`/semantic/analyze`

元数据字典已外置为可维护文件：
- `metadata/tables.json`
- `metadata/joins.json`
- `metadata/metrics.json`

后续你只要改这些 JSON，就能维护元数据，不需要改 Python 代码。

并支持两种分析模式：
- **rule**：规则分析器
- **llm**：接入本机 `custom_openai/gpt-5.4` 的大模型分析器

支持的典型问题：
- 昨天某台区电量多少？
- 最近7天哪个台区最大负荷最高？
- 最近7天哪个供电所最大负荷最高？
- 本月各供电所总电量排行
- 本月某线路下台区线损率情况
- 本月城南台区线损率同比情况

新增非枚举式原型模块：
- `app/semantic_parser.py`
- `app/metadata_retriever.py`
- `app/query_planner.py`
- `app/sql_compiler.py`

对应接口：
- `POST /semantic/analyze`：返回 semantic / candidates / plan / sql / params

当前样本数据已补成更完整的小型样本库，覆盖：
- 8 个台区
- 4 个供电所
- 8 条线路
- 4 个区域方向样例
- 3 段时间：`2026-03`、`2026-02`、`2025-03`

---

## 二、从零开始运行

### 1. 准备环境
确保机器安装：
- Docker Engine
- Docker Compose plugin

如果是 Ubuntu 24.04，可以执行：

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

### 2. 准备环境变量
先复制一份环境变量模板：

```bash
cd power-demo
cp .env.example .env
```

然后按需修改 `.env`，至少建议改掉：
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `LLM_API_KEY`

### 3. 启动服务
在项目目录执行：

```bash
cd power-demo
docker compose up -d --build
```

### 3. 查看容器状态
```bash
docker compose ps
```

---

## 三、接口演示

### 打开前端页面
浏览器访问：

```text
http://127.0.0.1:8000/
```

页面里可以直接演示：
- 输入自然语言问题
- 切换是否使用 gpt-5.4 分析
- 查看分析结果
- 查看生成 SQL
- 查看查询结果
- 查看元数据字典

### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

### 查看支持的主题
```bash
curl http://127.0.0.1:8000/themes | jq
```

### 查看元数据字典
```bash
curl http://127.0.0.1:8000/metadata | jq
```

### 只做问题分析（规则模式）
```bash
curl -s http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"question":"本月城南台区线损率同比情况"}' | jq
```

### 只做问题分析（大模型模式，走 gpt-5.4）
```bash
curl -s http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"question":"本月城南台区线损率同比情况", "use_llm": true}' | jq
```

### 示例 1：负荷排行
```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"最近7天哪个台区最大负荷最高？"}' | jq
```

### 示例 2：本月电量汇总
```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"本月城区总电量是多少？"}' | jq
```

### 示例 3：昨天负荷明细
```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"昨天各台区负荷情况"}' | jq
```

### 示例 4：线损排行
```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"本月城区台区线损率排行"}' | jq
```

### 示例 5：同比查询（真实对比 SQL）
```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"本月城南台区线损率同比情况", "use_llm": true}' | jq
```

---

## 四、Demo 的内部逻辑

### 1. 问题分析器 `analyzer.py`
当前是规则版分析器，负责识别：
- 主题：电量 / 负荷 / 线损
- 指标：电量 / 最大负荷 / 平均负荷 / 线损率
- 时间：昨天 / 最近7天 / 本月 / 上月
- 查询类型：排行 / 汇总 / 明细 / 对比
- 区域：全市 / 城区 / 城东 / 城西 / 城南 / 城北
- 对比：同比 / 环比

### 2. Schema Registry `schema_registry.py`
负责“主题到表”的映射，例如：
- `energy -> energy_daily`
- `load -> load_daily`
- `line_loss -> line_loss_daily`

### 3. SQL Builder `sql_builder.py`
由程序生成 SQL，而不是让模型直接执行任意 SQL。

这一步在正式环境里可以继续加强：
- 白名单表
- 白名单字段
- 只读账号
- 查询超时
- 审计日志

---

## 五、对领导汇报时怎么讲

### 业务目标
让业务人员直接提问：
- 最近7天哪个台区最大负荷最高？
- 本月城区总电量是多少？
- 本月城区台区线损率排行如何？

系统自动完成：
- 问题理解
- 业务语义识别
- 主题路由
- SQL 查询
- 结果返回

### 为什么不直接让大模型查几百张表
因为会带来：
- 选错表
- 选错字段
- Join 错误
- SQL 不可控
- 查询性能失控

### 正确做法
采用分层架构：
1. **问题分析层**：识别“电量、负荷、线损”等主题
2. **语义层**：把“日电量、月电量、最大负荷、同比、环比”等标准化
3. **路由层**：将问题路由到少量主题表
4. **执行层**：程序生成 SQL 并执行
5. **回答层**：整理结果并输出给用户

---

## 六、正式版本建议怎么演进

1. 增加主题：
   - 电压
   - 采集成功率
   - 异常告警
   - 设备运行状态

2. 增加行业词典：
   - 台区
   - 专变 / 公变
   - 峰谷平
   - 同比 / 环比
   - 线损率
   - 越限

3. 增加指标中心：
   - 日电量
   - 月电量
   - 最大负荷
   - 平均负荷
   - 线损率
   - 采集成功率

4. 增加元数据中心：
   - 表注释
   - 字段注释
   - 业务域分类
   - Join 关系

5. 再把问题分析器替换成大模型 JSON 输出

---

## 七、建议现场演示的问题

1. `最近7天哪个台区最大负荷最高？`
2. `本月城区总电量是多少？`
3. `昨天各台区负荷情况`
4. `本月城区台区线损率排行`
5. `本月城南台区线损率同比情况`

这样能展示：
- 排行
- 汇总
- 明细
- 主题识别
- 对比类问题入口

---

## 八、注意事项

这个 Demo 用来演示“思路和架构”，不是直接上生产。

它当前简化了：
- 行业术语词典
- 指标定义
- 时间解析
- SQL 安全控制
- 表关系路由
- 真正的大模型接入

但整体路线是适合继续扩展的。
