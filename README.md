
# 📝 Research Paper Summarizer  
An NLP-based tool that automatically generates concise summaries of academic papers (PDF and Word documents) using advanced transformer models.  

## 🚀 **Project Overview**  
This project uses state-of-the-art NLP models to extract and summarize research papers efficiently. It leverages GPU acceleration for faster processing and can handle both PDF and Word document formats.  

### ✅ **Features:**  
- **Automatic Summarization:** Uses `facebook/bart-large-cnn` for high-quality text summarization.  
- **Smart Chunking:** Handles long documents by processing them in manageable chunks.  
- **Batch Processing:** Supports processing multiple documents simultaneously.  
- **GPU Acceleration:** Uses PyTorch with CUDA support for faster inference.  

---

## 🛠️ **Tech Stack:**  
- **PyTorch** – Deep Learning Framework  
- **Transformers** – NLP Models  
- **PyMuPDF** – PDF Processing  
- **python-docx** – Word Document Handling  
- **BART** – Summarization Model  

---

## 📥 **Installation**  

### 1. **Clone the Repository**  
```bash
git clone https://github.com/Avinash8055/Research_summarizer.git  
cd Paper_Summarizer
```

### 2. **Create a Virtual Environment (Optional but Recommended)**  
```bash
python -m venv venv  
source venv/bin/activate  # On Windows, use: .\venv\Scripts\activate
```

### 3. **Install Dependencies**  
```bash
pip install -r requirements.txt
```

---

## ▶️ **Usage**  

### 1. **Summarize Research Papers**  
Place research papers (PDF or Word) into the `input` folder:  
```bash
python paper_summarizer.py
```

### 2. **Run the Main App**  
Launch the main interface to view and manage summaries:  
```bash
python main.py
```
---

