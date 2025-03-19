import fitz  # PyMuPDF for better text extraction
import os
from transformers import pipeline
import re
import docx
import torch

class ResearchPaperSummarizer:
    def __init__(self):
        # Check GPU availability and set device
        if torch.cuda.is_available():
            print("Using GPU:", torch.cuda.get_device_name(0))
            device = torch.device("cuda:0")
        else:
            print("GPU not available, using CPU")
            device = torch.device("cpu")
            
        # Initialize the summarization pipeline with GPU settings
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=device,
            batch_size=16,  # Increased batch size for GPU
            torch_dtype=torch.float16  # Use half precision for better GPU performance
        )

    def extract_metadata(self, file_path):
        """Extract metadata from document"""
        metadata = {
            'title': None,
            'authors': None
        }
        
        try:
            doc = fitz.open(file_path)
            first_page = doc[0].get_text()
            
            # Clean and split text
            lines = [line.strip() for line in first_page.split('\n') if line.strip()]
            
            # Find title
            title_lines = []
            start_idx = 0
            for i, line in enumerate(lines):
                # Skip header information
                if any(x in line for x in ['©', 'ISSN', 'Volume', 'DOI', 'International Journal']):
                    continue
                
                # Title characteristics
                if (len(line.split()) >= 3 and 
                    not any(x in line.lower() for x in ['university', 'department', 'journal', 'doi', 'issn', 'volume', 'abstract']) and
                    not re.match(r'^\d+\s|^Page\s|^Abstract\s|^Introduction\s', line, re.I)):
                    
                    # If line ends with punctuation, it's complete
                    if re.search(r'[.!?:]$', line):
                        title_lines.append(line)
                        start_idx = i
                        break
                    # If not, look for continuation
                    else:
                        title_lines.append(line)
                        continue
                elif title_lines:
                    start_idx = i
                    break
            
            if title_lines:
                metadata['title'] = ' '.join(title_lines)
            
            # Look for author names after title
            for i in range(start_idx + 1, min(len(lines), start_idx + 10)):
                line = lines[i].strip()
                
                # Skip empty or too long lines
                if not line or len(line) > 100:
                    continue
                
                # Check for author patterns
                if (re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$', line) or  # Simple name
                    re.match(r'^(?:By|Author|Prof|Dr|Mr|Ms|Mrs)[.:]?\s*[A-Z]', line, re.I) or  # Title with name
                    re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+.*(?:Department|University)', line)):  # Name with affiliation
                    
                    # Clean up author line
                    author = line
                    author = re.sub(r'\S+@\S+', '', author)  # Remove email
                    author = re.sub(r'^(?:By|Author|Prof|Dr|Mr|Ms|Mrs)[.:]?\s*', '', author, re.I)  # Remove titles
                    author = re.sub(r'(?:Department|University|College|Institute|Assistant|Professor).*$', '', author, re.I)
                    author = author.strip('., ')
                    
                    if author and len(author.split()) >= 2:
                        metadata['authors'] = author
                        break
            
            doc.close()
            
        except Exception as e:
            print(f"Warning: Error extracting metadata: {str(e)}")
        
        return metadata

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")

    def extract_text_from_word(self, docx_path):
        """Extract text from Word document"""
        try:
            doc = docx.Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading Word file: {str(e)}")

    def extract_text_from_file(self, file_path):
        """Extract text from either PDF or Word document"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_word(file_path)
        else:
            raise Exception(f"Unsupported file format: {file_ext}")

    def generate_summary(self, text):
        """Generate summary using transformers with optimized processing"""
        try:
            # Use larger chunks to reduce processing overhead
            chunk_size = 2048  # Increased from 1024
            chunks = []
            words = text.split()
            current_chunk = []
            current_length = 0
            
            # Create chunks more efficiently
            for word in words:
                current_length += len(word) + 1
                current_chunk.append(word)
                
                if current_length >= chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Filter chunks for meaningful content
            valid_chunks = [chunk for chunk in chunks if len(chunk.split()) > 100]
            
            # Process all chunks in a single batch
            if valid_chunks:
                summaries = self.summarizer(
                    valid_chunks,
                    max_length=150,
                    min_length=50,
                    do_sample=False,
                    truncation=True
                )
                
                # Combine summaries
                final_summary = ' '.join(s['summary_text'] for s in summaries)
                
                # Generate a final, condensed summary if needed
                if len(final_summary.split()) > 500:
                    final_summary = self.summarizer(
                        final_summary,
                        max_length=300,
                        min_length=200,
                        do_sample=False,
                        truncation=True
                    )[0]['summary_text']
                
                return final_summary
            
            return None
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return None

    def process_paper(self, input_path, output_path):
        """Process paper and generate summary"""
        try:
            # Extract metadata and text
            metadata = self.extract_metadata(input_path)
            full_text = self.extract_text_from_file(input_path)
            
            # Generate summary using transformers
            final_summary = self.generate_summary(full_text)
            
            if not final_summary:
                print("Warning: No summary generated")
                return None
            
            # Format output
            output_text = "Research Paper Analysis\n\n"
            if metadata['title']:
                output_text += f"Title: {metadata['title']}\n\n"
            if metadata['authors']:
                output_text += f"Author: {metadata['authors']}\n\n"
            output_text += f"Summary:\n{final_summary}\n"
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            
            return output_text

        except Exception as e:
            print(f"Error processing paper: {str(e)}")
            return None