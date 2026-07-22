"use client"

import { Plus, MessageSquare, PanelLeftClose, PanelLeft, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

export type ChatSession = {
  id: string
  title: string
  modelId: string
  createdAt: number
}

type SidebarProps = {
  chats: ChatSession[]
  activeChatId: string | null
  onSelectChat: (id: string) => void
  onNewChat: () => void
  onDeleteChat: (id: string) => void
  isCollapsed: boolean
  setIsCollapsed: (collapsed: boolean) => void
}

export function Sidebar({
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  isCollapsed,
  setIsCollapsed,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "relative h-screen flex flex-col glass-panel border-r border-y-0 border-l-0 border-border transition-all duration-300 ease-in-out z-30 shrink-0",
        isCollapsed ? "w-0 border-none overflow-hidden" : "w-72"
      )}
    >
      {/* Top Header - No Logos */}
      <div className={cn(
        "flex items-center justify-between p-4",
        isCollapsed && "md:flex-col md:gap-4 md:items-center"
      )}>
        {!isCollapsed && (
          <span className="font-semibold text-foreground tracking-tight text-sm">
            Conversaciones
          </span>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          title={isCollapsed ? "Expandir" : "Contraer"}
        >
          {isCollapsed ? <PanelLeft className="size-4" /> : <PanelLeftClose className="size-4" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-3 py-2">
        <button
          onClick={onNewChat}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300",
            "bg-primary text-primary-foreground hover:opacity-90 shadow-md cursor-pointer",
            isCollapsed && "md:p-2.5 md:rounded-full md:aspect-square"
          )}
        >
          <Plus className="size-4 shrink-0" />
          {!isCollapsed && <span>Nuevo Chat</span>}
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
        {chats.map((chat) => {
          const isActive = chat.id === activeChatId
          return (
            <div
              key={chat.id}
              className={cn(
                "group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-300 text-muted-foreground hover:text-foreground",
                isActive ? "bg-secondary font-medium text-foreground" : "hover:bg-secondary/40"
              )}
              onClick={() => onSelectChat(chat.id)}
            >
              <MessageSquare className="size-4 shrink-0" />
              {!isCollapsed && (
                <span className="flex-1 text-xs truncate select-none">
                  {chat.title}
                </span>
              )}
              {!isCollapsed && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteChat(chat.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all duration-200 cursor-pointer"
                >
                  <Trash2 className="size-3" />
                </button>
              )}
            </div>
          )
        })}

        {chats.length === 0 && !isCollapsed && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
            <MessageSquare className="size-8 stroke-[1] mb-2 opacity-50" />
            <p className="text-xs">No hay conversaciones</p>
          </div>
        )}
      </div>

      {/* Bottom Footer Actions - No theme toggles, no Project Final texts, no logos */}
      <div className={cn(
        "p-3 border-t border-border flex flex-col gap-2 items-center justify-center",
        isCollapsed && "md:items-center"
      )}>
        {!isCollapsed && (
          <span className="text-[10px] uppercase tracking-wider font-mono text-muted-foreground/50">
            Chat AI
          </span>
        )}
      </div>
    </aside>
  )
}
