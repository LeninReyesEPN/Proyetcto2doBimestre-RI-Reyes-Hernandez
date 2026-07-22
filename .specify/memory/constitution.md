# Project Constitution

## 1. Development Principles
* **Spec-Driven**: Specifications and plans guide execution.
* **Component-Driven**: Build modular, reusable UI components.
* **TypeScript First**: Ensure all files are strictly typed. No `any` types.

## 2. Design System: Glassmorphism & Minimalism
* **Minimalist Layouts**: Clean spacing, plenty of negative space, elegant layout alignments, clear typographic hierarchy.
* **Glassmorphic Accents**: Use backdrops with `backdrop-blur-md` or `backdrop-blur-lg`, semi-transparent borders, and subtle shadows.
* **Colors**: Premium dark-mode-first aesthetic. Deep grays/blacks (`#09090b` or HSL equivalents), smooth gradients, neon/vibrant highlights (e.g. violet, emerald) used sparingly for accents.
* **Typography**: **Josefin Sans** exclusively. Do not switch or revert to default sans-serif, system-ui, or other font families.
* **Interactions**: Subtle scale transitions, opacity fading, micro-interactions on hover and focus.

## 3. Technology Stack
* **Framework**: React 19, Next.js 15 (App Router), Tailwind CSS v4/v3.
* **UI Foundation**: shadcn/ui.
* **AI Layouts**: prompt-kit.
