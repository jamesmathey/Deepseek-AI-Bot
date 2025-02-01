# AI Document Assistant

An intelligent document assistant that allows users to chat with their documents using state-of-the-art language models. Built with FastAPI, React, and LangChain.

## Features

- 📄 Document Processing: Support for PDF, DOCX, CSV, and JSON files
- 💬 Interactive Chat: Natural conversation with your documents
- 🔍 Smart Search: Semantic search across all uploaded documents
- 📊 Source Citations: Automatic citation of sources in responses
- 💾 Persistent Conversations: Chat history preserved between sessions
- 📥 Export Functionality: Export conversations as PDF or TXT

## Tech Stack

### Backend
- FastAPI
- LangChain
- Ollama (DeepSeek model)
- ChromaDB
- ReportLab
- Python 3.11+

### Frontend
- React
- Material-UI
- Axios
- React Markdown
- React Syntax Highlighter

## Local Development Setup

### Prerequisites

1. Install Python 3.11 or higher
2. Install Node.js 18 or higher
3. Install Ollama from [ollama.ai](https://ollama.ai)
4. Pull the DeepSeek model:
   ```bash
   ollama pull deepseek-r1:32b
   ```

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-doc-assistant.git
   cd ai-doc-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create necessary directories:
   ```bash
   mkdir -p uploads exports vectordb/conversations
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

## Production Deployment

### Backend Deployment

1. Set up a Linux server (Ubuntu 20.04+ recommended)

2. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv nginx
   ```

3. Install Ollama:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

4. Pull the DeepSeek model:
   ```bash
   ollama pull deepseek-r1:32b
   ```

5. Clone and set up the application:
   ```bash
   git clone https://github.com/yourusername/ai-doc-assistant.git
   cd ai-doc-assistant
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. Create a systemd service for Ollama:
   ```bash
   sudo nano /etc/systemd/system/ollama.service
   ```
   Add the following content:
   ```ini
   [Unit]
   Description=Ollama Service
   After=network.target

   [Service]
   Type=simple
   User=root
   ExecStart=/usr/bin/ollama serve
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. Create a systemd service for the FastAPI application:
   ```bash
   sudo nano /etc/systemd/system/aidoc.service
   ```
   Add the following content:
   ```ini
   [Unit]
   Description=AI Document Assistant
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/ai-doc-assistant
   Environment="PATH=/path/to/ai-doc-assistant/venv/bin"
   ExecStart=/path/to/ai-doc-assistant/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

8. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/aidoc
   ```
   Add the following content:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           root /path/to/ai-doc-assistant/frontend/build;
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

9. Enable and start services:
   ```bash
   sudo ln -s /etc/nginx/sites-available/aidoc /etc/nginx/sites-enabled/
   sudo systemctl enable nginx
   sudo systemctl enable ollama
   sudo systemctl enable aidoc
   sudo systemctl start nginx
   sudo systemctl start ollama
   sudo systemctl start aidoc
   ```

### Frontend Deployment

1. Build the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. Copy the build files to the server:
   ```bash
   scp -r build/* user@your_server:/path/to/ai-doc-assistant/frontend/build/
   ```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Backend
UPLOAD_DIR=uploads
DB_DIR=vectordb
EXPORT_DIR=exports
MAX_UPLOAD_SIZE=10485760  # 10MB

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

For production, update the `REACT_APP_API_URL` to your domain.

## Security Considerations

1. Set up SSL/TLS using Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain.com
   ```

2. Configure firewall:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 22
   sudo ufw enable
   ```

3. Set up proper file permissions:
   ```bash
   sudo chown -R ubuntu:ubuntu /path/to/ai-doc-assistant
   chmod -R 755 /path/to/ai-doc-assistant
   ```

## Maintenance

- Monitor logs:
  ```bash
  sudo journalctl -u ollama -f
  sudo journalctl -u aidoc -f
  ```

- Update the application:
  ```bash
  cd /path/to/ai-doc-assistant
  git pull
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart aidoc
  ```

## Troubleshooting

1. Check service status:
   ```bash
   sudo systemctl status ollama
   sudo systemctl status aidoc
   sudo systemctl status nginx
   ```

2. Check logs:
   ```bash
   sudo journalctl -u ollama -n 100
   sudo journalctl -u aidoc -n 100
   sudo tail -f /var/log/nginx/error.log
   ```

3. Common issues:
   - Port conflicts: Check if ports 8000 and 3000 are free
   - Memory issues: Monitor RAM usage with `htop`
   - Disk space: Check available space with `df -h`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 