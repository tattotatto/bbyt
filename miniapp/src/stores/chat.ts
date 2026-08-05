import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMessage {
  id: string
  type: 'text' | 'thinking' | 'product_card' | 'order_confirm' | 'order_result' | 'quick_replies' | 'error'
  content?: string
  products?: any[]
  order?: any
  items?: string[]
  isUser?: boolean
  _streaming?: boolean
  timestamp: number
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const connected = ref(false)

  const lastMessage = computed(() => messages.value[messages.value.length - 1] || null)
  const messageCount = computed(() => messages.value.length)

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function updateLastMessage(updates: Partial<ChatMessage>) {
    const last = messages.value[messages.value.length - 1]
    if (last) Object.assign(last, updates)
  }

  function clearQuickReplies() {
    messages.value = messages.value.filter(
      m => m.type !== 'quick_replies' && m.type !== 'thinking'
    )
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    connected,
    lastMessage,
    messageCount,
    addMessage,
    updateLastMessage,
    clearQuickReplies,
    clearMessages
  }
})
