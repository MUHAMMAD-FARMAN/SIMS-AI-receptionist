import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { GiftedChat } from 'react-native-gifted-chat';
import { LinearGradient } from 'expo-linear-gradient';
import uuid from 'react-native-uuid';
import { useUser } from '../context/UserContext';
import { BACKEND_URL } from '../config/config';

const ChatScreen = () => {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const { user } = useUser();

  useEffect(() => {
    // Welcome message
    setMessages([
      {
        _id: uuid.v4(),
        text: 'Hello! I\'m your RAG Assistant. How can I help you today?',
        createdAt: new Date(),
        user: {
          _id: 2,
          name: 'RAG Assistant',
          avatar: 'https://ui-avatars.com/api/?name=AI&background=8b5cf6&color=fff',
        },
        system: false,
      },
    ]);
  }, []);

  const sendQueryToBackend = async (userMessage) => {
    try {
      console.log('Attempting to connect to:', `${BACKEND_URL}/query`);
      
      const response = await fetch(`${BACKEND_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage,
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      return data.answer || 'Sorry, I couldn\'t process your request.';
    } catch (error) {
      console.error('Detailed error information:');
      console.error('Error type:', error.name);
      console.error('Error message:', error.message);
      console.error('Full error:', error);
      
      Alert.alert(
        'Connection Error',
        `Unable to connect to the server: ${error.message}\n\nTrying to reach: ${BACKEND_URL}/query`,
        [{ text: 'OK' }]
      );
      return `Sorry, I'm having trouble connecting to the server: ${error.message}`;
    }
  };

  const onSend = useCallback(async (newMessages = []) => {
    setMessages(previousMessages => GiftedChat.append(previousMessages, newMessages));
    
    // Show typing indicator
    setIsTyping(true);
    
    // Get the user's message
    const userMessage = newMessages[0].text;
    
    // Send to backend and get response
    const response = await sendQueryToBackend(userMessage);
    
    // Hide typing indicator
    setIsTyping(false);
    
    // Add bot response
    const botMessage = {
      _id: uuid.v4(),
      text: response,
      createdAt: new Date(),
      user: {
        _id: 2,
        name: 'RAG Assistant',
        avatar: 'https://ui-avatars.com/api/?name=AI&background=8b5cf6&color=fff',
      },
    };
    
    setMessages(previousMessages => GiftedChat.append(previousMessages, [botMessage]));
  }, []);

  return (
    <LinearGradient
      colors={['#f9fafb', '#f3f4f6']}
      style={styles.container}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
        keyboardVerticalOffset={90}
      >
        <GiftedChat
          messages={messages}
          onSend={messages => onSend(messages)}
          user={{
            _id: user._id,
            name: user.name,
            avatar: user.avatar,
          }}
          placeholder="Type your message..."
          alwaysShowSend
          isTyping={isTyping}
          showUserAvatar
          showAvatarForEveryMessage={false}
          scrollToBottom
          renderUsernameOnMessage
          timeFormat="HH:mm"
          dateFormat="MMM DD, YYYY"
          inverted={true}
        />
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  inputToolbar: {
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    backgroundColor: '#fff',
    paddingTop: 6,
    paddingBottom: 6,
  },
  sendButton: {
    marginRight: 10,
    marginBottom: 5,
    backgroundColor: '#6366f1',
    borderRadius: 20,
    padding: 10,
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  systemMessageContainer: {
    backgroundColor: 'transparent',
    alignItems: 'center',
    marginVertical: 10,
  },
  systemMessageText: {
    fontSize: 12,
    color: '#9ca3af',
    fontStyle: 'italic',
  },
});

export default ChatScreen;
