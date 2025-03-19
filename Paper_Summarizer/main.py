from paper_summarizer import ResearchPaperSummarizer
import os

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
    summarizer = ResearchPaperSummarizer()
    
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
    
    print("\nAll papers processed. Check the 'output' folder for summaries.")

if __name__ == "__main__":
    main() 