import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { chatService } from '../services/api';

export const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: "Привет! Я твой финансовый ассистент. Спроси меня о балансе или тратах.", sender: 'bot' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = { id: Date.now(), text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const data = await chatService.sendMessage(userMsg.text);
      const botMsg = { id: Date.now() + 1, text: data.response, sender: 'bot' };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg = { id: Date.now() + 1, text: "Ошибка связи с сервером.", sender: 'bot' };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Окно чата */}
      {isOpen && (
        <div className="bg-white w-80 h-96 rounded-lg shadow-xl mb-4 flex flex-col border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="bg-primary p-3 flex justify-between items-center text-white">
            <div className="flex items-center gap-2">
              <Bot size={20} />
              <span className="font-medium">WealthWise AI</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-blue-600 rounded p-1">
              <X size={18} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                  ${msg.sender === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}`}>
                  {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className={`max-w-[80%] p-2 rounded-lg text-sm whitespace-pre-line
                  ${msg.sender === 'user' ? 'bg-primary text-white rounded-tr-none' : 'bg-white border text-gray-700 rounded-tl-none shadow-sm'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-2">
                 <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <Bot size={14} className="text-green-600" />
                 </div>
                 <div className="bg-white border p-2 rounded-lg rounded-tl-none shadow-sm text-gray-400 text-sm italic">
                    Печатает...
                 </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t flex gap-2">
            <input
              type="text"
              placeholder="Спроси о финансах..."
              className="flex-1 text-sm border rounded-full px-3 py-1 focus:outline-none focus:ring-2 focus:ring-primary"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="bg-primary text-white p-2 rounded-full hover:bg-blue-600 disabled:opacity-50 transition"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}

      {/* Кнопка открытия */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-primary text-white p-4 rounded-full shadow-lg hover:bg-blue-600 transition duration-200 flex items-center justify-center"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>
    </div>
  );
};