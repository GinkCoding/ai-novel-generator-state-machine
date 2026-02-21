#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel CI - 硬规则校验器

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


class WorldStateValidator:
    """World State 硬规则校验器"""
    
    def __init__(self, canon_path: str, world_path: str, timeline_path: str):
        self.canon = self._load_json(canon_path)
        self.world = self._load_json(world_path)
        self.timeline = self._load_jsonl(timeline_path)
        self.issues: List[Dict[str, Any]] = []
    
    def _load_json(self, path: str) -> Dict:
        """加载 JSON 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _load_jsonl(self, path: str) -> List[Dict]:
        """加载 JSONL 文件"""
        events = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        events.append(json.loads(line))
        except FileNotFoundError:
            pass
        return events
    
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
        # TODO: 实现时间线检查
        pass
    
    def _check_no_teleport(self, extract_data: Dict):
        """H2.2: 禁止瞬移检查"""
        # TODO: 实现位置连续性检查
        pass
    
    def _check_no_item_spawn(self, extract_data: Dict):
        """H3.1: 禁止物品凭空出现"""
        # TODO: 实现物品来源检查
        pass
    
    def _check_no_item_duplicate(self, extract_data: Dict):
        """H3.2: 禁止物品同时被多人持有"""
        # TODO: 实现物品唯一性检查
        pass
    
    def _check_pov_knowledge_boundary(self, extract_data: Dict):
        """H1.3: 视角人物知识边界检查"""
        # TODO: 实现知识边界检查
        pass
    
    def _check_relation_change_trigger(self, extract_data: Dict):
        """H4.1: 关系变化需有触发"""
        # TODO: 实现关系变化检查
        pass
    
    def _check_causal_chain(self, extract_data: Dict):
        """H5: 因果链完整检查"""
        # TODO: 实现因果链检查
        pass
    
    def _check_canon_exists(self, extract_data: Dict):
        """H2.3/H3.3: 地点/物品必须在 canon 中定义"""
        # TODO: 实现 canon 存在性检查
        pass


def main():
    """主函数"""
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
    
    # 执行校验
    validator = WorldStateValidator(canon_path, world_path, sys.argv[3])
    # 注意：timeline_path 应该是独立的，这里简化处理
    result = validator.validate_all(extract_data)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回状态码
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
