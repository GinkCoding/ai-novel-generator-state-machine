#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Machine Novel Generator - 整合 LLM 调用

基于状态机 + 约束系统的小说生成器
7 步流水线：PLAN → WRITE → EXTRACT → VALIDATE → PATCH → COMMIT → OUTPUT
"""

import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class StateMachineNovelGenerator:
    """基于状态机的小说生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(config.get('project_root', '.'))
        self.novel_ci_dir = self.project_root / 'novel_ci'
        self.state_dir = self.novel_ci_dir / 'state'
        
        # API 配置
        self.api_key = os.getenv('SILICONFLOW_API_KEY')
        if not self.api_key:
            raise ValueError("❌ SILICONFLOW_API_KEY not found in .env file")
        
        self.api_base = "https://api.siliconflow.cn/v1"
        self.model_writer = "Qwen/Qwen2.5-72B-Instruct"  # 写作模型
        self.model_architect = "THUDM/glm-4-9b-chat"  # 大纲模型
        self.model_coder = "Qwen/Qwen2.5-Coder-32B-Instruct"  # 编辑/校验模型
        
        # 加载 World State
        self.canon = self._load_state('canon.json')
        self.world = self._load_state('world.json')
        self.timeline = self._load_timeline()
    
    def _load_state(self, filename: str) -> Dict:
        """加载状态文件"""
        path = self.state_dir / filename
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _load_timeline(self) -> List[Dict]:
        """加载时间线"""
        path = self.state_dir / 'timeline.jsonl'
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
    
    def _save_state(self, filename: str, data: Dict):
        """保存状态文件"""
        path = self.state_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _append_timeline(self, event: Dict):
        """追加事件到时间线"""
        path = self.state_dir / 'timeline.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def _call_llm(self, messages: List[Dict], model: Optional[str] = None, 
                  temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """调用 LLM API"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.model_writer,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
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
    
    def _extract_json(self, text: str) -> Dict:
        """从文本中提取 JSON"""
        import re
        # 尝试匹配 ```json ... ``` 或纯 JSON
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue
        
        # 如果都失败，尝试直接解析
        try:
            return json.loads(text)
        except:
            return {}
    
    def generate_chapter(self, chapter_num: int, scene_num: int, 
                        outline: Dict, word_count: int = 4000) -> Dict[str, Any]:
        """
        生成章节（8 步流水线 - 新增逻辑审查）
        """
        print(f"\n🚀 开始生成 第{chapter_num}章 第{scene_num}场")
        print("=" * 60)
        
        # Step 1: PLAN - 生成 SceneCard
        print("\n📋 Step 1/8: PLAN - 场景规划")
        scene_card = self._plan_scene(chapter_num, scene_num, outline)
        self._save_scene_card(chapter_num, scene_num, scene_card)
        print(f"✓ SceneCard 生成完成")
        
        # Step 2: WRITE - 基于 SceneCard 写正文
        print("\n✍️  Step 2/8: WRITE - 正文写作")
        draft = self._write_prose(scene_card, word_count)
        print(f"✓ 正文草稿完成 ({len(draft.get('content', ''))} 字)")
        
        # Step 3: EXTRACT - 从正文抽取事实
        print("\n🔍 Step 3/8: EXTRACT - 事实抽取")
        extract_data = self._extract_facts(draft, scene_card)
        print(f"✓ 抽取 {len(extract_data.get('events', []))} 个事件")
        
        # Step 4: VALIDATE - 硬规则校验
        print("\n⚖️  Step 4/8: VALIDATE - 硬校验")
        validation_result = self._validate(extract_data)
        
        if not validation_result['pass']:
            print(f"⚠️  发现 {len(validation_result['issues'])} 个硬规则问题")
            
            # Step 5: PATCH - 最小补丁修复
            print("\n🔧 Step 5/8: PATCH - 最小补丁修复")
            max_retries = 3
            for attempt in range(max_retries):
                draft = self._patch_prose(draft, validation_result['issues'])
                extract_data = self._extract_facts(draft, scene_card)
                validation_result = self._validate(extract_data)
                
                if validation_result['pass']:
                    print(f"✓ 硬规则修复完成（第{attempt + 1}轮）")
                    break
            else:
                print(f"⚠️  达到最大修复次数，保留硬规则警告")
        else:
            print("✓ 硬规则校验通过（无问题）")
        
        # Step 6: LOGIC_REVIEW - 智能逻辑审查 ⭐ 新增
        print("\n🧠 Step 6/8: LOGIC_REVIEW - 智能逻辑审查")
        logic_result = self._logic_review(scene_card, draft)
        
        if not logic_result['pass']:
            print(f"⚠️  发现 {len(logic_result['issues'])} 个逻辑问题")
            for issue in logic_result['issues'][:3]:  # 只显示前 3 个
                print(f"  - [{issue['severity']}] {issue['message']}")
            
            # 逻辑问题修复
            print("\n🔧 Step 7/8: LOGIC_PATCH - 逻辑问题修复")
            draft = self._patch_logic(draft, logic_result['issues'])
            logic_result = self._logic_review(scene_card, draft)
            
            if logic_result['pass']:
                print("✓ 逻辑问题修复完成")
            else:
                print(f"⚠️  仍有 {len(logic_result['issues'])} 个逻辑问题待人工审查")
        else:
            print("✓ 逻辑审查通过（无问题）")
        
        # Step 8: COMMIT - 更新 World State
        print("\n💾 Step 8/8: COMMIT - 更新 World State")
        self._commit_changes(extract_data)
        print("✓ World State 已更新")
        
        # Step 9: OUTPUT - 输出最终版本
        print("\n📦 Step 9/9: OUTPUT - 输出最终版本")
        output = self._generate_output(draft, validation_result, logic_result, extract_data)
        self._save_chapter(chapter_num, scene_num, output)
        print(f"✓ 输出完成")
        
        print("\n" + "=" * 60)
        print(f"✅ 第{chapter_num}章 第{scene_num}场 生成完成！")
        
        return output
    
    def _plan_scene(self, chapter: int, scene: int, outline: Dict) -> Dict:
        """Step 1: 生成 SceneCard"""
        
        system_prompt = """你是一个专业的小说编剧。你的任务是根据提供的信息生成 SceneCard（场景卡）。

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
}"""

        user_prompt = f"""请为以下场景生成 SceneCard：

小说标题：{outline.get('title', '未命名')}
章节：{chapter}
场景：{scene}
地点：{outline.get('location', '未知')}
视角角色：{outline.get('pov', '主角')}
场景目标：{outline.get('goal', '推进剧情')}
障碍：{outline.get('obstacle', '无明显障碍')}
预期结果：{outline.get('outcome', '待定')}

当前 World State：
{json.dumps(self.world, ensure_ascii=False, indent=2)}

请生成 SceneCard（仅输出 JSON，不要其他内容）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_architect)
        scene_card = self._extract_json(response)
        
        # 确保必要字段存在
        scene_card.setdefault('ch', chapter)
        scene_card.setdefault('sc', scene)
        scene_card.setdefault('time_anchor', f'chapter_{chapter}_start')
        
        return scene_card
    
    def _write_prose(self, scene_card: Dict, word_count: int) -> Dict:
        """Step 2: 基于 SceneCard 写正文"""
        
        system_prompt = """你是一个专业的小说作家。你的任务是根据 SceneCard 写正文。

重要规则：
1. 不得引入 SceneCard 之外的新设定（地点/物品/角色）
2. 必须遵守 World State 中的角色位置/物品状态
3. 文风要符合小说类型（玄幻/科幻/言情等）
4. 字数要达到要求"""

        user_prompt = f"""请根据以下 SceneCard 写正文：

SceneCard:
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

当前 World State:
{json.dumps(self.world, ensure_ascii=False, indent=2)}

要求：
- 字数：约 {word_count} 字
- 视角：{scene_card.get('pov', '第三人称')}
- 地点：{scene_card.get('location', '未知')}
- 参与角色：{', '.join(scene_card.get('participants', []))}

请写正文（不要输出 SceneCard 中已有的内容，只写正文）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_writer)
        
        return {
            "chapter": scene_card['ch'],
            "scene": scene_card['sc'],
            "content": response,
            "word_count": len(response)
        }
    
    def _extract_facts(self, draft: Dict, scene_card: Dict) -> Dict:
        """Step 3: 从正文抽取事实"""
        
        system_prompt = """你是一个事实抽取器。你的任务是从小说正文中抽取结构化事实。

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
      "changes": {"character_changes": {}, "item_changes": {}},
      "evidence_quote": "原文证据句"
    }
  ],
  "character_changes": {"char_001": {"location": "loc_002"}},
  "item_changes": {"item_001": {"state": "used"}},
  "location_changes": {"char_001": "loc_002"}
}"""

        user_prompt = f"""请从以下正文中抽取事实：

SceneCard:
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

正文:
{draft['content'][:3000]}  # 限制长度

请抽取事实（仅输出 JSON）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_coder)
        extract_data = self._extract_json(response)
        
        # 确保必要字段存在
        extract_data.setdefault('events', [])
        extract_data.setdefault('character_changes', {})
        extract_data.setdefault('item_changes', {})
        extract_data.setdefault('location_changes', {})
        
        return extract_data
    
    def _validate(self, extract_data: Dict) -> Dict:
        """Step 4: 硬规则校验"""
        from novel_ci.scripts import validate as validator
        
        canon_path = str(self.state_dir / 'canon.json')
        world_path = str(self.state_dir / 'world.json')
        
        # 调用校验器
        result = validator.validate_all(
            canon_path, world_path, extract_data, self.timeline
        )
        return result
    
    def _logic_review(self, scene_card: Dict, draft: Dict) -> Dict:
        """Step 6: 智能逻辑审查"""
        from novel_ci.scripts import logic_reviewer as reviewer
        
        canon_path = self.state_dir / 'canon.json'
        world_path = self.state_dir / 'world.json'
        
        with open(canon_path, 'r', encoding='utf-8') as f:
            canon = json.load(f)
        with open(world_path, 'r', encoding='utf-8') as f:
            world = json.load(f)
        
        # 调用逻辑审查器
        result = reviewer.review_logic(
            scene_card=scene_card,
            draft=draft['content'],
            world_state=world,
            canon=canon
        )
        return result
    
    def _patch_logic(self, draft: Dict, issues: List[Dict]) -> Dict:
        """Step 7: 逻辑问题修复"""
        
        system_prompt = """你是一个专业的编辑，擅长发现并修复逻辑漏洞。

你的任务是根据逻辑审查问题修复正文。

重要规则：
1. 保持原文风格和情节
2. 只修改导致逻辑问题的部分
3. 修复后的内容必须符合常识和逻辑
4. 不要引入新的逻辑问题"""

        issues_text = "\n".join([
            f"- [{issue['severity'].upper()}] {issue['category']}: {issue['message']}"
            f"\n  建议：{issue['suggestion']}"
            for issue in issues
        ])
        
        user_prompt = f"""请根据以下逻辑问题修复正文：

逻辑问题:
{issues_text}

原文:
{draft['content'][:8000]}

请只修改必要的部分，修复逻辑问题（输出完整修复后的正文）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_writer)
        
        return {
            "chapter": draft['chapter'],
            "scene": draft['scene'],
            "content": response,
            "word_count": len(response)
        }
    
    def _patch_prose(self, draft: Dict, issues: List[Dict]) -> Dict:
        """Step 5: 最小补丁修复"""
        
        system_prompt = """你是一个专业的编辑。你的任务是根据校验问题修复正文。

重要规则：
1. 只改导致报错的最小句子集合
2. 不要重写整段
3. 保留原文风格"""

        issues_text = "\n".join([
            f"- {issue['type']}: {issue['message']} (建议：{issue.get('suggestion', '无')})"
            for issue in issues
        ])
        
        user_prompt = f"""请根据以下校验问题修复正文：

校验问题:
{issues_text}

原文:
{draft['content']}

请只修改必要的部分（输出完整修复后的正文）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_writer)
        
        return {
            "chapter": draft['chapter'],
            "scene": draft['scene'],
            "content": response,
            "word_count": len(response)
        }
    
    def _commit_changes(self, extract_data: Dict):
        """Step 6: 更新 World State"""
        # 更新角色状态
        for char_id, changes in extract_data.get('character_changes', {}).items():
            if char_id not in self.world['characters']:
                self.world['characters'][char_id] = {}
            self.world['characters'][char_id].update(changes)
        
        # 更新物品状态
        for item_id, changes in extract_data.get('item_changes', {}).items():
            if item_id not in self.world['items']:
                self.world['items'][item_id] = {}
            self.world['items'][item_id].update(changes)
        
        # 更新时间线
        for event in extract_data.get('events', []):
            self._append_timeline(event)
        
        # 更新时间
        self.world['time']['chapter'] = max(
            self.world['time'].get('chapter', 0),
            extract_data.get('chapter', 0)
        )
        self.world['time']['scene'] = max(
            self.world['time'].get('scene', 0),
            extract_data.get('scene', 0)
        )
        self.world['time']['last_updated'] = datetime.now().isoformat()
        
        # 保存
        self._save_state('world.json', self.world)
    
    def _save_scene_card(self, chapter: int, scene: int, scene_card: Dict):
        """保存 SceneCard"""
        path = self.novel_ci_dir / 'scenes' / f'CH{chapter:02d}_SC{scene:02d}.scene.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(scene_card, f, ensure_ascii=False, indent=2)
    
    def _save_chapter(self, chapter: int, scene: int, output: Dict):
        """保存章节输出"""
        path = self.project_root / 'novels' / f'chapter_{chapter:02d}_scene_{scene:02d}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        # 同时保存纯文本版本
        txt_path = self.project_root / 'novels' / f'chapter_{chapter:02d}_scene_{scene:02d}.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(output['draft']['content'])
    
    def _generate_output(self, draft: Dict, validation: Dict, logic_review: Dict, extract: Dict) -> Dict:
        """Step 9: 生成最终输出"""
        return {
            "meta": {
                "chapter": draft['chapter'],
                "scene": draft['scene'],
                "generated_at": datetime.now().isoformat(),
                "word_count": draft['word_count']
            },
            "draft": draft,
            "validation": validation,
            "logic_review": logic_review,
            "extract": extract,
            "world_state_snapshot": self.world.copy()
        }


def main():
    """主函数"""
    config = {
        'project_root': str(Path(__file__).parent.parent)
    }
    
    print("\n🤖 State Machine Novel Generator v2.0")
    print("=" * 60)
    
    generator = StateMachineNovelGenerator(config)
    
    # 示例：生成第 1 章第 1 场
    outline = {
        'title': '测试小说',
        'location': 'loc_001',
        'pov': 'char_001',
        'goal': '开始冒险',
        'obstacle': '未知挑战',
        'outcome': '成功启程'
    }
    
    result = generator.generate_chapter(1, 1, outline, word_count=4000)
    
    print(f"\n📁 结果已保存到：{config['project_root']}/novels/")


if __name__ == "__main__":
    main()
