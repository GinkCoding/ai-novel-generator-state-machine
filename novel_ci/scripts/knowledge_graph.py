#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Graph - 角色知识图谱管理

核心功能：
1. 记录每个角色知道什么
2. 什么时候知道的
3. 从谁那里知道的
4. 能否告诉别人
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class KnowledgeGraph:
    """角色知识图谱"""
    
    def __init__(self, world_state_path: str):
        self.world_state_path = Path(world_state_path)
        self.world = self._load_world()
    
    def _load_world(self) -> Dict:
        """加载 World State"""
        try:
            with open(self.world_state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"characters": {}}
    
    def save(self):
        """保存 World State"""
        with open(self.world_state_path, 'w', encoding='utf-8') as f:
            json.dump(self.world, f, ensure_ascii=False, indent=2)
    
    def get_character_knowledge(self, char_id: str) -> Dict[str, Any]:
        """获取角色的知识"""
        char_data = self.world.get('characters', {}).get(char_id, {})
        return char_data.get('knowledge', {})
    
    def add_knowledge(self, char_id: str, fact_id: str, fact_data: Dict):
        """添加角色的知识"""
        if char_id not in self.world['characters']:
            self.world['characters'][char_id] = {}
        
        if 'knowledge' not in self.world['characters'][char_id]:
            self.world['characters'][char_id]['knowledge'] = {}
        
        self.world['characters'][char_id]['knowledge'][fact_id] = {
            **fact_data,
            "known_at": fact_data.get('known_at', datetime.now().isoformat()),
            "source": fact_data.get('source', 'unknown'),
            "source_char": fact_data.get('source_char', None)
        }
    
    def can_know(self, char_id: str, fact_id: str) -> tuple[bool, str]:
        """
        检查角色能否知道某个事实
        
        Returns:
            (能否知道，原因)
        """
        knowledge = self.get_character_knowledge(char_id)
        
        # 已经知道
        if fact_id in knowledge:
            return True, f"{char_id} 已经知道 {fact_id}"
        
        # 不知道，需要信息传递
        return False, f"{char_id} 还不知道 {fact_id}，需要有人告诉他"
    
    def can_reveal(self, speaker_id: str, listener_id: str, fact_id: str) -> tuple[bool, str]:
        """
        检查 A 能否告诉 B 关于 fact 的信息
        
        Returns:
            (能否告诉，原因)
        """
        # 检查 1: A 是否知道 fact？
        speaker_knowledge = self.get_character_knowledge(speaker_id)
        if fact_id not in speaker_knowledge:
            return False, f"{speaker_id} 不知道 {fact_id}，无法告诉别人"
        
        # 检查 2: B 是否已经知道？
        listener_knowledge = self.get_character_knowledge(listener_id)
        if fact_id in listener_knowledge:
            return True, f"{listener_id} 已经知道 {fact_id}，可以讨论"
        
        # 检查 3: A 是否有动机告诉 B？
        trust_level = self._get_trust_level(speaker_id, listener_id)
        if trust_level < 5:
            return False, f"{speaker_id} 不信任 {listener_id} (trust={trust_level})，不会告诉"
        
        # 检查 4: fact 是否是秘密？
        fact_info = speaker_knowledge[fact_id]
        if fact_info.get('is_secret', False):
            return False, f"{fact_id} 是秘密，{speaker_id} 不会轻易告诉别人"
        
        return True, f"信息传递合理：{speaker_id} → {listener_id}"
    
    def _get_trust_level(self, char_a: str, char_b: str) -> int:
        """获取两个角色之间的信任度"""
        char_data = self.world.get('characters', {}).get(char_a, {})
        relationships = char_data.get('relationships', {})
        
        if char_b in relationships:
            return relationships[char_b].get('trust', 0)
        
        return 0
    
    def record_information_transfer(self, speaker_id: str, listener_id: str, fact_id: str, timeline_path: str):
        """记录信息传递到 timeline"""
        timeline_event = {
            "event_id": f"info_{fact_id}_{speaker_id}_to_{listener_id}",
            "type": "information_transfer",
            "from": speaker_id,
            "to": listener_id,
            "fact": fact_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 追加到 timeline
        with open(timeline_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(timeline_event, ensure_ascii=False) + '\n')
        
        # 更新 listener 的知识
        self.add_knowledge(listener_id, fact_id, {
            "what": fact_id,
            "known_at": datetime.now().isoformat(),
            "source": f"{speaker_id} 告知",
            "source_char": speaker_id
        })
        
        # 保存
        self.save()
    
    def generate_knowledge_constraints(self, scene_card: Dict) -> str:
        """生成知识约束提示词"""
        pov = scene_card.get('pov', '')
        participants = scene_card.get('participants', [])
        
        constraints = []
        
        # 每个角色的已知事实
        for char_id in participants:
            knowledge = self.get_character_knowledge(char_id)
            if knowledge:
                facts = list(knowledge.keys())
                constraints.append(f"{char_id} 已知：{facts}")
            else:
                constraints.append(f"{char_id} 无特殊知识")
        
        return "\n".join(constraints)


def check_information_flow(scene_card: Dict, draft: str, world_state_path: str) -> Dict:
    """
    检查信息流是否合理
    
    Returns:
        {
            "pass": bool,
            "issues": [...],
            "reasoning": "..."
        }
    """
    kg = KnowledgeGraph(world_state_path)
    issues = []
    
    # 提取对话中的信息传递
    # 简化实现：查找"告诉"、"说"等关键词
    # 实际需要更复杂的 NLP 分析
    
    lines = draft.split('\n')
    for i, line in enumerate(lines):
        # 检查是否有信息传递
        if '告诉' in line or '说' in line:
            # 提取说话者和听话者
            # 简化：假设是对话形式
            pass
    
    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "reasoning": "信息流检查完成"
    }


if __name__ == "__main__":
    # 测试
    kg = KnowledgeGraph("novel_ci/state/world.json")
    
    # 添加知识
    kg.add_knowledge("char_004", "fact_1959_team", {
        "what": "1959 年地质队被请走",
        "source": "师父告知",
        "source_char": "char_master",
        "is_secret": True
    })
    
    # 检查能否告诉
    can_reveal, reason = kg.can_reveal("char_004", "char_001", "fact_1959_team")
    print(f"陈三爷能否告诉胡念一？{can_reveal}, {reason}")
    
    # 保存
    kg.save()
