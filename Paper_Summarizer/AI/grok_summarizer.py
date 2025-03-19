import fitz  # PyMuPDF for better text extraction
import os
from openai import OpenAI
import re
import docx
from dotenv import load_dotenv

class GrokPaperSummarizer:
    def __init__(self):
        # Initialize Grok client
        load_dotenv()
        self.api_key = os.getenv("XAI_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
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
        """Generate summary using Grok"""
        try:
            system_prompt = """You are a research paper analyzer. Analyze this paper and provide:
            1. A comprehensive summary of the main research objectives and methodology
            2. Key findings and important results
            3. Significant conclusions and implications
            
            Format the response in clear sections and maintain academic tone."""
            
            completion = self.client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating summary with Grok: {str(e)}")
            return None

    def process_paper(self, input_path, output_path):
        """Process paper and generate summary"""
        try:
            # Extract metadata and text
            metadata = self.extract_metadata(input_path)
            full_text = self.extract_text_from_file(input_path)
            
            # Generate summary using Grok
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