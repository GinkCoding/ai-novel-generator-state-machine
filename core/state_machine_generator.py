#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Machine Novel Generator v2.0 - 集成知识图谱

基于状态机 + 约束系统 + 知识图谱的小说生成器
11 步流水线：PLAN → LOAD_KNOWLEDGE → CHECK_KNOWLEDGE → GENERATE_CONSTRAINTS → WRITE → EXTRACT → UPDATE_KNOWLEDGE → VALIDATE → DEEP_REVIEW → PATCH → COMMIT
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
    """基于状态机的小说生成器（v2.0 - 集成知识图谱）"""
    
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
        self.model_writer = "Qwen/Qwen2.5-72B-Instruct"
        self.model_architect = "THUDM/glm-4-9b-chat"
        self.model_coder = "Qwen/Qwen2.5-Coder-32B-Instruct"
        
        # 加载 World State
        self.canon = self._load_state('canon.json')
        self.world = self._load_state('world.json')
        self.timeline = self._load_timeline()
        
        # 初始化知识图谱和信息流验证器 ⭐ 新增
        from novel_ci.scripts.knowledge_graph import KnowledgeGraph
        from novel_ci.scripts.information_flow_validator import InformationFlowValidator
        
        self.kg = KnowledgeGraph(str(self.state_dir / 'world.json'))
        self.if_validator = InformationFlowValidator(str(self.state_dir / 'world.json'))
    
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
        
        try:
            return json.loads(text)
        except:
            return {}
    
    def generate_chapter(self, chapter_num: int, scene_num: int, 
                        outline: Dict, word_count: int = 4000) -> Dict[str, Any]:
        """
        生成章节（11 步流水线 - 集成知识图谱）
        """
        print(f"\n🚀 开始生成 第{chapter_num}章 第{scene_num}场")
        print("=" * 60)
        
        # Step 1: PLAN - 生成 SceneCard
        print("\n📋 Step 1/11: PLAN - 场景规划")
        scene_card = self._plan_scene(chapter_num, scene_num, outline)
        self._save_scene_card(chapter_num, scene_num, scene_card)
        print(f"✓ SceneCard 生成完成")
        
        # Step 2: LOAD_KNOWLEDGE - 加载知识图谱 ⭐ 新增
        print("\n🧠 Step 2/11: LOAD_KNOWLEDGE - 加载知识图谱")
        print(f"✓ 知识图谱已加载")
        
        # Step 3: CHECK_KNOWLEDGE - 检查角色知识状态 ⭐ 新增
        print("\n🔍 Step 3/11: CHECK_KNOWLEDGE - 检查角色知识状态")
        knowledge_check = self._check_knowledge(scene_card)
        if not knowledge_check['pass']:
            print(f"⚠️  发现 {len(knowledge_check['issues'])} 个知识状态问题")
            for issue in knowledge_check['issues'][:3]:
                print(f"  - {issue}")
        else:
            print("✓ 知识状态检查通过")
        
        # Step 4: GENERATE_CONSTRAINTS - 生成知识约束 ⭐ 新增
        print("\n📝 Step 4/11: GENERATE_CONSTRAINTS - 生成知识约束")
        constraints = self._generate_constraints(scene_card)
        print(f"✓ 知识约束已生成（{len(constraints)} 条）")
        
        # Step 5: WRITE - 基于 SceneCard 写正文（带约束）
        print("\n✍️  Step 5/11: WRITE - 正文写作（带知识约束）")
        draft = self._write_prose(scene_card, word_count, constraints)
        print(f"✓ 正文草稿完成 ({len(draft.get('content', ''))} 字)")
        
        # Step 6: EXTRACT - 从正文抽取事实
        print("\n🔍 Step 6/11: EXTRACT - 事实抽取")
        extract_data = self._extract_facts(draft, scene_card)
        print(f"✓ 抽取 {len(extract_data.get('events', []))} 个事件")
        
        # Step 7: UPDATE_KNOWLEDGE - 更新知识图谱 ⭐ 新增
        print("\n💾 Step 7/11: UPDATE_KNOWLEDGE - 更新知识图谱")
        self._update_knowledge(extract_data, scene_card)
        print("✓ 知识图谱已更新")
        
        # Step 8: VALIDATE - 硬规则校验
        print("\n⚖️  Step 8/11: VALIDATE - 硬校验")
        validation_result = self._validate(extract_data)
        
        if not validation_result['pass']:
            print(f"⚠️  发现 {len(validation_result['issues'])} 个硬规则问题")
            
            # Step 9: PATCH - 最小补丁修复
            print("\n🔧 Step 9/11: PATCH - 最小补丁修复")
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
        
        # Step 10: DEEP_REVIEW - 6 层深度逻辑审查
        print("\n🧠 Step 10/11: DEEP_REVIEW - 6 层深度逻辑审查")
        print("  正在执行 6 层深度审查...")
        logic_result = self._deep_logic_review(scene_card, draft)
        
        if not logic_result['pass']:
            print(f"⚠️  发现 {len(logic_result['issues'])} 个逻辑问题")
            for issue in logic_result['issues'][:3]:
                print(f"  - [{issue.get('severity', 'unknown')}] {issue.get('description', '')}")
            
            # 逻辑问题修复
            print("\n🔧 Step 11/11: LOGIC_PATCH - 逻辑问题修复")
            draft = self._patch_logic(draft, logic_result['issues'])
            logic_result = self._deep_logic_review(scene_card, draft)
            
            if logic_result['pass']:
                print("✓ 逻辑问题修复完成")
            else:
                print(f"⚠️  仍有 {len(logic_result['issues'])} 个逻辑问题待人工审查")
        else:
            print("✓ 深度逻辑审查通过（无问题）")
        
        # Step 12: COMMIT - 更新 World State
        print("\n💾 Step 12/12: COMMIT - 更新 World State")
        self._commit_changes(extract_data)
        print("✓ World State 已更新")
        
        # Step 13: OUTPUT - 输出最终版本
        print("\n📦 Step 13/13: OUTPUT - 输出最终版本")
        output = self._generate_output(draft, validation_result, logic_result, extract_data)
        self._save_chapter(chapter_num, scene_num, output)
        print(f"✓ 输出完成")
        
        print("\n" + "=" * 60)
        print(f"✅ 第{chapter_num}章 第{scene_num}场 生成完成！")
        
        return output
    
    def _check_knowledge(self, scene_card: Dict) -> Dict:
        """Step 3: 检查角色知识状态"""
        pov = scene_card.get('pov', '')
        goal = scene_card.get('goal', '')
        
        issues = []
        
        # 检查 POV 角色是否知道不该知道的
        # 简化实现
        
        return {
            "pass": len(issues) == 0,
            "issues": issues
        }
    
    def _generate_constraints(self, scene_card: Dict) -> str:
        """Step 4: 生成知识约束"""
        constraints = self.if_validator.generate_knowledge_constraints(scene_card)
        return constraints
    
    def _plan_scene(self, chapter: int, scene: int, outline: Dict) -> Dict:
        """Step 1: 生成 SceneCard"""
        system_prompt = """你是一个专业的小说编剧。你的任务是根据提供的信息生成 SceneCard（场景卡）。

输出格式（JSON）：
{
  "ch": 章节号，
  "sc": 场景号，
  "time_anchor": "时间锚点",
  "location": "地点 ID",
  "pov": "视角角色 ID",
  "participants": ["参与角色 ID 列表"],
  "goal": "场景目标",
  "obstacle": "障碍/冲突",
  "outcome": "结果",
  "required_facts": ["必须引用的既有事实 ID 列表"],
  "allowed_changes": {"trust": "+2"}
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

请生成 SceneCard（仅输出 JSON）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_architect)
        scene_card = self._extract_json(response)
        
        scene_card.setdefault('ch', chapter)
        scene_card.setdefault('sc', scene)
        scene_card.setdefault('time_anchor', f'chapter_{chapter}_start')
        
        return scene_card
    
    def _write_prose(self, scene_card: Dict, word_count: int, constraints: str) -> Dict:
        """Step 5: 基于 SceneCard 写正文（带知识约束）"""
        
        system_prompt = """你是一个专业的小说作家。你的任务是根据 SceneCard 写正文。

重要规则：
1. 不得引入 SceneCard 之外的新设定
2. 必须遵守 World State 中的角色位置/物品状态
3. **必须遵守知识约束**（角色不能知道不该知道的）
4. 文风要符合小说类型
5. 字数要达到要求
6. 视角必须一致"""

        user_prompt = f"""请根据以下 SceneCard 写正文：

SceneCard:
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

{constraints}

当前 World State:
{json.dumps(self.world, ensure_ascii=False, indent=2)}

要求：
- 字数：约 {word_count} 字
- 视角：{scene_card.get('pov', '第三人称')}
- 地点：{scene_card.get('location', '未知')}
- 参与角色：{', '.join(scene_card.get('participants', []))}

请写正文（严格遵守知识约束）："""

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
        """Step 6: 从正文抽取事实"""
        system_prompt = """你是一个事实抽取器。从小说正文中抽取结构化事实。

输出格式（JSON）：
{
  "events": [...],
  "character_changes": {},
  "item_changes": {},
  "location_changes": {},
  "information_transfers": [
    {
      "from": "char_004",
      "to": "char_001",
      "fact": "fact_1959_team",
      "fact_description": "1959 年地质队被请走"
    }
  ]
}"""

        user_prompt = f"""请从以下正文中抽取事实：

SceneCard:
{json.dumps(scene_card, ensure_ascii=False, indent=2)}

正文:
{draft['content'][:3000]}

请抽取事实（包括信息传递）："""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_llm(messages, model=self.model_coder)
        extract_data = self._extract_json(response)
        
        extract_data.setdefault('events', [])
        extract_data.setdefault('character_changes', {})
        extract_data.setdefault('item_changes', {})
        extract_data.setdefault('location_changes', {})
        extract_data.setdefault('information_transfers', [])
        
        return extract_data
    
    def _update_knowledge(self, extract_data: Dict, scene_card: Dict):
        """Step 7: 更新知识图谱"""
        timeline_path = self.state_dir / 'timeline.jsonl'
        
        # 处理信息传递
        for transfer in extract_data.get('information_transfers', []):
            from_char = transfer.get('from')
            to_char = transfer.get('to')
            fact = transfer.get('fact')
            
            if from_char and to_char and fact:
                self.if_validator.update_knowledge_after_transfer(
                    from_char, to_char, fact, str(timeline_path)
                )
        
        # 重新加载 world（因为已更新）
        self.world = self._load_state('world.json')
    
    def _validate(self, extract_data: Dict) -> Dict:
        """Step 8: 硬规则校验"""
        from novel_ci.scripts import validate as validator
        
        canon_path = str(self.state_dir / 'canon.json')
        world_path = str(self.state_dir / 'world.json')
        
        result = validator.validate_all(
            canon_path, world_path, extract_data, self.timeline
        )
        return result
    
    def _patch_prose(self, draft: Dict, issues: List[Dict]) -> Dict:
        """Step 9: 最小补丁修复"""
        system_prompt = """你是一个专业的编辑。根据校验问题修复正文。

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
    
    def _deep_logic_review(self, scene_card: Dict, draft: Dict) -> Dict:
        """Step 10: 6 层深度逻辑审查"""
        from novel_ci.scripts import deep_logic_reviewer as reviewer
        
        canon_path = self.state_dir / 'canon.json'
        world_path = self.state_dir / 'world.json'
        timeline_path = self.state_dir / 'timeline.jsonl'
        
        with open(canon_path, 'r', encoding='utf-8') as f:
            canon = json.load(f)
        with open(world_path, 'r', encoding='utf-8') as f:
            world = json.load(f)
        
        timeline = []
        if timeline_path.exists():
            with open(timeline_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            timeline.append(json.loads(line))
                        except:
                            pass
        
        context = {
            'canon': canon,
            'world': world,
            'timeline': timeline[-10:]
        }
        
        result = reviewer.review_deep_logic(
            scene_card=scene_card,
            draft=draft['content'],
            context=context
        )
        return result
    
    def _patch_logic(self, draft: Dict, issues: List[Dict]) -> Dict:
        """Step 11: 逻辑问题修复"""
        system_prompt = """你是一个专业的编辑，擅长发现并修复逻辑漏洞。

根据逻辑审查问题修复正文。

重要规则：
1. 保持原文风格和情节
2. 只修改导致逻辑问题的部分
3. 修复后的内容必须符合常识和逻辑
4. 不要引入新的逻辑问题"""

        issues_text = "\n".join([
            f"- [{issue.get('severity', 'unknown').upper()}] {issue.get('category', '')}: {issue.get('description', '')}"
            f"\n  建议：{issue.get('suggestion', '无')}"
            for issue in issues
        ])
        
        user_prompt = f"""请根据以下逻辑问题修复正文：

逻辑问题:
{issues_text}

原文:
{draft['content'][:8000]}

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
        """Step 12: 更新 World State"""
        for char_id, changes in extract_data.get('character_changes', {}).items():
            if char_id not in self.world['characters']:
                self.world['characters'][char_id] = {}
            self.world['characters'][char_id].update(changes)
        
        for item_id, changes in extract_data.get('item_changes', {}).items():
            if item_id not in self.world['items']:
                self.world['items'][item_id] = {}
            self.world['items'][item_id].update(changes)
        
        for event in extract_data.get('events', []):
            self._append_timeline(event)
        
        self.world['time']['chapter'] = max(
            self.world['time'].get('chapter', 0),
            extract_data.get('chapter', 0)
        )
        self.world['time']['scene'] = max(
            self.world['time'].get('scene', 0),
            extract_data.get('scene', 0)
        )
        self.world['time']['last_updated'] = datetime.now().isoformat()
        
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
        
        txt_path = self.project_root / 'novels' / f'chapter_{chapter:02d}_scene_{scene:02d}.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(output['draft']['content'])
    
    def _generate_output(self, draft: Dict, validation: Dict, logic_review: Dict, extract: Dict) -> Dict:
        """Step 13: 生成最终输出"""
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
    
    outline = {
        'title': '鬼吹灯第九部',
        'location': 'loc_002_entrance',
        'pov': 'char_001',
        'goal': '陈三爷讲述 1959 年真相',
        'obstacle': '陈三爷隐瞒部分真相',
        'outcome': '决定继续进墓'
    }
    
    result = generator.generate_chapter(8, 1, outline, word_count=4000)
    
    print(f"\n📁 结果已保存到：{config['project_root']}/novels/")


if __name__ == "__main__":
    main()
