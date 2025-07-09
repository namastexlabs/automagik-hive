'use client'
import { useState, useRef } from 'react'
import { toast } from 'sonner'
import { TextArea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { usePlaygroundStore } from '@/store'
import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useQueryState } from 'nuqs'
import Icon from '@/components/ui/icon'

const ChatInput = () => {
  const { chatInputRef } = usePlaygroundStore()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { handleStreamResponse } = useAIChatStreamHandler()
  const [selectedAgent] = useQueryState('agent')
  const [inputMessage, setInputMessage] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const isStreaming = usePlaygroundStore((state) => state.isStreaming)
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files) {
      setSelectedFiles(Array.from(files))
    }
  }

  const handleSubmit = async () => {
    if (!inputMessage.trim()) return

    const currentMessage = inputMessage
    setInputMessage('')
    setSelectedFiles([])

    try {
      await handleStreamResponse(currentMessage)
    } catch (error) {
      toast.error(
        `Error in handleSubmit: ${
          error instanceof Error ? error.message : String(error)
        }`
      )
    }
  }

  return (
    <div className="relative mx-auto mb-1 w-full max-w-2xl">
      {selectedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {selectedFiles.map((file, index) => (
            <div key={index} className="flex items-center gap-1 rounded bg-secondary px-2 py-1 text-xs">
              <span>{file.name}</span>
              <button
                onClick={() => setSelectedFiles(files => files.filter((_, i) => i !== index))}
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      
      <div className="flex items-end gap-x-2 font-geist">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={!selectedAgent}
          size="icon"
          variant="outline"
          className="rounded-xl"
        >
          <Icon type="plus-icon" />
        </Button>
        
        <TextArea
          placeholder={'Ask anything'}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (
              e.key === 'Enter' &&
              !e.nativeEvent.isComposing &&
              !e.shiftKey &&
              !isStreaming
            ) {
              e.preventDefault()
              handleSubmit()
            }
          }}
          className="w-full border border-input bg-background px-4 text-sm text-foreground focus:border-ring"
          disabled={!selectedAgent}
          ref={chatInputRef}
        />
        
        <Button
          onClick={handleSubmit}
          disabled={!selectedAgent || !inputMessage.trim() || isStreaming}
          size="icon"
          className="rounded-xl bg-primary p-5 text-primary-foreground"
        >
          <Icon type="send" />
        </Button>
      </div>
    </div>
  )
}

export default ChatInput
