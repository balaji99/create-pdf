import json
import os
from typing import Union, List, Dict
from pathlib import Path
import pypdf
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFConverter:
    def __init__(self, config_path: str, output_path: str):
        """
        Initialize the PDF converter with config and output paths.
        
        Args:
            config_path: Path to JSON configuration file
            output_path: Path where the final PDF should be saved
        """
        self.config_path = config_path
        self.output_path = output_path
        self.writer = pypdf.PdfWriter()

    def get_next_available_filename(self, filepath: str) -> str:
        """
        Get the next available filename by adding a number suffix.
        Example: if test.pdf exists, try test_1.pdf, test_2.pdf, etc.
        
        Args:
            filepath: Original file path
            
        Returns:
            Available file path with number suffix
        """
        path = Path(filepath)
        parent = path.parent
        stem = path.stem
        suffix = path.suffix
        
        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return str(new_path)
            counter += 1

    def handle_existing_file(self) -> str:
        """
        Handle the case where output file already exists.
        
        Returns:
            Final output path to use, or None if processing should stop
        """
        if not os.path.exists(self.output_path):
            return self.output_path
            
        logger.warning(f"Output file already exists: {self.output_path}")
        while True:
            print("\nOutput file already exists. Choose an option:")
            print("1. Overwrite existing file")
            suggested_name = self.get_next_available_filename(self.output_path)
            print(f"2. Use alternative filename: {suggested_name}")
            print("3. Stop processing")
            
            try:
                choice = input("Enter your choice (1/2/3): ").strip()
                
                if choice == '1':
                    logger.info("User chose to overwrite existing file")
                    return self.output_path
                elif choice == '2':
                    logger.info(f"User chose to use alternative filename: {suggested_name}")
                    return suggested_name
                elif choice == '3':
                    logger.info("User chose to stop processing")
                    return None
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except KeyboardInterrupt:
                logger.info("User interrupted the process")
                return None

    def load_config(self) -> dict:
        """Load and validate the JSON configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            if not isinstance(config, dict) or 'files' not in config:
                raise ValueError("Config must be a dictionary with 'files' key")
            
            logger.info(f"Successfully loaded configuration from {self.config_path}")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON config: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise

    def get_files_from_path(self, path: str, recursive: bool = False) -> List[str]:
        """
        Get list of files from a path, which could be a file or directory.
        Files are returned in lexicographical order.
        
        Args:
            path: Path to file or directory
            recursive: Whether to search recursively in directories
            
        Returns:
            List of file paths in lexicographical order
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return []
            
        if path.is_file():
            logger.debug(f"Single file path: {path}")
            return [str(path)]
            
        if path.is_dir():
            logger.info(f"Processing directory: {path} {'recursively' if recursive else 'non-recursively'}")
            if recursive:
                files = []
                for root, _, filenames in sorted(os.walk(str(path))):
                    for filename in sorted(filenames):
                        files.append(str(Path(root) / filename))
                logger.debug(f"Found {len(files)} files recursively in {path}")
                return files
            else:
                files = sorted(str(f) for f in path.glob('*') if f.is_file())
                logger.debug(f"Found {len(files)} files in directory {path}")
                return files
            
        return []

    def process_files_array(self, files_array: List[Union[str, Dict]], 
                          inherited_options: List[str] = None) -> List[Dict]:
        """
        Process the files array from config, returning list of files with their options.
        Maintains lexicographical ordering of files within each context.
        
        Args:
            files_array: Array of file paths or configuration dictionaries
            inherited_options: Options inherited from parent configuration
            
        Returns:
            List of dictionaries containing file paths and their options
        """
        result = []
        inherited_options = inherited_options or []
        
        if inherited_options:
            logger.info(f"Processing with inherited options: {inherited_options}")
            
        for item in files_array:
            if isinstance(item, str):
                logger.info(f"Processing path entry: {item}")
                files = self.get_files_from_path(item)
                for file in files:
                    result.append({
                        'path': file,
                        'options': inherited_options.copy()
                    })
            elif isinstance(item, dict):
                current_options = inherited_options.copy()
                if 'options' in item:
                    new_options = [opt for opt in item['options'] if opt not in current_options]
                    if new_options:
                        logger.info(f"Adding new options: {new_options}")
                    current_options.extend(new_options)
                    
                is_recursive = 'recursive' in current_options
                logger.info(f"Processing dictionary entry with options: {current_options}")
                
                if 'files' in item:
                    sorted_paths = sorted(item['files'])
                    logger.debug(f"Processing files in order: {sorted_paths}")
                    for path in sorted_paths:
                        files = self.get_files_from_path(path, recursive=is_recursive)
                        for file in files:
                            result.append({
                                'path': file,
                                'options': current_options.copy()
                            })
                            
        return result

    def apply_transformations(self, page: pypdf.PageObject, options: List[str]) -> pypdf.PageObject:
        """
        Apply the specified transformations to a PDF page.
        
        Args:
            page: PDF page object
            options: List of transformation options to apply
            
        Returns:
            Transformed PDF page object
        """
        if not options:
            return page

        logger.info(f"Applying transformations: {options}")
        for option in options:
            if option == 'rotate90':
                logger.debug("Rotating page 90 degrees counter-clockwise")
                page.rotate(90)
            elif option == 'rotate180':
                logger.debug("Rotating page 180 degrees")
                page.rotate(180)
            elif option == 'rotate270':
                logger.debug("Rotating page 270 degrees counter-clockwise")
                page.rotate(270)
            elif option == 'flipV':
                logger.debug("Flipping page vertically")
                page.scale(1, -1)
                page.translate_y(page.mediabox.height)
            elif option == 'flipH':
                logger.debug("Flipping page horizontally")
                page.scale(-1, 1)
                page.translate_x(page.mediabox.width)
            elif option == 'recursive':
                # Skip logging for recursive as it's not a page transformation
                continue
            else:
                logger.warning(f"Unknown transformation option: {option}")
                
        return page

    def convert_to_pdf(self, file_path: str) -> pypdf.PdfReader:
        """
        Convert a file to PDF. Currently supports PDFs and common image formats.
        
        Args:
            file_path: Path to the file to convert
            
        Returns:
            PdfReader object containing the converted file
        """
        file_path = Path(file_path)
        if file_path.suffix.lower() == '.pdf':
            logger.debug(f"Processing PDF file directly: {file_path}")
            return pypdf.PdfReader(file_path)
            
        # Handle images
        image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        if file_path.suffix.lower() in image_extensions:
            logger.info(f"Converting image to PDF: {file_path}")
            img = Image.open(file_path)
            if img.mode == 'RGBA':
                logger.debug("Converting RGBA image to RGB")
                img = img.convert('RGB')
            
            pdf_path = file_path.with_suffix('.temp.pdf')
            img.save(pdf_path, 'PDF')
            reader = pypdf.PdfReader(pdf_path)
            os.remove(pdf_path)
            return reader
            
        logger.warning(f"Unsupported file type: {file_path}")
        return None

    def process(self) -> bool:
        """
        Main processing function to create the final PDF.
        
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Handle existing output file
            final_output_path = self.handle_existing_file()
            if final_output_path is None:
                logger.info("Processing stopped due to output file handling")
                return False
            
            # Update output path based on user choice
            self.output_path = final_output_path
            
            config = self.load_config()
            files_with_options = self.process_files_array(config['files'])
            
            logger.info(f"Processing {len(files_with_options)} files in total")
            
            for file_info in files_with_options:
                path = file_info['path']
                options = file_info['options']
                
                logger.info(f"Processing file: {path}")
                if options:
                    logger.info(f"  With options: {options}")
                    
                pdf_reader = self.convert_to_pdf(path)
                
                if pdf_reader:
                    logger.debug(f"Successfully loaded PDF with {len(pdf_reader.pages)} pages")
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        logger.debug(f"Processing page {page_num}")
                        transformed_page = self.apply_transformations(page, options)
                        self.writer.add_page(transformed_page)
                else:
                    logger.error(f"Failed to convert file: {path}")
            
            # Write final PDF
            logger.info(f"Writing final PDF to: {self.output_path}")
            with open(self.output_path, 'wb') as output_file:
                self.writer.write(output_file)
            logger.info("PDF creation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            return False

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert and combine files into a single PDF')
    parser.add_argument('config', help='Path to JSON configuration file')
    parser.add_argument('output', help='Path for output PDF file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    converter = PDFConverter(args.config, args.output)
    success = converter.process()
    
    if not success:
        logger.error("Processing failed")

if __name__ == '__main__':
    main()