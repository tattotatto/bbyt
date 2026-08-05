// WebSocket 聊天连接管理
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

let socketTask: any = null

const BASE_WS_URL = 'wss://baby.mx.yn.cn' // 生产环境

export function connectChat() {
  const userStore = useUserStore()
  const chatStore = useChatStore()

  if (socketTask) {
    console.log('WebSocket already connected')
    return
  }

  const url = `${BASE_WS_URL}/api/v1/ai/ws/chat?token=${userStore.token}`
  console.log('Connecting to:', url)

  socketTask = uni.connectSocket({
    url,
    success: () => {
      console.log('WebSocket connecting...')
    },
    fail: (err: any) => {
      console.error('WebSocket connect failed:', err)
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'error',
        content: '连接失败，请检查网络后重试',
        isUser: false,
        timestamp: Date.now(),
      })
    }
  })

  socketTask.onOpen(() => {
    console.log('WebSocket connected')
    chatStore.connected = true
  })

  socketTask.onMessage((res: any) => {
    try {
      const msg = JSON.parse(res.data)
      handleMessage(msg)
    } catch (e) {
      console.error('Failed to parse message:', e)
    }
  })

  socketTask.onClose((res: any) => {
    console.log('WebSocket closed:', res)
    chatStore.connected = false
    socketTask = null
  })

  socketTask.onError((err: any) => {
    console.error('WebSocket error:', err)
    chatStore.connected = false
  })
}

function handleMessage(msg: any) {
  const chatStore = useChatStore()

  switch (msg.type) {
    case 'text_chunk':
      // 流式追加：找到最后一条 AI 文本消息并追加
      const messages = chatStore.messages
      const lastMsg = messages[messages.length - 1]
      if (lastMsg && lastMsg.type === 'text' && !lastMsg.isUser && lastMsg._streaming !== false) {
        lastMsg.content = (lastMsg.content || '') + msg.content
        lastMsg._streaming = true
      } else {
        chatStore.addMessage({
          id: Date.now().toString(),
          type: 'text',
          content: msg.content,
          isUser: false,
          _streaming: true,
          timestamp: Date.now(),
        })
      }
      break

    case 'text_done':
      // 流式结束标记
      const last = chatStore.messages[chatStore.messages.length - 1]
      if (last && last._streaming) {
        last._streaming = false
      }
      break

    case 'text':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'text',
        content: msg.content,
        isUser: false,
        timestamp: Date.now(),
      })
      break

    case 'thinking':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'thinking',
        content: msg.content,
        isUser: false,
        timestamp: Date.now(),
      })
      break

    case 'product_card':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'product_card',
        products: msg.products,
        content: msg.message,
        isUser: false,
        timestamp: Date.now(),
      })
      break

    case 'order_confirm':
    case 'order_result':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: msg.type,
        order: msg.order,
        content: msg.content || '',
        isUser: false,
        timestamp: Date.now(),
      })
      break

    case 'quick_replies':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'quick_replies',
        items: msg.items,
        isUser: false,
        timestamp: Date.now(),
      })
      break

    case 'error':
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'error',
        content: msg.content,
        isUser: false,
        timestamp: Date.now(),
      })
      break
  }
}

export function sendMessage(content: string) {
  if (!socketTask) {
    uni.showToast({ title: '连接已断开，请重新进入', icon: 'none' })
    return
  }

  const chatStore = useChatStore()

  // 添加用户消息
  chatStore.addMessage({
    id: Date.now().toString(),
    type: 'text',
    content,
    isUser: true,
    timestamp: Date.now(),
  })

  // 清除旧的 quick_replies 和 thinking
  chatStore.clearQuickReplies()

  // 发送
  socketTask.send({
    data: JSON.stringify({ content }),
    fail: (err: any) => {
      console.error('Send failed:', err)
      chatStore.addMessage({
        id: Date.now().toString(),
        type: 'error',
        content: '发送失败，请重试',
        isUser: false,
        timestamp: Date.now(),
      })
    }
  })
}

export function disconnectChat() {
  if (socketTask) {
    socketTask.close()
    socketTask = null
  }
  const chatStore = useChatStore()
  chatStore.connected = false
}

export function isConnected(): boolean {
  const chatStore = useChatStore()
  return chatStore.connected
}
