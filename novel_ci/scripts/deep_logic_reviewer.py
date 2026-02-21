#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Logic Reviewer - 深度逻辑审查器

6 层深度审查：
1. 信息流审查 - 信息是如何传递的？谁告诉谁的？
2. 视角一致性审查 - 这句话是谁说的？他知道这个吗？
3. 情感弧线审查 - 情感变化是否有触发事件？
4. 动机深度审查 - 行为背后的真正动机是什么？
5. 主题一致性审查 - 情节是否服务于主题？
6. 伏笔追踪审查 - 伏笔是否在合理时间回收？
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class DeepLogicReviewer:
    """深度逻辑审查器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SILICONFLOW_API_KEY')
        self.api_base = "https://api.siliconflow.cn/v1"
        self.model = "Qwen/Qwen2.5-Coder-32B-Instruct"
    
    def _call_llm(self, messages: List[Dict], temperature: float = 0.3) -> str:
        """调用 LLM API"""
        import requests
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8000,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ LLM API 调用失败：{e}")
            return ""
    
    def review_all_dimensions(self, scene_card: Dict, draft: str, context: Dict) -> Dict[str, Any]:
        """
        6 层深度审查
        """
        all_issues = []
        all_reasoning = []
        
        # Layer 1: 信息流审查
        print("  🔍 Layer 1/6: 信息流审查...")
        result = self._review_information_flow(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        # Layer 2: 视角一致性审查
        print("  🔍 Layer 2/6: 视角一致性审查...")
        result = self._review_pov_consistency(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        # Layer 3: 情感弧线审查
        print("  🔍 Layer 3/6: 情感弧线审查...")
        result = self._review_emotional_arc(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        # Layer 4: 动机深度审查
        print("  🔍 Layer 4/6: 动机深度审查...")
        result = self._review_motivation_depth(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        # Layer 5: 主题一致性审查
        print("  🔍 Layer 5/6: 主题一致性审查...")
        result = self._review_theme_consistency(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        # Layer 6: 伏笔追踪审查
        print("  🔍 Layer 6/6: 伏笔追踪审查...")
        result = self._review_foreshadowing(scene_card, draft, context)
        if result['issues']:
            all_issues.extend(result['issues'])
            all_reasoning.append(result['reasoning'])
        
        return {
            "pass": len(all_issues) == 0 or all(i['severity'] == 'minor' for i in all_issues),
            "issues": all_issues,
            "reasoning": "\n\n".join(all_reasoning),
            "summary": {
                "total_issues": len(all_issues),
                "by_layer": self._count_by_layer(all_issues),
                "by_severity": self._count_by_severity(all_issues)
            }
        }
    
    def _count_by_layer(self, issues: List[Dict]) -> Dict[str, int]:
        counts = {}
        for issue in issues:
            layer = issue.get('layer', 'unknown')
            counts[layer] = counts.get(layer, 0) + 1
        return counts
    
    def _count_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        counts = {}
        for issue in issues:
            sev = issue.get('severity', 'unknown')
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def _review_information_flow(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 1: 信息流审查"""
        
        prompt = f"""请分析以下内容的信息流逻辑：

## 审查重点
1. 每个角色知道什么信息？
2. 信息是如何传递的？（谁告诉谁的？）
3. 信息传递是否合理？（为什么告诉他？）
4. 是否有信息跳跃？（突然知道了不该知道的事）

## 场景信息
SceneCard: {json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 正文
{draft[:8000]}

## 世界观设定
{json.dumps(context.get('canon', {}), ensure_ascii=False, indent=2)[:3000]}

请找出所有信息流逻辑问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个信息流逻辑审查员。

审查原则：
1. 每个角色只能知道自己应该知道的信息
2. 信息传递必须有明确渠道（谁告诉谁的）
3. 信息传递必须有合理动机（为什么告诉他）
4. 警惕"突然知道"的情况

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "信息流审查",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么信息流不合理",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _review_pov_consistency(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 2: 视角一致性审查"""
        
        pov_char = scene_card.get('pov', '')
        
        prompt = f"""请分析以下内容的视角一致性：

## 审查重点
1. 当前视角角色是谁？（{pov_char}）
2. 每句话/每个描述是否符合该视角？
3. 是否有视角跳跃？（突然知道视角角色不该知道的）
4. 是否有"上帝视角"混入？

## 场景信息
视角角色：{pov_char}

## 正文
{draft[:8000]}

请找出所有视角一致性问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个视角一致性审查员。

审查原则：
1. 严格限制在视角角色的知识范围内
2. 视角角色不能知道别人的内心想法（除非对方说出来）
3. 视角角色不能看到自己看不到的东西（除非转述）
4. 警惕"他眼中闪过..."这类描述（视角角色怎么看到的？）

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "视角一致性",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么视角不一致",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _review_emotional_arc(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 3: 情感弧线审查"""
        
        prompt = f"""请分析以下内容的情感弧线逻辑：

## 审查重点
1. 每个角色的情感状态是什么？
2. 情感变化是否有触发事件？
3. 情感强度是否与事件匹配？
4. 是否有情感突变？（没有触发就变了）

## 场景信息
SceneCard: {json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 正文
{draft[:8000]}

请找出所有情感弧线问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个情感弧线审查员。

审查原则：
1. 情感变化必须有明确的触发事件
2. 情感强度应该与事件重要性匹配
3. 警惕"突然"、"不知为何"的情感变化
4. 考虑角色性格对情感表达的影响

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "情感弧线",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么情感变化不合理",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _review_motivation_depth(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 4: 动机深度审查"""
        
        prompt = f"""请分析以下内容的动机深度逻辑：

## 审查重点
1. 每个角色的行为动机是什么？
2. 动机是否充分支持行为？
3. 是否有更深层的动机？（表面动机之下）
4. 动机是否与角色背景一致？

## 场景信息
SceneCard: {json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 正文
{draft[:8000]}

## 角色设定
{json.dumps(context.get('canon', {}).get('characters', []), ensure_ascii=False, indent=2)[:3000]}

请找出所有动机深度问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个动机深度审查员。

审查原则：
1. 每个重要行为都应该有明确动机
2. 动机应该与角色背景和性格一致
3. 警惕"为坏而坏"的反派
4. 考虑多层动机（表面/深层）

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "动机深度",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么动机不充分",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _review_theme_consistency(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 5: 主题一致性审查"""
        
        prompt = f"""请分析以下内容的主题一致性：

## 审查重点
1. 这个故事的核心主题是什么？
2. 每个情节是否服务于主题？
3. 是否有偏离主题的内容？
4. 角色行为是否体现主题？

## 场景信息
SceneCard: {json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 正文
{draft[:8000]}

请找出所有主题一致性问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个主题一致性审查员。

审查原则：
1. 识别故事的核心主题
2. 检查每个情节是否服务于主题
3. 警惕与主题无关的"支线"
4. 角色行为应该体现或挑战主题

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "主题一致性",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么与主题不一致",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _review_foreshadowing(self, scene_card: Dict, draft: str, context: Dict) -> Dict:
        """Layer 6: 伏笔追踪审查"""
        
        timeline = context.get('timeline', [])
        
        prompt = f"""请分析以下内容的伏笔逻辑：

## 审查重点
1. 本场景埋下了哪些伏笔？
2. 本场景回收了哪些伏笔？
3. 伏笔的埋下和回收是否合理？
4. 是否有伏笔被遗忘？

## 历史伏笔（来自 Timeline）
{json.dumps(timeline, ensure_ascii=False, indent=2)[:3000]}

## 场景信息
SceneCard: {json.dumps(scene_card, ensure_ascii=False, indent=2)}

## 正文
{draft[:8000]}

请找出所有伏笔问题，输出 JSON 格式。"""

        messages = [
            {"role": "system", "content": """你是一个伏笔追踪审查员。

审查原则：
1. 伏笔应该在合理时间内回收
2. 回收的伏笔应该有明确呼应
3. 警惕"埋下就忘"的伏笔
4. 警惕"突然冒出来"的解决方案（之前没铺垫）

输出格式：
{
  "reasoning": "分析过程",
  "issues": [
    {
      "layer": "伏笔追踪",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么伏笔不合理",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}"""},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        return self._parse_result(response)
    
    def _parse_result(self, response: str) -> Dict:
        """解析结果"""
        import re
        
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue
        
        return {
            "pass": False,
            "issues": [{
                "layer": "解析错误",
                "severity": "major",
                "description": "无法解析 AI 返回结果",
                "why_illogical": "格式错误",
                "suggestion": "重新运行审查"
            }],
            "reasoning": "解析失败"
        }


def review_deep_logic(scene_card: Dict, draft: str, context: Dict) -> Dict:
    """便捷函数：执行深度逻辑审查"""
    reviewer = DeepLogicReviewer()
    return reviewer.review_all_dimensions(scene_card, draft, context)


if __name__ == "__main__":
    # 测试
    print("深度逻辑审查器 - 测试模式")
