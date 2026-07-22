# Technical Plan: Chat Interface (001)

## 1. Architecture
We will build a Next.js App Router application written in TypeScript. 
* **State Management**: React `useState` and custom hook `useChatHistory` stored in localStorage.
* **Styling**: Tailwind CSS classes coupled with custom glassmorphic properties.
* **Component Library**: shadcn/ui components (`button`, `dropdown-menu`, `textarea`, `tooltip`, etc.) as primitives, layered with custom styles.
* **Core Layout Library**: prompt-kit custom UI structures (`chat-container`, `prompt-input`, `markdown`, `message`, `thinking-bar`, `scroll-button`).

## 2. Components Design
* **`Sidebar`**: Left-anchored fixed panel, slides offscreen on mobile or collapses to minimal width on desktop. Contains conversation item lists.
* **`ModelPicker`**: Centered or left-aligned floating header selector.
* **`ChatArea`**: Full-flex middle column. Displays suggestion chips if no messages are present.
* **`MessageBubble`**: Contains user message and assistant message. User message is simple, right-aligned. Assistant message is left-aligned with a clean robot logo, rendering Markdown (`prompt-kit/markdown`) and syntax-highlighted code blocks (`prompt-kit/code-block`).

## 3. Glassmorphic Design Specifications
* **Backdrop**: Deep zinc/slate background with radial subtle mesh gradient.
* **Glass class**: `.glass-panel` will use:
  ```css
  background: rgba(24, 24, 27, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  ```
* **Active items**: Subtle white transparency hover `hover:bg-white/5` or `hover:bg-zinc-800/50`.
