# 正则匹配引擎 — 问题分析与修复方案

## 问题背景

`ai任务/完善蜜罐与流量识别任务.md` 要求构建"正则 → 频次 → AI"三级识别漏斗。  
正则匹配引擎位于 `backend/service/log_service.py` 的 `create_log()` 方法（第 538–575 行），  
规则数据由 `backend/init_data.py` 初始化写入 `match_rules` 表。

---

## Bug 1：`match_field` 字段名与日志字典 Key 不一致

### 位置
`log_service.py` L547：
```python
match_content = log_data.get(rule.match_field)
```

### 问题
- 数据库中所有规则的 `match_field` 均存储为 `raw_log`。
- `log_data` 字典由蜜罐上报，其实际字段名是 `raw_log`、`payload`、`request_path` 等。
- **当 `match_field='payload'` 时，取到 `None`，规则直接跳过，不会触发任何正则匹配。**
- 当 `match_field` 为 `raw_log`（默认值）且 `match_content is None` 时，下面的 `if match_content is not None` 判断使整个规则静默失败，且没有 fallback。

### 根本原因
L549–550 有一段废弃的空操作 `pass`，原本应该是"当字段不存在时 fallback 到 `raw_log`"，但实际上什么都没做：
```python
if match_content is None and rule.match_field != "raw_log":
    pass   # ← 留空的 fallback，逻辑缺失
```

### 修复方案
```python
match_content = log_data.get(rule.match_field)

# fallback：若指定字段为空，拼接 raw_log 兜底
if not match_content:
    match_content = log_data.get("raw_log") or ""
```

---

## Bug 2：第一条命中规则后 `break`，后续高优先级攻击被漏判

### 位置
`log_service.py` L569：
```python
break
```

### 问题
规则按 `priority ASC` 排列，一旦某条优先级较低的规则先于更高优先级规则被命中（例如"扫描探测"规则 priority=9 先匹配，而"SQL注入" priority=1 的规则后面才遍历），则直接 break，SQL注入不会被识别。

> 实际上 `ORDER BY priority ASC` 已经确保小数字先执行，`break` 在此语义上是"命中最高优先级规则后停止"，逻辑上是对的——**但存在另一个问题：**  
> 若某个载荷同时触发多个规则（如 SQLi + RCE），系统只能记录第一条的 `attack_type`，丢失后续攻击维度信息。

### 当前行为
- 只记录最先匹配的规则攻击类型
- `attack_description` 理论上可以追加，但 `break` 阻断了迭代

### 修复方案（可选增强）
去掉 `break`，改为"命中优先级最高（数字最小）的规则，但继续扫描后续规则追加到 description"：
```python
matched_priority = None

for rule in rules:
    ...
    if re.search(...):
        if matched_priority is None:
            # 第一条（最高优先级）命中，设定 attack_type/threat_level
            attack_type = rule.attack_type
            threat_level = rule.threat_level
            is_malicious = ...
            matched_priority = rule.priority

        # 无论是否是第一条，都追加到描述
        rule_msg = f"触发规则: {rule.name}"
        if not attack_description:
            attack_description = rule_msg
        elif rule_msg not in attack_description:
            attack_description += f" | {rule_msg}"

        rule.match_count += 1
        rule.last_matched = get_beijing_time()
        # 不 break，继续扫描其他规则
```

---

## Bug 3：`raw_log` 由蜜罐在上报时已拼接，但 payload 独立字段未参与正则匹配

### 位置
`log_service.py` L547 + 各蜜罐脚本上报逻辑

### 问题
蜜罐上报字典通常如下：
```json
{
  "raw_log": "...",      // 已经包含大部分信息
  "payload": "...',      // SQL/命令注入 payload 单独字段
  "request_path": "/admin?id=1 UNION SELECT..."
}
```
所有规则的 `match_field = 'raw_log'`，但部分攻击场景中 `raw_log` 可能**不包含** payload 原始字符串（例如 POST body 不写入 raw_log），导致正则无法命中。

### 修复方案
在正则匹配时，构造一个包含所有关键字段的联合字符串，覆盖全部可能的注入点：
```python
# 构建联合匹配内容（涵盖所有关键字段）
combined_content = " ".join(filter(None, [
    str(log_data.get("raw_log") or ""),
    str(log_data.get("payload") or ""),
    str(log_data.get("request_path") or ""),
    str(log_data.get("user_agent") or ""),
]))

# 根据 match_field 决定匹配范围
if rule.match_field == "raw_log":
    match_content = combined_content
else:
    match_content = str(log_data.get(rule.match_field) or "") or combined_content
```

---

## Bug 4：正则 pattern 大量使用捕获组 `()` 而非非捕获组 `(?:)`，性能低下

### 位置
`init_data.py` 中 15 条规则的 `regex_pattern` 字段

### 问题
几乎所有规则均使用 `(...)` 捕获组（例如 SQL注入规则有 30+ 个捕获组），而 `re.search` 只需要判断是否匹配，无需捕获子串。  
捕获组会产生**额外的内存分配和回溯**，在高频蜜罐日志场景下影响性能。

### 修复方案
将所有 `(...)` 替换为 `(?:...)`（非捕获组）。例如 SQL注入规则：
```python
# 原（部分）
r"(?i)(union\s+(all\s+)?select|select\s+.+\s+from|...)"
# → 改为
r"(?i)(?:union\s+(?:all\s+)?select|select\s+.+\s+from|...)"
```
由于规则较多，建议统一在代码层做转换而非手动修改 DB：
```python
# 在 create_log 中预处理
compiled_pattern = re.compile(rule.regex_pattern, re.IGNORECASE)
if compiled_pattern.search(content_str):
    ...
```
同时在 `MatchRuleService` 中加入**规则预编译缓存**，避免每次请求都重新 `re.compile`。

---

## Bug 5：暴力破解 HTTP 过滤条件错误（SQL LIKE 大小写不匹配）

### 位置
`log_service.py` L116：
```python
base_filter.append(Log.payload.like("%Username:%Password:%"))
```

### 问题
SQLite 的 `LIKE` 默认**不区分大小写（仅限 ASCII）**，但上报的 payload 格式为：
```
Username: admin, Password: 123456
```
注意中间有**空格**，而 `%Username:%Password:%` 不包含空格，导致匹配不上，HTTP 暴力破解永远不会被计数。

### 修复方案
修改 LIKE pattern，与 `_CREDENTIAL_PATTERN` 保持一致：
```python
# 原
base_filter.append(Log.payload.like("%Username:%Password:%"))
# → 改为（宽松匹配，有空格也能命中）
base_filter.append(
    Log.payload.like("%Username:%") & Log.payload.like("%Password:%")
)
```

---

## 修复优先级

| # | Bug | 影响 | 优先级 |
|---|-----|------|--------|
| 1 | match_field 字段 fallback 缺失 | **规则完全失效** → 正则引擎任何规则都不命中 | 🔴 P0 |
| 3 | payload/request_path 不参与匹配 | POST 注入检测盲区 | 🔴 P0 |
| 5 | HTTP 暴力破解 LIKE 条件错误 | HTTP 暴力破解永不触发 | 🟠 P1 |
| 2 | break 导致多规则无法联合标注 | 攻击描述不完整 | 🟡 P2 |
| 4 | 捕获组性能问题 | 高并发时延增加 | 🟢 P3 |

---

## 下一步

直接修改 `log_service.py` 中 `create_log` 方法的正则匹配段（L538–575），完成以下改动：
1. **Bug 1+3 合并修复**：构建 `combined_content`，替换单字段取值逻辑
2. **Bug 5 修复**：修正 HTTP 暴力破解 LIKE 条件
3. **Bug 2 可选增强**：去掉 `break`，改为继续扫描追加描述
4. **性能优化（Bug 4）**：加入 `_compiled_rules` 类级缓存

是否立即开始代码修改？
