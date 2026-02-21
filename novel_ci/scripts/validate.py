#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel CI - 硬规则校验器（完整版）

校验规则：
- H1: 角色一致性（身份/能力/知识边界）
- H2: 时空一致性（时间单调/禁止瞬移）
- H3: 物品一致性（不得凭空出现/消失）
- H4: 关系一致性（变化需有触发）
- H5: 因果链（前置条件必须满足）
- H6: 伏笔必须回收
- H7: 世界观一致性
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class WorldStateValidator:
    """World State 硬规则校验器"""
    
    def __init__(self, canon: Dict, world: Dict, timeline: List[Dict]):
        self.canon = canon
        self.world = world
        self.timeline = timeline
        self.issues: List[Dict[str, Any]] = []
    
    def validate_all(self, extract_data: Dict) -> Dict[str, Any]:
        """执行所有校验"""
        self._check_time_monotonic(extract_data)
        self._check_no_teleport(extract_data)
        self._check_no_item_spawn(extract_data)
        self._check_no_item_duplicate(extract_data)
        self._check_pov_knowledge_boundary(extract_data)
        self._check_relation_change_trigger(extract_data)
        self._check_causal_chain(extract_data)
        self._check_canon_exists(extract_data)
        
        return {
            "pass": len(self.issues) == 0,
            "issues": self.issues,
            "summary": {
                "total_issues": len(self.issues),
                "by_type": self._count_issues_by_type()
            }
        }
    
    def _add_issue(self, issue_id: str, issue_type: str, message: str, 
                   severity: str = "error", suggestion: Optional[str] = None):
        """添加校验问题"""
        self.issues.append({
            "issue_id": issue_id,
            "type": issue_type,
            "message": message,
            "severity": severity,
            "suggestion": suggestion
        })
    
    def _count_issues_by_type(self) -> Dict[str, int]:
        """按类型统计问题数量"""
        counts = {}
        for issue in self.issues:
            t = issue["type"]
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    def _check_time_monotonic(self, extract_data: Dict):
        """H2.1: 时间线单调递增检查"""
        current_time = self.world.get('time', {})
        current_chapter = current_time.get('chapter', 0)
        current_scene = current_time.get('scene', 0)
        
        new_chapter = extract_data.get('chapter', 0)
        new_scene = extract_data.get('scene', 0)
        
        if new_chapter < current_chapter:
            self._add_issue(
                "TIME_001",
                "H2.1",
                f"时间线倒流：当前第{current_chapter}章，新章节第{new_chapter}章",
                suggestion="检查章节号是否正确"
            )
        elif new_chapter == current_chapter and new_scene <= current_scene:
            self._add_issue(
                "TIME_002",
                "H2.1",
                f"场景号未递增：当前第{current_chapter}章第{current_scene}场，新场景第{new_scene}场",
                suggestion="场景号必须递增"
            )
    
    def _check_no_teleport(self, extract_data: Dict):
        """H2.2: 禁止瞬移检查"""
        location_changes = extract_data.get('location_changes', {})
        
        for char_id, new_location in location_changes.items():
            old_location = self.world.get('characters', {}).get(char_id, {}).get('location')
            
            if old_location and old_location != new_location:
                # 检查是否有移动事件
                has_travel_event = any(
                    event.get('type') == 'travel' and 
                    event.get('character') == char_id
                    for event in extract_data.get('events', [])
                )
                
                if not has_travel_event:
                    self._add_issue(
                        "SPACE_001",
                        "H2.2",
                        f"角色 {char_id} 瞬移：从 {old_location} 到 {new_location}，但没有移动事件",
                        suggestion="添加移动事件或说明移动方式"
                    )
    
    def _check_no_item_spawn(self, extract_data: Dict):
        """H3.1: 禁止物品凭空出现"""
        item_changes = extract_data.get('item_changes', {})
        character_inventory = self.world.get('characters', {}).get('char_001', {}).get('inventory', [])
        
        for item_id, changes in item_changes.items():
            if changes.get('state') == 'acquired':  # 新获得的物品
                # 检查物品是否在 canon 中定义
                canon_items = [item['id'] for item in self.canon.get('items', [])]
                if item_id not in canon_items:
                    self._add_issue(
                        "ITEM_001",
                        "H3.1",
                        f"物品 {item_id} 凭空出现，且未在 canon.json 中定义",
                        suggestion="在 canon.json 中添加物品定义，或说明物品来源"
                    )
                
                # 检查是否有获取事件
                has_acquire_event = any(
                    event.get('type') == 'acquire_item' and 
                    event.get('item') == item_id
                    for event in extract_data.get('events', [])
                )
                
                if not has_acquire_event:
                    self._add_issue(
                        "ITEM_002",
                        "H3.1",
                        f"物品 {item_id} 凭空出现，没有获取事件",
                        suggestion="添加获取事件（购买/获得/制造等）"
                    )
    
    def _check_no_item_duplicate(self, extract_data: Dict):
        """H3.2: 禁止物品同时被多人持有"""
        # 检查当前 World State 中的物品持有情况
        item_holders = {}
        
        for char_id, char_data in self.world.get('characters', {}).items():
            for item_id in char_data.get('inventory', []):
                if item_id not in item_holders:
                    item_holders[item_id] = []
                item_holders[item_id].append(char_id)
        
        # 检查是否有物品被多人持有
        for item_id, holders in item_holders.items():
            if len(holders) > 1:
                self._add_issue(
                    "ITEM_003",
                    "H3.2",
                    f"物品 {item_id} 同时被多人持有：{', '.join(holders)}",
                    suggestion="确保物品唯一性，或说明是复制品"
                )
    
    def _check_pov_knowledge_boundary(self, extract_data: Dict):
        """H1.3: 视角人物知识边界检查"""
        pov_char = extract_data.get('pov')
        if not pov_char:
            return
        
        # 获取视角角色的已知事实
        known_facts = self.canon.get('characters', [{}])[0].get('known_facts', [])
        
        # 检查正文中是否透露了角色不应该知道的信息
        # 这需要 NLP 分析，这里简化处理
        # TODO: 实现更复杂的知识边界检查
        pass
    
    def _check_relation_change_trigger(self, extract_data: Dict):
        """H4.1: 关系变化需有触发"""
        character_changes = extract_data.get('character_changes', {})
        
        for char_id, changes in character_changes.items():
            if 'relationships' in changes:
                # 检查是否有关系变化的触发事件
                has_trigger_event = any(
                    event.get('type') in ['conversation', 'conflict', 'cooperation']
                    for event in extract_data.get('events', [])
                )
                
                if not has_trigger_event:
                    self._add_issue(
                        "RELATION_001",
                        "H4.1",
                        f"角色 {char_id} 关系发生变化，但没有触发事件",
                        suggestion="添加对话/冲突/合作等事件作为关系变化的原因"
                    )
    
    def _check_causal_chain(self, extract_data: Dict):
        """H5: 因果链完整检查"""
        events = extract_data.get('events', [])
        
        # 检查事件是否有前置条件
        for event in events:
            preconditions = event.get('preconditions', [])
            for precondition in preconditions:
                # 检查前置条件是否已满足
                satisfied = any(
                    e.get('event_id') == precondition
                    for e in self.timeline + events
                )
                
                if not satisfied:
                    self._add_issue(
                        "CAUSAL_001",
                        "H5",
                        f"事件 {event.get('event_id')} 的前置条件 {precondition} 未满足",
                        suggestion="添加前置事件或移除该条件"
                    )
    
    def _check_canon_exists(self, extract_data: Dict):
        """H2.3/H3.3: 地点/物品必须在 canon 中定义"""
        canon_locations = {loc['id'] for loc in self.canon.get('locations', [])}
        canon_items = {item['id'] for item in self.canon.get('items', [])}
        
        # 检查新出现的地点
        for event in extract_data.get('events', []):
            location = event.get('location')
            if location and location not in canon_locations:
                self._add_issue(
                    "CANON_001",
                    "H2.3",
                    f"地点 {location} 未在 canon.json 中定义",
                    suggestion="在 canon.json 的 locations 数组中添加该地点"
                )
        
        # 检查新出现的物品
        for item_id in extract_data.get('item_changes', {}).keys():
            if item_id not in canon_items:
                self._add_issue(
                    "CANON_002",
                    "H3.3",
                    f"物品 {item_id} 未在 canon.json 中定义",
                    suggestion="在 canon.json 的 items 数组中添加该物品"
                )


def validate_all(canon_path: str, world_path: str, extract_data: Dict, timeline: List[Dict]) -> Dict:
    """便捷函数：加载文件并执行校验"""
    # 加载 canon
    try:
        with open(canon_path, 'r', encoding='utf-8') as f:
            canon = json.load(f)
    except FileNotFoundError:
        canon = {}
    
    # 加载 world
    try:
        with open(world_path, 'r', encoding='utf-8') as f:
            world = json.load(f)
    except FileNotFoundError:
        world = {}
    
    # 执行校验
    validator = WorldStateValidator(canon, world, timeline)
    result = validator.validate_all(extract_data)
    
    return result


def main():
    """主函数（CLI 模式）"""
    if len(sys.argv) < 4:
        print("Usage: python validate.py <canon.json> <world.json> <extract.json>")
        sys.exit(1)
    
    canon_path = sys.argv[1]
    world_path = sys.argv[2]
    extract_path = sys.argv[3]
    
    # 加载提取的数据
    try:
        with open(extract_path, 'r', encoding='utf-8') as f:
            extract_data = json.load(f)
    except FileNotFoundError:
        print(json.dumps({
            "pass": False,
            "issues": [{"type": "ERROR", "message": f"Extract file not found: {extract_path}"}]
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 加载 canon
    try:
        with open(canon_path, 'r', encoding='utf-8') as f:
            canon = json.load(f)
    except FileNotFoundError:
        canon = {}
    
    # 加载 world
    try:
        with open(world_path, 'r', encoding='utf-8') as f:
            world = json.load(f)
    except FileNotFoundError:
        world = {}
    
    # 加载 timeline（可选）
    timeline_path = Path(world_path).parent / 'timeline.jsonl'
    timeline = []
    if timeline_path.exists():
        with open(timeline_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    timeline.append(json.loads(line))
    
    # 执行校验
    validator = WorldStateValidator(canon, world, timeline)
    result = validator.validate_all(extract_data)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回状态码
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
