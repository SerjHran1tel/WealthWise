import React, { useState, useRef, useEffect } from 'react';
import {
	Paper,
	IconButton,
	TextField,
	Avatar,
	Box,
	Typography,
	CircularProgress,
} from '@mui/material';
import {
	Chat as MessageCircleIcon,
	Close as XIcon,
	Send as SendIcon,
	SmartToy as BotIcon,
	Person as UserIcon,
} from '@mui/icons-material';
import { chatService } from '../services/api';

export const ChatWidget = () => {
	const [isOpen, setIsOpen] = useState(false);
	const [messages, setMessages] = useState([
		{ id: 1, text: 'Привет! Я твой финансовый ассистент. Спроси меня о балансе или тратах.', sender: 'bot' },
	]);
	const [inputValue, setInputValue] = useState('');
	const [isLoading, setIsLoading] = useState(false);

	const messagesEndRef = useRef(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages, isOpen]);

	const handleSend = async (e) => {
		e.preventDefault();
		if (!inputValue.trim()) return;

		const userMsg = { id: Date.now(), text: inputValue, sender: 'user' };
		setMessages((prev) => [...prev, userMsg]);
		setInputValue('');
		setIsLoading(true);

		try {
			const data = await chatService.sendMessage(userMsg.text);
			const botMsg = { id: Date.now() + 1, text: data.response, sender: 'bot' };
			setMessages((prev) => [...prev, botMsg]);
		} catch (error) {
			console.error('Chat error:', error);
			const errorMsg = { id: Date.now() + 1, text: 'Ошибка связи с сервером.', sender: 'bot' };
			setMessages((prev) => [...prev, errorMsg]);
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<Box sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 50, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
			{isOpen && (
				<Paper
					elevation={6}
					sx={{
						width: 320,
						height: 400,
						mb: 2,
						display: 'flex',
						flexDirection: 'column',
						overflow: 'hidden',
						borderRadius: 3,
					}}
				>
					{/* Header */}
					<Box sx={{ bgcolor: 'primary.main', color: 'white', p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
						<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
							<BotIcon />
							<Typography variant="subtitle1" fontWeight="bold">WealthWise AI</Typography>
						</Box>
						<IconButton size="small" sx={{ color: 'white' }} onClick={() => setIsOpen(false)}>
							<XIcon />
						</IconButton>
					</Box>

					{/* Messages */}
					<Box sx={{ flex: 1, overflowY: 'auto', p: 2, bgcolor: 'grey.50' }}>
						{messages.map((msg) => (
							<Box
								key={msg.id}
								sx={{ display: 'flex', gap: 1, mb: 2, flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row' }}
							>
								<Avatar sx={{ width: 32, height: 32, bgcolor: msg.sender === 'user' ? 'primary.light' : 'success.light' }}>
									{msg.sender === 'user' ? <UserIcon fontSize="small" /> : <BotIcon fontSize="small" />}
								</Avatar>
								<Paper
									variant="outlined"
									sx={{
										p: 1.5,
										maxWidth: '70%',
										bgcolor: msg.sender === 'user' ? 'primary.main' : 'background.paper',
										color: msg.sender === 'user' ? 'white' : 'text.primary',
										borderRadius: 2,
										borderTopLeftRadius: msg.sender === 'bot' ? 0 : 2,
										borderTopRightRadius: msg.sender === 'user' ? 0 : 2,
									}}
								>
									<Typography variant="body2">{msg.text}</Typography>
								</Paper>
							</Box>
						))}
						{isLoading && (
							<Box sx={{ display: 'flex', gap: 1 }}>
								<Avatar sx={{ width: 32, height: 32, bgcolor: 'success.light' }}>
									<BotIcon fontSize="small" />
								</Avatar>
								<Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'background.paper', borderRadius: 2 }}>
									<Typography variant="body2" color="text.secondary" fontStyle="italic">
										Печатает...
									</Typography>
								</Paper>
							</Box>
						)}
						<div ref={messagesEndRef} />
					</Box>

					{/* Input */}
					<Box component="form" onSubmit={handleSend} sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
						<TextField
							size="small"
							fullWidth
							placeholder="Спроси о финансах..."
							value={inputValue}
							onChange={(e) => setInputValue(e.target.value)}
							disabled={isLoading}
						/>
						<IconButton type="submit" color="primary" disabled={isLoading || !inputValue.trim()}>
							<SendIcon />
						</IconButton>
					</Box>
				</Paper>
			)}

			<IconButton
				onClick={() => setIsOpen(!isOpen)}
				sx={{
					bgcolor: 'primary.main',
					color: 'white',
					'&:hover': { bgcolor: 'primary.dark' },
					width: 56,
					height: 56,
				}}
			>
				{isOpen ? <XIcon /> : <MessageCircleIcon />}
			</IconButton>
		</Box>
	);
};