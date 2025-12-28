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
		<div className={`chat-widget ${isOpen ? 'chat-widget--open' : ''}`}>
			{/* Окно чата */}
			{isOpen && (
				<div className="chat-window">
					{/* Header */}
					<div className="chat-window__header">
						<div className="chat-window__status">
							<div className="chat-window__avatar-main">
								<Bot size={20} />
							</div>
							<div className="chat-window__details">
								<span className="chat-window__name">WealthWise AI</span>
								<span className="chat-window__online-tag">В сети</span>
							</div>
						</div>
						<button onClick={() => setIsOpen(false)} className="chat-window__close">
							<X size={20} />
						</button>
					</div>

					{/* Messages Area */}
					<div className="chat-window__content">
						{messages.map((msg) => (
							<div
								key={msg.id}
								className={`chat-message ${msg.sender === 'user' ? 'chat-message--user' : 'chat-message--bot'}`}
							>
								<div className="chat-message__avatar">
									{msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
								</div>
								<div className="chat-message__bubble">
									{msg.text}
								</div>
							</div>
						))}
						{isLoading && (
							<div className="chat-message chat-message--bot">
								<div className="chat-message__avatar">
									<Bot size={14} />
								</div>
								<div className="chat-message__bubble chat-message__bubble--loading">
									<span className="dot-loader"></span>
									<span className="dot-loader"></span>
									<span className="dot-loader"></span>
								</div>
							</div>
						)}
						<div ref={messagesEndRef} />
					</div>

					{/* Input Area */}
					<form onSubmit={handleSend} className="chat-window__footer">
						<input
							type="text"
							placeholder="Спроси меня о чем угодно..."
							className="chat-window__input"
							value={inputValue}
							onChange={(e) => setInputValue(e.target.value)}
						/>
						<button
							type="submit"
							disabled={isLoading || !inputValue.trim()}
							className="chat-window__send-btn"
						>
							<Send size={18} />
						</button>
					</form>
				</div>
			)}

			{/* Кнопка открытия (FAB) */}
			<button
				onClick={() => setIsOpen(!isOpen)}
				className={`chat-toggle ${isOpen ? 'chat-toggle--active' : ''}`}
			>
				{isOpen ? <X size={28} /> : <MessageCircle size={28} />}
			</button>
		</div>
	);
};