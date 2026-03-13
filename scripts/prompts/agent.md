# Prompt Reference — 10min AI Daily

This is copied from [.github/agent.md](../../.github/agent.md) to keep the hackathon context close to the codebase. Update this copy if the upstream prompt changes.

> Paste the following content in full to an LLM (e.g. Claude / GPT) to receive a complete PRD, individual task breakdowns, and tech stack recommendations.

---

## System Prompt

```
You are a senior technical product manager and engineering lead. You are helping a 6-person hackathon team plan and execute their project from idea to demo. You must produce three deliverables in order:

1. A detailed PRD (Product Requirements Document)
2. Individual task breakdowns for each team member
3. A concrete tech stack recommendation for every component

Be specific, actionable, and hackathon-aware — prioritize speed, feasibility, and demo impact. All project management will be done in Linear, so structure tasks in a way that maps cleanly to Linear issues (with labels, priorities, and dependencies).
```

## User Prompt

```
We are a 6-person hackathon team building a product called "10min AI Daily." Please complete the following three tasks in order:

---

### Task 1: Write a Detailed PRD

Based on the product description below, generate a complete, well-structured PRD containing the following sections:

#### Product Context

**Product positioning:** 10 minutes a day to stay up-to-date on the latest AI developments.

**Core value proposition:** Spark user curiosity, minimize cognitive load, deliver fast understanding — no wading through repetitive or redundant information. Users get first-hand sources and relief from FOMO/anxiety.

**Core pain points solved:**
a. The AI industry moves too fast — practitioners and enthusiasts struggle to keep up.
b. Reporting delays + too many sources → noise, anxiety, wasted time.

#### PRD Sections Required:

1. **Product Overview**
   - Product name, one-line positioning, target user persona
   - Core value proposition (as described above)
   - Pain points addressed

2. **Feature Specifications**
   For each module below, provide: feature description, user stories, inputs/outputs, acceptance criteria, and priority level (P0/P1/P2).

   - **Module 1: Data Ingestion**
     - Scrape/API-fetch daily trending content from:
       - GitHub Trending repos
       - Hugging Face daily papers / trending models
       - Official blogs/news from OpenAI, Anthropic, Google DeepMind, etc.
     - Output: structured raw content list (title, summary, URL, source, timestamp)

   - **Module 2: Pre-processing**
     - Quality assessment: is a single source sufficient? If not, trigger supplementary web searches
     - Text cleaning: strip HTML tags, ads, irrelevant content; extract core text
     - Generate structured data for cards (title, keywords/thumbnail, one-line summary)
     - Generate cleaned full text for briefing generation

   - **Module 3: Card Interaction (Tinder-style UI)**
     - Present users with a daily set of info cards
     - Card content: title + image or keyword tags (minimal, like a YouTube thumbnail + title)
     - Goal: let users quickly judge interest without needing domain expertise
     - Interaction: swipe left = Pass, swipe right = add to today's Knowledge Basket
     - Constraint: Basket has a cap (e.g. max 5 cards) to keep briefing length manageable

   - **Module 4: Recommendation System**
     - Log user-card interaction history (swipe direction, dwell time, etc.)
     - Use a lightweight recommendation algorithm to personalize future card feeds
     - A simple, open-source approach is sufficient

   - **Module 5: Knowledge Graph**
     - Extract keywords from each card the user adds to their Basket
     - Feature 1: Create Node — extract key concepts as graph nodes
     - Feature 2: Connect Nodes — identify relationships between nodes and create edges
     - Feature 3: Merge Graph — each time new content is added, merge the new subgraph with the user's accumulated historical graph
     - Provide interactive visualization to enhance understanding, sense of achievement, and retention

   - **Module 6: 10-Minute Briefing**
     - Generate a readable AI daily briefing based on the user's selected Basket cards
     - Requirements: understandable without a technical background; focus on what happened and its impact on the industry/individual
     - Not a deep technical analysis — low cognitive load information consumption
     - Target reading time: ~10 minutes

   - **Module 7 (P2 — only if time permits): Sharing**
     - Share the briefing with others
     - Share the knowledge graph; the recipient's account should support Connect + Merge with their own graph

3. **User Flow**
   - Complete user journey from opening the app to reading the briefing
   - Annotate which backend module corresponds to each step

4. **Data Model**
   - List core data entities and their fields (User, Card, Interaction Record, Knowledge Graph Node/Edge, Briefing, etc.)
   - Describe entity relationships (ER diagram description is fine)

5. **Non-Functional Requirements**
   - Performance targets (card load time, briefing generation time, etc.)
   - Reasonable expectations for a hackathon context

6. **MVP Scope & Prioritization**
   - Clearly distinguish Must-have (P0), Should-have (P1), Nice-to-have (P2)
   - Define the critical path for the hackathon demo

7. **Risks & Dependencies**
   - Technical risks, time risks, API rate limits, etc.

---

### Task 2: Generate Detailed Individual Task Lists for Each Team Member

Our team assignments are:
1. **Sam**: Web scraping + pre-processing + project management (Linear)
2. **Sunny**: Pre-processing + 10-min briefing generation + demo video
3. **Steve**: UI + database + testing
4. **Alex**: UI + demo video + knowledge graph (assisting Harry)
5. **Liam**: Recommendation system + web scraping + pre-processing
6. **Harry**: Knowledge graph (primary owner)

For each team member, generate:

#### Each person's task list must include:
a. **Role Summary**: all modules they own and their role within the team
b. **Detailed Task List** (ready to import as Linear Issues), where each task contains:
   - Task title (concise, actionable)
   - Task description (what to do, how to do it, what the output is)
   - Priority: P0 / P1 / P2
   - Estimated time
   - Upstream dependencies (which person's task must be completed first)
   - Suggested Linear labels (e.g. `backend`, `frontend`, `data`, `infra`, `testing`, `design`)
c. **Collaboration interfaces**: clearly state what data/APIs this person needs from whom, and what they need to deliver to whom
d. **Milestones / Checkpoints**: break down by timeline (e.g. Day 1 Morning, Day 1 Afternoon, Day 2 Morning, etc. — assume a 2-day hackathon)

#### Additional requirement for Sam (Project Manager):
Generate a **Linear project structure recommendation** including:
- Project naming and hierarchy
- Label taxonomy (module labels + type labels)
- Milestone / Cycle setup suggestions
- Board View status columns (e.g. Backlog → In Progress → In Review → Done)
- A suggested workflow for standup check-ins during the hackathon

---

### Task 3: Tech Stack Recommendations for Each Component

For each module below, recommend a specific tech stack. Requirements:
- Suitable for a hackathon (fast development, low configuration overhead)
- Provide a **primary choice + alternative**
- Explain the reasoning

Modules to cover:
1. **Data Ingestion / Scraping**: scraping GitHub, HuggingFace, company blogs
2. **Pre-processing**: text cleaning, quality assessment, supplementary search
3. **Backend Services**: API framework, task scheduling
4. **Database**: storing user data, cards, interaction logs, graph data
5. **Frontend / UI**: Tinder-style card swiping, knowledge graph visualization
6. **Recommendation System**: lightweight recommendation algorithm
7. **Knowledge Graph**: keyword extraction, graph data structure, visualization library
8. **Briefing Generation**: LLM API integration, prompt design approach
9. **Sharing Feature**: link generation, graph import/export
10. **Project Management / DevOps**: Linear setup, code repository, deployment
11. **Demo Video**: recording and editing tools

Present this in table format with columns: Module | Primary Choice | Alternative | Reasoning

---

### Output Format Requirements:
- Use Markdown formatting throughout
- PRD section should follow standard document structure
- Task lists should be organized by team member, using tables or numbered lists per task
- Tech stack section should use tables
- If the output is too long, you may split across multiple responses — but provide a table of contents at the beginning
```

---

## How to Use

1. Set the **System Prompt** as the system message (if the platform supports it); otherwise place it at the very top
2. Paste the entire **User Prompt** and send
3. If the output gets cut off, send `Please continue` to get the rest
4. After receiving the output, you can follow up with questions like:
   - `Please generate Sam's tasks in CSV format importable to Linear`
   - `Please refine the tech stack recommendations down to specific package names and versions`
   - `Please write a detailed technical design doc for the Knowledge Graph module`
   - `Please generate an hour-by-hour schedule for the full hackathon`
   - `Please write the system prompts needed for the briefing generation module`
   - `Please define the API contracts (endpoints, request/response schemas) between frontend and backend`
