import os
from openai import OpenAI
from dotenv import load_dotenv
import agentql
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
from grok_summarizer import GrokPaperSummarizer
import glob

print("Starting script...")
load_dotenv()
print("Environment variables loaded")

class AIChat:
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
        )
    
    async def summarize_articles(self, folder_path):
        """Summarize all articles in the folder using Grok"""
        try:
            all_content = []
            for filename in os.listdir(folder_path):
                if filename.endswith(".txt"):
                    with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    system_prompt = """Analyze this article and provide:
                    1. A concise 2-3 sentence summary
                    2. Key findings or main points
                    3. Important quotes if any
                    Keep only the most important information."""
                    
                    completion = self.client.chat.completions.create(
                        model="grok-beta",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": content}
                        ],
                    )
                    
                    # Extract article metadata
                    title = next((line.replace("Title: ", "") for line in content.split('\n') if line.startswith("Title: ")), "")
                    author = next((line.replace("Author: ", "") for line in content.split('\n') if line.startswith("Author: ")), "")
                    date = next((line.replace("Publication Date: ", "") for line in content.split('\n') if line.startswith("Publication Date: ")), "")
                    
                    summary = {
                        "title": title,
                        "author": author,
                        "date": date,
                        "summary": completion.choices[0].message.content
                    }
                    all_content.append(summary)
            
            # Save combined summary
            summary_file = os.path.join(folder_path, "combined_summary.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=== COMBINED ARTICLE SUMMARIES ===\n\n")
                for article in all_content:
                    f.write(f"Article: {article['title']}\n")
                    f.write(f"Author: {article['author']}\n")
                    f.write(f"Date: {article['date']}\n")
                    f.write("\nSummary:\n")
                    f.write(article['summary'])
                    f.write("\n" + "="*50 + "\n\n")
            
            print(f"\nSummary saved to: {summary_file}")
            return summary_file
            
        except Exception as e:
            print(f"Error during summarization: {str(e)}")
            return None

class ArticleScraper:
    def __init__(self):
        print("ArticleScraper initialized")
        self.query = """
        {
            article_title
            article_author
            article_date
            article_content
            important_quotes[]
        }
        """
        self.output_dir = "scraped_articles"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def sanitize_filename(self, title):
        """Convert title to valid filename"""
        return re.sub(r'[<>:"/\\|?*]', '', title)[:100]
    
    async def save_article(self, article_data, url):
        """Save article data to a text file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.sanitize_filename(article_data['article_title'])}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {article_data['article_title']}\n")
            f.write(f"Author: {article_data['article_author']}\n")
            f.write(f"Publication Date: {article_data['article_date']}\n")
            f.write(f"URL: {url}\n")
            f.write("\nMain Content:\n")
            f.write(article_data['article_content'])
            f.write("\n\nKey Quotes:\n")
            for quote in article_data['important_quotes']:
                f.write(f"- {quote}\n")
        
        print(f"Saved article to: {filepath}")
    
    async def scrape_articles(self, topic, num_articles):
        print(f"\nStarting to scrape {num_articles} articles about: {topic}")
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = agentql.wrap(await browser.new_page())
                
                search_query = f"{topic} article"
                await page.goto(f"https://www.google.com/search?q={search_query}")
                await page.wait_for_timeout(3000)
                
                article_urls = await page.evaluate("""() => {
                    const results = Array.from(document.querySelectorAll('.g'));
                    return results
                        .map(result => {
                            const link = result.querySelector('a');
                            return link ? link.href : null;
                        })
                        .filter(url => url && !url.includes('google.com'))
                        .slice(0, 10);
                }""")
                
                for url in article_urls[:num_articles]:
                    print(f"\nScraping article: {url}")
                    try:
                        await page.goto(url)
                        await page.wait_for_timeout(3000)
                        
                        response = await page.query_data(self.query)
                        if response and response.get('article_title'):
                            await self.save_article(response, url)
                        else:
                            print(f"Failed to extract data from: {url}")
                    
                    except Exception as e:
                        print(f"Error scraping article {url}: {str(e)}")
                
                await browser.close()
                
        except Exception as e:
            print(f"ERROR occurred during scraping: {str(e)}")
            return f"Error during scraping: {str(e)}"

class ResearchPaperAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
        )
    
    def analyze_paper(self, input_path, output_path):
        try:
            # First extract metadata and text using Grok
            metadata = self.summarizer.extract_metadata(input_path)
            full_text = self.summarizer.extract_text_from_file(input_path)
            
            # Create prompt for Grok analysis
            system_prompt = """Analyze this research paper and provide:
            1. A comprehensive summary of the main research
            2. Key findings and contributions
            3. Important methodologies used
            4. Significant conclusions
            Keep the focus on the most important aspects of the research."""
            
            # Get Grok's analysis
            completion = self.client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text}
                ],
            )
            
            # Format output
            output_text = "=== Research Paper Analysis ===\n\n"
            
            if metadata['title']:
                output_text += f"Title: {metadata['title']}\n\n"
            if metadata['authors']:
                output_text += f"Author: {metadata['authors']}\n\n"
            
            output_text += "Analysis:\n"
            output_text += completion.choices[0].message.content
            output_text += "\n\n" + "="*50 + "\n"
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            
            return output_text
            
        except Exception as e:
            print(f"Error analyzing paper: {str(e)}")
            return None

def main():
    # Create input/output directories
    input_dir = "input"
    output_dir = "output"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n=== Research Paper Summarizer ===")
    print(f"Reading papers from '{input_dir}' folder...")
    
    # Get all PDF and Word files
    files = []
    for file in os.listdir(input_dir):
        if file.lower().endswith(('.pdf', '.doc', '.docx')):
            files.append(os.path.join(input_dir, file))
    
    if not files:
        print(f"\nNo PDF or Word files found in {input_dir}")
        return
    
    # Initialize summarizer
    summarizer = GrokPaperSummarizer()
    
    # Process each file
    for file_path in files:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        try:
            # Create output filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_summary.txt")
            
            # Process the paper
            summary = summarizer.process_paper(file_path, output_path)
            
            if summary:
                print(f"Summary saved to: {output_path}")
            else:
                print(f"Failed to generate summary for {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
    
    print("\nAll papers processed. Check the 'output1' folder for summaries.")

if __name__ == "__main__":
    main()
