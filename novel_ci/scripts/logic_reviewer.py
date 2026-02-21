#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logic Reviewer - 智能逻辑合理性审查器

检查硬规则校验器无法发现的深层逻辑问题：
- 常识合理性（帝王墓应该隐蔽）
- 动机合理性（701 为什么要灭口）
- 世界观一致性（是否符合时代/社会背景）
- 因果链深度（为什么→为什么→为什么）
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class LogicReviewer:
    """智能逻辑审查器"""
    
    def __init__(self, common_sense_path: str):
        self.common_sense = self._load_common_sense(common_sense_path)
        self.issues: List[Dict[str, Any]] = []
    
    def _load_common_sense(self, path: str) -> Dict:
        """加载常识知识库"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def review_all(self, scene_card: Dict, draft: str, world_state: Dict, canon: Dict) -> Dict[str, Any]:
        """执行所有逻辑审查"""
        self.issues = []
        
        # 1. 常识合理性检查
        self._check_common_sense(scene_card, draft)
        
        # 2. 动机合理性检查
        self._check_motivation(scene_card, draft, canon)
        
        # 3. 世界观一致性检查
        self._check_worldview_consistency(scene_card, draft, canon)
        
        # 4. 因果链深度检查
        self._check_causal_depth(scene_card, draft)
        
        # 5. 角色行为合理性检查
        self._check_character_behavior(scene_card, draft, canon)
        
        # 6. 设定自洽性检查
        self._check_internal_consistency(scene_card, draft, world_state)
        
        return {
            "pass": len(self.issues) == 0,
            "issues": self.issues,
            "summary": {
                "total_issues": len(self.issues),
                "by_category": self._count_by_category(),
                "severity_distribution": self._count_by_severity()
            }
        }
    
    def _add_issue(self, category: str, severity: str, message: str, 
                   suggestion: str, context: Optional[str] = None):
        """添加逻辑问题"""
        self.issues.append({
            "category": category,
            "severity": severity,  # critical / major / minor
            "message": message,
            "suggestion": suggestion,
            "context": context
        })
    
    def _count_by_category(self) -> Dict[str, int]:
        """按类别统计问题"""
        counts = {}
        for issue in self.issues:
            cat = issue["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def _count_by_severity(self) -> Dict[str, int]:
        """按严重程度统计"""
        counts = {}
        for issue in self.issues:
            sev = issue["severity"]
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def _check_common_sense(self, scene_card: Dict, draft: str):
        """1. 常识合理性检查"""
        rules = self.common_sense.get('historical', {})
        
        # 帝王墓检查
        if '墓' in scene_card.get('location', '') or '墓' in draft:
            for rule in rules.get('帝王墓', []):
                if self._violate_rule(draft, rule):
                    self._add_issue(
                        category="常识合理性",
                        severity="critical",
                        message=f"违反常识：{rule}",
                        suggestion="修改设定，使其符合常识",
                        context=self._find_context(draft, rule)
                    )
        
        # 政府机构检查
        if '701' in draft or '部门' in draft:
            for rule in rules.get('政府机构', []):
                if self._violate_rule(draft, rule):
                    self._add_issue(
                        category="常识合理性",
                        severity="major",
                        message=f"违反常识：{rule}",
                        suggestion="重新考虑组织动机，避免简单化的阴谋论",
                        context=self._find_context(draft, rule)
                    )
    
    def _check_motivation(self, scene_card: Dict, draft: str, canon: Dict):
        """2. 动机合理性检查"""
        rules = self.common_sense.get('human_nature', {}).get('动机合理性', [])
        
        # 检查角色动机
        for rule in rules:
            if self._violate_rule(draft, rule):
                self._add_issue(
                    category="动机合理性",
                    severity="major",
                    message=f"动机不合理：{rule}",
                    suggestion="为角色行为提供更合理的动机解释",
                    context=self._find_context(draft, rule)
                )
        
        # 检查组织动机
        if '701' in draft:
            # 701 为什么要收容？
            if '灭口' in draft or '追杀' in draft:
                self._add_issue(
                    category="动机合理性",
                    severity="critical",
                    message="701 作为国家机构，灭口自己人不符合理性逻辑",
                    suggestion="改为保护性收容，或提供更合理的动机",
                    context="701 部门行为"
                )
    
    def _check_worldview_consistency(self, scene_card: Dict, draft: str, canon: Dict):
        """3. 世界观一致性检查"""
        # 时代背景检查
        time_anchor = scene_card.get('time_anchor', '')
        if '1959' in time_anchor or '1950' in draft:
            # 检查是否有不符合 1950 年代的元素
            anachronisms = ['手机', '电脑', '互联网', 'GPS']
            for item in anachronisms:
                if item in draft:
                    self._add_issue(
                        category="世界观一致性",
                        severity="critical",
                        message=f"时代错误：1950 年代不应该有{item}",
                        suggestion="移除或替换为符合时代的物品",
                        context=self._find_context(draft, item)
                    )
    
    def _check_causal_depth(self, scene_card: Dict, draft: str):
        """4. 因果链深度检查"""
        # 检查是否有未解释的事件
        unexplained_patterns = ['突然', '莫名其妙', '不知为何', '居然']
        for pattern in unexplained_patterns:
            if pattern in draft:
                self._add_issue(
                    category="因果链深度",
                    severity="minor",
                    message=f"因果链不完整：'{pattern}'表示事件缺乏解释",
                    suggestion="补充事件原因，完善因果链",
                    context=self._find_context(draft, pattern)
                )
        
        # 检查"为什么"链条
        why_count = draft.count('为什么')
        if why_count > 3:
            self._add_issue(
                category="因果链深度",
                severity="minor",
                message=f"过多未解答的'为什么'（{why_count}个），建议提供部分答案",
                suggestion="在适当位置揭示部分真相，保持悬念但不过度",
                context="对话中的疑问"
            )
    
    def _check_character_behavior(self, scene_card: Dict, draft: str, canon: Dict):
        """5. 角色行为合理性检查"""
        # 检查角色行为是否符合设定
        characters = canon.get('characters', [])
        for char in characters:
            char_name = char.get('name', '')
            personality = char.get('personality', [])
            
            if char_name in draft:
                # 检查是否有不符合性格的行为
                # 这里需要更复杂的 NLP 分析，简化处理
                pass
    
    def _check_internal_consistency(self, scene_card: Dict, draft: str, world_state: Dict):
        """6. 设定自洽性检查"""
        # 检查前后矛盾
        contradictions = [
            ('自动开启', '需要钥匙'),
            ('保护', '灭口'),
            ('自己人', '追杀')
        ]
        
        for pair in contradictions:
            if pair[0] in draft and pair[1] in draft:
                self._add_issue(
                    category="设定自洽性",
                    severity="critical",
                    message=f"设定矛盾：'{pair[0]}'和'{pair[1]}'同时存在",
                    suggestion="重新设计设定，消除矛盾",
                    context=f"同时提及'{pair[0]}'和'{pair[1]}'的段落"
                )
    
    def _violate_rule(self, text: str, rule: str) -> bool:
        """检查文本是否违反规则"""
        # 简化实现：检查规则中的关键词是否在文本中被违反
        # 实际需要更复杂的 NLP 分析
        return False  # 占位，实际实现需要语义分析
    
    def _find_context(self, text: str, keyword: str) -> Optional[str]:
        """找到关键词的上下文"""
        idx = text.find(keyword)
        if idx == -1:
            return None
        
        start = max(0, idx - 50)
        end = min(len(text), idx + 50)
        return text[start:end]


def review_logic(scene_card: Dict, draft: str, world_state: Dict, canon: Dict) -> Dict:
    """便捷函数：执行逻辑审查"""
    common_sense_path = Path(__file__).parent / 'common_sense.json'
    reviewer = LogicReviewer(str(common_sense_path))
    return reviewer.review_all(scene_card, draft, world_state, canon)


if __name__ == "__main__":
    # 测试
    scene_card = {"location": "墓门外门"}
    draft = "墓门会自动开启，但需要钥匙才能打开"
    world_state = {}
    canon = {}
    
    result = review_logic(scene_card, draft, world_state, canon)
    print(json.dumps(result, ensure_ascii=False, indent=2))
