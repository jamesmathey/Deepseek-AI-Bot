import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const sendMessage = async (message, conversationId = null, onProgress = null) => {
  try {
    const response = await api.post('/chat', {
      message,
      conversation_id: conversationId,
    }, {
      onDownloadProgress: (progressEvent) => {
        if (onProgress && progressEvent.event.target.response) {
          const lines = progressEvent.event.target.response.split('\n');
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                onProgress(data);
              } catch (e) {
                console.error('Error parsing streaming response:', e);
              }
            }
          }
        }
      },
      responseType: 'text',
      headers: {
        'Accept': 'text/event-stream',
      },
    });
    
    // Parse the last complete response
    const lines = response.data.split('\n');
    const lastLine = lines.filter(line => line.trim()).pop();
    return lastLine ? JSON.parse(lastLine) : null;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const getDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const exportChat = async (conversationId, format) => {
  try {
    const response = await api.post('/export', {
      conversation_id: conversationId,
      format,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};

export const downloadExport = (fileName) => {
  window.open(`${API_URL}/download/${fileName}`, '_blank');
};

export default api;
