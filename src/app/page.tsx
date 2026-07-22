/* eslint-disable react-hooks/set-state-in-effect, react-hooks/purity */
"use client"

import { useState, useEffect, useRef } from "react"
import { Sidebar, ChatSession } from "@/components/sidebar"
import { ChatArea, MessageType } from "@/components/chat-area"

export default function Home() {
  const [chats, setChats] = useState<ChatSession[]>([])
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [messages, setMessages] = useState<MessageType[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  
  const activeStreamRef = useRef<{ stop: () => void } | null>(null)

  // Load chat sessions from localStorage on mount
  useEffect(() => {
    const savedChats = localStorage.getItem("ri_chat_sessions")
    if (savedChats) {
      try {
        const parsed = JSON.parse(savedChats) as ChatSession[]
        setChats(parsed)
        if (parsed.length > 0) {
          setActiveChatId(parsed[0].id)
        }
      } catch (e) {
        console.error("Error parsing chat sessions", e)
      }
    } else {
      // Create a default first chat
      const defaultChat: ChatSession = {
        id: "default-session",
        title: "Nueva conversación",
        modelId: "gemini",
        createdAt: Date.now(),
      }
      setChats([defaultChat])
      setActiveChatId(defaultChat.id)
      localStorage.setItem("ri_chat_sessions", JSON.stringify([defaultChat]))
    }
  }, [])

  // Load messages whenever activeChatId changes
  useEffect(() => {
    if (!activeChatId) {
      setMessages([])
      return
    }
    const savedMessages = localStorage.getItem(`ri_chat_msg_${activeChatId}`)
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages))
      } catch (e) {
        console.error("Error parsing chat messages", e)
        setMessages([])
      }
    } else {
      setMessages([])
    }
  }, [activeChatId, chats])

  const handleSelectChat = (id: string) => {
    setActiveChatId(id)
  }

  const handleNewChat = () => {
    const newId = `session-${Date.now()}`
    const newChat: ChatSession = {
      id: newId,
      title: "Nueva conversación",
      modelId: "gemini",
      createdAt: Date.now(),
    }
    const updatedChats = [newChat, ...chats]
    setChats(updatedChats)
    setActiveChatId(newId)
    localStorage.setItem("ri_chat_sessions", JSON.stringify(updatedChats))
  }

  const handleDeleteChat = (id: string) => {
    const updatedChats = chats.filter(c => c.id !== id)
    setChats(updatedChats)
    localStorage.setItem("ri_chat_sessions", JSON.stringify(updatedChats))
    
    // Clear messages for deleted chat
    localStorage.removeItem(`ri_chat_msg_${id}`)

    if (activeChatId === id) {
      if (updatedChats.length > 0) {
        setActiveChatId(updatedChats[0].id)
      } else {
        setActiveChatId(null)
      }
    }
  }

  const handleSendMessage = (
    content: string,
    files?: Array<{ name: string; type: "image" | "file" }>
  ) => {
    if (!activeChatId) return

    // 1. Create user message
    const userMsg: MessageType = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content,
      files,
    }

    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    localStorage.setItem(`ri_chat_msg_${activeChatId}`, JSON.stringify(newMessages))

    // 2. Update chat title if it was default
    const activeChat = chats.find(c => c.id === activeChatId)
    if (activeChat && activeChat.title === "Nueva conversación") {
      const firstWords = content.split(" ").slice(0, 4).join(" ") + (content.split(" ").length > 4 ? "..." : "")
      const updatedChats = chats.map(c => 
        c.id === activeChatId ? { ...c, title: firstWords || "Conversación" } : c
      )
      setChats(updatedChats)
      localStorage.setItem("ri_chat_sessions", JSON.stringify(updatedChats))
    }

    // 3. Trigger assistant query RAG
    triggerRAGResponse(newMessages, content)
  }

  const triggerRAGResponse = async (currentHistory: MessageType[], userQuery: string) => {
    setIsGenerating(true)

    // Append placeholder assistant message with thinking state
    const assistantMsgId = `msg-${Date.now()}-assistant`
    const initialAssistantMsg: MessageType = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      thinking: true,
    }

    const updatedHistoryWithPlaceholder = [...currentHistory, initialAssistantMsg]
    setMessages(updatedHistoryWithPlaceholder)

    const startTime = Date.now()

    try {
      // Build history for backend, removing the last placeholder message
      const historyPayload = currentHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      // Call local FastAPI RAG API
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: userQuery,
          history: historyPayload
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const fullResponse = data.answer || "No se obtuvo respuesta del sistema RAG."
      const evidences = data.evidences || []
      
      const thinkingSecs = ((Date.now() - startTime) / 1000).toFixed(1)

      // Setup streaming effect for the returned response
      let index = 0
      const charsPerChunk = 6 // Typing speed chunking

      const streamInterval = setInterval(() => {
        index += charsPerChunk
        const currentText = fullResponse.slice(0, index)
        const isDone = index >= fullResponse.length

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  thinking: false,
                  thinkingDuration: `Recuperación y generación en ${thinkingSecs}s`,
                  content: currentText,
                  isStreaming: !isDone,
                  evidences: isDone ? evidences : undefined, // Attach evidences at the end
                }
              : msg
          )
        )

        if (isDone) {
          clearInterval(streamInterval)
          setIsGenerating(false)
          activeStreamRef.current = null

          // Save final messages to localStorage
          setMessages((finalMessages) => {
            localStorage.setItem(
              `ri_chat_msg_${activeChatId}`,
              JSON.stringify(finalMessages)
            )
            return finalMessages
          })
        }
      }, 25)

      activeStreamRef.current = {
        stop: () => {
          clearInterval(streamInterval)
          setIsGenerating(false)
          activeStreamRef.current = null
          // Save current state
          setMessages((currentMsgs) => {
            const updated = currentMsgs.map((m) =>
              m.id === assistantMsgId
                ? { ...m, thinking: false, isStreaming: false, evidences }
                : m
            )
            localStorage.setItem(`ri_chat_msg_${activeChatId}`, JSON.stringify(updated))
            return updated
          })
        }
      }

    } catch (e) {
      console.error("Error connecting to RAG API", e)
      const thinkingSecs = ((Date.now() - startTime) / 1000).toFixed(1)
      
      // Fallback message showing the error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                thinking: false,
                thinkingDuration: `Error en ${thinkingSecs}s`,
                content: "Hubo un error al intentar conectar con el servicio RAG local en `http://localhost:8000`. Asegúrate de que el backend de Python esté corriendo e inicializado.",
                isStreaming: false,
              }
            : msg
        )
      )
      setIsGenerating(false)
    }
  }

  const handleStopGeneration = () => {
    if (activeStreamRef.current) {
      activeStreamRef.current.stop()
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground font-sans transition-colors duration-300">
      {/* Sidebar Component */}
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
      />

      {/* Main Chat Pane */}
      <ChatArea
        messages={messages}
        onSendMessage={handleSendMessage}
        onStopGeneration={handleStopGeneration}
        isGenerating={isGenerating}
        isSidebarCollapsed={isSidebarCollapsed}
        setIsSidebarCollapsed={setIsSidebarCollapsed}
      />
    </div>
  )
}
