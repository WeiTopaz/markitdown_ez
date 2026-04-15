# Skill 樣板與資料夾結構

> **適用範圍**：本文件提供 SKILL.md 的實際樣式、章節骨架、以及 skill 資料夾的標準結構，方便 AI 與人類在新建或重寫 skill 時直接對照。

## 資料夾結構

一份完整的 skill 存放在 `skills/<skill-name>/` 底下，標準樣貌如下：

```
skills/
├── <skill-name>/
│   ├── SKILL.md              # 必要：主檔，含 frontmatter 與行為節點
│   └── references/           # 可選：輔助材料
│       ├── <topic-a>.md      # 檢查清單、對照表、方法論、樣板
│       └── <topic-b>.md
```

### 命名規則

- **資料夾名**：`<skill-name>` 使用小寫、連字號分隔（例如 `craft-skill`、`build`、`qa`）。資料夾名必須與 frontmatter 的 `name` 欄位一致。
- **主檔名**：固定為 `SKILL.md`（全大寫副檔名前綴）。不要用 `skill.md` 或 `README.md`。
- **references 檔名**：用主題命名、小寫連字號分隔（例如 `tdd-cycle.md`、`issue-sorting-card.md`、`description-checklist.md`）。避免用編號（`01-xxx.md`）或日期。

### 什麼時候要有 references 資料夾

- **需要**：有檢查清單、對照表、方法論來源、範例、樣板、術語表、超過五步的詳細流程
- **不需要**：主檔本身就短、所有內容都是行為節點、沒有可被獨立引用的輔助材料

單一 skill 可以只有 SKILL.md（例如 `debug`、`plan`、`workflow`），也可以有多份 references（例如 `review` 有 `code-checklist.md` 與 `design-checklist.md`）。

## SKILL.md 的樣式骨架

```markdown
---
name: <skill-name>
description: |
  <一句話：什麼情況該叫出這份 skill>。
  關鍵字：<動詞1>、<動詞2>、<名詞1>、<名詞2>、<口語1>、<口語2>、<英文詞1>、<英文詞2>。
  也適用於：<容易被忽略但應該觸發的邊緣情境>。
  不處理：<不該處理的工作> → <要轉去哪個 skill>；
  <另一種不該處理的> → <另一個 skill>。
---

# <Skill 標題>

## 這份技能的角色

<一到兩段，說明這份 skill 處理什麼、不處理什麼、核心模式是什麼。>

## 進場訊號

- <使用者會說什麼 / 會打什麼字>
- <什麼情境下代理應該主動切進來>
- <前置條件：已經知道什麼、已經定下什麼>

<不該觸發時要轉去哪：方向沒定 → `plan`；要找根因 → `debug`。>

## <關鍵判斷點 1>

<拿掉就會做錯的節點。用短段落或清單呈現。>

## <關鍵判斷點 2>

<另一個不能省的節點。>

## 完成線

這一輪可以收工，代表：

- <可觀測的完成條件 1>
- <可觀測的完成條件 2>
- <可觀測的完成條件 3>

## 換道規則

- <什麼情況要回頭> → `<前一道 skill>`
- <什麼情況要往下> → `<下一道 skill>`
- <什麼情況要轉交> → `<相鄰 skill>`

## 危險訊號

- <常見的做錯樣態 1>
- <常見的做錯樣態 2>
- <常見的做錯樣態 3>
```

### 章節的增減原則

上面是最小骨架。依 skill 性質，可以增補：

- **方法論來源**：若 skill 來自某套公認方法論（TDD、Conventional Commits 等），在主檔點名並把細節放 references
- **強制回報格式**：若完成後需要結構化回報（例如 `build` 要求列出測試證據），加一段「強制回報格式」
- **與某 skill 的分工**：若和某個相鄰 skill 常被搞混，加一段明確的「與 X 的分工」（例如 `qa` 有「與 review 的分工」段）
- **開工前先鎖的事項**：若這份 skill 需要預先定範圍（例如 `build` 的「交付目標 / 測試清單 / 邊界宣告」），加一段

**但不要為了章節而加章節。** 每個章節都必須對應一個真實會發生的決策點或失誤點。

## Frontmatter 寫法要點

```yaml
---
name: craft-skill
description: |
  要新建、重寫、調整、修整 skill 檔案（SKILL.md）或 skill 描述時使用。
  關鍵字：新增 skill、改 skill、寫 skill、SKILL.md、skills/、
  skill 觸發不準、skill 邊界、description、skill 重疊。
  也適用於：發現某類工作反覆做錯、代理每次在同一個判斷點翻車。
  不處理：要寫程式 → build；要先拆工作 → plan；
  要看整體技能地圖 → workflow。
---
```

### 硬規則

1. **`name` 必須與資料夾名一致**。路由器靠這個對齊。
2. **`description` 用 `|` 多行寫法**。單行會失去可讀性，也難放多組關鍵字。
3. **關鍵字必須是使用者真的會打的字**。抽象狀態句不算關鍵字。
4. **末端必寫「不處理 / 邊界」**。點名至少一個相鄰 skill。
5. **中英夾雜是 OK 的**。使用者真的會同時打「refactor」與「重構」，兩個都要放。

### description 反例與修法

| 反例 | 問題 | 修法 |
|---|---|---|
| `description: 當你想要把想法變成可執行的東西時使用` | 全是抽象狀態，沒有關鍵字 | 加上「實作、寫 code、新增功能、refactor、implement」 |
| `description: skill for writing code` | 太短、單語言、無邊界 | 加多行、補中英關鍵字、加「不處理：單行修正 → 直接做」 |
| `description: 寫程式的時候用這個` | 關鍵字太泛，會誤觸所有 coding 相關 | 限定範圍：「把已定需求落成代碼」，加排除條款 |

## references 檔案的樣式骨架

references 裡的檔案不需要 frontmatter，但建議開頭用引言段點出適用範圍：

```markdown
# <檔案標題>

> **適用範圍**：本文件服務 `<skill-name>` 的 <哪個步驟 / 哪個分支>。<什麼情況下才需要翻開這份檔案。>

## <主題章節 1>

<內容>

## <主題章節 2>

<內容>
```

### references 內容的常見類型

- **檢查清單**：`tdd-cycle.md`（紅/綠/重構各階段的打勾清單）
- **對照表 / 卡片**：`issue-sorting-card.md`（嚴重度與類型分類）
- **反模式表**：列出常見做錯樣態與修法（表格形式最好讀）
- **方法論出處**：引用書籍、論文、標準文件，供需要時回查
- **範例語料**：真實使用者輸入樣本，給 description 自測用
- **樣板**：像本檔這樣的骨架模板

## 一份最小可用 skill 的範例

以一個假想的 `lint` skill 為例：

```
skills/lint/
├── SKILL.md
└── references/
    └── rule-priority.md
```

**`skills/lint/SKILL.md`**：

```markdown
---
name: lint
description: |
  代碼寫完後要跑 linter、檢查風格、修 warning、對齊 formatter 時使用。
  關鍵字：lint、linter、eslint、ruff、prettier、格式、風格、
  跑一下 lint、修 warning、formatter、格式化。
  不處理：要寫新功能 → build；要驗收系統行為 → qa。
---

# Lint 與風格對齊

## 這份技能的角色

這份 skill 處理的是「代碼已寫完、要把風格與靜態分析警告清乾淨」的最後一哩。它不負責寫功能，也不負責找 bug，只負責讓代碼符合專案已定的風格與 linter 規則。

## 進場訊號

- 使用者說「跑一下 lint」「修 warning」「格式化一下」
- PR 被 CI 的 lint job 擋下
- 新寫完的一段代碼要在提交前對齊風格

要寫新功能 → `build`。要找系統行為問題 → `qa`。

## 關鍵判斷點

1. 先跑專案指定的 linter，抓出完整清單
2. 依 `references/rule-priority.md` 判斷哪些是硬性錯誤、哪些是可忽略建議
3. 修硬性錯誤，不動邏輯；可忽略建議另外列出交由使用者決定

## 完成線

- linter 回傳 0 error
- 沒有為了過 lint 而改動行為
- 被忽略的 warning 已列出並說明原因

## 換道規則

- 發現 lint 擋下的其實是邏輯 bug → `debug`
- 需要修改 linter 設定本身 → 回頭確認是不是該改規則而不是改碼

## 危險訊號

- 為了過 lint 而改掉行為
- 大量使用 `// eslint-disable` 而不說明原因
- 把 formatter 變動與邏輯變動混在同一個 commit
```

這個範例示範了：
- description 包含中英關鍵字與邊界
- 主檔短、只講判斷點
- references 只放一份規則優先順序
- 完成線、換道規則、危險訊號三段齊全

## 檢查表：送出新 skill 前

- [ ] 資料夾名 = frontmatter 的 `name`
- [ ] 主檔叫 `SKILL.md`（不是 `skill.md` 或 `README.md`）
- [ ] description 用 `|` 多行、包含真實語料關鍵字、末端點名邊界
- [ ] 主檔回答了「什麼情況該用 / 不能省的判斷點 / 產出 / 停手時機」四件事
- [ ] 每段章節都對應一個真實決策點，不是為了排版而加
- [ ] 超過五步的流程、檢查清單、對照表已搬進 `references/`
- [ ] references 檔案開頭有「適用範圍」引言段
- [ ] 至少跑過一個真實情境試觸發
