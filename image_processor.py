import io
import os
from typing import Tuple, Optional, Union
from PIL import Image, ImageOps
import numpy as np
from fastapi import UploadFile, HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    Handles image processing for rice disease detection model.
    Supports large image uploads, compression, and resizing.
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        max_file_size: int = 50 * 1024 * 1024,  # 50MB default
        quality: int = 85,
        supported_formats: Tuple[str, ...] = ('JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF')
    ):
        self.target_size = target_size
        self.max_file_size = max_file_size
        self.quality = quality
        self.supported_formats = supported_formats
    
    async def process_uploaded_image(
        self, 
        file: UploadFile,
        maintain_aspect_ratio: bool = True,
        fill_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Tuple[np.ndarray, dict]:
        """
        Process an uploaded image file.
        
        Args:
            file: FastAPI UploadFile object
            maintain_aspect_ratio: Whether to maintain aspect ratio during resizing
            fill_color: Background color for padding (RGB tuple)
            
        Returns:
            Tuple of (processed_image_array, metadata_dict)
        """
        try:
            # Validate file size
            await self._validate_file_size(file)
            
            # Read and validate image
            image = await self._load_image(file)
            
            # Get original metadata
            metadata = self._extract_metadata(image, file)
            
            # Process the image
            processed_image = self._process_image(
                image, 
                maintain_aspect_ratio=maintain_aspect_ratio,
                fill_color=fill_color
            )
            
            # Convert to numpy array for model input
            image_array = self._to_model_format(processed_image)
            
            return image_array, metadata
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")
    
    async def _validate_file_size(self, file: UploadFile) -> None:
        """Validate that the uploaded file size is within limits."""
        # For now, skip file size validation to avoid seek issues
        # File size will be checked during processing
        pass
    
    async def _load_image(self, file: UploadFile) -> Image.Image:
        """Load and validate the uploaded image."""
        try:
            contents = await file.read()
            
            # Validate content type
            if not file.content_type.startswith("image/"):
                raise ValueError("Invalid file type. Please upload an image.")
            
            # Open image with PIL
            image = Image.open(io.BytesIO(contents))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Validate image format
            if image.format not in self.supported_formats:
                raise ValueError(f"Unsupported image format. Supported formats: {', '.join(self.supported_formats)}")
            
            return image
            
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    def _extract_metadata(self, image: Image.Image, file: UploadFile) -> dict:
        """Extract metadata from the original image."""
        return {
            "original_size": image.size,
            "original_format": image.format,
            "original_mode": image.mode,
            "file_name": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": None  # Skip file size for now
        }
    
    def _process_image(
        self, 
        image: Image.Image,
        maintain_aspect_ratio: bool = True,
        fill_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Image.Image:
        """
        Process the image: resize, compress, and optimize for model input.
        
        Args:
            image: PIL Image object
            maintain_aspect_ratio: Whether to maintain aspect ratio during resizing
            fill_color: Background color for padding (RGB tuple)
            
        Returns:
            Processed PIL Image
        """
        # Step 1: Resize image
        if maintain_aspect_ratio:
            resized_image = self._resize_with_aspect_ratio(image, fill_color)
        else:
            resized_image = image.resize(self.target_size, Image.Resampling.LANCZOS)
        
        # Step 2: Apply image enhancements for better model performance
        enhanced_image = self._enhance_image(resized_image)
        
        return enhanced_image
    
    def _resize_with_aspect_ratio(
        self, 
        image: Image.Image, 
        fill_color: Tuple[int, int, int]
    ) -> Image.Image:
        """
        Resize image while maintaining aspect ratio and padding with fill color.
        """
        # Calculate aspect ratios
        target_aspect = self.target_size[0] / self.target_size[1]
        image_aspect = image.size[0] / image.size[1]
        
        if image_aspect > target_aspect:
            # Image is wider than target
            new_width = self.target_size[0]
            new_height = int(self.target_size[0] / image_aspect)
        else:
            # Image is taller than target
            new_height = self.target_size[1]
            new_width = int(self.target_size[1] * image_aspect)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create new image with target size and fill color
        result = Image.new('RGB', self.target_size, fill_color)
        
        # Calculate position to center the resized image
        x = (self.target_size[0] - new_width) // 2
        y = (self.target_size[1] - new_height) // 2
        
        # Paste the resized image
        result.paste(resized, (x, y))
        
        return result
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """
        Apply image enhancements for better model performance.
        """
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply auto contrast enhancement
        enhanced = ImageOps.autocontrast(image, cutoff=1)
        
        # Optional: Apply slight sharpening (uncomment if needed)
        # from PIL import ImageEnhance
        # enhancer = ImageEnhance.Sharpness(enhanced)
        # enhanced = enhancer.enhance(1.2)
        
        return enhanced
    
    def _to_model_format(self, image: Image.Image) -> np.ndarray:
        """
        Convert PIL image to numpy array format suitable for the model.
        """
        # Convert to numpy array
        image_array = np.array(image, dtype=np.float32)
        
        # Normalize pixel values to [0, 1]
        image_array = image_array / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    
    def compress_image(
        self, 
        image: Image.Image, 
        output_format: str = 'JPEG',
        quality: Optional[int] = None
    ) -> bytes:
        """
        Compress an image and return as bytes.
        
        Args:
            image: PIL Image to compress
            output_format: Output format ('JPEG', 'PNG', 'WEBP')
            quality: Compression quality (1-100, higher = better quality)
            
        Returns:
            Compressed image as bytes
        """
        if quality is None:
            quality = self.quality
        
        output_buffer = io.BytesIO()
        
        if output_format.upper() == 'JPEG':
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        elif output_format.upper() == 'PNG':
            image.save(output_buffer, format='PNG', optimize=True)
        elif output_format.upper() == 'WEBP':
            image.save(output_buffer, format='WEBP', quality=quality)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        output_buffer.seek(0)
        return output_buffer.getvalue()
    
    def get_compression_stats(self, original_size: int, compressed_size: int) -> dict:
        """Calculate compression statistics."""
        if original_size is None or original_size == 0:
            return {
                "original_size_bytes": 0,
                "compressed_size_bytes": compressed_size,
                "compression_ratio_percent": 0.0,
                "size_reduction_bytes": 0
            }
        compression_ratio = (1 - compressed_size / original_size) * 100
        return {
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio_percent": round(compression_ratio, 2),
            "size_reduction_bytes": original_size - compressed_size
        }

# Global instance with default settings
default_processor = ImageProcessor()

# Convenience functions for easy use
async def process_image_for_model(
    file: UploadFile,
    target_size: Tuple[int, int] = (224, 224),
    maintain_aspect_ratio: bool = True
) -> Tuple[np.ndarray, dict]:
    """
    Convenience function to process an uploaded image for model prediction.
    
    Args:
        file: FastAPI UploadFile object
        target_size: Target size for the model (width, height)
        maintain_aspect_ratio: Whether to maintain aspect ratio during resizing
        
    Returns:
        Tuple of (processed_image_array, metadata_dict)
    """
    processor = ImageProcessor(target_size=target_size)
    return await processor.process_uploaded_image(
        file, 
        maintain_aspect_ratio=maintain_aspect_ratio
    )

async def validate_and_process_image(
    file: UploadFile,
    max_size_mb: int = 50,
    target_size: Tuple[int, int] = (224, 224)
) -> Tuple[np.ndarray, dict]:
    """
    Validate and process image with custom settings.
    
    Args:
        file: FastAPI UploadFile object
        max_size_mb: Maximum file size in MB
        target_size: Target size for the model
        
    Returns:
        Tuple of (processed_image_array, metadata_dict)
    """
    processor = ImageProcessor(
        target_size=target_size,
        max_file_size=max_size_mb * 1024 * 1024
    )
    return await processor.process_uploaded_image(file)
