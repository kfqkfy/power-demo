# 旧式 `.xls` 月报接入说明（第一版）

这份说明描述如何把**本地私有**的老式 `.xls` 月报接入到当前原型链路。

## 安全边界

默认约定：

- **真实报表文件不进入 git**
- **从真实报表导出的 raw / semantic JSON 不进入 git**
- 所有私有数据统一放在：`power-demo/localdata/`
- `localdata/` 已加入 `.gitignore`

也就是说，仓库里只保留：
- 代码
- 元数据结构
- 映射逻辑
- 导入/预览脚本
- 通用文档

不保留真实业务数据。

## 当前已实现

已完成一个**第一版可用接入链路**：

1. 从老式 BIFF `.xls` 文件中直接解析单元格
2. 提取出原始报表行，生成 `raw` JSON
3. 再通过 `report_mapper.py` 转成统一 `semantic` 事实行骨架
4. 可通过独立脚本把 `raw` JSON 转成 `semantic` JSON 进行本地核对

## 转换脚本

- `/root/.openclaw/workspace/power-demo/scripts/import_legacy_xls_report.py`
- `/root/.openclaw/workspace/power-demo/scripts/preview_legacy_semantic.py`

## 本地私有文件位置

默认路径：

- 原始私有报表：`power-demo/localdata/private_report.xls`
- 导出的 raw JSON：`power-demo/localdata/raw_legacy_report.json`
- 导出的 semantic JSON：`power-demo/localdata/semantic_legacy_report.json`

你也可以在命令行里传入自己的路径，不依赖默认文件名。

## 脚本用途

当前 raw 行结构包含：

- `stat_month`
- `report_code`
- `report_name`
- `metric_code`
- `metric_name`
- `entity_code`
- `entity_name`
- `entity_level`
- `parent_code`
- `parent_name`
- `time_scope`
- `value`
- `unit`
- `raw_values`

其中：
- `metric_code` 直接来自报表中的“指标代码”列
- `metric_name` 直接来自“指标名称”列
- `value` 当前第一版默认优先取“上网电量(合计)”列，对应列 11；若无则回退到“发电量(合计)”列，对应列 5

## 本地验证方式

### 1. 从 `.xls` 生成 raw JSON

```bash
python3 power-demo/scripts/import_legacy_xls_report.py \
  /path/to/private_report.xls \
  /path/to/raw_legacy_report.json
```

如果不传参数，默认读取/写入 `power-demo/localdata/` 下的私有文件。

> 说明：该脚本依赖 `olefile`，已补充到 `app/requirements.txt`。

### 2. 从 raw JSON 生成 semantic JSON 预览

```bash
python3 power-demo/scripts/preview_legacy_semantic.py \
  /path/to/raw_legacy_report.json \
  /path/to/semantic_legacy_report.json
```

这一步的作用是先确认：
- raw 层字段是否抽对
- semantic 骨架字段是否齐全
- 哪些字段还需要更细的 mapping 规则

## 当前限制

这是第一版，不是最终版，所以还有限制：

1. 目前主要抽的是行主干，不是整张表所有列全部语义化展开
2. `value` 现在默认偏向“上网电量(合计)”这一个口径
3. `energy_type_lv1` / `energy_type_lv2` / `category_path` 还没完全推断出来
4. 还没直接落 MySQL，只先落成 raw JSON 做本地验证

## 下一步

下一步会继续补：

1. raw MySQL 表结构
2. 从 raw JSON / raw 表 转成 semantic fact 的更完整规则
3. 指标代码优先匹配的 mapping 机制
4. 更完整的多指标展开（发电量 / 上网电量 / 装机 / 利用小时等）
