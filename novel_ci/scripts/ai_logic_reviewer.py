#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Logic Reviewer - AI 驱动的智能逻辑审查器

不用写死的规则，而是让 LLM 自己推理发现逻辑问题：
- 因果推理：这个原因能推出这个结果吗？
- 常识推理：这符合常理吗？
- 动机推理：这个角色为什么会这样做？
- 一致性推理：前后矛盾吗？
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class AILogicReviewer:
    """AI 驱动的逻辑审查器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SILICONFLOW_API_KEY')
        self.api_base = "https://api.siliconflow.cn/v1"
        self.model = "Qwen/Qwen2.5-Coder-32B-Instruct"
    
    def _call_llm(self, messages: List[Dict]) -> str:
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
            "temperature": 0.3,  # 低温度，更严谨
            "max_tokens": 4000,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ LLM API 调用失败：{e}")
            return ""
    
    def review(self, scene_card: Dict, draft: str, context: Dict) -> Dict[str, Any]:
        """
        智能逻辑审查
        
        Args:
            scene_card: 场景卡
            draft: 正文内容
            context: 上下文（canon + world_state + timeline）
        
        Returns:
            {
                "pass": bool,
                "issues": [...],
                "reasoning": "审查推理过程"
            }
        """
        
        # 构建审查提示词
        prompt = self._build_review_prompt(scene_card, draft, context)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_llm(messages)
        
        # 解析结果
        return self._parse_review_result(response)
    
    def _get_system_prompt(self) -> str:
        """系统提示词 - 定义审查员角色"""
        return """你是一个专业的小说逻辑审查员。你的任务是发现故事中的逻辑漏洞。

## 审查维度

### 1. 因果推理
- 这个原因能推出这个结果吗？
- 是否有未解释的事件？
- 因果链是否完整？

### 2. 常识推理
- 这符合现实世界的常识吗？
- 是否符合时代背景？
- 是否符合物理规律？

### 3. 动机推理
- 角色为什么会这样做？
- 动机是否充分？
- 行为是否符合动机？

### 4. 一致性推理
- 前后是否矛盾？
- 设定是否自洽？
- 角色行为是否一致？

### 5. 世界观推理
- 是否符合故事设定的世界观？
- 是否符合社会背景？
- 是否符合组织性质？

## 输出格式

请输出 JSON 格式：
{
  "reasoning": "你的推理过程（详细分析）",
  "issues": [
    {
      "type": "因果/常识/动机/一致性/世界观",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "context": "原文相关段落",
      "why_illogical": "为什么不合逻辑",
      "suggestion": "修复建议"
    }
  ],
  "pass": true/false
}

## 重要原则

1. 不要放过任何逻辑漏洞
2. 但也不要过度挑剔（允许艺术夸张）
3. 关注深层逻辑，不是表面细节
4. 考虑故事类型和风格
5. 区分"不合理"和"你不喜欢"

开始审查！"""
    
    def _build_review_prompt(self, scene_card: Dict, draft: str, context: Dict) -> str:
        """构建审查提示词"""
        
        prompt = f"""## 待审查内容

### SceneCard
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

### 正文内容
{draft[:10000]}  # 限制长度

### 世界观设定（Canon）
{json.dumps(context.get('canon', {}), ensure_ascii=False, indent=2)[:5000]}

### 当前状态（World State）
{json.dumps(context.get('world', {}), ensure_ascii=False, indent=2)[:3000]}

### 历史事件（Timeline）
{json.dumps(context.get('timeline', []), ensure_ascii=False, indent=2)[:3000]}

---

## 审查任务

请仔细分析以上内容，找出所有逻辑漏洞。

### 重点检查

1. **因果链**
   - 事件发生的原因是否充分？
   - 结果是否能从原因推出？
   - 是否有"突然"、"莫名其妙"的事件？

2. **角色动机**
   - 每个角色的行为是否有合理动机？
   - 动机是否充分支持行为？
   - 是否有"为坏而坏"的反派？

3. **常识合理性**
   - 是否符合现实常识？
   - 是否符合时代背景？
   - 是否符合专业常识（如考古/军事/政治）？

4. **设定自洽性**
   - 前后是否矛盾？
   - 设定是否自洽？
   - 是否有双重标准？

5. **世界观一致性**
   - 是否符合故事设定的世界观？
   - 组织行为是否符合其性质？
   - 社会背景是否合理？

### 输出要求

1. 用 JSON 格式输出
2. 推理过程要详细
3. 每个问题都要说明"为什么不合逻辑"
4. 提供具体修复建议
5. 区分严重程度（critical/major/minor）

开始审查！"""
        
        return prompt
    
    def _parse_review_result(self, response: str) -> Dict:
        """解析审查结果"""
        import re
        
        # 尝试提取 JSON
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                    return result
                except:
                    continue
        
        # 如果解析失败，返回结构化错误
        return {
            "pass": False,
            "issues": [{
                "type": "解析错误",
                "severity": "major",
                "description": "无法解析 AI 返回结果",
                "context": response[:500],
                "why_illogical": "格式错误",
                "suggestion": "重新运行审查"
            }],
            "reasoning": "解析失败"
        }


def review_logic(scene_card: Dict, draft: str, context: Dict) -> Dict:
    """便捷函数：执行逻辑审查"""
    reviewer = AILogicReviewer()
    return reviewer.review(scene_card, draft, context)


if __name__ == "__main__":
    # 测试
    scene_card = {
        "ch": 8,
        "sc": 1,
        "location": "墓门外门",
        "goal": "陈三爷讲述真相"
    }
    
    draft = """
    天快黑的时候，我们到了墓门外。
    说是墓门，其实就是一处天然形成的石阙，两扇石门半掩着，上面爬满了青苔。
    "明早卯时，墓门会开半个时辰。"陈三爷说。
    "那还要三件信物干嘛？"王浩然问。
    "信物是开门用的。"陈三爷说。
    """
    
    context = {
        "canon": {
            "characters": [{"name": "陈三爷", "identity": ["守墓人"]}],
            "invariants": ["帝王墓应该隐蔽"]
        },
        "world": {"time": {"chapter": 7}},
        "timeline": []
    }
    
    result = review_logic(scene_card, draft, context)
    print(json.dumps(result, ensure_ascii=False, indent=2))
