#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Generator with State Machine CI

整合了 Novel CI 的状态机+约束系统架构
核心转变：从"纯文本驱动"到"事实层 + 表现层分离"
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class StateMachineNovelGenerator:
    """基于状态机的小说生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(config.get('project_root', '.'))
        self.novel_ci_dir = self.project_root / 'novel_ci'
        self.state_dir = self.novel_ci_dir / 'state'
        
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
    
    def generate_chapter(self, chapter_num: int, scene_num: int, 
                        outline: Dict, word_count: int = 4000) -> Dict[str, Any]:
        """
        生成章节（7 步流水线）
        
        流程：
        1. PLAN - 场景规划
        2. WRITE - 正文写作
        3. EXTRACT - 事实抽取
        4. VALIDATE - 硬校验
        5. PATCH - 最小补丁修复（如需）
        6. COMMIT - 更新 World State
        7. OUTPUT - 输出最终版本
        """
        print(f"\n🚀 开始生成 第{chapter_num}章 第{scene_num}场")
        print("=" * 60)
        
        # Step 1: PLAN - 生成 SceneCard
        print("\n📋 Step 1/7: PLAN - 场景规划")
        scene_card = self._plan_scene(chapter_num, scene_num, outline)
        print(f"✓ SceneCard 生成完成")
        
        # Step 2: WRITE - 基于 SceneCard 写正文
        print("\n✍️  Step 2/7: WRITE - 正文写作")
        draft = self._write_prose(scene_card, word_count)
        print(f"✓ 正文草稿完成 ({len(draft.get('content', ''))} 字)")
        
        # Step 3: EXTRACT - 从正文抽取事实
        print("\n🔍 Step 3/7: EXTRACT - 事实抽取")
        extract_data = self._extract_facts(draft, scene_card)
        print(f"✓ 抽取 {len(extract_data.get('events', []))} 个事件")
        
        # Step 4: VALIDATE - 硬规则校验
        print("\n⚖️  Step 4/7: VALIDATE - 硬校验")
        validation_result = self._validate(extract_data)
        
        if not validation_result['pass']:
            print(f"⚠️  发现 {len(validation_result['issues'])} 个问题")
            
            # Step 5: PATCH - 最小补丁修复
            print("\n🔧 Step 5/7: PATCH - 最小补丁修复")
            max_retries = 3
            for attempt in range(max_retries):
                draft = self._patch_prose(draft, validation_result['issues'])
                extract_data = self._extract_facts(draft, scene_card)
                validation_result = self._validate(extract_data)
                
                if validation_result['pass']:
                    print(f"✓ 修复完成（第{attempt + 1}轮）")
                    break
            else:
                print(f"⚠️  达到最大修复次数，保留警告")
        else:
            print("✓ 校验通过（无问题）")
        
        # Step 6: COMMIT - 更新 World State
        print("\n💾 Step 6/7: COMMIT - 更新 World State")
        self._commit_changes(extract_data)
        print("✓ World State 已更新")
        
        # Step 7: OUTPUT - 输出最终版本
        print("\n📦 Step 7/7: OUTPUT - 输出最终版本")
        output = self._generate_output(draft, validation_result, extract_data)
        print(f"✓ 输出完成")
        
        print("\n" + "=" * 60)
        print(f"✅ 第{chapter_num}章 第{scene_num}场 生成完成！")
        
        return output
    
    def _plan_scene(self, chapter: int, scene: int, outline: Dict) -> Dict:
        """Step 1: 生成 SceneCard"""
        # TODO: 调用 LLM 生成 SceneCard
        return {
            "ch": chapter,
            "sc": scene,
            "time_anchor": f"chapter_{chapter}_start",
            "location": outline.get('location', 'unknown'),
            "pov": outline.get('pov', 'char_001'),
            "goal": outline.get('goal', ''),
            "obstacle": outline.get('obstacle', ''),
            "outcome": outline.get('outcome', ''),
            "required_facts": [],
            "allowed_changes": {}
        }
    
    def _write_prose(self, scene_card: Dict, word_count: int) -> Dict:
        """Step 2: 基于 SceneCard 写正文"""
        # TODO: 调用 LLM 写正文
        return {
            "chapter": scene_card['ch'],
            "scene": scene_card['sc'],
            "content": "（正文内容）",
            "word_count": word_count
        }
    
    def _extract_facts(self, draft: Dict, scene_card: Dict) -> Dict:
        """Step 3: 从正文抽取事实"""
        # TODO: 调用 LLM 抽取事实
        return {
            "events": [],
            "character_changes": {},
            "item_changes": {},
            "location_changes": {}
        }
    
    def _validate(self, extract_data: Dict) -> Dict:
        """Step 4: 硬规则校验"""
        from novel_ci.scripts import validate as validator
        
        canon_path = str(self.state_dir / 'canon.json')
        world_path = str(self.state_dir / 'world.json')
        
        # 调用校验器
        result = validator.main(canon_path, world_path, extract_data)
        return result
    
    def _patch_prose(self, draft: Dict, issues: List[Dict]) -> Dict:
        """Step 5: 最小补丁修复"""
        # TODO: 调用 LLM 修复问题
        return draft
    
    def _commit_changes(self, extract_data: Dict):
        """Step 6: 更新 World State"""
        # 更新 world.json
        for char_id, changes in extract_data.get('character_changes', {}).items():
            if char_id not in self.world['characters']:
                self.world['characters'][char_id] = {}
            self.world['characters'][char_id].update(changes)
        
        # 更新 timeline.jsonl
        for event in extract_data.get('events', []):
            self._append_timeline(event)
        
        # 保存
        self._save_state('world.json', self.world)
    
    def _generate_output(self, draft: Dict, validation: Dict, extract: Dict) -> Dict:
        """Step 7: 生成最终输出"""
        return {
            "draft": draft,
            "validation": validation,
            "extract": extract,
            "world_state_snapshot": self.world.copy()
        }


def main():
    """主函数"""
    config = {
        'project_root': str(Path(__file__).parent.parent)
    }
    
    generator = StateMachineNovelGenerator(config)
    
    # 示例：生成第 1 章第 1 场
    outline = {
        'location': 'loc_001',
        'pov': 'char_001',
        'goal': '开始冒险',
        'obstacle': '未知挑战',
        'outcome': '成功启程'
    }
    
    result = generator.generate_chapter(1, 1, outline, word_count=4000)
    
    # 保存结果
    output_path = Path(config['project_root']) / 'novels' / 'chapter_01_scene_01.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 结果已保存到：{output_path}")


if __name__ == "__main__":
    main()
