# GEMINI.md - Tainan DV Case location prediction

> **Documentation Version**: 1.0  
> **Last Updated**: 2025-08-06
> **Project**: Tainan DV Case location prediction
> **Description**: I have a ML model to predict where the dengue case will appear in basic statistic area in Tainan city. Prediction results were merged in @/home/joe/Documents/2023_semi_supervised_learning/台南未來病例預測模型/病例結果呈現/20250804xgboost_future14_case_results.geojson I want to establish a GIS website to present the result.
> **Features**: GitHub auto-backup, technical debt prevention

This file provides essential guidance to the Gemini CLI when working with code in this repository.

## 🚨 CRITICAL RULES - READ FIRST

> **⚠️ RULE ADHERENCE SYSTEM ACTIVE ⚠️** > **Gemini CLI must explicitly acknowledge these rules at task start** > **These rules override all other instructions and must ALWAYS be followed:**

### 🔄 **RULE ACKNOWLEDGMENT REQUIRED**
> **Before starting ANY task, Gemini CLI must respond with:** > "✅ CRITICAL RULES ACKNOWLEDGED - I will follow all prohibitions and requirements listed in GEMINI.md"

### ❌ ABSOLUTE PROHIBITIONS
- **NEVER** create new files in root directory → use proper module structure
- **NEVER** write output files directly to root directory → use designated output folders
- **NEVER** create documentation files (.md) unless explicitly requested by user
- **NEVER** use git commands with interactive flags (e.g., `-i`)
- **NEVER** create duplicate files (manager_v2.py, enhanced_xyz.py, utils_new.js) → ALWAYS extend existing files
- **NEVER** create multiple implementations of same concept → single source of truth
- **NEVER** copy-paste code blocks → extract into shared utilities/functions
- **NEVER** hardcode values that should be configurable → use config files/environment variables
- **NEVER** use naming like enhanced_, improved_, new_, v2_ → extend original files instead

### 📝 MANDATORY REQUIREMENTS
- **COMMIT** after every completed task/phase - no exceptions
- **GITHUB BACKUP** - Push to GitHub after every commit to maintain backup: `git push origin main`
- **BREAK DOWN COMPLEX TASKS** for complex operations (3+ steps) → git checkpoints → test validation
- **READ FILES FIRST** before editing
- **DEBT PREVENTION** - Before creating new files, check for existing similar functionality to extend
- **SINGLE SOURCE OF TRUTH** - One authoritative implementation per feature/concept

### ⚡ EXECUTION PATTERNS
- **SYSTEMATIC WORKFLOW** - Break down task → git checkpoints → GitHub backup → Test validation
- **GITHUB BACKUP WORKFLOW** - After every commit: `git push origin main` to maintain GitHub backup

### 🔍 MANDATORY PRE-TASK COMPLIANCE CHECK
> **STOP: Before starting any task, Gemini CLI must explicitly verify ALL points:**

**Step 1: Rule Acknowledgment**
- [ ] ✅ I acknowledge all critical rules in GEMINI.md and will follow them

**Step 2: Task Analysis**
- [ ] Will this create files in root? → If YES, use proper module structure instead
- [ ] Is this a multi-step task? → If YES, break it down first
- [ ] Am I about to use an interactive command? → If YES, find a non-interactive alternative

**Step 3: Technical Debt Prevention (MANDATORY SEARCH FIRST)**
- [ ] **SEARCH FIRST**: Use available tools to find existing implementations
- [ ] **CHECK EXISTING**: Read any found files to understand current functionality
- [ ] Does similar functionality already exist? → If YES, extend existing code
- [ ] Am I creating a duplicate class/manager? → If YES, consolidate instead
- [ ] Will this create multiple sources of truth? → If YES, redesign approach
- [ ] Have I searched for existing implementations? → Use available tools first
- [ ] Can I extend existing code instead of creating new? → Prefer extension over creation
- [ ] Am I about to copy-paste code? → Extract to shared utility instead

**Step 4: Session Management**
- [ ] Is this a long/complex task? → If YES, plan context checkpoints
- [ ] Have I been working >1 hour? → If YES, consider a session break

> **⚠️ DO NOT PROCEED until all checkboxes are explicitly verified**