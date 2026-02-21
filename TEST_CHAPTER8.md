# 🧪 测试第 8 章生成

## 📋 当前状态

✅ **已完成配置：**
- ✅ canon.json - 鬼吹灯第九部权威设定（角色/地点/物品/线索）
- ✅ world.json - 第 7 章结束时的 World State
- ✅ timeline.jsonl - 事件时间线（包含背景事件）
- ✅ test_chapter8.py - 第 8 章生成测试脚本

## 🚀 运行步骤

### 1. 配置 API Key

```bash
cd /root/.openclaw/workspace/ai-novel-generator-state-machine
cp .env.example .env
nano .env  # 编辑填入你的真实 API Key
```

**.env 内容：**
```bash
SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxx  # 你的 SiliconFlow API Key
```

### 2. 安装依赖（如果还没安装）

```bash
pip3 install python-dotenv requests --break-system-packages
```

### 3. 运行生成器

```bash
python3 test_chapter8.py
```

### 4. 查看结果

生成完成后，查看输出：

```bash
# 查看正文
cat novels/chapter_08_scene_01.txt

# 查看 SceneCard
cat novel_ci/scenes/CH08_SC01.scene.json

# 查看 World State 更新
cat novel_ci/state/world.json | jq

# 查看校验报告
cat novels/chapter_08_scene_01.json | jq '.validation'
```

---

## 📊 预期输出

### Step 1: PLAN - 场景规划
```
📋 Step 1/7: PLAN - 场景规划
✓ SceneCard 生成完成
```

SceneCard 会包含：
- 时间锚点：chapter_8_start
- 地点：loc_002_entrance（墓门外门）
- 视角：char_001（胡念一）
- 目标：陈三爷讲述 1959 年真相
- 障碍：陈三爷隐瞒部分真相

### Step 2: WRITE - 正文写作
```
✍️  Step 2/7: WRITE - 正文写作
✓ 正文草稿完成 (约 4000 字)
```

### Step 3: EXTRACT - 事实抽取
```
🔍 Step 3/7: EXTRACT - 事实抽取
✓ 抽取 3-5 个事件
```

抽取的事件可能包括：
- 陈三爷讲述 1959 年地质队
- 胡念一表明身份
- 陈三爷讲述胡八一 10 年前来访
- 团队决定继续进墓

### Step 4: VALIDATE - 硬校验
```
⚖️  Step 4/7: VALIDATE - 硬校验
✓ 校验通过（无问题）
```

或发现问题：
```
⚠️  发现 2 个问题
  - H2.2: 角色 char_004 瞬移
  - H3.1: 物品 item_011 凭空出现
```

### Step 5: PATCH - 最小补丁修复（如需）
```
🔧 Step 5/7: PATCH - 最小补丁修复
✓ 修复完成（第 1 轮）
```

### Step 6: COMMIT - 更新 World State
```
💾 Step 6/7: COMMIT - 更新 World State
✓ World State 已更新
```

更新内容：
- 角色关系变化（trust: 8→9）
- 新增事件到 timeline
- 时间推进到 chapter_8_scene_1

### Step 7: OUTPUT - 输出最终版本
```
📦 Step 7/7: OUTPUT - 输出最终版本
✓ 输出完成
```

---

## 🎯 关键检查点

### 生成后检查：

1. **角色一致性**
   - ✅ 胡念一知道胡八一在美国（不问"他现在在哪"）
   - ✅ 陈三爷是守墓人后代 +701 眼线
   - ✅ 王浩然幽默、杨雨霏简洁

2. **时空连续性**
   - ✅ 地点在 loc_002_entrance（墓门外门）
   - ✅ 时间在第 7 章之后

3. **物品一致性**
   - ✅ 摸金符 hot（第 7 章发热）
   - ✅ 黑玉古琮在杨雨霏手中
   - ✅ 陈三爷持有 701 档案

4. **关系发展**
   - ✅ trust: 8→9（逐步建立信任）

5. **三层谜团**
   - ✅ Layer 1（已解开）：地质队被守墓人"请走"
   - ✅ Layer 2（未解开）：另外 7 人去向
   - ✅ Layer 3（未解开）："请走"vs"收容"哪个是真的

---

## 🔧 故障排除

### 问题 1：API Key 错误
```
❌ LLM API 调用失败：401 Unauthorized
```
**解决：** 检查 `.env` 中的 API Key 是否正确

### 问题 2：JSON 解析失败
```
❌ 无法解析 LLM 返回的 JSON
```
**解决：** 检查提示词模板，确保 LLM 仅输出 JSON

### 问题 3：校验失败
```
⚠️ 发现 3 个问题
```
**解决：** 
- 查看具体问题
- 自动修复（最多 3 轮）
- 如仍失败，手动修改 canon.json 或 world.json

---

## 📝 对比原版第 8 章

生成完成后，对比原版：

```bash
# 原版（你之前优化的）
cat ../AI_NovelGenerator/output_v2/chapter_08_revised.txt

# 新版（状态机生成）
cat novels/chapter_08_scene_01.txt
```

**对比要点：**
1. 逻辑一致性是否更好？
2. 角色知识边界是否正确？
3. 是否有三层谜团结构？
4. 文风是否一致？

---

## 🎉 成功标志

看到以下输出表示成功：

```
✅ 第 8 章第 1 场 生成完成！
📁 结果保存到：novels/chapter_08_scene_01.txt
📊 校验结果：通过
```

---

**准备好后，按上述步骤运行即可！** 🚀
