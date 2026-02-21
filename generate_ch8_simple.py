#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速生成第 8 章 - 使用当前会话模型配置
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 手动配置 World State
canon = {
    "characters": [
        {"id": "char_001", "name": "胡念一", "identity": ["摸金校尉传人", "胡八一之子"], "known_facts": ["father_alive_usa"]},
        {"id": "char_002", "name": "王浩然", "identity": ["机关术传人"]},
        {"id": "char_003", "name": "杨雨霏", "identity": ["Shirley 杨后人"]},
        {"id": "char_004", "name": "陈三爷", "identity": ["守墓人后代", "701 部门眼线"]}
    ],
    "invariants": ["时间线必须单调递增", "角色不能瞬移", "物品不能凭空出现", "胡念一知道胡八一在美国"]
}

world = {
    "characters": {
        "char_001": {"location": "loc_002_entrance", "inventory": ["item_001", "item_003"]},
        "char_002": {"location": "loc_002_entrance", "inventory": ["item_010"]},
        "char_003": {"location": "loc_002_entrance", "inventory": ["item_002"]},
        "char_004": {"location": "loc_002_entrance", "inventory": ["item_011"]}
    },
    "time": {"chapter": 7, "scene": 1}
}

# SceneCard（第 8 章第 1 场）
scene_card = {
    "ch": 8,
    "sc": 1,
    "time_anchor": "chapter_8_start",
    "location": "loc_002_entrance",
    "pov": "char_001",
    "participants": ["char_001", "char_002", "char_003", "char_004"],
    "goal": "陈三爷讲述 1959 年地质队真相，胡念一表明身份",
    "obstacle": "陈三爷隐瞒部分真相，701 部门监视",
    "outcome": "得知部分真相，决定继续进墓",
    "required_facts": ["evt_bg_001", "evt_bg_002"],
    "allowed_changes": {"trust": "+1"}
}

# 生成提示词
prompt = f"""你是《鬼吹灯第九部》小说作家。请根据以下 SceneCard 写第 8 章第 1 场正文。

## SceneCard
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 当前 World State
地点：墓门外门（loc_002_entrance）
时间：第 7 章之后
角色状态：
- 胡念一：摸金符 hot，知道胡八一在美国
- 王浩然：持有机关图
- 杨雨霏：持有黑玉古琮
- 陈三爷：守墓人后代 +701 眼线，持有 701 档案

## 核心设定（必须遵守）
1. 胡念一知道胡八一活着在美国（不要问"他现在在哪"）
2. 陈三爷是守墓人后代，也是 701 部门眼线
3. 1959 年地质队 12 人，5 人被守墓人"请走"，另外 7 人失踪
4. 三层谜团：
   - Layer 1（已解开）：地质队被守墓人"请走"
   - Layer 2（未解开）：另外 7 人去哪了
   - Layer 3（未解开）："请走"vs"特殊收容"哪个是真的

## 写作要求
1. 字数：约 4000 字
2. 视角：胡念一第一人称
3. 情绪描写含蓄化（用动作、神态代替直接情绪词）
4. 对话符合人物性格（胡念一内敛、王浩然幽默、杨雨霏简洁、陈三爷神秘）
5. 必须包含：
   - 破庙夜话场景
   - 陈三爷讲述 1959 年地质队（5 人被请走，7 人失踪）
   - 胡念一表明身份（"他是我爸。胡八一。"）
   - 陈三爷讲述胡八一 10 年前来访
   - 三层谜团揭示
   - 团队决定继续进墓

请写正文："""

print("\n📖 鬼吹灯第九部 - 第 8 章第 1 场 生成中...")
print("=" * 60)
print("📋 SceneCard:")
print(f"   地点：{scene_card['location']}")
print(f"   视角：{scene_card['pov']}")
print(f"   目标：{scene_card['goal']}")
print(f"   障碍：{scene_card['obstacle']}")
print("=" * 60)
print("\n✅ 配置完成，准备调用模型...\n")

# 保存 prompt 到文件
output_dir = Path(__file__).parent / 'novels'
output_dir.mkdir(exist_ok=True)

with open(output_dir / 'chapter_08_prompt.txt', 'w', encoding='utf-8') as f:
    f.write(prompt)

print(f"📁 Prompt 已保存到：{output_dir / 'chapter_08_prompt.txt'}")
print("\n⏳ 等待模型调用...\n")
