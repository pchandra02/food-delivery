import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  useToast,
  Container,
  Image,
  Spinner,
} from '@chakra-ui/react';
import { FiSend, FiImage } from 'react-icons/fi';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  const uploadImage = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.filepath;
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  };

  const sendMessage = async () => {
    if (!input.trim() && !selectedImage) return;

    const newMessage: Message = {
      role: 'user',
      content: input,
      metadata: {},
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput('');
    setIsLoading(true);

    try {
      let metadata = {};
      if (selectedImage) {
        const imagePath = await uploadImage(selectedImage);
        metadata = { image_url: imagePath };
        setSelectedImage(null);
      }

      const response = await axios.post('http://localhost:8000/api/v1/chat', {
        message: input,
        metadata,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.response,
          metadata: response.data.metadata,
        },
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: 'Error',
        description: 'Failed to send message. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <Container maxW="container.md" h="100vh" py={4}>
      <VStack h="full" spacing={4}>
        <Box
          flex={1}
          w="full"
          overflowY="auto"
          borderWidth={1}
          borderRadius="md"
          p={4}
        >
          {messages.map((message, index) => (
            <Box
              key={index}
              mb={4}
              p={3}
              borderRadius="md"
              bg={message.role === 'user' ? 'blue.50' : 'gray.50'}
              alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
            >
              <Text>{message.content}</Text>
              {message.metadata?.image_analysis && (
                <Text mt={2} fontSize="sm" color="gray.600">
                  Analysis: {message.metadata.image_analysis}
                </Text>
              )}
            </Box>
          ))}
          {isLoading && (
            <Box textAlign="center" py={4}>
              <Spinner />
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>

        <HStack w="full" spacing={2}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            colorScheme="blue"
            variant="outline"
            disabled={isLoading}
          >
            <FiImage />
          </Button>
          <Button
            onClick={sendMessage}
            colorScheme="blue"
            isLoading={isLoading}
            disabled={!input.trim() && !selectedImage}
          >
            <FiSend />
          </Button>
        </HStack>

        {selectedImage && (
          <Box p={2} borderWidth={1} borderRadius="md">
            <Text fontSize="sm" mb={2}>
              Selected image: {selectedImage.name}
            </Text>
            <Image
              src={URL.createObjectURL(selectedImage)}
              maxH="200px"
              borderRadius="md"
            />
          </Box>
        )}
      </VStack>
    </Container>
  );
};

export default ChatInterface; 