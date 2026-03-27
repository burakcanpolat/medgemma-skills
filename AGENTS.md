# Med-Rehber

Medical image analysis and general medical assistant project.

## Language Preference

At the start of every conversation, check `reports/user_config.md`.

- If the file exists and contains a `language:` field → use that language for all interactions.
- If the file does not exist:
  1. Ask:
     ```
     🌐 Please choose your language / Lütfen dilinizi seçin:

     1. 🇬🇧 English
     2. 🇹🇷 Türkçe
     ```
  2. Save the choice to `reports/user_config.md`:
     ```
     language: en
     ```
     (or `language: tr`)
  3. Confirm in the chosen language and proceed.

**All subsequent communication, reports, and analysis output MUST be in the user's chosen language.**

## First-Run Check

After setting the language, check if the `.env` file exists. If it doesn't:
1. Tell the user (in their chosen language): "Welcome! This looks like your first time. Shall we set things up together?"
2. If they agree, read `skills/setup-skill.md` and start the setup wizard
3. Do not perform any analysis until setup is complete

If the user says "setup", "install", "kurulum", "get started" → read `skills/setup-skill.md`.
If the user says "help", "yardım" → show the help section from the setup skill.

## Skill Routing

- **Setup / install** → `skills/setup-skill.md`
- **Medical images** (X-ray, CT, MRI) → Read and apply `skills/radiology-skill.md`
- **Lab results, medications, symptoms** → Read and apply `skills/medical-assistant-skill.md`

## Patient Intake (Before Any Analysis)

Before analyzing anything, collect the following from the user (ask one at a time, in their language):

1. **Who is this report for?** (themselves / a relative / general information)
2. **Age and gender**
3. **Complaint/reason** — "Why was this test done?"
4. **Known medical conditions** (if any)
5. **Current medications** (if any)

Save this to `reports/patient_info.md`. On subsequent analyses, read this file — do not ask again.
Always use the filename `patient_info.md` (in English) regardless of the user's language preference.

If emergency signs are present → stop intake, recommend calling emergency services (112 in Turkey, or local number).

## MedGemma Pipeline

For image analysis, use `scripts/medgemma_api.py`:

```bash
# Single image (always base64 — efficient for one file)
python3 scripts/medgemma_api.py images/xray.jpeg

# Multiple images (auto volume, base64 fallback)
python3 scripts/medgemma_api.py images/d0.jpg images/d1.jpg

# ZIP archive (auto volume, base64 fallback)
python3 scripts/medgemma_api.py archive.zip

# Force base64 mode (skip volume upload)
python3 scripts/medgemma_api.py --base64 archive.zip
```

**Volume-first strategy:** For ZIP files and multiple images, the script automatically uploads to Modal Volume and uses file:// paths (41MB → 25KB for 309 images). If Modal CLI is not installed or upload fails, it falls back to base64 silently.

**Cold start handling:** On first request, the script checks if the server is ready. If the Modal container is cold-starting (loading the AI model into GPU), progress feedback is shown until the server responds (typically 2-5 minutes).

Each series is independent: ≤85 images → single request, >85 → batched in groups of 85.
MedGemma outputs in English → translate findings into the user's chosen language in plain, simple terms.

## Modal Deployment

The MedGemma server runs on Modal. Deploy script: `scripts/modal_medgemma.py`.

```bash
modal deploy scripts/modal_medgemma.py
```

This creates:
- `medgemma-vllm` app with vLLM + MedGemma model
- `medgemma-hf-cache` volume for model weights (avoids re-download)
- `med-images` volume for image uploads (used automatically by volume-first strategy)

## Report Saving

Save reports as `reports/YYYY-MM-DD_short-description_report.md`.

## Language & Style

Use simple, plain language that anyone can understand — in the user's chosen language.
If medical terms are needed, explain them in parentheses.
