# coding: utf-8
"""
Background Manager - Handles application background image, blur effects and opacity settings
"""

import os
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class BackgroundManager(QObject):
    """Background manager - Unified management of background related settings and styles"""
    
    # Signal emitted when background settings change
    backgroundChanged = pyqtSignal()
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._background_style_cache = {}
        self._blurred_pixmap_cache = {}  # Cache for blurred images
        self._current_blur_key = None    # Current blur image cache key
        
    def validate_image_path(self, image_path: str) -> bool:
        """Validate if the image path is valid
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if the path is valid and points to a supported image format
        """
        if not image_path:
            return False
            
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            return False
            
        # Check if it's a supported image format
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        return path.suffix.lower() in supported_formats
    
    def get_background_style(self, theme_mode="light") -> str:
        """Generate background stylesheet (background image implemented via paintEvent)
        
        Args:
            theme_mode: Theme mode ("light" or "dark")
            
        Returns:
            str: Empty string (style implemented via paintEvent)
        """
        # Background image is now implemented via paintEvent, no CSS styles needed
        return ""
    
    def _get_background_hash(self) -> str:
        """Get hash value of current background settings for caching"""
        if not self.config_manager:
            return "default"
            
        bg_enabled = self.config_manager.get(self.config_manager.backgroundImageEnabled)
        bg_path = self.config_manager.get(self.config_manager.backgroundImagePath)
        bg_opacity = self.config_manager.get(self.config_manager.backgroundOpacity)
        bg_display_mode = self.config_manager.get(self.config_manager.backgroundDisplayMode)
        
        return f"{bg_enabled}_{bg_path}_{bg_opacity}_{bg_display_mode}"
    
    def clear_cache(self):
        """Clear background style cache and blurred image cache"""
        self._background_style_cache.clear()
        self._blurred_pixmap_cache.clear()
        self._current_blur_key = None
        logger.debug("Background style cache and blurred image cache cleared")
    
    def get_background_image_path(self) -> str:
        """Get current background image path
        
        Returns:
            str: Path to the background image
        """
        if not self.config_manager:
            return ""
        return self.config_manager.get(self.config_manager.backgroundImagePath)
        
    def is_background_enabled(self) -> bool:
        """Check if background image is enabled
        
        Returns:
            bool: True if background is enabled
        """
        if not self.config_manager:
            return False
        return self.config_manager.get(self.config_manager.backgroundImageEnabled)
        
    def get_background_opacity(self) -> float:
        """Get background opacity
        
        Returns:
            float: Opacity value between 0.0 and 1.0
        """
        if not self.config_manager:
            return 80
        return self.config_manager.get(self.config_manager.backgroundOpacity)
        
    def get_background_blur_radius(self) -> int:
        """Get background blur radius
        
        Returns:
            int: Blur radius in pixels
        """
        if not self.config_manager:
            return 0
        return self.config_manager.get(self.config_manager.backgroundBlurRadius)
        
    def get_background_display_mode(self) -> str:
        """Get background display mode
        
        Returns:
            str: Display mode ("Stretch", "Keep Aspect Ratio", "Tile", "Original Size", "Fit Window")
        """
        if not self.config_manager:
            return "Keep Aspect Ratio"
        return self.config_manager.get(self.config_manager.backgroundDisplayMode)
        
    def get_background_pixmap(self, window_size: QSize) -> QPixmap:
        """Get processed background image (with cached blur effects)
        
        Args:
            window_size: Size of the window to fit the background
            
        Returns:
            QPixmap: Processed background pixmap or None if not available
        """
        try:
            if not self.is_background_enabled():
                return None
                
            bg_path = self.get_background_image_path()
            if not bg_path or not self.validate_image_path(bg_path):
                return None
                
            blur_radius = self.get_background_blur_radius()
            display_mode = self.get_background_display_mode()
            
            # Generate cache key
            cache_key = f"{bg_path}_{window_size.width()}_{window_size.height()}_{blur_radius}_{display_mode}"
            
            # Check cache
            if cache_key in self._blurred_pixmap_cache:
                return self._blurred_pixmap_cache[cache_key]
                
            # Load original image
            pixmap = QPixmap(bg_path)
            if pixmap.isNull():
                return None
                
            # Scale image based on display mode
            scaled_pixmap = self._process_pixmap_by_display_mode(pixmap, window_size, display_mode)
            
            # Apply blur effect if needed
            if blur_radius > 0:
                scaled_pixmap = self._apply_efficient_blur(scaled_pixmap, blur_radius)
            
            # Cache processed image
            self._blurred_pixmap_cache[cache_key] = scaled_pixmap
            self._current_blur_key = cache_key
            
            # Clean old cache (keep recent 5 entries)
            if len(self._blurred_pixmap_cache) > 5:
                oldest_key = next(iter(self._blurred_pixmap_cache))
                del self._blurred_pixmap_cache[oldest_key]
                
            return scaled_pixmap
            
        except Exception as e:
            logger.error(f"Failed to get background pixmap: {str(e)}")
            return None
            
    def _process_pixmap_by_display_mode(self, pixmap: QPixmap, window_size: QSize, display_mode: str) -> QPixmap:
        """Process pixmap according to display mode
        
        Args:
            pixmap: Original pixmap
            window_size: Target window size
            display_mode: Display mode string
            
        Returns:
            QPixmap: Processed pixmap
        """
        try:
            if display_mode == "Stretch":
                # Stretch to fill window, may distort image
                return pixmap.scaled(window_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                
            elif display_mode == "Keep Aspect Ratio":
                # Keep aspect ratio, expand to fill (current default behavior)
                return pixmap.scaled(window_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
            elif display_mode == "Fit Window":
                # Keep aspect ratio, fit within window
                return pixmap.scaled(window_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
            elif display_mode == "Original Size":
                # Keep original size, no scaling
                return pixmap
                
            elif display_mode == "Tile":
                # For tile mode, we need to create a pixmap that covers the window
                # This will be handled specially in the paint event
                return pixmap
                
            else:
                # Default fallback
                return pixmap.scaled(window_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
        except Exception as e:
            logger.error(f"Failed to process pixmap by display mode {display_mode}: {str(e)}")
            return pixmap
            
    def _apply_efficient_blur(self, pixmap: QPixmap, blur_radius: int) -> QPixmap:
        """Apply efficient blur effect (simplified Gaussian blur)
        
        Args:
            pixmap: Source pixmap to blur
            blur_radius: Blur radius in pixels
            
        Returns:
            QPixmap: Blurred pixmap
        """
        try:
            # For performance, use simplified blur algorithm
            # For large blur radius, scale down first then scale up to improve performance
            original_size = pixmap.size()
            
            if blur_radius > 20:
                # For high blur radius, scale down to 1/4 for processing
                small_size = QSize(int(original_size.width() * 0.25), int(original_size.height() * 0.25))
                temp_pixmap = pixmap.scaled(small_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                blurred = self._simple_blur(temp_pixmap, blur_radius // 4)
                return blurred.scaled(original_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                return self._simple_blur(pixmap, blur_radius)
                
        except Exception as e:
            logger.error(f"Failed to apply blur effect: {str(e)}")
            return pixmap
            
    def _simple_blur(self, pixmap: QPixmap, radius: int) -> QPixmap:
        """Simple blur implementation without position offset (avoiding QGraphicsBlurEffect for performance)
        
        Args:
            pixmap: Source pixmap
            radius: Blur radius
            
        Returns:
            QPixmap: Blurred pixmap
        """
        try:
            if radius <= 0:
                return pixmap
                
            # Use scale-down and scale-up method for blur effect without position offset
            original_size = pixmap.size()
            
            # Calculate blur factor based on radius (more radius = more blur)
            blur_factor = max(0.1, 1.0 - (radius / 100.0))  # blur_factor decreases as radius increases
            
            # Scale down for blur effect
            blurred_size = QSize(
                max(1, int(original_size.width() * blur_factor)),
                max(1, int(original_size.height() * blur_factor))
            )
            
            # Scale down with smooth transformation
            small_pixmap = pixmap.scaled(
                blurred_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Scale back up to original size for blur effect
            blurred_pixmap = small_pixmap.scaled(
                original_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Optional: Apply additional opacity overlay for stronger blur effect
            if radius > 25:
                result = QPixmap(original_size)
                result.fill(Qt.transparent)
                
                painter = QPainter(result)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Draw the blurred image as base
                painter.setOpacity(0.8)
                painter.drawPixmap(0, 0, blurred_pixmap)
                
                # Overlay with additional transparency for stronger blur
                painter.setOpacity(0.3)
                painter.drawPixmap(0, 0, blurred_pixmap)
                
                painter.end()
                return result
            
            return blurred_pixmap
            
        except Exception as e:
            logger.error(f"Simple blur processing failed: {str(e)}")
            return pixmap
    
    def update_background(self):
        """Update background settings, clear cache and emit signal"""
        self.clear_cache()
        self.backgroundChanged.emit()
        logger.info("Background settings updated")


# Global background manager instance
_background_manager = None

def get_background_manager(config_manager=None):
    """Get global background manager instance
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        BackgroundManager: Global background manager instance
    """
    global _background_manager
    if _background_manager is None:
        _background_manager = BackgroundManager(config_manager)
    elif config_manager and not _background_manager.config_manager:
        _background_manager.config_manager = config_manager
    return _background_manager 