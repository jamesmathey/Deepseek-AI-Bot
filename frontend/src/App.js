import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Drawer,
  Menu,
  MenuItem,
  IconButton,
  Avatar,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import SendIcon from '@mui/icons-material/Send';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { uploadDocument, sendMessage, getDocuments, exportChat, downloadExport } from './services/api';

function App() {
  const theme = useTheme();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [currentResponse, setCurrentResponse] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);
  const [exportAnchorEl, setExportAnchorEl] = useState(null);
  const [exporting, setExporting] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    fetchDocuments();
    scrollToBottom();
  }, [messages]);

  const fetchDocuments = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const onDrop = async (acceptedFiles) => {
    setLoading(true);
    try {
      for (const file of acceptedFiles) {
        await uploadDocument(file);
      }
      await fetchDocuments();
    } catch (error) {
      console.error('Error uploading document:', error);
    }
    setLoading(false);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'application/json': ['.json']
    }
  });

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setCurrentResponse('🤔 Thinking...');

    try {
      // Add a temporary thinking message
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: currentResponse,
        isStreaming: true
      }]);

      await sendMessage(
        userMessage, 
        conversationId,
        (data) => {
          setCurrentResponse(data.response || '🤔 Thinking...');
          // Update the last message with the current response
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.isStreaming) {
              lastMessage.content = data.response || '🤔 Thinking...';
              if (data.sources) {
                lastMessage.sources = data.sources;
              }
              if (data.conversation_id) {
                setConversationId(data.conversation_id);
              }
            }
            return newMessages;
          });
        }
      );

      // Update the final message to mark it as complete
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.isStreaming) {
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.isStreaming) {
          lastMessage.content = 'Sorry, I encountered an error processing your request.';
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });
    }
    setLoading(false);
    setCurrentResponse('');
  };

  const handleExportClick = (event) => {
    setExportAnchorEl(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportAnchorEl(null);
  };

  const handleExport = async (format) => {
    if (!conversationId || messages.length === 0) return;
    
    setExporting(true);
    handleExportClose();
    
    try {
      const response = await exportChat(conversationId, format);
      downloadExport(response.file_name);
    } catch (error) {
      console.error('Error exporting chat:', error);
    }
    
    setExporting(false);
  };

  const copyToClipboard = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const MessageAvatar = ({ role }) => (
    <Avatar
      sx={{
        bgcolor: role === 'assistant' ? 'primary.main' : 'secondary.main',
        width: 36,
        height: 36,
      }}
    >
      {role === 'assistant' ? <SmartToyIcon /> : <PersonIcon />}
    </Avatar>
  );

  const ThinkingIndicator = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
      <CircularProgress size={16} />
      <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
        Thinking...
      </Typography>
    </Box>
  );

  const CodeBlock = ({ language, value }) => (
    <Box sx={{ position: 'relative', my: 2 }}>
      <Box sx={{ 
        position: 'absolute', 
        top: 8, 
        right: 8, 
        zIndex: 1,
        display: 'flex',
        gap: 1
      }}>
        <Typography variant="caption" sx={{ color: 'grey.500' }}>
          {language}
        </Typography>
        <IconButton
          size="small"
          onClick={() => copyToClipboard(value, value)}
          sx={{ color: 'grey.500' }}
        >
          {copiedIndex === value ? <CheckCircleIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
        </IconButton>
      </Box>
      <SyntaxHighlighter
        language={language}
        style={atomDark}
        customStyle={{
          margin: 0,
          borderRadius: theme.shape.borderRadius,
          padding: '2rem 1rem 1rem 1rem',
        }}
      >
        {value}
      </SyntaxHighlighter>
    </Box>
  );

  const MessageContent = ({ message }) => {
    const components = {
      code({ node, inline, className, children, ...props }) {
        const match = /language-(\w+)/.exec(className || '');
        return !inline && match ? (
          <CodeBlock language={match[1]} value={String(children).replace(/\n$/, '')} />
        ) : (
          <code className={className} {...props}>
            {children}
          </code>
        );
      }
    };

    return (
      <Box sx={{ width: '100%' }}>
        <ReactMarkdown components={components}>
          {message.content}
        </ReactMarkdown>
        {message.sources && (
          <Box sx={{ 
            mt: 2,
            p: 1.5,
            borderRadius: 1,
            bgcolor: alpha(theme.palette.primary.main, 0.08),
          }}>
            <Typography variant="subtitle2" sx={{ mb: 1, color: 'primary.main' }}>
              Sources
            </Typography>
            {message.sources.map((source, idx) => (
              <Box key={idx} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  • {source.document_name} (Page {source.page_number})
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ height: '100vh', py: 4 }}>
      <Box sx={{ display: 'flex', height: '100%', gap: 2 }}>
        {/* Document Upload and List Sidebar */}
        <Drawer
          variant="permanent"
          sx={{
            width: 300,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 300,
              boxSizing: 'border-box',
              position: 'relative',
              height: '100%',
              bgcolor: 'grey.50',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Paper
              {...getRootProps()}
              sx={{
                p: 3,
                mb: 2,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? alpha(theme.palette.primary.main, 0.08) : 'background.paper',
                border: `2px dashed ${isDragActive ? theme.palette.primary.main : theme.palette.grey[300]}`,
                borderRadius: 2,
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                  borderColor: theme.palette.primary.main,
                }
              }}
            >
              <input {...getInputProps()} />
              <UploadFileIcon sx={{ fontSize: 40, mb: 1, color: 'primary.main' }} />
              <Typography variant="subtitle1" sx={{ mb: 1, color: 'text.primary' }}>
                {isDragActive ? "Drop files here" : "Upload Documents"}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Drag & drop or click to select
              </Typography>
            </Paper>

            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Documents</Typography>
            <List sx={{ 
              maxHeight: 'calc(100vh - 280px)', 
              overflow: 'auto',
              '& .MuiListItem-root': {
                borderRadius: 1,
                mb: 1,
                '&:hover': {
                  bgcolor: 'action.hover',
                }
              }
            }}>
              {documents.map((doc, index) => (
                <ListItem key={index} sx={{ bgcolor: 'background.paper' }}>
                  <ListItemText 
                    primary={doc.filename}
                    secondary={
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 0.5,
                        color: doc.status === 'processed' ? 'success.main' : 'text.secondary'
                      }}>
                        {doc.status === 'processed' ? <CheckCircleIcon fontSize="small" /> : <CircularProgress size={16} />}
                        <Typography variant="caption">
                          {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>

        {/* Chat Interface */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            {(!conversationId || messages.length === 0 || exporting) ? (
              <IconButton
                disabled
                color="primary"
                sx={{
                  bgcolor: 'background.paper',
                  boxShadow: 1,
                  '&.Mui-disabled': {
                    bgcolor: 'grey.100',
                  }
                }}
              >
                {exporting ? <CircularProgress size={24} /> : <DownloadIcon />}
              </IconButton>
            ) : (
              <Tooltip title="Export Conversation" arrow>
                <IconButton
                  onClick={handleExportClick}
                  color="primary"
                  sx={{
                    bgcolor: 'background.paper',
                    boxShadow: 1,
                    '&:hover': {
                      bgcolor: 'grey.100',
                    }
                  }}
                >
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            )}
            <Menu
              anchorEl={exportAnchorEl}
              open={Boolean(exportAnchorEl)}
              onClose={handleExportClose}
              PaperProps={{
                elevation: 3,
                sx: {
                  mt: 1,
                  minWidth: 180,
                }
              }}
            >
              <MenuItem onClick={() => handleExport('pdf')}>
                <Typography>Export as PDF</Typography>
              </MenuItem>
              <MenuItem onClick={() => handleExport('txt')}>
                <Typography>Export as Text</Typography>
              </MenuItem>
            </Menu>
          </Box>

          <Paper 
            sx={{ 
              flex: 1, 
              mb: 2, 
              overflow: 'auto',
              bgcolor: 'grey.50',
              borderRadius: 2,
              p: 3,
            }}
          >
            {messages.map((message, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  gap: 2,
                  mb: 3,
                  opacity: message.isStreaming ? 0.7 : 1,
                }}
              >
                <MessageAvatar role={message.role} />
                <Box sx={{ flex: 1 }}>
                  <Paper
                    elevation={message.role === 'assistant' ? 1 : 0}
                    sx={{
                      p: 2,
                      bgcolor: message.role === 'assistant' ? 'background.paper' : alpha(theme.palette.primary.main, 0.05),
                      borderRadius: 2,
                    }}
                  >
                    {message.isStreaming && message.role === 'assistant' && <ThinkingIndicator />}
                    <MessageContent message={message} />
                  </Paper>
                </Box>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </Paper>

          <Paper
            component="form"
            elevation={2}
            sx={{
              p: 1,
              display: 'flex',
              gap: 1,
              bgcolor: 'background.paper',
              borderRadius: 3,
            }}
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <TextField
              fullWidth
              variant="standard"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              InputProps={{
                disableUnderline: true,
                sx: { 
                  px: 2, 
                  py: 1,
                  '&.Mui-disabled': {
                    bgcolor: 'transparent',
                  }
                }
              }}
            />
            <Tooltip title={loading ? "Sending..." : "Send message"} arrow>
              <span>
                <Button
                  variant="contained"
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  sx={{
                    borderRadius: 3,
                    px: 3,
                    minWidth: 54,
                    bgcolor: 'primary.main',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '&.Mui-disabled': {
                      bgcolor: 'grey.300',
                    }
                  }}
                >
                  {loading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
                </Button>
              </span>
            </Tooltip>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}

export default App; 