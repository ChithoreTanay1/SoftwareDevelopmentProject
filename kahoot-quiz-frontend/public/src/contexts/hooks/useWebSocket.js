// hooks/useWebSocket.js
import { useState, useCallback, useRef } from 'react';

export const useWebSocket = (dispatch) => {
  const [connectionState, setConnectionState] = useState('disconnected');
  const ws = useRef(null);

  const connect = useCallback((url, onMessage) => {
    try {
      setConnectionState('connecting');
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setConnectionState('connected');
        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        onMessage(message);
      };

      ws.current.onclose = () => {
        setConnectionState('disconnected');
        console.log('WebSocket disconnected');
      };

      ws.current.onerror = (error) => {
        setConnectionState('error');
        console.error('WebSocket error:', error);
        dispatch({ type: 'SET_ERROR', payload: 'Connection error' });
      };

    } catch (error) {
      console.error('Failed to connect:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to connect' });
    }
  }, [dispatch]);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  return {
    connect,
    sendMessage,
    disconnect,
    connectionState,
  };
};