# AutoResearch PRD & Project Plan

> **เอกสาร:** Product Requirements Document (PRD) และ Project Plan สำหรับระบบ **AutoResearch Agent**  
> **ผู้จัดทำ:** DevPooh (puwanath baibua)
> **วันที่:** 13 กันยายน 2569  

---

## สารบัญ

1. [Product Introduction & Vision](#1-product-introduction--vision)
   - [1.1 Product Vision](#11-product-vision)
   - [1.2 Key Objectives](#12-key-objectives)
   - [1.3 Target Users & Personas](#13-target-users--personas)
   - [1.4 High-level Use Cases](#14-high-level-use-cases)
2. [Functional Requirements & Agentic Workflow](#2-functional-requirements--agentic-workflow)
   - [2.1 Input Stage (Keyword / URL Ingestion)](#21-input-stage-keyword--url-ingestion)
   - [2.2 Research Stage (Web Scraping & Search)](#22-research-stage-web-scraping--search)
   - [2.3 Extraction Stage (Data Parsing)](#23-extraction-stage-data-parsing)
   - [2.4 Analysis Stage (Competitor Comparison via LLM)](#24-analysis-stage-competitor-comparison-via-llm)
   - [2.5 Output Stage (Report Generation)](#25-output-stage-report-generation)
   - [2.6 สรุปบทบาทของ vLLM ใน Agentic Loop](#26-สรุปบทบาทของ-vllm-ใน-agentic-loop)
3. [Technical Architecture & Stack](#3-technical-architecture--stack)
   - [3.1 ภาพรวมสถาปัตยกรรม (System Architecture Overview)](#31-ภาพรวมสถาปัตยกรรม-system-architecture-overview)
   - [3.2 Tech Stack ที่แนะนำ](#32-tech-stack-ที่แนะนำ)
   - [3.3 Technology Decision Rationale](#33-technology-decision-rationale)
   - [3.4 Environment Configuration](#34-environment-configuration)
4. [Data Flow Diagram & Architecture Details](#4-data-flow-diagram--architecture-details)
   - [4.1 High-Level Data Flow (End-to-End)](#41-high-level-data-flow-end-to-end)
   - [4.2 Detailed Data Flow by Agentic Loop Stage](#42-detailed-data-flow-by-agentic-loop-stage)
   - [4.3 Data Schema Overview (Key Tables)](#43-data-schema-overview-key-tables)
5. [Data Schema & Output Formats](#5-data-schema--output-formats)
   - [5.1 Competitor Info Schema](#51-competitor-info-schema)
   - [5.2 Product Price Schema](#52-product-price-schema)
   - [5.3 Image Asset Schema](#53-image-asset-schema)
   - [5.4 Supported Export Formats](#54-supported-export-formats)
   - [5.5 Sample Report Layout](#55-sample-report-layout)
   - [5.6 Tech Stack for Export](#56-tech-stack-for-export)
6. [Project Plan & Timeline](#6-project-plan--timeline)
   - [6.1 Phase 1: MVP — Core Research & Basic Analysis](#61-phase-1-mvp--core-research--basic-analysis)
   - [6.2 Phase 2: Advanced Features — Image Analysis & Multi-channel Tracking](#62-phase-2-advanced-features--image-analysis--multi-channel-tracking)
   - [6.3 Phase 3: Integration & UI Polish](#63-phase-3-integration--ui-polish)
   - [6.4 สรุป Timeline ทั้งหมด](#64-สรุป-timeline-ทั้งหมด)
   - [6.5 Team Structure & Resource Allocation](#65-team-structure--resource-allocation)
   - [6.6 Risks & Mitigation](#66-risks--mitigation)
   - [6.7 Next Steps](#67-next-steps)

---

## 1. Product Introduction & Vision

### 1.1 Product Vision

**"เปลี่ยนงานวิจัยตลาดที่ใช้เวลานานหลายวัน ให้กลายเป็นรายงานเชิงลึกที่พร้อมนำเสนอในไม่กี่นาที ด้วยพลังของ Autonomous AI Agent"**

AutoResearch Agent คือระบบอัจฉริยะที่ทำหน้าที่เป็น **"นักวิจัยส่วนตัว"** ของทีม Siam Sindhorn โดยทำงานแบบ End-to-End ตั้งแต่การค้นหาข้อมูลจากแหล่งต่างๆ บนอินเทอร์เน็ต การเก็บรวบรวมข้อมูลสำคัญ (ราคา, ลิงก์อ้างอิง, รูปภาพ, ช่องทางการขาย) ไปจนถึงการวิเคราะห์เปรียบเทียบและสรุปผลเป็นรายงานมาตรฐาน (PDF/PPTX) เพื่อสนับสนุนการตัดสินใจทางธุรกิจได้อย่างรวดเร็วและแม่นยำ

### 1.2 Key Objectives

| # | Objective | รายละเอียด |
|---|-----------|------------|
| 1 | **ลดระยะเวลาการทำงาน (Time Efficiency)** | ลดเวลาในการรวบรวมข้อมูลและทำรายงานจากการใช้คน (Manual Research) ที่อาจใช้เวลาหลายวัน หรือหลายสัปดาห์ ให้เหลือเพียงไม่กี่นาทีหรือชั่วโมง |
| 2 | **เพิ่มความถูกต้องและครบถ้วน (Data Accuracy & Completeness)** | เก็บข้อมูลจากแหล่งที่หลากหลายและตรวจสอบความถูกต้องผ่าน LLM ช่วยกรองข้อมูลซ้ำซ้อนและดึงเฉพาะข้อมูลที่สำคัญต่อการตัดสินใจ |
| 3 | **ยกระดับคุณภาพการตัดสินใจ (Decision Intelligence)** | เปลี่ยนข้อมูลดิบให้เป็น Insight เชิงลึก เช่น การวิเคราะห์จุดแข็ง-จุดอ่อนคู่แข่ง (Competitor Analysis) หรือแนวโน้มตลาด (Market Trends) ที่ช่วยกำหนดกลยุทธ์ได้ทันท่วงที |
| 4 | **สร้างมาตรฐานรายงาน (Standardization)** | จัดรูปแบบผลลัพธ์ให้ออกมาในรูปแบบมาตรฐานที่นำไปใช้งานต่อได้ทันที ไม่ว่าจะเป็น PDF, PPTX หรือ Excel |

### 1.3 Target Users & Personas

| Persona | บทบาทในองค์กร | ความต้องการหลัก (Pain Points) |
|---------|--------------|-------------------------------|
| **Marketing / Brand Manager** | ผู้วางแผนกลยุทธ์การตลาดและติดตามเทรนด์แบรนด์ | ต้องการข้อมูลคู่แข่งที่ทันสมัยที่สุดเพื่อปรับแผนแคมเปญ, ต้องการเห็นภาพรวมช่องทางการขาย (Omnichannel) ของคู่แข่ง, ต้องการข้อมูลรีวิวผู้บริโภคเพื่อปรับปรุง Positioning |
| **Sales Team** | ผู้รับผิดชอบยอดขายและการขยายตลาด | ต้องการข้อมูลราคาและโปรโมชั่นล่าสุดของคู่แข่งเพื่อตั้งราคาหรือเจรจาต่อรอง, ต้องการระบุช่องทางจัดจำหน่ายใหม่ๆ ที่คู่แข่งกำลังบุกเข้า, ต้องการข้อมูลสินค้าที่กำลังมาแรง (Hot Products) ในตลาด |
| **Executive / Management** | ผู้บริหารระดับสูงที่ต้องการภาพรวมธุรกิจ | ต้องการ Dashboard สรุปผลการวิจัยที่อ่านง่ายและเข้าใจได้ใน 5 นาที, ต้องการข้อมูลสนับสนุนการตัดสินใจลงทุนในโครงการใหม่ หรือการปรับโครงสร้างพอร์ตโฟลิโอ |

### 1.4 High-level Use Cases

#### Use Case 1: การวิเคราะห์คู่แข่งรายใหม่ (New Competitor Analysis)

- **Scenario:** ทีม Marketing ต้องการศึกษาบริษัทคู่แข่งรายใหม่ที่เพิ่งเปิดตัวสินค้าประเภทเดียวกัน
- **Workflow:**
  1. User ป้อนชื่อคู่แข่งและหมวดหมู่สินค้า
  2. Agent ค้นหาเว็บไซต์, Social Media, และ Review Platforms ของคู่แข่ง
  3. ดึงข้อมูล: ราคา, จุดขายหลัก (USP), ช่องทางขาย, ภาพลักษณ์แบรนด์
  4. วิเคราะห์ SWOT เบื้องต้นและสรุปเป็นรายงาน PDF ส่งเข้า Inbox

#### Use Case 2: การติดตามราคาและโปรโมชั่น (Price & Promo Monitoring)

- **Scenario:** Sales Team ต้องการรู้ราคาปัจจุบันของสินค้ากลุ่มเดียวกันในตลาดออนไลน์ (E-commerce)
- **Workflow:**
  1. User กำหนดรายการสินค้าเป้าหมายและแพลตฟอร์ม (Shopee, Lazada, Website ฯลฯ)
  2. Agent สแกนราคาและโปรโมชั่นที่-active อยู่ ณ เวลานั้น
  3. เปรียบเทียบราคาเฉลี่ยและส่วนลดสูงสุด
  4. สร้างตารางเปรียบเทียบ (Comparison Table) พร้อมกราฟแสดงแนวโน้มราคา

#### Use Case 3: การสำรวจโอกาสทางตลาด (Market Opportunity Scouting)

- **Scenario:** Executive ต้องการทราบเทรนด์สินค้าหรือบริการที่กำลังได้รับความนิยมเพื่อพิจารณาพัฒนาโครงการใหม่
- **Workflow:**
  1. User ระบุหมวดหมู่กว้างๆ (เช่น "Co-working Space", "Healthy Food")
  2. Agent วิเคราะห์บทความข่าว, รายงานอุตสาหกรรม, และบทสนทนาบน Social Media
  3. สรุปเทรนด์หลัก, ขนาดตลาดโดยประมาณ, และผู้เล่นรายใหญ่
  4. นำเสนอเป็น Presentation Deck (PPTX) พร้อมกราฟและภาพประกอบสำหรับประชุมผู้บริหาร

---

## 2. Functional Requirements & Agentic Workflow

ระบบ **AutoResearch Agent** ทำงานภายใต้สถาปัตยกรรมแบบ **Agentic Loop** ซึ่งประกอบด้วย 5 ขั้นตอนหลัก (**Input → Research → Extraction → Analysis → Output**) โดยมี **vLLM** ทำหน้าที่เป็น "สมอง" ในการตัดสินใจและประมวลผลในแต่ละขั้นตอน

### 2.1 Input Stage (Keyword / URL Ingestion)

**วัตถุประสงค์:** รับข้อมูลตั้งต้นจากผู้ใช้เพื่อนำไปวิจัยต่อ

| Item | รายละเอียด (Functional Requirement) | บทบาทของ vLLM |
|------|-------------------------------------|----------------|
| **FR-1.1: Multi-Format Input** | ระบบต้องรองรับการรับ Input ได้หลายรูปแบบ:<br>- **Keywords:** คำค้นหาทั่วไป (เช่น "ครีมกันแดด SPF50+")<br>- **URLs:** ลิงก์หน้าเว็บคู่แข่งโดยตรง<br>- **Product IDs/SKUs:** รหัสสินค้า<br>- **Competitor Names:** รายชื่อแบรนด์คู่แข่ง | **Intent Classification:** วิเคราะห์ประเภทของ Input ว่าต้องการให้ทำการ Search แบบกว้าง หรือเจาะจงไปที่ URL นั้นๆ |
| **FR-1.2: Query Expansion & Refinement** | แปลง Keyword สั้นๆ ให้เป็นชุดคำสั่งค้นหา (Search Queries) ที่ครอบคลุมมากขึ้น เพื่อไม่ให้พลาดข้อมูลสำคัญ | **Query Generation:** ใช้ LLM สร้างชุดคำค้นหา (Synonyms, Related Terms) เช่น จาก "กาแฟดริป" เป็น "กาแฟดริป ราคา", "กาแฟดริป ยี่ห้อไหนดี", "กาแฟดริป ส่งออก" |
| **FR-1.3: Target Channel Selection** | กำหนดว่าควรไปเก็บข้อมูลจากช่องทางใดบ้าง (Shopee, Lazada, TikTok Shop, Website เจ้าตัวเอง, Blog Review) | **Strategy Planning:** แนะนำช่องทางการขายที่เหมาะสมกับสินค้านั้นๆ ตามบริบทของ Keyword |

### 2.2 Research Stage (Web Scraping & Search)

**วัตถุประสงค์:** เก็บรวบรวมข้อมูลดิบจากแหล่งต่างๆ อย่างอัตโนมัติ

| Item | รายละเอียด (Functional Requirement) | บทบาทของ vLLM |
|------|-------------------------------------|----------------|
| **FR-2.1: Dynamic Search Execution** | ดำเนินการค้นหาผ่าน Search Engine (Google/Bing API) หรือเข้าเว็บเป้าหมายโดยตรงตามกลยุทธ์ที่ได้วางแผนไว้ | **Orchestration:** สั่งงาน Module การค้นหา (Search Module/Scraper) ให้ทำงานตามลำดับความสำคัญ และจัดการ Retry หากพบ Error |
| **FR-2.2: Anti-Bot Handling** | จัดการกับการป้องกัน Bot ของเว็บไซต์เป้าหมาย (เช่น Captcha, IP Block) โดยใช้ Proxy Rotation หรือ Headless Browser | **Decision Making:** ตัดสินใจเมื่อเจอปัญหา Access Denied ให้เปลี่ยน Strategy (เช่น เปลี่ยนจาก API เป็น Screenshot/Headless Browser แทน) |
| **FR-2.3: Content Diversity Collection** | เก็บข้อมูลทั้ง Text, Image URLs, และ HTML Structure จากหน้าเว็บที่หลากหลาย | **Instruction Tuning:** กำหนด Schema ของข้อมูลที่อยากให้ Scraper เก็บ (เช่น "เน้นเก็บเฉพาะส่วน Price และ Product Title") เพื่อให้ได้ข้อมูลที่มีคุณภาพ |

### 2.3 Extraction Stage (Data Parsing)

**วัตถุประสงค์:** แยกแยะข้อมูลดิบให้เป็นโครงสร้าง (Structured Data) ที่เข้าใจง่าย

| Item | รายละเอียด (Functional Requirement) | บทบาทของ vLLM |
|------|-------------------------------------|----------------|
| **FR-3.1: Key Information Extraction** | ดึงข้อมูลสำคัญออกมาเป็น Field ชัดเจน:<br>- **Price:** ราคาขาย (รวม/แยก VAT)<br>- **Link:** URL ต้นทาง<br>- **Image:** URL รูปภาพสินค้า<br>- **Channel:** แหล่งที่มา (Shopee, Website ฯลฯ)<br>- **Specs:** สเปกสินค้า, ขนาด, สี | **Information Extraction (IE):** อ่าน HTML/Text แล้วดึงข้อมูลออกมาใส่ JSON Schema ที่กำหนดไว้ (Zero-shot/Few-shot Extraction) แม้โครงสร้างเว็บจะต่างกัน |
| **FR-3.2: Data Normalization** | แปลงข้อมูลให้อยู่ในรูปแบบเดียวกัน (เช่น แปลงราคาทุกสกุลเป็น THB, แปลงขนาด "100ml" และ "100 มล." ให้เหมือนกัน) | **Data Cleaning:** ตรวจสอบความถูกต้องของข้อมูล (Validation) และปรับ Format ให้สอดคล้องกันก่อนส่งไปวิเคราะห์ต่อ |
| **FR-3.3: Image Retrieval & Validation** | ดาวน์โหลดหรือบันทึก URL รูปภาพสินค้าที่เกี่ยวข้อง พร้อมตรวจสอบว่าเป็นรูปภาพสินค้าจริง ไม่ใช่ Banner โฆษณา | **Visual Context Understanding:** (ถ้าใช้ Vision Model) ช่วยยืนยันว่ารูปภาพนั้นตรงกับสินค้าที่กำลังวิจัยหรือไม่ |

### 2.4 Analysis Stage (Competitor Comparison via LLM)

**วัตถุประสงค์:** วิเคราะห์ข้อมูลเชิงลึก เปรียบเทียบคู่แข่ง และสรุปแนวโน้ม

| Item | รายละเอียด (Functional Requirement) | บทบาทของ vLLM |
|------|-------------------------------------|----------------|
| **FR-4.1: Competitor Benchmarking** | เปรียบเทียบสินค้าของเรา vs คู่แข่ง ในด้านราคา, คุณภาพ (จาก Review), ช่องทางการขาย | **Comparative Analysis:** ใช้ LLM ประมวลผลข้อมูลทั้งหมดแล้วสรุปจุดแข็ง-จุดอ่อน (SWOT Analysis เบื้องต้น) ของแต่ละคู่แข่ง |
| **FR-4.2: Pricing Strategy Insight** | วิเคราะห์ช่วงราคาตลาด (Market Price Range) และแนะนำจุด positioning ที่ดี | **Insight Generation:** สรุปว่า "ตลาดนี้แข่งขันเรื่องราคา" หรือ "แข่งขันเรื่องคุณภาพ" พร้อมแนะนำช่วงราคาที่เหมาะสม |
| **FR-4.3: Channel Recommendation** | วิเคราะห์ว่าคู่แข่งขายดีในช่องทางไหน และแนะนำช่องทางที่เหมาะกับสินค้าเรา | **Strategic Advice:** ให้คำแนะนำเชิงกลยุทธ์ เช่น "ควรเริ่มขายใน Shopee ก่อน เพราะ Traffic สูงสำหรับสินค้านี้" |
| **FR-4.4: Sentiment Analysis** | วิเคราะห์ความรู้สึกจาก Review หรือ Comment ในโซเชียลมีเดียเกี่ยวกับคู่แข่ง | **Sentiment Scoring:** ให้คะแนนความพึงพอใจของลูกค้าต่อคู่แข่ง (Positive/Negative/Neutral) เพื่อบอกโอกาสในการเจาะตลาด |

### 2.5 Output Stage (Report Generation)

**วัตถุประสงค์:** จัดทำรายงานอัตโนมัติในรูปแบบที่ต้องการ

| Item | รายละเอียด (Functional Requirement) | บทบาทของ vLLM |
|------|-------------------------------------|----------------|
| **FR-5.1: Report Structuring** | จัดเรียงเนื้อหาเป็นหัวข้อมาตรฐาน: Executive Summary, Market Overview, Competitor Analysis, Recommendations | **Content Synthesis:** เขียนสรุปผู้บริหาร (Executive Summary) และเนื้อหาแต่ละส่วนด้วยภาษาที่เป็นทางการและกระชับ |
| **FR-5.2: Multi-Format Export** | รองรับการจัดรูปแบบไฟล์ส่งออก:<br>- **Markdown (.md):** สำหรับ Developer/Technical Team<br>- **PDF:** สำหรับ Presentation<br>- **PPTX:** สำหรับนำเสนอผู้บริหาร<br>- **Excel/CSV:** สำหรับข้อมูลดิบ | **Format Translation:** แปลงเนื้อหาจาก Internal Representation ไปยัง Template ของแต่ละฟอร์แมต โดยคงโครงสร้างและความสวยงาม |
| **FR-5.3: Visual Enhancement** | เพิ่มกราฟเปรียบเทียบราคา, ตารางสรุปคู่แข่ง, และแทรกภาพสินค้าลงในรายงาน | **Visual Description:** อธิบายข้อมูลเพื่อให้ Module สร้างกราฟอัตโนมัติ (เช่น "สร้าง Bar Chart เปรียบเทียบราคา Top 5") |

### 2.6 สรุปบทบาทของ vLLM ใน Agentic Loop

| ขั้นตอน | บทบาทหลักของ vLLM | ตัวอย่าง Prompt/Task |
|---------|-------------------|---------------------|
| **1. Input** | **Planner & Classifier** | "จัดประเภท Input นี้ว่าเป็น Keyword หรือ URL และสร้างชุดคำค้นหาเพิ่มเติม" |
| **2. Research** | **Orchestrator** | "เนื่องจากหน้าเว็บนี้ป้องกัน Bot ให้เปลี่ยนไปใช้ Headless Browser แทน" |
| **3. Extraction** | **Parser & Cleaner** | "ดึงข้อมูลราคาและลิงก์จาก HTML นี้ให้อยู่ในรูปแบบ JSON" |
| **4. Analysis** | **Analyst & Strategist** | "เปรียบเทียบสินค้า A กับ B ด้านราคาและรีวิว แล้วสรุปจุดแข็งจุดอ่อน" |
| **5. Output** | **Writer & Formatter** | "เขียนรายงานสรุปผลการวิจัยตลาดครีมกันแดดในรูปแบบ Markdown พร้อมตารางเปรียบเทียบ" |

---

## 3. Technical Architecture & Stack

### 3.1 ภาพรวมสถาปัตยกรรม (System Architecture Overview)

ระบบ AutoResearch Agent ถูกออกแบบด้วยแนวคิด **Modular Microservices** โดยแบ่งการทำงานออกเป็น 5 ชั้นหลัก (Layers):

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer (Frontend)                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│   │ Web App  │  │ Dashboard│  │ Report   │  │ Admin Panel  │   │
│   │ (React)  │  │ (Grafana/│  │ Export   │  │              │   │
│   │          │  │  Custom) │  │ (PDF/PPTX│  │              │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   API Gateway / Backend Layer                    │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │           FastAPI (Python) — REST + WebSocket            │  │
│   │  • Authentication & Authorization                        │  │
│   │  • Request Routing & Rate Limiting                       │  │
│   │  • Task Queue Management                                 │  │
│   └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     Agent Orchestration Layer                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│   │ Planner  │  │ Research │  │ Extract- │  │ Analyzer     │   │
│   │ Agent    │  │ Agent    │  │ or       │  │ Agent        │   │
│   │          │  │          │  │ Agent    │  │              │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         LangGraph / AutoGen — Agentic Loop Engine        │  │
│   └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      LLM Inference Layer                         │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         vLLM Endpoint: http://192.168.3.238:8000/v1      │  │
│   │   • Model: Qwen2.5-72B-Instruct / Llama-3.1-70B         │  │
│   │   • Serving: vLLM (PagedAttention, Continuous Batching)  │  │
│   └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Infrastructure & Data Layer                   │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│   │ PostgreSQL│  │ Redis    │  │ MinIO/S3 │  │ Elasticsearch│   │
│   │ (Relational│ │ (Cache/  │  │ (Object  │  │ (Full-text   │   │
│   │  DB)     │  │  Queue)  │  │  Storage)│  │  Search)     │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Tech Stack ที่แนะนำ

#### 3.2.1 Backend Framework

| องค์ประกอบ | เทคโนโลยี | เหตุผลที่เลือก |
|-----------|----------|---------------|
| **Web Framework** | **FastAPI (Python)** | Async-native, auto-generate OpenAPI/Swagger docs, performance สูง, ecosystem Python ครบถ้วนสำหรับ AI/ML |
| **Agentic Framework** | **LangGraph** (หรือ **AutoGen**) | LangGraph ให้ control flow แบบ state-machine ชัดเจน เหมาะกับ multi-agent loop; AutoGen ดีถ้าต้องการ multi-agent conversation แบบกระจายศูนย์ |
| **Task Queue** | **Celery + Redis** | จัดการ long-running tasks (web scraping, report generation) แบบ async, มี retry mechanism, monitoring ได้ง่าย |
| **Authentication** | **JWT + OAuth2** | Stateless auth, รองรับ multi-user/multi-team |
| **HTTP Client** | **httpx** | Async HTTP client สำหรับเรียก API ต่างๆ |

#### 3.2.2 LLM & AI Components

| องค์ประกอบ | เทคโนโลยี | รายละเอียด |
|-----------|----------|-----------|
| **LLM Endpoint** | **vLLM** @ `http://192.168.3.238:8000/v1` | Compatible กับ OpenAI API format (`/v1/chat/completions`, `/v1/embeddings`) |
| **Model แนะนำ** | **Qwen2.5-72B-Instruct** หรือ **Llama-3.1-70B** | ความสามารถภาษาไทยดี, reasoning สูง, รองรับ context window 128K+ |
| **Embedding Model** | **bge-large-th** (Thai-optimized) | สำหรับ semantic search, document clustering ในภาษาไทย |
| **Web Scraping** | **Playwright** + **BeautifulSoup** | Playwright สำหรับ JS-rendered pages, BeautifulSoup สำหรับ HTML parsing เร็ว |
| **Browser Automation** | **Playwright** | จำลอง browser จริง, bypass bot detection บางระดับ, capture screenshots |
| **Image Processing** | **Pillow** + **OpenCV** | ประมวลผลภาพ, resize, OCR (Tesseract) |
| **Report Generation** | **python-docx** (PPTX), **WeasyPrint** (PDF), **openpyxl** (Excel) | สร้างรายงานหลายรูปแบบจาก template |

#### 3.2.3 Database & Storage

| องค์ประกอบ | เทคโนโลยี |用途 |
|-----------|----------|-----|
| **Primary Database** | **PostgreSQL 16** | เก็บข้อมูลโครงสร้างหลัก: Users, Projects, Tasks, Results, Configurations |
| **Vector Store** | **pgvector** (extension ของ PostgreSQL) | เก็บ embeddings ของเอกสาร/เนื้อหา เพื่อ semantic search ภายใน PostgreSQL เดียว ไม่ต้องเพิ่ม infra |
| **Cache / Message Queue** | **Redis 7** | Cache ผลลัพธ์ชั่วคราว, Celery broker, session storage, rate limiting |
| **Object Storage** | **MinIO** (Self-hosted S3-compatible) | เก็บไฟล์ดิบ: screenshots, images, scraped HTML, generated reports |
| **Full-text Search** | **Elasticsearch 8** (หรือ PostgreSQL FTS) | ค้นหาข้อความในข้อมูลดิบและผลลัพธ์อย่างรวดเร็ว |

#### 3.2.4 Frontend & Dashboard

| องค์ประกอบ | เทคโนโลยี | เหตุผลที่เลือก |
|-----------|----------|---------------|
| **Web Application** | **Next.js 14 (React 18)** + **TypeScript** | SSR/SSG, component-based, ecosystem กว้างขวาง, TypeScript ช่วยเรื่อง type safety |
| **UI Component Library** | **shadcn/ui** + **Tailwind CSS** | Modern design, customizable, lightweight |
| **Dashboard Charts** | **Recharts** หรือ **Apache ECharts** | กราฟเชิงโต้ตอบได้, รองรับภาษาไทย |
| **Real-time Updates** | **WebSocket** (ผ่าน FastAPI + Next.js) | แสดงสถานะ agent ทำงานแบบ real-time |
| **State Management** | **Zustand** | Lightweight state management |

#### 3.2.5 DevOps & Infrastructure

| องค์ประกอบ | เทคโนโลยี | เหตุผลที่เลือก |
|-----------|----------|---------------|
| **Containerization** | **Docker** + **Docker Compose** | Containerize ทุก service, reproduce environment ได้ง่าย |
| **Orchestration** | **Kubernetes (K8s)** (เมื่อ scale) | สำหรับ production environment ที่มี traffic สูง |
| **CI/CD** | **GitHub Actions** | Automated testing, building, deployment |
| **Monitoring** | **Prometheus** + **Grafana** | Monitor system metrics, agent performance, LLM latency |
| **Logging** | **ELK Stack** (Elasticsearch + Logstash + Kibana) หรือ **Loki** | Centralized logging |
| **Secrets Management** | **HashiCorp Vault** หรือ **AWS Secrets Manager** | จัดการ API keys, database credentials อย่างปลอดภัย |

### 3.3 Technology Decision Rationale

#### ทำไมเลือก LangGraph แทน LangChain Chain?

- **LangGraph** ให้ explicit state management และ cyclic graph (loop) ซึ่งจำเป็นสำหรับ Agentic workflow ที่ต้องตัดสินใจวนซ้ำ (เช่น scrape → extract → ถ้าข้อมูลไม่ครบ → กลับไป scrape อีกครั้ง)
- LangChain Chains เป็น linear flow ไม่รองรับ decision branching และ self-correction loop ได้ดีเท่า

#### ทำไมเลือก PostgreSQL + pgvector แทน Pinecone/Milvus?

- ลดความซับซ้อนของ infrastructure — ใช้ database เดียวทั้ง relational data และ vector search
- PostgreSQL มีความเสถียรสูง, มี tooling ครบ (backup, replication, migration)
- pgvector รองรับ HNSW index สำหรับ approximate nearest neighbor search ที่เร็วพอสำหรับ use case นี้

#### ทำไมใช้ Playwright แทน Selenium?

- Playwright เร็วกว่า, รองรับ headless mode ได้ดีกว่า, มี auto-wait mechanism, รองรับ multiple browsers (Chromium, Firefox, WebKit)
- สามารถ capture screenshot และ PDF จาก browser ได้โดยตรง

### 3.4 Environment Configuration

```yaml
# .env.example
# =====================
# LLM Configuration
VLLM_ENDPOINT=http://192.168.3.238:8000/v1
VLLM_MODEL=Qwen3.6-35B-A3B-FP8
VLLM_TEMPERATURE=0.3
VLLM_MAX_TOKENS=131072
VLLM_TOP_P=0.9

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ss_autoresearch
REDIS_URL=redis://localhost:6379/0

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=scraped-data

# Embedding
EMBEDDING_MODEL=bge-large-th
EMBEDDING_DIMENSION=1024

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 4. Data Flow Diagram & Architecture Details

### 4.1 High-Level Data Flow (End-to-End)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   User /     │     │   FastAPI    │     │  Agent           │     │   vLLM       │
│   Scheduler  │────▶│   Backend    │────▶│  Orchestration   │────▶│   Endpoint   │
│              │     │              │     │  (LangGraph)     │     │              │
└─────────────┘     └──────┬───────┘     └────────┬─────────┘     └──────┬───────┘
                           │                       │                      │
                           │                       │◀─────────────────────┤
                           │                       │   LLM Response       │
                           │                       │   (Analysis, JSON)   │
                           │                       │                      │
                           ▼                       ▼                      │
                    ┌──────────────┐     ┌──────────────────┐            │
                    │   PostgreSQL │     │  Playwright /     │            │
                    │   + pgvector │     │  Web Scrapers    │            │
                    │   + Redis    │     │  (External Web)   │            │
                    └──────┬───────┘     └────────┬─────────┘            │
                           │                       │                      │
                           │                       ▼                      │
                           │               ┌──────────────────┐          │
                           │               │  MinIO / S3      │          │
                           │               │  (Images, HTML,  │          │
                           │               │   Raw Data)      │          │
                           │               └──────────────────┘          │
                           │                                               │
                           ▼                                               │
                    ┌──────────────┐                                      │
                    │   Report     │◀─────────────────────────────────────┤
                    │   Generator  │        LLM-generated content         │
                    │   (PDF/PPTX) │        + extracted data              │
                    └──────┬───────┘                                      │
                           │                                               │
                           ▼                                               │
                    ┌──────────────┐                                      │
                    │   Next.js    │                                      │
                    │   Frontend   │                                      │
                    │   Dashboard  │                                      │
                    └──────────────┘                                      │
```

### 4.2 Detailed Data Flow by Agentic Loop Stage

#### Stage 1: Input & Planning (User → Planner Agent)

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User    │────▶│  FastAPI     │────▶│  Planner     │────▶│  vLLM        │
│  submits │     │  receives    │     │  Agent       │     │  generates   │
│  query   │     │  request     │     │              │     │  plan JSON   │
└──────────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
                        │                     │                     │
                        │                     │◀────────────────────┤
                        │                     │   Plan: URLs,       │
                        │                     │   Keywords,         │
                        │                     │   Search Strategy   │
                        ▼                     ▼                     │
                 ┌──────────────┐     ┌──────────────┐            │
                 │  PostgreSQL  │     │  Task Queue  │            │
                 │  (log input, │     │  (Celery     │            │
                 │   store task)│     │   dispatch)  │            │
                 └──────────────┘     └──────────────┘            │
```

**ข้อมูลที่ไหล:**
- **Input:** `query`, `target_competitors[]`, `product_category`, `time_range`, `output_format`
- **Output:** `research_plan` (JSON) — รายการ URL ที่ต้อง scrape, keywords, priority order

#### Stage 2: Research & Extraction (Planner → Research Agents)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Research    │────▶│  Playwright  │────▶│  Extractor   │────▶│  vLLM        │
│  Agent       │     │  / Scraper   │     │  Agent       │     │  validates   │
│  (dispatch)  │     │              │     │              │     │  & enrich    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │                     │
       │                    │                     │◀────────────────────┤
       │                    │                     │   Structured data   │
       │                    │                     │   (price, image,    │
       │                    │                     │    channel, etc.)   │
       ▼                    ▼                     ▼                     │
┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  Celery      │     │  MinIO       │     │  PostgreSQL  │            │
│  Worker      │     │  (raw HTML,  │     │  (store      │            │
│  (parallel)  │     │   screenshots│     │   extracted  │            │
│              │     │   files)     │     │   records)   │            │
└──────────────┘     └──────────────┘     └──────────────┘            │
```

**ข้อมูลที่ไหล:**
- **Input to Scraper:** `url_list`, `extraction_schema` (กำหนดว่าต้องการดึง field อะไร)
- **Raw Output:** HTML source, screenshots, images (เก็บใน MinIO)
- **Extracted Data:** JSON structured data — `{ product_name, price, currency, image_url, seller, channel, rating, review_count, ... }`
- **Validation:** vLLM ตรวจสอบความถูกต้องของข้อมูล, เติมข้อมูลที่ขาดหาย

#### Stage 3: Analysis & Synthesis (Extractor → Analyzer Agent)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│  Analyzer    │────▶│  vLLM        │────▶│  Analysis    │
│  (extracted  │     │  Agent       │     │  generates   │     │  Report      │
│   data +    │     │              │     │  insights    │     │  (Markdown/  │
│   embeddings)│     │              │     │              │     │   JSON)      │
└──────────────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │                     │
                            │                     │◀────────────────────┤
                            │                     │   Comparison matrix,│
                            │                     │   SWOT, trends,     │
                            │                     │   recommendations   │
                            ▼                     ▼                     │
                     ┌──────────────┐     ┌──────────────┐            │
                     │  pgvector    │     │  PostgreSQL  │            │
                     │  (semantic   │     │  (store      │            │
                     │   similarity  │     │   analysis   │            │
                     │   search)    │     │   results)   │            │
                     └──────────────┘     └──────────────┘            │
```

**ข้อมูลที่ไหล:**
- **Input to Analyzer:** Extracted data จากทุก competitor, historical data (ถ้ามี), research objectives
- **Processing:** Semantic clustering (pgvector), statistical comparison, trend detection
- **Output:** `analysis_report` — SWOT analysis, competitive positioning, pricing strategy, channel recommendation, market opportunity

#### Stage 4: Report Generation & Delivery (Analyzer → Report Generator → Frontend)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Analysis    │────▶│  Report      │────▶│  MinIO       │────▶│  Next.js     │
│  Results     │     │  Generator   │     │  (final      │     │  Frontend    │
│  (Markdown/  │     │              │     │   reports)   │     │  Dashboard   │
│   JSON)      │     │              │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │                     │
                            │                     │                     │
                            ▼                     ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                     │  PDF file    │     │  PPTX file   │     │  Real-time   │
                     │  (WeasyPrint)│     │  (python-    │     │  status via  │
                     │              │     │   pptx)      │     │  WebSocket   │
                     └──────────────┘     └──────────────┘     └──────────────┘
```

**ข้อมูลที่ไหล:**
- **Input to Generator:** `analysis_report`, `brand_template`, `chart_data`
- **Output Files:** `.pdf`, `.pptx`, `.xlsx` — เก็บใน MinIO พร้อม metadata
- **Frontend Display:** รายงานสรุป, กราฟเปรียบเทียบ, ตารางข้อมูล, ดาวน์โหลดไฟล์

### 4.3 Data Schema Overview (Key Tables)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE SCHEMA                              │
│                                                                      │
│  ┌──────────┐    1:N    ┌──────────────┐    1:N    ┌──────────────┐ │
│  │  users   │──────────▶│  projects    │──────────▶│  tasks       │ │
│  │          │           │              │           │              │ │
│  │ id       │           │ id           │           │ id           │ │
│  │ name     │           │ name         │           │ type         │ │
│  │ email    │           │ description  │           │ status       │ │
│  │ role     │           │ created_at   │           │ payload      │ │
│  └──────────┘           └──────────────┘           └──────┬───────┘ │
│                                                           │         │
│                                                           │ 1:N     │
│                                                           ▼         │
│                                                    ┌──────────────┐ │
│                                                    │ results      │ │
│                                                    │              │ │
│                                                    │ id           │ │
│                                                    │ task_id      │ │
│                                                    │ data_type    │ │
│                                                    │ content      │ │
│                                                    │ raw_file_url │ │
│                                                    │ created_at   │ │
│                                                    └──────────────┘ │
│                                                                      │
│  ┌──────────────┐    1:N    ┌──────────────┐                         │
│  │  competitors │──────────▶│  products    │                         │
│  │              │           │              │                         │
│ ...[truncated]
```

---

## 5. Data Schema & Output Formats

เพื่อให้ระบบ **AutoResearch Agent** สามารถเก็บข้อมูล วิเคราะห์ และนำเสนอผลลัพธ์ได้อย่างเป็นระบบและครบถ้วน เราจึงกำหนดโครงสร้างข้อมูล (JSON Schema) สำหรับข้อมูลดิบ และรูปแบบไฟล์สำหรับรายงานส่งออก (Export Formats) ดังนี้

### 5.1 Competitor Info Schema

ใช้เก็บข้อมูลพื้นฐานของคู่แข่งหรือแบรนด์ต่างๆ ที่พบในการวิจัย

```json
{
  "competitor_id": "string (UUID)",
  "brand_name": "string",
  "website_url": "string (URI)",
  "market_segment": "string (e.g., Premium, Mass Market)",
  "target_audience": ["string"],
  "key_products": [
    {
      "product_id": "string (UUID)",
      "product_name": "string",
      "category": "string",
      "description": "string",
      "launch_date": "date (YYYY-MM-DD)",
      "status": "enum (Active, Discontinued, Upcoming)"
    }
  ],
  "social_media_presence": {
    "facebook_url": "string",
    "instagram_handle": "string",
    "tiktok_handle": "string"
  },
  "last_updated": "datetime (ISO 8601)"
}
```

### 5.2 Product Price Schema

ใช้เก็บข้อมูลราคา สินค้า ช่องทางการขาย และโปรโมชั่น

```json
{
  "price_record_id": "string (UUID)",
  "competitor_id": "string (FK to Competitor Info)",
  "product_id": "string (FK to Competitor Products)",
  "product_name": "string",
  "variant": "string (e.g., Size, Color)",
  "price": {
    "amount": "number",
    "currency": "string (THB, USD, etc.)",
    "unit_price": "number (optional, e.g., price per ml/g)",
    "discount_percentage": "number (0-100)",
    "original_price": "number (optional)"
  },
  "sales_channels": [
    {
      "channel_name": "string (e.g., Shopee, Lazada, Official Website)",
      "channel_url": "string (URI)",
      "availability": "enum (In Stock, Out of Stock, Pre-order)",
      "seller_rating": "number (optional)"
    }
  ],
  "promotions": [
    {
      "promo_type": "string (e.g., Buy 1 Get 1, Flash Sale)",
      "promo_description": "string",
      "valid_until": "date (YYYY-MM-DD)"
    }
  ],
  "data_source_url": "string (URI)",
  "scraped_at": "datetime (ISO 8601)"
}
```

### 5.3 Image Asset Schema

ใช้เก็บข้อมูลรูปภาพที่ดาวน์โหลดมาประกอบรายงาน

```json
{
  "image_id": "string (UUID)",
  "competitor_id": "string (FK)",
  "product_id": "string (FK, optional)",
  "image_url": "string (URI)",
  "local_file_path": "string (Path in workspace/storage)",
  "image_type": "enum (Product Photo, Logo, Screenshot, Infographic)",
  "alt_text": "string (คำอธิบายภาพสำหรับรายงาน)",
  "width_px": "integer",
  "height_px": "integer",
  "file_size_kb": "integer",
  "tags": ["string"]
}
```

### 5.4 Supported Export Formats

ระบบจะถูกออกแบบให้สามารถ Export ผลลัพธ์ออกมาได้ 3 รูปแบบหลัก เพื่อตอบโจทย์การใช้งานที่แตกต่างกันของผู้บริหารและทีมการตลาด

#### 2.1 PDF Report (รายงานฉบับสมบูรณ์)

- **วัตถุประสงค์:** ใช้สำหรับการส่งต่อให้ผู้บริหารระดับสูง (C-Level), การพิมพ์แจกในงานประชุม, หรือการเก็บเป็นเอกสารอ้างอิง
- **ลักษณะเด่น:**
  - มี Cover Page, สารบัญอัตโนมัติ
  - กราฟและแผนภูมิถูก Render เป็น Vector Graphics (คมชัด)
  - รูปภาพคู่แข่งถูกจัดวางใน Layout ที่สวยงาม
  - มี Footer/Header พร้อมเลขหน้าและโลโก้บริษัท

#### 2.2 PPTX Presentation (สไลด์นำเสนอ)

- **วัตถุประสงค์:** ใช้สำหรับนำเสนองาน (Presentation) ในที่ประชุม
- **ลักษณะเด่น:**
  - แยก Slide ตามหัวข้อสำคัญ (Executive Summary, Competitor Overview, Price Comparison, SWOT Analysis)
  - ใช้ Template ขององค์กร (Siam Sindhorn Branding)
  - ข้อมูลตารางและกราฟถูกแปลงเป็น SmartArt หรือ Chart Objects ของ PowerPoint (แก้ไขตัวเลขต่อได้)

#### 2.3 Excel / CSV Summary (สรุปข้อมูลดิบ)

- **วัตถุประสงค์:** ใช้สำหรับทีมวิเคราะห์ข้อมูล (Data Analyst) นำไปทำ Pivot Table หรือวิเคราะห์เชิงลึกต่อ
- **ลักษณะเด่น:**
  - แยก Sheet เป็น Tab ชัดเจน (Competitors, Products, Prices, Promotions)
  - มี Hyperlink ลิงก์กลับไปยังแหล่งข้อมูลต้นทาง
  - คำนวณค่าเฉลี่ยราคา (Average Price) และส่วนแบ่งตลาดโดยประมาณให้ล่วงหน้า

### 5.5 Sample Report Layout

นี่คือตัวอย่างโครงสร้างหน้าตาของรายงาน (PDF/PPTX) ที่ระบบจะสร้างขึ้นอัตโนมัติ:

#### หน้าปก (Cover Page)

- **หัวข้อใหญ่:** รายงานวิเคราะห์คู่แข่งและแนวโน้มตลาด [ชื่อสินค้า/อุตสาหกรรม]
- **หัวข้อย่อย:** สรุปผลการวิจัยโดย AutoResearch Agent
- **วันที่:** [วันที่สร้างรายงาน]
- **โลโก้:** Siam Sindhorn Co., Ltd.

#### บทสรุปผู้บริหาร (Executive Summary)

- **Key Findings:** จุดแข็ง-จุดอ่อนของคู่แข่ง Top 3
- **Price Benchmark:** ช่วงราคาที่เหมาะสมในตลาด
- **Recommendation:** แนวทางการตั้งราคาและช่องทางการขายที่แนะนำ

#### ส่วนที่ 1: ภาพรวมคู่แข่ง (Competitor Landscape)

- **ตารางเปรียบเทียบ:** ชื่อคู่แข่ง, ส่วนแบ่งตลาดโดยประมาณ, จุดเด่น, จุดด้อย
- **รูปภาพ:** โลโก้และภาพหน้าร้าน/Website ของคู่แข่ง

#### ส่วนที่ 2: วิเคราะห์ราคาและโปรโมชั่น (Price & Promotion Analysis)

- **กราฟแท่ง (Bar Chart):** เปรียบเทียบราคาของสินค้าที่คล้ายกันระหว่างคู่แข่ง
- **ตารางรายละเอียด:** รายละเอียด Variant, ราคา, โปรโมชั่นปัจจุบัน, ช่องทางขาย
- **Insight จาก AI:** "พบว่าคู่แข่ง A มักลดราคาในช่วงวันธรรมดา แต่คู่แข่ง B จะเน้น Bundle Deal"

#### ส่วนที่ 3: ช่องทางการขาย (Sales Channel Strategy)

- **แผนที่ความร้อน (Heatmap):** แสดงความเข้มข้นของการขายในแต่ละแพลตฟอร์ม (Shopee, Lazada, TikTok Shop)
- **ตารางช่องทาง:** ชื่อแพลตฟอร์ม, จำนวนร้านค้า, คะแนนรีวิวเฉลี่ย

#### ส่วนที่ 4: ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations)

- **SWOT Analysis:** ตาราง Strengths, Weaknesses, Opportunities, Threats
- **Action Plan:** ขั้นตอนการดำเนินการที่แนะนำ (เช่น ควรเริ่มขายใน TikTok Shop ก่อน เพราะคู่แข่งยังเข้าไม่ถึง)

### 5.6 Tech Stack for Export

| Format | Library / Tool | เหตุผลที่เลือก |
| :--- | :--- | :--- |
| **PDF** | `ReportLab` หรือ `WeasyPrint` | รองรับภาษาไทยได้ดี, จัด Layout ได้ละเอียด, สร้างกราฟได้ |
| **PPTX** | `python-pptx` | แก้ไข Slide, เพิ่ม Chart, ใส่ Template ขององค์กรได้ง่าย |
| **Excel** | `OpenPyXL` หรือ `XlsxWriter` | เขียนข้อมูลลง Sheet หลายๆ หน้า, สร้าง Hyperlink ได้ |

---

## 6. Project Plan & Timeline

### ภาพรวมโครงการ

| รายละเอียด | ค่า |
|-----------|-----|
| **ชื่อโปรเจกต์** | AutoResearch Agent (Siam Sindhorn Automated Research) |
| **เป้าหมาย** | สร้างระบบ Autonomous Web Research & Analysis Agent ที่ใช้ LLM ผ่าน vLLM เพื่อวิจัยตลาด วิเคราะห์คู่แข่ง และสรุปเป็นรายงานอัตโนมัติ |
| **ระยะเวลาโดยประมาณ** | 24 สัปดาห์ (6 เดือน) |

---

### 6.1 Phase 1: MVP — Core Research & Basic Analysis

**ระยะเวลา:** 8 สัปดาห์ (สัปดาห์ 1-8)  
**เป้าหมาย:** ระบบพื้นฐานที่สามารถค้นหาข้อมูล วิเคราะห์ข้อความ และสร้างรายงานเบื้องต้นได้

#### 🎯 Key Objectives

1. ตั้งค่า Infrastructure พื้นฐาน (Backend, Database, vLLM Integration)
2. พัฒนา Agentic Loop ขั้นพื้นฐาน (Planning → Research → Extraction → Analysis → Output)
3. รองรับ Text-based Research จากเว็บไซต์หลัก (HTML scraping + LLM extraction)
4. สร้างรายงานพื้นฐานในรูปแบบ Markdown และ PDF

#### 📋 Deliverables

| ลำดับ | Deliverable | รายละเอียด | สัปดาห์ที่ |
|:-----:|-------------|------------|:----------:|
| 1.1 | Infrastructure Setup | Backend API (FastAPI), PostgreSQL, Redis, Docker Compose | 1-2 |
| 1.2 | vLLM Integration Module | เชื่อมต่อ LLM ผ่าน `http://192.168.3.238:8000/v1` พร้อม Error Handling | 2-3 |
| 1.3 | Web Scraper Engine | HTML-based scraper สำหรับดึงข้อมูลจากเว็บไซต์เป้าหมาย | 3-4 |
| 1.4 | Agentic Loop Core | Planning → Research → Extraction → Analysis → Output (Text only) | 4-6 |
| 1.5 | Data Schema & Storage | เก็บ Competitor, Price, URL, Source ใน PostgreSQL | 5-6 |
| 1.6 | Report Generator (Markdown) | แปลงผลลัพธ์เป็น Markdown format | 6-7 |
| 1.7 | Report Generator (PDF) | Export รายงานเป็น PDF พร้อม Header/Footer | 7-8 |
| 1.8 | Basic CLI / API Testing | ทดสอบ End-to-End workflow ด้วยคำสั่งหรือ API call | 8 |

#### ⏱️ Estimated Time Breakdown

- **Week 1-2:** Infrastructure & Environment Setup
- **Week 3-4:** Web Scraping & vLLM Integration
- **Week 5-6:** Agentic Loop Development & Data Storage
- **Week 7-8:** Report Generation & Testing

#### ✅ Success Criteria (Phase 1)

- สามารถรัน Research Workflow เต็มรูปแบบได้จาก API call
- ดึงข้อมูล Text (ราคา, ลิงก์, แหล่งที่มา) ได้ถูกต้อง ≥ 80%
- สร้างรายงาน PDF ได้สำเร็จภายใน 5 นาทีต่อหนึ่ง Research Task
- ระบบรองรับ Concurrent Requests อย่างน้อย 5 requests/นาที

---

### 6.2 Phase 2: Advanced Features — Image Analysis & Multi-channel Tracking

**ระยะเวลา:** 8 สัปดาห์ (สัปดาห์ 9-16)  
**เป้าหมาย:** เพิ่มความสามารถในการวิเคราะห์รูปภาพ ติดตามหลายช่องทาง และเพิ่มความแม่นยำของการวิเคราะห์

#### 🎯 Key Objectives

1. เพิ่ม Image Recognition & Analysis (ดึงภาพสินค้า, วิเคราะห์ภาพประกอบ)
2. รองรับ Multi-channel Tracking (Shopee, Lazada, TikTok Shop, Website)
3. เพิ่ม Deep Analysis Capabilities (Sentiment Analysis, Trend Detection)
4. สร้าง Dashboard เบื้องต้นสำหรับติดตามสถานะ Research

#### 📋 Deliverables

| ลำดับ | Deliverable | รายละเอียด | สัปดาห์ที่ |
|:-----:|-------------|------------|:----------:|
| 2.1 | Image Scraper & Downloader | ดึงและบันทึกภาพสินค้าจากเว็บไซต์เป้าหมาย | 9-10 |
| 2.2 | Image Analysis Module | ใช้ LLM/Vision Model วิเคราะห์ภาพสินค้า (แบรนด์, สี, ขนาด) | 10-11 |
| 2.3 | Multi-channel Integrations | รองรับ Shopee, Lazada, TikTok Shop APIs/Web Scrapers | 11-13 |
| 2.4 | Price Tracking System | ติดตามการเปลี่ยนแปลงราคาตามเวลา (Price History) | 13-14 |
| 2.5 | Sentiment & Trend Analysis | วิเคราะห์ความรู้สึกและแนวโน้มจากรีวิว/บทความ | 14-15 |
| 2.6 | Basic Dashboard (Web UI) | แสดงสถานะ Research, ผลลัพธ์เบื้องต้น, กราฟราคา | 15-16 |
| 2.7 | Enhanced Report Generator | เพิ่มกราฟ, ตารางเปรียบเทียบ, รูปภาพในรายงาน | 16 |

#### ⏱️ Estimated Time Breakdown

- **Week 9-10:** Image Scraping & Processing Pipeline
- **Week 11-12:** Image Analysis & Vision Model Integration
- **Week 13-14:** Multi-channel Tracking & Price History
- **Week 15-16:** Dashboard & Enhanced Reporting

#### ✅ Success Criteria (Phase 2)

- สามารถดึงและวิเคราะห์ภาพสินค้าได้ถูกต้อง ≥ 75%
- รองรับอย่างน้อย 3 ช่องทางการขาย (Shopee, Lazada, Website)
- ระบบ Price Tracking บันทึกประวัติราคาได้ครบถ้วน
- Dashboard แสดงผล Real-time ของ Research Tasks
- รายงานมีกราฟและตารางเปรียบเทียบอัตโนมัติ

---

### 6.3 Phase 3: Integration & UI Polish

**ระยะเวลา:** 8 สัปดาห์ (สัปดาห์ 17-24)  
**เป้าหมาย:** ปรับปรุง User Interface ให้ใช้งานง่าย เพิ่มฟีเจอร์ขั้นสูง และเตรียมพร้อมสำหรับการ Deploy จริง

#### 🎯 Key Objectives

1. พัฒนา Full-featured Web UI/UX ที่ใช้งานง่าย
2. เพิ่มฟีเจอร์ Collaboration (Share Report, Comment, Review)
3. เพิ่ม Export Options (PPTX, Excel, Custom Templates)
4. ปรับปรุง Performance, Security, และ Monitoring
5. เอกสารการใช้งาน และ Training Materials

#### 📋 Deliverables

| ลำดับ | Deliverable | รายละเอียด | สัปดาห์ที่ |
|:-----:|-------------|------------|:----------:|
| 3.1 | Full Web UI (Frontend) | React/Vue Dashboard พร้อม Navigation, Search, Filters | 17-19 |
| 3.2 | User Authentication & RBAC | Login, Role-based Access Control (Admin, User, Viewer) | 19-20 |
| 3.3 | Report Sharing & Collaboration | Share Link, Comment, Review Workflow | 20-21 |
| 3.4 | Export Modules (PPTX, Excel) | Export รายงานเป็น PowerPoint และ Excel พร้อม Format | 21-22 |
| 3.5 | Custom Report Templates | ผู้ใช้สามารถสร้าง Template รายงานของตัวเองได้ | 22-23 |
| 3.6 | Performance Optimization | Caching, Async Processing, Load Balancing | 23 |
| 3.7 | Security Hardening | API Rate Limiting, Input Validation, Audit Logs | 23-24 |
| 3.8 | Monitoring & Alerting | Prometheus/Grafana Dashboard, Error Alerts | 24 |
| 3.9 | Documentation & Training | User Manual, API Docs, Video Tutorial | 24 |
| 3.10 | UAT & Production Deployment | User Acceptance Testing, Staging → Production | 24 |

#### ⏱️ Estimated Time Breakdown

- **Week 17-19:** Full Web UI Development
- **Week 20-21:** Authentication, Sharing & Collaboration
- **Week 22-23:** Export Features, Optimization & Security
- **Week 24:** Documentation, UAT & Deployment

#### ✅ Success Criteria (Phase 3)

- Web UI ใช้งานง่าย มี UX/UI ที่สวยงาม Responsive
- รองรับ Multi-user พร้อม Role-based Permissions
- Export รายงานเป็น PDF, PPTX, Excel ได้สำเร็จ
- ระบบรองรับ Users พร้อมกัน ≥ 50 คน
- Response Time ≤ 3 วินาที สำหรับ Dashboard interactions
- Zero Critical Security Vulnerabilities หลัง Penetration Test

---

### 6.4 สรุป Timeline ทั้งหมด

```
Phase 1 (MVP)          Phase 2 (Advanced)         Phase 3 (Integration)
Week 1 ──────────────── Week 9 ─────────────────── Week 17 ──────────────── Week 24
│                        │                           │
├─ Infrastructure        ├─ Image Analysis          ├─ Full Web UI
├─ vLLM Integration     ├─ Multi-channel           ├─ Auth & RBAC
├─ Web Scraper          ├─ Price Tracking          ├─ Collaboration
├─ Agentic Loop         ├─ Dashboard               ├─ Export (PPTX/Excel)
├─ Data Storage         ├─ Enhanced Reports        ├─ Optimization
├─ Report Gen (MD/PDF)  │                           ├─ Security
└─ Testing              └─ Testing                  ├─ Documentation
                                                       └─ UAT & Deploy
```

---

### 6.5 Team Structure & Resource Allocation

| บทบาท | จำนวน | ความรับผิดชอบหลัก |
|--------|-------|-------------------|
| Project Manager | 1 | จัดการ Timeline, Coordinate ทีม, Report to Stakeholders |
| Backend Developer | 2 | API, Agentic Loop, Database, Integrations |
| Frontend Developer | 1 | Web UI, Dashboard, UX/UI |
| AI/ML Engineer | 1 | vLLM Integration, Prompt Engineering, Image Analysis |
| QA Engineer | 1 | Testing, Automation, Performance Testing |
| DevOps Engineer | 1 (Part-time) | Docker, CI/CD, Monitoring, Deployment |

---

### 6.6 Risks & Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| vLLM Server Downtime | High | Implement Fallback LLM Provider, Retry Logic |
| Website Anti-bot Protection | Medium | Rotate Proxies, Respect robots.txt, Rate Limiting |
| LLM Hallucination in Analysis | High | Add Fact-checking Step, Confidence Scoring |
| Scope Creep | Medium | Strict Phase Boundaries, Change Request Process |
| Data Quality Issues | High | Data Validation Layer, Manual Review Option |

---

### 6.7 Next Steps (หลังเสร็จ Phase 1)

1. **Demo Internal:** นำเสนอ MVP ให้ทีม Siam Sindhorn ทดลองใช้งาน
2. **Feedback Collection:** รวบรวม Feedback เพื่อปรับปรุง Phase 2
3. **Prioritize Features:** จัดลำดับความสำคัญของฟีเจอร์ใน Phase 2
4. **Budget Review:** ตรวจสอบงบประมาณและทรัพยากรสำหรับ Phase 2-3

---