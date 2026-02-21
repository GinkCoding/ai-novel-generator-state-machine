#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Information Flow Validator - 信息流验证器

核心功能：
1. 生成前验证信息传递路径
2. 检查角色能否知道某事
3. 检查 A 能否告诉 B 某事
4. 生成知识约束提示词
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime


class InformationFlowValidator:
    """信息流验证器"""
    
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
    
    def get_character_name(self, char_id: str) -> str:
        """获取角色名称"""
        # 简化实现，实际需要映射表
        name_map = {
            "char_001": "胡念一",
            "char_002": "王浩然",
            "char_003": "杨雨霏",
            "char_004": "陈三爷"
        }
        return name_map.get(char_id, char_id)
    
    def can_character_know(self, char_id: str, fact_description: str) -> Tuple[bool, str]:
        """
        检查角色能否知道某事
        
        Returns:
            (能否知道，原因)
        """
        char_data = self.world.get('characters', {}).get(char_id, {})
        knowledge = char_data.get('knowledge', {})
        
        # 检查是否已经知道
        for fact_id, fact_info in knowledge.items():
            if fact_description.lower() in fact_info.get('what', '').lower():
                return True, f"{self.get_character_name(char_id)} 已经知道：{fact_info['what']}"
        
        # 不知道，需要信息传递
        return False, f"{self.get_character_name(char_id)} 还不知道\"{fact_description}\"，需要有人告诉他"
    
    def can_reveal_information(self, speaker_id: str, listener_id: str, fact_description: str) -> Tuple[bool, str]:
        """
        检查 A 能否告诉 B 关于某事的信息
        
        Returns:
            (能否告诉，原因)
        """
        speaker_name = self.get_character_name(speaker_id)
        listener_name = self.get_character_name(listener_id)
        
        # 检查 1: A 是否知道？
        speaker_data = self.world.get('characters', {}).get(speaker_id, {})
        speaker_knowledge = speaker_data.get('knowledge', {})
        
        known_fact = None
        for fact_id, fact_info in speaker_knowledge.items():
            if fact_description.lower() in fact_info.get('what', '').lower():
                known_fact = fact_info
                break
        
        if not known_fact:
            return False, f"{speaker_name} 不知道\"{fact_description}\"，无法告诉别人"
        
        # 检查 2: B 是否已经知道？
        listener_data = self.world.get('characters', {}).get(listener_id, {})
        listener_knowledge = listener_data.get('knowledge', {})
        
        for fact_id, fact_info in listener_knowledge.items():
            if fact_description.lower() in fact_info.get('what', '').lower():
                return True, f"{listener_name} 已经知道，可以讨论"
        
        # 检查 3: 信任度是否足够？
        trust_level = self._get_trust_level(speaker_id, listener_id)
        is_secret = known_fact.get('is_secret', False)
        
        required_trust = 7 if is_secret else 3
        
        if trust_level < required_trust:
            return False, f"{speaker_name} 不信任 {listener_name} (trust={trust_level}<{required_trust})，不会告诉"
        
        # 检查 4: 是否有动机告诉？
        # 简化：假设有信任就会告诉
        return True, f"信息传递合理：{speaker_name} → {listener_name} (trust={trust_level})"
    
    def _get_trust_level(self, char_a: str, char_b: str) -> int:
        """获取两个角色之间的信任度"""
        char_data = self.world.get('characters', {}).get(char_a, {})
        relationships = char_data.get('relationships', {})
        
        if char_b in relationships:
            return relationships[char_b].get('trust', 0)
        
        return 0
    
    def generate_knowledge_constraints(self, scene_card: Dict) -> str:
        """生成知识约束提示词"""
        pov = scene_card.get('pov', '')
        participants = scene_card.get('participants', [])
        
        constraints = []
        constraints.append("## 信息流约束（必须严格遵守）\n")
        
        # POV 角色的知识
        pov_data = self.world.get('characters', {}).get(pov, {})
        pov_knowledge = pov_data.get('knowledge', {})
        
        if pov_knowledge:
            known_facts = [f["what"] for f in pov_knowledge.values()]
            constraints.append(f"{self.get_character_name(pov)} 已知的事实：")
            for fact in known_facts:
                constraints.append(f"  - {fact}")
        else:
            constraints.append(f"{self.get_character_name(pov)} 无特殊知识")
        
        constraints.append("\n")
        
        # 其他角色的秘密知识（POV 角色不知道的）
        secrets = []
        for char_id in participants:
            if char_id == pov:
                continue
            
            char_data = self.world.get('characters', {}).get(char_id, {})
            char_knowledge = char_data.get('knowledge', {})
            
            for fact_id, fact_info in char_knowledge.items():
                if fact_info.get('is_secret', False):
                    # POV 角色不知道的秘密
                    pov_knows = any(
                        fact_info['what'].lower() in f.get('what', '').lower()
                        for f in pov_knowledge.values()
                    )
                    if not pov_knows:
                        secrets.append({
                            "holder": self.get_character_name(char_id),
                            "what": fact_info['what']
                        })
        
        if secrets:
            constraints.append(f"{self.get_character_name(pov)} 不知道的秘密：")
            for secret in secrets:
                constraints.append(f"  - {secret['what']} (只有{secret['holder']}知道)")
            constraints.append("\n重要：{self.get_character_name(pov)} 不能直接知道这些秘密！")
            constraints.append("必须等知情角色告诉他，他才能知道。")
        
        return "\n".join(constraints)
    
    def validate_dialogue(self, dialogue_text: str, speaker_id: str, listener_id: str) -> List[Dict]:
        """
        验证对话中的信息传递是否合理
        
        Returns:
            问题列表
        """
        issues = []
        
        # 简化实现：检查是否提到了秘密信息
        # 实际需要更复杂的 NLP 分析
        
        speaker_data = self.world.get('characters', {}).get(speaker_id, {})
        speaker_knowledge = speaker_data.get('knowledge', {})
        
        listener_data = self.world.get('characters', {}).get(listener_id, {})
        listener_knowledge = listener_data.get('knowledge', {})
        
        # 检查对话中是否提到了 listener 不该知道的信息
        for fact_id, fact_info in speaker_knowledge.items():
            if fact_info.get('is_secret', False):
                # 检查 listener 是否已经知道
                listener_knows = any(
                    fact_info['what'].lower() in f.get('what', '').lower()
                    for f in listener_knowledge.values()
                )
                
                if not listener_knows:
                    # 检查对话中是否提到了
                    if fact_info['what'] in dialogue_text:
                        issues.append({
                            "type": "信息流错误",
                            "severity": "critical",
                            "description": f"{self.get_character_name(listener_id)} 不该知道\"{fact_info['what']}\"",
                            "context": dialogue_text[:200],
                            "why_illogical": f"只有{self.get_character_name(speaker_id)}知道这个秘密，{self.get_character_name(listener_id)} 还没被告知",
                            "suggestion": "改为{self.get_character_name(speaker_id)}告诉{self.get_character_name(listener_id)}，或者不要让{self.get_character_name(listener_id)}知道"
                        })
        
        return issues
    
    def update_knowledge_after_transfer(self, speaker_id: str, listener_id: str, fact_id: str, timeline_path: str):
        """信息传递后，更新 listener 的知识"""
        speaker_data = self.world.get('characters', {}).get(speaker_id, {})
        speaker_knowledge = speaker_data.get('knowledge', {})
        
        if fact_id not in speaker_knowledge:
            return False, f"{speaker_id} 不知道 {fact_id}"
        
        # 更新 listener 的知识
        listener_data = self.world.get('characters', {}).get(listener_id, {})
        if 'knowledge' not in listener_data:
            self.world['characters'][listener_id]['knowledge'] = {}
        
        fact_info = speaker_knowledge[fact_id].copy()
        fact_info['known_at'] = f"chapter_{self.world['time']['chapter']}"
        fact_info['source'] = f"{self.get_character_name(speaker_id)} 告知"
        fact_info['source_char'] = speaker_id
        
        self.world['characters'][listener_id]['knowledge'][fact_id] = fact_info
        
        # 保存
        self._save_world()
        
        # 记录到 timeline
        self._record_to_timeline(speaker_id, listener_id, fact_id, timeline_path)
        
        return True, "知识已更新"
    
    def _save_world(self):
        """保存 World State"""
        with open(self.world_state_path, 'w', encoding='utf-8') as f:
            json.dump(self.world, f, ensure_ascii=False, indent=2)
    
    def _record_to_timeline(self, speaker_id: str, listener_id: str, fact_id: str, timeline_path: str):
        """记录信息传递到 timeline"""
        event = {
            "event_id": f"info_{fact_id}_{speaker_id}_to_{listener_id}",
            "type": "information_transfer",
            "from": speaker_id,
            "to": listener_id,
            "fact": fact_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(timeline_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')


def validate_before_generation(scene_card: Dict, world_state_path: str) -> Dict:
    """
    生成前验证
    
    Returns:
        {
            "pass": bool,
            "constraints": "知识约束提示词",
            "issues": [...]
        }
    """
    validator = InformationFlowValidator(world_state_path)
    
    # 生成知识约束
    constraints = validator.generate_knowledge_constraints(scene_card)
    
    # 检查是否有明显的信息流问题
    pov = scene_card.get('pov', '')
    goal = scene_card.get('goal', '')
    
    issues = []
    
    # 检查 SceneCard 的 goal 是否要求 POV 角色知道不该知道的
    # 简化实现
    
    return {
        "pass": len(issues) == 0,
        "constraints": constraints,
        "issues": issues
    }


if __name__ == "__main__":
    # 测试
    validator = InformationFlowValidator("novel_ci/state/world.json")
    
    # 测试 1: 陈三爷能否告诉胡念一关于地质队的事
    can_reveal, reason = validator.can_reveal_information(
        "char_004", "char_001", "1959 年地质队"
    )
    print(f"测试 1: {can_reveal}, {reason}")
    
    # 测试 2: 生成知识约束
    scene_card = {
        "pov": "char_001",
        "participants": ["char_001", "char_002", "char_003", "char_004"]
    }
    constraints = validator.generate_knowledge_constraints(scene_card)
    print(f"\n测试 2:\n{constraints}")
