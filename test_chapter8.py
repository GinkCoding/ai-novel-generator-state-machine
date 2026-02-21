#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 生成鬼吹灯第九部 第 8 章
"""

from core.state_machine_generator import StateMachineNovelGenerator
from pathlib import Path

def main():
    config = {
        'project_root': str(Path(__file__).parent)
    }
    
    print("\n🤖 鬼吹灯第九部 - 状态机 Novel Generator v2.0")
    print("=" * 60)
    print("📖 生成：第 8 章 第 1 场 - 破庙夜话")
    print("=" * 60)
    
    generator = StateMachineNovelGenerator(config)
    
    # 第 8 章大纲
    outline = {
        'title': '鬼吹灯第九部',
        'chapter': 8,
        'scene': 1,
        'location': 'loc_002_entrance',
        'pov': 'char_001',
        'participants': ['char_001', 'char_002', 'char_003', 'char_004'],
        'goal': '陈三爷讲述 1959 年地质队真相，胡念一表明身份',
        'obstacle': '陈三爷隐瞒部分真相，701 部门监视',
        'outcome': '得知部分真相，决定继续进墓',
        'word_count': 4000,
        'genre': '盗墓/悬疑'
    }
    
    result = generator.generate_chapter(
        chapter_num=8,
        scene_num=1,
        outline=outline,
        word_count=4000
    )
    
    print(f"\n✅ 第 8 章第 1 场 生成完成！")
    print(f"📁 结果保存到：novels/chapter_08_scene_01.txt")
    print(f"📊 校验结果：{'通过' if result['validation']['pass'] else '发现问题'}")
    
    if not result['validation']['pass']:
        print(f"\n⚠️  校验问题:")
        for issue in result['validation']['issues']:
            print(f"  - {issue['type']}: {issue['message']}")


if __name__ == "__main__":
    main()
