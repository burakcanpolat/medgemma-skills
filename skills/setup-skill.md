# Setup Skill

This skill guides non-technical users through the complete Med-Rehber setup from scratch.

Detailed instructions: `.agents/skills/medgemma-setup/SKILL.md`

## Summary Flow

```
STEP 0:  Welcome + language selection
STEP 1:  Editor check (Zed / Cursor / Claude Code)
STEP 2:  Python 3.10+ check / install
STEP 3:  Modal account creation (free, modal.com/signup)
STEP 4:  Modal CLI install + auth (modal setup)
STEP 5:  HuggingFace account + token + model license
STEP 6:  Deploy MedGemma (modal deploy scripts/modal_medgemma.py)
STEP 7:  Create .env with endpoint URL
STEP 8:  Connection test
STEP 9:  First analysis trial (user picks from 3 options)
STEP 10: Complete + usage guide
```

## Triggers

Apply this skill when the user says:
- "setup", "install", "kurulum", "get started", "start setup"
- "first time", "how to use", "what do I need to do"
- Automatically trigger if `.env` file does not exist
