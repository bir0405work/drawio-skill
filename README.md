# Draw.io skill 與 Draw.io MCP Tools Server 整合指南

## 🌟 用途簡介
`drawio` Skill 是一個專為 AI Agent 設計的強大繪圖輔助技能。它的核心用途是**將基礎設施程式碼（如 Terraform）或系統邏輯，自動轉換為高品質、具備官方圖示的專業架構圖**。

透過此技能，AI 不只能理解你的系統架構，還能精準輸出原生 `.drawio` (mxGraphModel) XML 格式，並且原生支援 Google Cloud (GCP) 與 AWS 的官方架構圖示標準與排版。

---

## 🚀 與 Draw.io MCP Tools Server 的協同運作

為了達到「無縫預覽」與「精準繪圖」的最佳體驗，此技能強烈建議搭配 **Draw.io MCP (Model Context Protocol) Server** 一起使用。這兩者結合後，能達成完全自動化的繪圖體驗。

### 完美協作流程
1. **精準解析與資料擷取**：
   當你給予 Terraform 等設定檔時，AI 會先分析架構關聯，並使用技能內建的 Python 腳本（`extract-cloud-icons.py`）精準提取所需的雲端元件官方圖示 (Base64 SVG 或原生 mxgraph shape)。
2. **自動生成高還原度 XML**：
   使用 `build-cloud-diagram.py` 腳本，將所有節點、連線、從屬關係轉換為符合 Draw.io 規範的 XML。這裡可以精確控制座標、大小與樣式（例如我們剛優化的純淨無框圖示）。
3. **MCP 即時渲染 (關鍵步驟)**：
   - AI 在背景直接呼叫 MCP Server 提供的 `open_drawio_xml` 工具。
   - 將產生的 XML 內容直接推播給 Draw.io MCP Server。
   - 你的電腦螢幕上會**立刻自動開啟 Draw.io 編輯器**，並完美呈現這張熱騰騰的架構圖。
   
### 為什麼這樣能達成最「精準」的成效？
- **突破純文字限制**：比起單純產出 Mermaid.js 這種依賴排版引擎、難以控制細節的語法，結合 MCP + XML 能夠做到「絕對座標定位」與「豐富的自訂樣式設定」。
- **告別手動流程**：過去需要 AI 產出 XML，使用者再手動存成檔案然後用軟體打開。現在透過 MCP 伺服器，繪圖結果是**直達桌面**的。
- **保持完全可編輯性**：MCP 打開的圖表並非死板的圖片，而是包含所有 Metadata 與從屬關係（如 VPC 包含 Subnet，Subnet 包含 GKE Node Pool）的原生圖形。使用者可以接續 AI 的成果，直接在軟體內進行最終的微調與匯出。

---

### 💡 如何啟用
只要在你的 AI 客戶端 (如 Claude Desktop / Antigravity 等) 的 MCP 設定中加入以下執行指令：
```bash
npx -y @drawio/mcp
```
連線成功後，只要對 AI 說：「**請幫我根據這些 Terraform 產出 GCP 架構圖，並用 drawio 打開**」，最精確順暢的自動化架構繪圖流程就會直接啟動！

---

## 📚 參考與資料來源
- **官方圖示與形狀索引庫**：本技能底層腳本 (`extract-cloud-icons.py`) 抓取圖示所依賴的 `search-index.json`，其資料源頭完全來自 **Draw.io 官方 (由開源專案 JGraph 維護)**。藉由內建此官方索引，能確保 AI 產出的每一張 GCP 或 AWS 架構圖，其圖示語法與官方標準擁有 100% 的渲染精確度與相容性。
