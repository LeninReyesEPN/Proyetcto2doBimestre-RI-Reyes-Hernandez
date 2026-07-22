# Specification: Chat Interface (001)

## 1. Goal
Create a beautiful, fully functional Gemini/ChatGPT/Claude-style conversational chat application featuring glassmorphism and minimalism design paradigms, utilizing Next.js, React, Tailwind CSS, shadcn/ui, and prompt-kit.

## 2. Target Audience & UX Goals
* **Developer/AI Enthusiast**: Clean, highly readable text, and elegant code blocks.
* **Premium feel**: Minimalist workspace with glassmorphic cards and floating controls. Fluid layouts, seamless sidebar collapsible animation, and intuitive controls.

## 3. Key Features
* **Collapsible Sidebar**: Lists current/past conversations, settings, theme toggle, and a "New Chat" button.
* **Model Picker**: High-fidelity dropdown to select AI engines (Gemini Pro, Claude 3.5 Sonnet, GPT-4o).
* **Prompt suggestions**: Floating chips at the start of a chat to quickly insert prompts.
* **Prompt Input**: Custom textarea with file attachment visual chips, input actions (send, stop generation, microphone visual icon, paperclip).
* **Chat Container**: Displays system instructions, user prompts, thinking states (with a progressive thinking indicator), and assistant messages (formatted in markdown with custom styled code blocks).
* **Message Actions**: Hover options to Copy, Regenerate, or rate (Thumbs Up/Down with Feedback bar).
* **Response Streaming**: Simulated progressive response rendering to show a real LLM typing state.

## 4. Visual Styles
* **Minimalism**: White or black backgrounds with light grey lines, generous padding, absence of cluttered decorations.
* **Glassmorphism**: Cards, sidebars, and input containers having semi-transparent borders (`bg-zinc-950/40 border-white/10 backdrop-blur-md`), subtle radial gradients, and soft drop-shadows.
