"use client"

import { useState } from "react"
import { Sparkles, Brain, Bot, ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export type Model = {
  id: string
  name: string
  provider: string
  icon: React.ComponentType<{ className?: string }>
  description: string
  accentColor: string
}

export const MODELS: Model[] = [
  {
    id: "gemini-pro",
    name: "Gemini 1.5 Pro",
    provider: "Google",
    icon: Sparkles,
    description: "Multimodal and advanced reasoning capabilities",
    accentColor: "text-blue-500 dark:text-blue-400",
  },
  {
    id: "claude-sonnet",
    name: "Claude 3.5 Sonnet",
    provider: "Anthropic",
    icon: Brain,
    description: "Exceptional coding, writing, and logic skills",
    accentColor: "text-amber-600 dark:text-amber-500",
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "OpenAI",
    icon: Bot,
    description: "High-speed reasoning and rich conversational agent",
    accentColor: "text-emerald-600 dark:text-emerald-500",
  },
]

type ModelPickerProps = {
  selectedModel: Model
  onModelChange: (model: Model) => void
}

export function ModelPicker({ selectedModel, onModelChange }: ModelPickerProps) {
  const [open, setOpen] = useState(false)
  const Icon = selectedModel.icon

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium hover:bg-black/5 dark:hover:bg-white/5 border border-transparent hover:border-black/5 dark:hover:border-white/5 backdrop-blur-xs transition-all duration-300 cursor-pointer outline-none">
        <Icon className={cn("size-4", selectedModel.accentColor)} />
        <span className="text-zinc-700 dark:text-zinc-300">{selectedModel.name}</span>
        <ChevronDown className={cn("size-3 text-zinc-400 transition-transform duration-300", open && "rotate-180")} />
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        className="w-80 p-2 rounded-2xl glass-panel border-white/10 dark:border-white/5 shadow-2xl backdrop-blur-xl animate-in fade-in-50 zoom-in-95 duration-200"
      >
        <div className="px-2 py-1.5 text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider">
          Seleccionar Modelo AI
        </div>
        {MODELS.map((model) => {
          const ModelIcon = model.icon
          const isSelected = model.id === selectedModel.id
          return (
            <DropdownMenuItem
              key={model.id}
              onClick={() => onModelChange(model)}
              className={cn(
                "flex items-start gap-3 p-2.5 my-1 rounded-xl cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 transition-all duration-200 outline-none",
                isSelected && "bg-black/5 dark:bg-white/5"
              )}
            >
              <div className={cn("p-2 rounded-lg bg-black/5 dark:bg-white/5 mt-0.5", isSelected && "bg-white/10 dark:bg-white/10")}>
                <ModelIcon className={cn("size-4", model.accentColor)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{model.name}</p>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-black/5 dark:bg-white/5 text-zinc-500 font-mono">
                    {model.provider}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-0.5 line-clamp-1">
                  {model.description}
                </p>
              </div>
              {isSelected && (
                <div className="self-center pr-1 text-primary">
                  <Check className="size-4" />
                </div>
              )}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
