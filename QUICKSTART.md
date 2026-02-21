# 🚀 快速开始指南

## 1. 克隆项目

```bash
git clone https://github.com/GinkCoding/ai-novel-generator-state-machine.git
cd ai-novel-generator-state-machine
```

---

## 2. 配置环境

### 2.1 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

### 2.2 安装依赖
```bash
pip install -r requirements.txt
```

### 2.3 配置 API Key
```bash
cp .env.example .env
nano .env  # 编辑填入真实 API Key
```

**.env 内容：**
```bash
# 矽基流動 API 配置
SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxx  # 你的真实 API Key
```

⚠️ **重要：** `.env` 文件已在 `.gitignore` 中，不会被提交到 GitHub

---

## 3. 测试连接

```bash
python novel_generator.py --test-api
```

如果看到 `✅ API 连接成功`，说明配置正确。

---

## 4. 运行传统模式

```bash
python novel_generator.py
```

按提示输入：
- 小说标题
- 类型
- 主题
- 章节数

---

## 5. 运行状态机 CI 模式（新功能）⭐

### 5.1 初始化 World State

首先编辑 `novel_ci/state/canon.json`，添加你的小说设定：

```json
{
  "characters": [
    {
      "id": "char_001",
      "name": "胡念一",
      "identity": ["摸金校尉传人"],
      "abilities": ["分金定穴", "风水术"],
      "known_facts": ["father_alive_usa"]
    }
  ],
  "locations": [
    {
      "id": "loc_001",
      "name": "北京",
      "type": "city"
    },
    {
      "id": "loc_002",
      "name": "蜀山王墓入口",
      "type": "tomb_entrance"
    }
  ],
  "items": [
    {
      "id": "item_001",
      "name": "摸金符",
      "type": "key_item",
      "spiritual": true
    }
  ],
  "invariants": [
    "时间线必须单调递增",
    "角色不能瞬移",
    "物品不能凭空出现"
  ]
}
```

### 5.2 运行状态机生成器

```bash
python core/state_machine_generator.py
```

会自动生成第 1 章第 1 场，并执行完整的 7 步流水线。

---

## 6. 查看生成结果

### 6.1 查看 SceneCard
```bash
cat novel_ci/scenes/CH01_SC01.scene.json
```

### 6.2 查看正文
```bash
cat novels/chapter_01_scene_01.txt
```

### 6.3 查看 World State
```bash
cat novel_ci/state/world.json | jq
```

### 6.4 查看时间线
```bash
cat novel_ci/state/timeline.jsonl | jq -s
```

---

## 7. 自定义配置

### 7.1 修改模型配置

编辑 `core/state_machine_generator.py`：

```python
self.model_writer = "Qwen/Qwen2.5-72B-Instruct"  # 写作模型
self.model_architect = "THUDM/glm-4-9b-chat"     # 大纲模型
self.model_coder = "Qwen/Qwen2.5-Coder-32B-Instruct"  # 编辑模型
```

### 7.2 修改提示词模板

编辑 `templates/prompts.md`，调整各个模板的提示词。

### 7.3 添加新的校验规则

编辑 `novel_ci/scripts/validate.py`，添加新的 `_check_*` 方法。

---

## 8. 故障排除

### 问题 1：API Key 错误
```bash
❌ LLM API 调用失败：401 Unauthorized
```

**解决：** 检查 `.env` 文件中的 API Key 是否正确

### 问题 2：JSON 解析失败
```bash
❌ 无法解析 LLM 返回的 JSON
```

**解决：** 检查提示词模板，要求 LLM 仅输出 JSON

### 问题 3：校验失败
```bash
⚠️ 发现 3 个问题
```

**解决：** 查看具体问题，自动修复或手动修改 canon.json

---

## 9. 最佳实践

### 9.1 先规划再写作
1. 先完善 `canon.json`（角色/地点/物品设定）
2. 再运行生成器

### 9.2 小步快跑
- 一场一场生成（不要一次生成整章）
- 每场都跑完整流水线

### 9.3 及时更新 World State
- 每生成一场，检查 `world.json` 是否正确更新
- 如有错误，手动修正后继续

---

## 10. 进阶使用

### 10.1 批量生成
```python
from core.state_machine_generator import StateMachineNovelGenerator

config = {'project_root': '.'}
generator = StateMachineNovelGenerator(config)

outline = {
    'title': '我的小说',
    'location': 'loc_001',
    'pov': 'char_001',
    'goal': '开始冒险',
    'obstacle': '未知挑战',
    'outcome': '成功启程'
}

# 生成前 3 章
for chapter in range(1, 4):
    generator.generate_chapter(chapter, 1, outline)
```

### 10.2 手动校验
```bash
python novel_ci/scripts/validate.py \
  novel_ci/state/canon.json \
  novel_ci/state/world.json \
  novel_ci/reports/extract.json
```

---

## 📚 更多资源

- [完整文档](docs/)
- [提示词模板](templates/prompts.md)
- [校验规则说明](novel_ci/scripts/validate.py)
- [GitHub 仓库](https://github.com/GinkCoding/ai-novel-generator-state-machine)

---

**🎉 开始创作你的小说吧！**
