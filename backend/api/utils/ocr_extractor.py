import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import cv2
import numpy as np
import io

class OCRExtractor:
    def __init__(self):
        # Configure tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_text_from_pdf_images(self, file_bytes):
        """Extract text from images within PDF pages"""
        try:
            print("Converting PDF pages to images for OCR...")
            # Convert PDF pages to images
            images = convert_from_bytes(file_bytes, dpi=300)
            
            extracted_text = ""
            for i, image in enumerate(images):
                print(f"Processing page {i+1} with OCR...")
                
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Extract text using tesseract
                page_text = pytesseract.image_to_string(processed_image, lang='eng')
                
                if page_text.strip():
                    extracted_text += f"\n--- Page {i+1} OCR ---\n"
                    extracted_text += page_text
                    
            return extracted_text
            
        except Exception as e:
            print(f"OCR extraction failed: {str(e)}")
            return ""
    
    def extract_text_from_image(self, image_bytes):
        """Extract text from a single image"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            processed_image = self._preprocess_image(image)
            text = pytesseract.image_to_string(processed_image, lang='eng')
            return text
        except Exception as e:
            print(f"Image OCR failed: {str(e)}")
            return ""
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert PIL image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL image
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except Exception as e:
            print(f"Image preprocessing failed: {str(e)}")
            return image  # Return original if preprocessing fails
    
    def is_image_heavy_pdf(self, text, file_size_mb):
        """Check if PDF likely contains important text in images"""
        # If extracted text is very short but file is large, likely image-heavy
        text_length = len(text.strip())
        
        # Heuristics for image-heavy PDFs
        if text_length < 100 and file_size_mb > 0.5:
            return True
        if text_length < 50:
            return True
        if file_size_mb > 2.0 and text_length < 500:
            return True
            
        return False
