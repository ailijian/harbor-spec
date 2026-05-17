# Harbor-spec 经典案例｜代码变了，契约没变：一次 `IndexBuilder.iter_build` 的真实漂移治理
>测试通过并不代表上下文可信；Harbor-spec 捕获的是实现、契约与 AI coding 记忆之间的漂移。

## 1. 案例摘要

本案例发生在 Harbor-spec v1.4.0 的 **Core Neutralization + TypeScript Contract Governance** 改造过程中。

在 Task 2B 中，我们将 `IndexBuilder.iter_build()` 的文件发现来源从原来的 Python-only 扫描逻辑，切换为通过 `AdapterRegistry` 做语言适配器门控。虽然该改动在行为上仍保持 Python-only，且所有单元测试通过，但 `harbor checkpoint --ci --format json` 检测到：

```text
harbor.core.index.IndexBuilder.iter_build
body changed, contract static
```

也就是：

> **实现已经变化，但契约说明没有同步变化。**

这正是 Harbor-spec 要解决的经典问题：**测试通过，不代表上下文契约仍然可信；代码能跑，不代表 AI / 人类协作者理解的契约仍然准确。**

本案例的最终处理方式不是直接 `harbor accept`，而是先进行 drift triage，确认这是“真实契约漂移”，然后最小更新 `iter_build` 的 docstring 契约，再重新运行 checkpoint，最后由人工 review 后执行 `harbor accept`。

---

## 2. 背景：为什么会发生这个案例

v1.4.0 的目标不是简单增加 TypeScript 文件扫描，而是把 Harbor-spec 从 Python docstring governance 推进到 language-neutral contract governance。实施规格已经明确：v1.4.0 要覆盖 Core Neutralization + TypeScript MVP，同时把 Python zero regression、JSON additive compatibility、`target_id` / `func_id` 兼容策略前置为约束。

在任务拆解中，Task 2 的目标是：

```text
引入 adapter registry，解除 IndexBuilder / SyncEngine 对 PythonAdapter() 的硬编码依赖。
```

其中 Task 2.2 明确要求改造 `harbor/core/index.py`，让 `IndexBuilder` 通过 registry 统一调用语言 adapter，同时 Task 2.4 又要求默认仅启用 Python，TypeScript 处于关闭或显式启用状态。

因此，Task 2B 的真实目标是：

```text
让 IndexBuilder 知道 AdapterRegistry 的存在，
但不改变现有 Python index 行为。
```

这也是 checklist 中“IndexBuilder 与 SyncEngine 已改为通过 adapter registry 工作，不再硬编码 PythonAdapter()”和“Python 解析、func_id、contract_hash、contract presence、DDT 与 semantic audit 行为保持零回归”的具体落地。

---

## 3. 发生了什么

### 3.1 Task 2B 的实现变化

Task 2B 中，Codex 对 `harbor/core/index.py` 做了最小改造：

```text
IndexBuilder.__init__ 新增 self.registry = AdapterRegistry.from_config(cfg)

iter_build() 的文件来源：
从 _iter_py_files()
切换为 _iter_files_by_enabled_adapters()

新增 _iter_files_by_enabled_adapters()
当前仅做 Python 门控，保持 Python-only 文件发现行为不变。
```

同时严格保持：

```text
process_file_worker 仍保持原 multiprocessing / Windows 兼容路径
HarborDB 写入 entry 结构不变
id / qualified_name / name 不变
signature_hash / body_hash / contract_hash 不变
docstring_raw_hash / scope / strictness / lineno 不变
checkpoint / DDT / audit / stale / doctor 输出语义不变
```

### 3.2 测试结果

Task 2B 后的测试结果是：

```text
pytest tests/test_adapter_registry.py：通过
pytest tests/test_index_builder_registry_integration.py：通过
pytest：通过
```

也就是说，从传统测试视角看：

> 代码没坏，功能没坏，Python 行为也没明显回归。

但 Harbor-spec 的 checkpoint 发现了另一个问题。

---

## 4. Harbor-spec 检测到的问题

运行：

```powershell
harbor checkpoint --ci --format json
```

结果失败，核心阻断项为：

```text
drift=1

target:
harbor.core.index.IndexBuilder.iter_build

reason:
body changed, contract static
```

这意味着 Harbor-spec 判断：

```text
函数实现发生变化
但对应契约文档没有变化
```

它没有报告：

```text
untracked_function
contract_gap
contract_parse_error
```

而是准确报告了：

```text
possible contract drift
```

在这个案例中，Harbor-spec 的判断是正确的。

因为 `iter_build()` 的内部文件来源已经从直接 Python 文件扫描，变成通过 `AdapterRegistry` 门控的文件发现机制。即使当前默认仍然只启用 Python，函数的工程语义已经发生变化：

```text
过去：
iter_build 直接面向 Python 文件发现。

现在：
iter_build 通过 adapter registry 的 enabled adapters 决定文件发现入口。
```

这已经不是纯实现细节，而是函数契约需要向未来维护者、AI coding agent 和文档上下文说明的新事实。

---

## 5. 为什么这是 Harbor-spec 的经典案例

这个案例经典在于：**所有传统信号都显示“没问题”，只有契约治理信号显示“需要处理”。**

| 检查方式                 | 结果 | 说明                |
| -------------------- | -- | ----------------- |
| 单元测试                 | 通过 | 行为没有明显回归          |
| 全量 pytest            | 通过 | 项目测试体系未发现错误       |
| checkpoint           | 失败 | Harbor 发现代码与契约不同步 |
| contract_gap         | 0  | 并不是缺少契约           |
| contract_parse_error | 0  | 契约格式没有坏           |
| drift                | 1  | 实现变了，但契约没变        |

这说明 Harbor-spec 不是简单的 lint，也不是普通测试工具。

它治理的是：

```text
代码实现
契约文档
上下文索引
AI coding 记忆
CI gate
人工 review
```

之间的一致性。

v1.4.0 的实施规格也明确强调，任务完成不能只靠代码测试，还需要通过 fixture、golden JSON、回归测试和命令级集成检查验证边界。

---

## 6. 正确解决流程

本案例采用了 5 步标准流程。

---

### Step 1：不要直接 accept

当 checkpoint 报告：

```text
body changed, contract static
```

时，第一反应不应该是：

```powershell
harbor accept
```

因为这会把可能的真实契约漂移直接压入 baseline。

正确做法是先判断：

```text
这是实现细节变化？
还是函数契约真的需要同步？
```

---

### Step 2：进行 drift triage

本案例的 triage 问题清单如下：

```text
1. iter_build 的外部行为是否改变？
2. index entry schema 是否改变？
3. body_hash / contract_hash / signature_hash 语义是否改变？
4. 文件发现来源是否改变？
5. docstring 是否仍准确描述当前实现？
6. 当前变化是否会影响未来多语言适配？
```

结论是：

```text
外部 Python 行为保持兼容。
index entry schema 没变。
hash 语义没变。
但文件发现来源从 Python-only 入口变成 AdapterRegistry 门控。
docstring 没有同步描述这一点。
```

因此这是：

```text
真实契约漂移
```

而不是：

```text
误报
```

---

### Step 3：最小更新 docstring 契约

处理方式不是扩大实现范围，而是只更新 `IndexBuilder.iter_build` 的 docstring。

同步内容包括：

```text
1. 文件来源通过 AdapterRegistry 门控获取。
2. v1.4.0 当前默认仅启用 Python。
3. 当前仍保持 Python-only index 语义。
4. worker 路径暂不改变。
5. HarborDB entry schema 暂不改变。
```

同时保留原有 Harbor 标签：

```text
@harbor.scope
@harbor.l3_strictness
@harbor.idempotency
```

这一步体现了 Harbor-spec 的一个关键原则：

> **契约更新不等于重写文档，而是把已经发生的工程事实最小同步到契约层。**

---

### Step 4：重新运行 checkpoint

更新 docstring 后再次运行：

```powershell
harbor checkpoint --ci --format json
```

结果从：

```text
drift=1
body changed, contract static
```

变为：

```text
modified=1
body + contract changed
```

同时：

```text
contract_gap = 0
contract_parse_error = 0
drift = 0
```

这个变化非常关键。

它说明 Harbor-spec 已经识别到：

```text
代码变了
契约也同步变了
现在不再是“静态契约下的潜在漂移”
而是“有意识的代码 + 契约共同修改”
```

---

### Step 5：人工 review 后 accept

最后，在人工确认：

```text
实现变化符合 Task 2B 边界
docstring 更新准确
Python 行为零回归
checkpoint 只剩 modified
```

之后执行：

```powershell
harbor accept
```

随后完整验证：

```powershell
pytest
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

最终全部通过：

```text
pytest：pass
checkpoint：pass
stale：pass
doctor：pass
```

---

## 7. 案例时间线

```text
Task 0
捕获 v1.3.x 干净基线：
pytest / checkpoint / stale / doctor 全部通过。

Task 1
新增 ContractSubject / ContractSource / LanguageAdapter。
首次出现 untracked_function，经人工 review 后 accept。

Task 3.1
新增 FunctionContract -> ContractSubject 兼容映射层。
pytest 与 checkpoint 均通过。

Task 2A
新增 AdapterRegistry skeleton。
默认 Python enabled，TypeScript disabled。
pytest 与 checkpoint 均通过。

Task 2B
IndexBuilder 接入 AdapterRegistry skeleton。
pytest 通过，但 checkpoint 报 drift：
IndexBuilder.iter_build body changed, contract static。

Task 2B-Repair
最小同步 iter_build docstring。
checkpoint 从 drift 转为 modified：
body + contract changed。

Task 2B Accept
人工 review 后执行 harbor accept。
pytest / checkpoint / stale / doctor 全部通过。
```

---

## 8. 关键命令

### 8.1 发现问题

```powershell
harbor checkpoint --ci --format json
```

输出关键信号：

```text
drift=1
target=harbor.core.index.IndexBuilder.iter_build
reason=body changed, contract static
```

---

### 8.2 修复后验证

```powershell
pytest tests/test_index_builder_registry_integration.py
pytest
harbor checkpoint --ci --format json
```

输出关键信号：

```text
modified=1
target=harbor.core.index.IndexBuilder.iter_build
reason=body + contract changed

contract_gap=0
contract_parse_error=0
drift=0
```

---

### 8.3 人工接受后完整验证

```powershell
harbor accept

pytest
harbor checkpoint --ci --format json
harbor stale --ci --format json
harbor doctor --ci --format json
```

最终结果：

```text
pytest=pass
checkpoint=pass
stale=pass
doctor=pass
```

---

## 9. 这个案例中 Harbor-spec 捕获的不是 bug，而是“上下文漂移”

很多工具只能回答：

```text
代码是否能运行？
测试是否通过？
类型是否正确？
格式是否规范？
```

但 Harbor-spec 在这个案例里回答的是：

```text
代码实现变化后，契约说明是否仍然准确？
AI coding agent 以后读到的上下文是否会误导它？
未来维护者是否知道这里已经从 Python-only 文件发现切换到 adapter registry 门控？
```

这就是 Harbor-spec 与普通测试 / lint / 类型检查的根本区别。

---

## 10. 为什么不能直接 accept

如果当时直接执行：

```powershell
harbor accept
```

会产生一个隐患：

```text
baseline 会接受新的 body_hash
但 docstring 仍然描述旧的 Python-only 文件发现语义
```

长期后果是：

```text
1. AI coding agent 读到过期契约。
2. 后续 Task 2C / Task 4 继续接入多语言时，可能误以为 IndexBuilder 仍是 Python-only 设计。
3. generated context 可能传播错误认知。
4. 人类维护者看到契约时无法理解为什么这里已有 AdapterRegistry。
5. Harbor baseline 看似干净，但上下文事实已经腐烂。
```

这就是 Harbor-spec 要防止的“静默上下文腐烂”。

---

## 11. 这个案例证明了什么

### 11.1 证明 Harbor-spec 不只是检测缺文档

本次没有 `contract_gap`。

问题不是：

```text
没有契约
```

而是：

```text
契约存在，但没有跟上实现变化
```

这比缺文档更隐蔽，也更危险。

---

### 11.2 证明 Harbor-spec 可以约束 AI coding 的任务边界

Task 2B 原本很容易被 Agent 扩大成：

```text
顺手接 SyncEngine
顺手实现 TypeScriptAdapter
顺手改 checkpoint JSON
顺手更新更多 core 行为
```

但 Harbor checkpoint 把改动集中到了具体目标：

```text
harbor.core.index.IndexBuilder.iter_build
```

并要求明确处理：

```text
实现变了
契约是否也应该变？
```

这帮助任务保持边界。

---

### 11.3 证明“测试通过”不等于“契约一致”

本案例中：

```text
pytest 全部通过
```

但 checkpoint 仍然失败。

这是合理的。

因为测试验证的是行为结果，Harbor 验证的是：

```text
行为事实
契约事实
上下文事实
baseline 事实
```

之间是否一致。

---

### 11.4 证明 Core Neutralization 必须分阶段推进

v1.4.0 的任务规格要求避免一次性大改，并将方案拆成任务、依赖、验证、边界四位一体的执行规格。

本案例证明这个策略是正确的：

```text
如果 Task 2B 和 Task 2C 一起做，
checkpoint 可能同时报多个 drift，
很难判断哪个契约需要同步。
```

分阶段推进让问题被定位到一个函数：

```text
IndexBuilder.iter_build
```

因此修复成本很低。

---

## 12. 可复用的标准处理流程

以后凡是出现：

```text
body changed, contract static
```

都可以使用以下流程。

### 12.1 标准流程

```text
1. 停止继续开发。
2. 不要直接 harbor accept。
3. 定位 checkpoint 报告的 target。
4. 阅读该 target 的 docstring / contract。
5. 对照本次实现变化。
6. 判断是否真实契约漂移。
7. 如果是误报或纯实现细节，记录原因，人工决定是否 accept。
8. 如果是真实契约漂移，最小更新契约说明。
9. 重新运行 pytest + checkpoint。
10. 如果 drift 变为 modified / contract_changed，进行人工 review。
11. review 通过后 harbor accept。
12. 再运行 checkpoint / stale / doctor。
```

---

### 12.2 判断矩阵

| Harbor 信号                              | 含义                   | 推荐处理                    |
| -------------------------------------- | -------------------- | ----------------------- |
| `untracked_function`                   | 新函数未进入 baseline      | review 新函数后 accept      |
| `contract_gap`                         | 需要契约但缺失              | 补契约，不直接 accept          |
| `contract_parse_error`                 | 契约格式无法解析             | 修契约格式                   |
| `drift: body changed, contract static` | 实现变了，契约没变            | triage，必要时更新契约          |
| `modified: body + contract changed`    | 实现和契约都变了             | review 后 accept         |
| `contract_changed`                     | 契约变了，实现没变            | 判断是否文档修订或契约收紧           |
| `stale`                                | generated context 过期 | review 后运行 sync-context |

---

## 13. 可复用 Prompt：给 Agent 的处理指令

```text
当前 harbor checkpoint --ci --format json 发现：
- target: <TARGET>
- reason: body changed, contract static

请执行 contract drift triage。

严格要求：
1. 不要执行 harbor accept。
2. 不要继续后续开发任务。
3. 不要扩大当前任务范围。
4. 只分析 checkpoint 指定 target。

处理步骤：
1. 阅读该 target 的 docstring / contract。
2. 对照本次实现变化。
3. 判断这是纯实现细节变化，还是契约需要同步。
4. 如果契约需要同步，请最小更新 docstring，保留所有 @harbor.* 标签。
5. 不改变函数签名。
6. 不改变与本次 drift 无关的实现。
7. 运行：
   - pytest <相关测试>
   - pytest
   - harbor checkpoint --ci --format json
8. 如果 checkpoint 从 drift 变为 modified / contract_changed，停止并报告，等待人工 review/accept。
9. 不要自动执行 harbor accept。
```

---

## 14. 可复用的 docstring 更新模板

适用于“内部实现入口变化，但外部行为兼容”的场景：

```python
def target_function(...):
    """
    <一句话说明函数职责>。

    Implementation notes:
    - This function now obtains its input candidates through <new coordination layer>.
    - In v<version>, the default behavior remains compatible with <old behavior>.
    - The worker path and persisted entry schema are intentionally unchanged.
    - This change prepares the code path for <future capability>, without enabling it by default.

    @harbor.scope <public/internal>
    @harbor.l3_strictness <strict/standard/light>
    @harbor.idempotency <...>
    """
```

对应本案例：

```text
新的 coordination layer = AdapterRegistry
旧行为 = Python-only index
future capability = multi-language adapter discovery
```

---

## 15. 可复用的 review checklist

人工 review 时检查：

```text
[ ] checkpoint 报告的 target 是否唯一？
[ ] pytest 是否通过？
[ ] checkpoint 是否已从 drift 变为 modified / contract_changed？
[ ] contract_gap 是否为 0？
[ ] contract_parse_error 是否为 0？
[ ] docstring 是否准确描述了真实实现变化？
[ ] 是否保留了原 @harbor.* 标签？
[ ] 是否没有扩大任务范围？
[ ] 是否没有引入 TypeScriptAdapter 或 SyncEngine 改造？
[ ] 是否没有改变 Python 行为和 index entry schema？
[ ] 是否可以执行 harbor accept？
```

---

## 17. 一句话总结

这个案例最能说明 Harbor-spec 的价值：

> **Harbor-spec 不是为了阻止代码变化，而是为了确保代码变化之后，契约、上下文、baseline 和协作者认知也一起被正确更新。**

在本案例中，`IndexBuilder.iter_build` 的代码变化本身没有破坏测试，也没有破坏 Python 行为；但它改变了函数的工程事实：文件发现来源从 Python-only 入口切换到了 AdapterRegistry 门控。Harbor-spec 正确识别出“代码变了，契约没变”，推动我们先同步契约，再接受 baseline。

这就是 Harbor-spec 在 AI coding 场景下的核心价值：**让代码实现和上下文契约不再静默漂移。**
