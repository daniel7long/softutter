# SoftUtter — LLM-driven Speech Scaffolding

> Friendly speech scaffolding for language learners.

[![Live demo](https://img.shields.io/badge/Live%20demo-softutter.vercel.app-2ea44f?style=for-the-badge)](https://softutter.vercel.app)

Learners often know **what** they want to say but not **how** to say it in a new language. SoftUtter takes a rough attempt, spoken or typed, and uses a large language model to **scaffold** it into a target sentence with audio, so learners can hear it, repeat it and make it their own.

The first version was a focused prototype for French learners. **SoftUtter 2.0** is a redesigned, much richer web app that supports six languages.

<!-- Add 3–4 screenshots here, e.g.:
<p align="center"><img src="docs/screenshots/compose.png" width="22%"> <img src="docs/screenshots/result.png" width="22%"> <img src="docs/screenshots/shadow.png" width="22%"></p>
-->

| | |
| --- | --- |
| **Live demo** | <https://softutter.vercel.app> |
| **Type** | AI-powered language-learning web app |
| **Languages** | French, Spanish, German, Japanese, Korean, Mandarin Chinese |

---

## How it works

1. **Compose:** record your voice (with a timer) or type what you want to say.
2. **Scaffold:** the model turns your input into a target utterance.
3. **Listen and shadow:** play the target audio and speak along with it.
4. **Keep it:** save useful phrases to your phrasebook.

## Key features (SoftUtter 2.0)

- **Choose your language:** pick which of six languages you want to be scaffolded in.
- **Compose:** voice or text input.
- **Result:** the scaffolded sentence with playable audio.
- **Shadow:** repeat after the target audio.
- **Conversation mode.**
- **Phrasebook:** a personal library of saved phrases.
- **"My sounds" tracker** for the sounds you are working on.

## Design and UX highlights

- **A soft, friendly brand:** a blue-to-teal speech bubble with lips and sound waves, "Soft" in blue and "Utter" in teal.
- **Redesign before rebuild.** Version 2.0 started on the design canvas: compose, result, shadow, conversation and phrasebook screens were designed and approved first, then built.
- **A deliberately small interaction loop:** say it, scaffold it, hear it, repeat it.

## Tech stack

| Layer | Technology |
| --- | --- |
| Intelligence | **Large language model** for scaffolding |
| Front end | Responsive web app |
| Hosting | **Vercel** |
| Design | **Figma** |

<!-- TODO(stack): add the framework, LLM provider and model, speech-to-text and text-to-speech services, and back-end (check package.json / requirements.txt). -->

## Engineering highlights

- **Six languages, including non-Latin scripts** (Japanese, Korean and Mandarin Chinese) alongside French, Spanish and German.
- **From prototype to product.** The project grew from a minimal Streamlit-style tool into a multi-screen web application.
- **Audio in the loop.** Recording, generated target audio and shadowing all sit in one interaction.

---

**Designed and built by [Daniel Long](https://daniel7long.com)** · M.S. Human-Computer Interaction, Carnegie Mellon University
