# 🏥 SIMS AI Receptionist

An intelligent healthcare receptionist application powered by **Retrieval-Augmented Generation (RAG)** technology with **advanced hybrid search**. This AI assistant combines **BM25 sparse retrieval** and **Gemini dense embeddings** to provide precise, contextually-aware answers about hospital services, departments, and healthcare information.


## 🎯 Project Overview

The SIMS AI Receptionist uses advanced **hybrid search** technology combining:
- **BM25 sparse retrieval** for keyword-based search
- **Gemini text embedding model** for dense semantic embeddings
- **Google Gemini AI** for contextual response generation

This dual approach ensures both precise keyword matching and semantic understanding of patient queries.

## 🏗️ Architecture

### Backend (FastAPI + RAG Pipeline)
- **Framework**: FastAPI with Python
- **AI Model**: Google Gemini AI integration
- **Vector Database**: Qdrant for document embeddings and similarity search
- **Hybrid Search**: 
  - **Sparse Retrieval**: BM25 for keyword matching
  - **Dense Retrieval**: Gemini text embeddings for semantic search
- **Data Processing**: Hospital departments data from Excel files
- **Deployment**: Dockerized on DigitalOcean

### Frontend (React Native + Expo)
- **Framework**: React Native with Expo
- **UI Design**: Professional black/white healthcare theme
- **Chat Interface**: GiftedChat component for seamless messaging
- **Cross-platform**: Works on both Android and iOS
- **Distribution**: EAS Build for APK generation

## 📁 Project Structure

```
SIMS receptionist/
├── Backend/                          # FastAPI RAG application
│   ├── main.py                      # Main FastAPI application
│   ├── docker-compose.yml           # Docker configuration
│   ├── Dockerfile                   # Container setup
│   ├── requirements.txt             # Python dependencies
│   ├── qdrant_loader.py            # Vector database loader
│   ├── rag_eval_pipeline.py        # RAG evaluation pipeline
│   └── hospital_chunks.txt          # Processed hospital data
├── Dataset_preparation/              # Data processing utilities
│   ├── SHL Departments data.xlsx    # Source hospital data
│   ├── xlsx_to_text.py             # Excel to text converter
│   ├── xlsx_to_sql_with_uiqueID.py # Excel to SQL converter
│   └── hospital_chunks.txt          # Processed text chunks
└── frontend/                        # React Native Expo app
    ├── App.js                       # Main app component
    ├── package.json                 # Node.js dependencies
    ├── app.json                     # Expo configuration
    ├── src/
    │   ├── screens/                 # App screens
    │   ├── context/                 # State management
    │   ├── config/                  # Configuration files
    │   └── styles/                  # UI themes and styles
    └── assets/                      # Images and icons
```

## 🚀 How to Run This Project

### Prerequisites
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **Docker** (optional, for containerized deployment)
- **Expo CLI** (`npm install -g @expo/cli`)
- **EAS CLI** (`npm install -g eas-cli`)

### Data Preparation

First, prepare your hospital data using the utilities in `Dataset_preparation/`:

#### Option 1: Convert Excel to Text
```bash
cd "Dataset_preparation"
python xlsx_to_text.py
```
This converts `SHL Departments data.xlsx` to text format for RAG processing.

#### Option 2: Convert Excel to SQL
```bash
cd "Dataset_preparation"
python xlsx_to_sql_with_uiqueID.py
```
This generates SQL scripts from the Excel data with unique IDs.

### Backend Setup and Deployment

#### Local Development
```bash
# Navigate to backend directory
cd Backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with your Google Gemini API key
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
# Similarily add QDRANT_URL, QDRANT_API_KEY in .env file

# Load data into Qdrant vector database
python qdrant_loader.py

# Start the FastAPI server
python main.py
```

The backend will be available at `http://localhost:8000`

#### Docker Deployment
```bash
# Navigate to backend directory
cd Backend

# Build and run with Docker Compose
docker-compose up --build

# Or run with Docker directly
docker build -t sims-ai-backend .
docker run -p 8000:8000 sims-ai-backend
```

#### Production Deployment (DigitalOcean)
```bash
# On your DigitalOcean droplet
git clone https://github.com/MUHAMMAD-FARMAN/SIMS-AI-receptionist.git
cd SIMS-AI-receptionist/Backend
docker-compose up -d
```

### Frontend Setup and Development

#### Development with Expo Go
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Install additional Expo dependencies
npx expo install

# Start the development server
npm start
# or
npx expo start

# Scan QR code with Expo Go app on your phone
```

#### Building APK for Production
```bash
# Navigate to frontend directory
cd frontend

# Configure EAS (first time only)
eas login
eas build:configure

# Build APK for Android
eas build --platform android --profile preview

# Build for iOS (requires Apple Developer account)
eas build --platform ios --profile preview
```

## 🔧 Configuration

### Backend Configuration
- Update `GOOGLE_API_KEY` in your environment variables
- Configure Qdrant database connection in `main.py`
- Adjust CORS settings for your frontend domain

### Frontend Configuration
- Update `BACKEND_URL` in `src/config/config.js` with your backend URL
- Configure app metadata in `app.json`
- Set up network security for Android in `app.json`

## 🌟 Key Features

- **🤖 Intelligent RAG**: Hybrid search with BM25 + Gemini embeddings
- **💬 Natural Chat Interface**: Intuitive messaging experience
- **🏥 Healthcare Focused**: Specialized for hospital/medical queries
- **📱 Cross-platform**: Works on Android and iOS
- **🎨 Professional UI**: Clean, healthcare-appropriate design
- **🚀 Production Ready**: Dockerized backend, APK distribution
- **🔒 Secure**: Network security configurations for mobile deployment

## 🛠️ Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **Qdrant** - Vector database for embeddings
- **Google Gemini AI** - Large language model
- **BM25** - Sparse retrieval algorithm
- **Docker** - Containerization

### Frontend
- **React Native** - Cross-platform mobile framework
- **Expo** - Development and build platform
- **GiftedChat** - Chat UI components
- **React Navigation** - Navigation library

## 🚀 Deployment Status

- **Backend**: ✅ Deployed on DigitalOcean (`167.71.234.204:8000`)
- **Frontend**: ✅ APK builds successfully with EAS
- **Network**: ✅ Android cleartext traffic configured
- **Database**: ✅ Qdrant vector database operational

## 📱 Testing

### Development Testing
```bash
# Test backend API
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What departments do you have?"}'

# Test frontend with Expo Go
npm start
# Scan QR code with Expo Go app
```

### Production Testing
```bash
# Test deployed backend
curl -X POST "http://167.71.234.204:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Tell me about cardiology department"}'

# Install and test APK on Android device
eas build --platform android --profile preview
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Muhammad Farman**
- GitHub: [@MUHAMMAD-FARMAN](https://github.com/MUHAMMAD-FARMAN)
- Project: [SIMS-AI-receptionist](https://github.com/MUHAMMAD-FARMAN/SIMS-AI-receptionist)

## 🙏 Acknowledgments

- Google Gemini AI for powerful language processing
- Qdrant for efficient vector database operations
- Expo team for excellent mobile development tools
- React Native community for robust cross-platform framework

---

**Ready to revolutionize healthcare communication with AI! 🏥✨**