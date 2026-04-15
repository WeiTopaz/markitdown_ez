---
name: craft-skill
description: |
  要新建、重寫、調整、修整 skill 檔案（SKILL.md）或 skill 描述時使用。
  關鍵字：新增 skill、改 skill、調 skill、寫 skill、重寫 skill、SKILL.md、skills/、
  skill 描述、description、skill 觸發不準、skill 不會被叫出、skill router、
  skill 路由、skill 邊界、skill 邊界打架、skill 太模糊、skill 重疊、
  skill 互相搶觸發、references 要放什麼、要不要做成 skill。
  也適用於：發現某類工作反覆做錯、代理每次都在同一個判斷點翻車。
  不處理：要寫程式、改功能 → build；要先拆工作 → plan；
  要看整體技能地圖或換道規則 → workflow。
---

# Skill 設計

## 這份技能的角色

這份 skill 處理的是「把一種反覆會做錯的工作方式，固化成可被路由叫出的 SKILL.md」。它不是知識整理，不是寫文件，也不是一次性腳本。工作是判斷「這件事值不值得成為 skill」、把觸發面切準、把行為會改變的節點留下來。

## 先確認它是不是 skill

不是所有筆記都值得長成 skill。下手前先回答三題：

- **它改變的是哪個決策？** ——說不出具體決策點，多半只是資料。
- **它靠什麼訊號被叫出來？** ——說不出使用者會打的字，description 掛不上。
- **不用它時，最常出什麼錯？** ——說不出錯的樣子，代表還沒看過足夠案例。

三題都答得出來，才開始寫。只是想整理知識、蒐連結或做一次性操作，退回筆記即可。

## 進場訊號

- 同一類任務每次都要重講一次做法
- 代理常在同一個判斷點上做錯選擇
- 你已經說得出觸發條件、關鍵節點與完成樣子
- 既有 skill 觸發失準、邊界互相打架、描述抓不到使用者真實用詞

方向還沒定、要先拆工作 → `plan`。要直接改 skill 內容的實作層細節 → `build`。

## 設計順序

> 開工前先翻一次 `references/skill-template.md`：裡面有資料夾結構、SKILL.md 章節骨架、frontmatter 寫法、最小可用 skill 範例，以及送出前的檢查表。需要複製樣板、對照格式時直接看這份。

### 1. 先定觸發面（description 優先）

先寫 description，不要先堆流程。description 只回答「何時該叫出它」，不要把整個做法濃縮在一句話裡。

**硬規則：description 必須包含使用者真的會打的動詞與名詞，不能只寫抽象狀態。**

抽象狀態句（如「方向已定但還不能開工」「感覺卡住」）對人類讀者有意義，但 skill 路由器是用使用者輸入的字面詞彙來比對的。description 若不含使用者真實會說的詞，就等於沒被掛上。

寫完 description 後，用 `references/description-checklist.md` 做五點自測，五點任何一點不過就回頭改。

### 2. 只留下行為會改變的節點，其餘搬出去

寫草稿時，把流程收成少數幾個缺一不可的判斷點。草稿完成後再做一輪清潔：清單、範例、術語表、對照表、方法論來源，全部搬進 `references/`；主檔只保留真正會影響執行方式的內容。判斷標準一句話：**拿掉這段後，skill 還能正確運作嗎？** 能就搬走。判斷什麼留主檔、什麼進 references，見 `references/skill-anatomy.md`；資料夾結構與 references 檔案骨架，見 `references/skill-template.md`。

### 3. 把邊界講明白

說清楚它不處理什麼、遇到哪些情況要轉交別的 skill。和最容易爭觸發權的兩個相鄰 skill，在 description 末端互相點名邊界。邊界比百科全書重要。

### 4. 用真實任務試跑

至少找一個實際情境測它：

- 該觸發時有沒有被叫出
- 不該觸發時會不會亂入
- 讀完後行為是否真的不同

沒試跑過就不算完成。

## 重寫既有 skill 時先看哪裡

出現以下任何一個訊號時，進入重寫流程：

- 觸發率下降，或兩份 skill 同時被叫出
- 讀完還是不知道先做什麼
- 前次只改了口氣，行為沒有變

進入後，重寫的判準與保守原則整理在 `references/skill-anatomy.md`，對照閱讀。

## 完成線

這一輪可以收工，代表：

- description 已通過 `references/description-checklist.md` 的五點自測
- 主檔只留下「行為會改變的節點」，其餘已搬進 `references/`
- 與相鄰 skill 的邊界已在 description 末端互相點名
- 至少跑過一個真實情境，確認觸發、不誤觸、行為有變

## 換道規則

- 想先看整體技能地圖或換道規則 → `workflow`
- 已決定要改版，先拆工作 → `plan`
- 要直接寫/改 skill 的程式化內容（例如腳本、模板產生器）→ `build`

## 危險訊號

- 為了完整，把每個例外都塞進主檔
- 把參考資料直接翻成 skill
- description 只寫抽象狀態，沒有使用者真實會打的詞
- 只改口氣，不改真正失準的地方
- 與相鄰 skill 的邊界從未互相點名
- 還沒試跑真實任務就宣稱完成
