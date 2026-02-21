# 提示词模板库

## 1. SceneCard 生成模板

### system_prompt
```
你是一个专业的小说编剧。你的任务是根据提供的信息生成 SceneCard（场景卡）。

SceneCard 是小说的结构层，必须在写正文之前完成。

输出格式（JSON）：
{
  "ch": 章节号，
  "sc": 场景号，
  "time_anchor": "时间锚点（如：chapter_1_start）",
  "location": "地点 ID",
  "pov": "视角角色 ID",
  "participants": ["参与角色 ID 列表"],
  "goal": "场景目标",
  "obstacle": "障碍/冲突",
  "outcome": "结果",
  "required_facts": ["必须引用的既有事实 ID 列表"],
  "allowed_changes": {"trust": "+2"}  # 允许的变化类型
}

重要规则：
1. 不得引入 canon.json 之外的新设定
2. 必须遵守 World State 中的角色位置/物品状态
3. 场景目标必须明确
4. 障碍/冲突必须具体
```

### user_prompt_template
```
请为以下场景生成 SceneCard：

小说标题：{title}
章节：{chapter}
场景：{scene}
地点：{location}
视角角色：{pov}
场景目标：{goal}
障碍：{obstacle}
预期结果：{outcome}

当前 World State：
{world_state_json}

当前时间线（最近 5 个事件）：
{recent_timeline_json}

请生成 SceneCard（仅输出 JSON，不要其他内容）：
```

---

## 2. 正文写作模板

### system_prompt
```
你是一个专业的小说作家。你的任务是根据 SceneCard 写正文。

重要规则：
1. 不得引入 SceneCard 之外的新设定（地点/物品/角色）
2. 必须遵守 World State 中的角色位置/物品状态
3. 文风要符合小说类型（玄幻/科幻/言情等）
4. 字数要达到要求
5. 视角必须一致（不能跳视角）
6. 对话要符合角色性格

文风要求：
- 情绪描写含蓄化（用动作、神态、生理反应代替直接情绪词）
- 对话精炼化（符合人物性格）
- 说书风格统一（章末说书人语句规范化）
- 专业知识校准（风水术语、历史考古信息准确）
```

### user_prompt_template
```
请根据以下 SceneCard 写正文：

SceneCard:
{scene_card_json}

当前 World State:
{world_state_json}

要求：
- 字数：约 {word_count} 字
- 视角：{pov}
- 地点：{location}
- 参与角色：{participants}
- 文风：{genre}

SceneCard 中的关键情节点：
1. {goal}
2. {obstacle}
3. {outcome}

请写正文（不要输出 SceneCard 中已有的内容，只写正文）：
```

---

## 3. 事实抽取模板

### system_prompt
```
你是一个事实抽取器。你的任务是从小说正文中抽取结构化事实。

输出格式（JSON）：
{
  "events": [
    {
      "event_id": "evt_XXX",
      "seq": 序号，
      "title": "事件标题",
      "time_anchor": "时间锚点",
      "location": "地点 ID",
      "participants": ["角色 ID 列表"],
      "description": "事件描述",
      "changes": {
        "character_changes": {"char_001": {"location": "loc_002"}},
        "item_changes": {"item_001": {"state": "used"}},
        "relationship_changes": {"char_001_char_002": {"trust": "+1"}}
      },
      "evidence_quote": "原文证据句（必须是原文）"
    }
  ],
  "character_changes": {"char_001": {"location": "loc_002"}},
  "item_changes": {"item_001": {"state": "used"}},
  "location_changes": {"char_001": "loc_002"}
}

重要规则：
1. evidence_quote 必须是原文片段
2. 变化必须具体（如：location 从哪到哪，trust 从多少到多少）
3. 事件必须有明确的 time_anchor
```

### user_prompt_template
```
请从以下正文中抽取事实：

SceneCard:
{scene_card_json}

正文:
{draft_content}

请抽取事实（仅输出 JSON）：
```

---

## 4. 最小补丁修复模板

### system_prompt
```
你是一个专业的编辑。你的任务是根据校验问题修复正文。

重要规则：
1. 只改导致报错的最小句子集合
2. 不要重写整段
3. 保留原文风格
4. 修复后必须通过校验
```

### user_prompt_template
```
请根据以下校验问题修复正文：

校验问题:
{issues_text}

原文:
{draft_content}

请只修改必要的部分（输出完整修复后的正文）：

修复要求：
1. 针对每个问题，只改必要的句子
2. 保持原文风格不变
3. 修复后必须通过校验
```

---

## 5. 校验规则模板

### H2.2 禁止瞬移检查
```
检查角色位置变化是否有移动事件支持。

如果角色从 loc_A 变到 loc_B，必须有：
- travel 事件（说明移动方式和时间）
- 或场景描述中提到移动过程

错误示例：
- 角色在汶川，下一章突然出现在墓门（没有移动）

正确示例：
- "我们开车三个小时，从汶川到了墓门"
- evt_XXX: {"type": "travel", "from": "loc_wenchuan", "to": "loc_entrance", "duration": "3h"}
```

### H3.1 禁止物品凭空出现
```
检查新物品是否有来源。

如果角色获得了 item_X，必须有：
- acquire_item 事件（购买/获得/制造/拾取等）
- 或 canon.json 中说明是初始物品

错误示例：
- 角色突然拿出一个没见过的道具

正确示例：
- "我从背包里拿出昨天买的指南针"
- evt_XXX: {"type": "acquire_item", "item": "item_001", "method": "购买"}
```

### H1.3 知识边界检查
```
检查视角角色是否知道不该知道的信息。

如果角色知道 fact_X，必须满足：
- 角色亲眼所见
- 或有人告诉角色
- 或角色推理得出（且有推理过程）

错误示例：
- 胡念一不知道陈三爷身份，但内心独白提到"陈三爷是守墓人"

正确示例：
- "我看着陈三爷，心想这人身份不简单"（不知道具体身份）
```

---

## 6. World State 更新模板

### canon.json 模板
```json
{
  "meta": {
    "version": "1.0.0",
    "name": "小说名称",
    "created_at": "2026-02-21"
  },
  "characters": [
    {
      "id": "char_001",
      "name": "角色名",
      "identity": ["身份 1", "身份 2"],
      "abilities": ["能力 1", "能力 2"],
      "personality": ["性格特点 1", "性格特点 2"],
      "secrets": ["秘密 1", "秘密 2"],
      "known_facts": ["fact_001", "fact_002"],
      "taboos": ["禁忌 1", "禁忌 2"]
    }
  ],
  "locations": [
    {
      "id": "loc_001",
      "name": "地点名",
      "type": "city/mountain/tomb/etc",
      "description": "地点描述",
      "connections": ["loc_002", "loc_003"],
      "travel_time": {"loc_002": "3h", "loc_003": "1d"}
    }
  ],
  "items": [
    {
      "id": "item_001",
      "name": "物品名",
      "type": "key_item/weapon/tool/etc",
      "description": "物品描述",
      "abilities": ["能力 1", "能力 2"],
      "origin": "来源",
      "spiritual": true/false
    }
  ],
  "threads": [
    {
      "id": "thread_001",
      "name": "线索/伏笔名",
      "description": "线索描述",
      "status": "active/resolved/dropped",
      "planted_at": "chapter_1",
      "resolved_at": null
    }
  ],
  "invariants": [
    "时间线必须单调递增",
    "角色不能瞬移（移动需要时间）",
    "物品不能凭空出现或消失",
    "角色知识边界必须遵守",
    "关系变化必须有触发事件",
    "伏笔必须回收",
    "世界观必须一致（时代/地理/超自然）"
  ]
}
```

### world.json 模板
```json
{
  "characters": {
    "char_001": {
      "location": "loc_001",
      "inventory": ["item_001", "item_002"],
      "relationships": {
        "char_002": {"trust": 5, "last_updated": "chapter_1"}
      },
      "status": {"health": 100, "energy": 80}
    }
  },
  "items": {
    "item_001": {
      "state": "active",
      "holder": "char_001",
      "last_used": "chapter_1_scene_1"
    }
  },
  "time": {
    "chapter": 1,
    "scene": 1,
    "last_updated": "2026-02-21T12:00:00+08:00"
  },
  "last_commit": {
    "chapter": 1,
    "scene": 1,
    "timestamp": "2026-02-21T12:00:00+08:00"
  }
}
```

---

## 使用示例

### Python 调用示例
```python
from pathlib import Path

# 加载模板
template_dir = Path(__file__).parent / 'templates'
with open(template_dir / 'scene_card_system.md', 'r') as f:
    system_prompt = f.read()

with open(template_dir / 'scene_card_user.md', 'r') as f:
    user_template = f.read()

# 填充模板
user_prompt = user_template.format(
    title="测试小说",
    chapter=1,
    scene=1,
    location="loc_001",
    pov="char_001",
    goal="开始冒险",
    obstacle="未知挑战",
    outcome="成功启程",
    world_state_json=json.dumps(world, ensure_ascii=False, indent=2),
    recent_timeline_json=json.dumps(timeline[-5:], ensure_ascii=False, indent=2)
)

# 调用 LLM
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]
response = call_llm(messages)
```
