"""
PDF Generation Service using WeasyPrint
"""
import io
from typing import Optional
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class PdfService:
    """Service for generating PDFs using WeasyPrint"""
    
    def __init__(self):
        self.font_config = FontConfiguration()
    
    def check_weasyprint(self) -> bool:
        """Check if WeasyPrint is available and working"""
        try:
            # Try to create a simple HTML document
            HTML(string='<html><body>Test</body></html>')
            return True
        except Exception:
            return False
    
    def generate_pdf(
        self,
        html: str,
        page_size: str = 'A4',
        orientation: str = 'portrait',
        base_url: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF from HTML content
        
        Args:
            html: The HTML content to convert to PDF
            page_size: Paper size (A4, Letter, Legal, etc.)
            orientation: Page orientation (portrait or landscape)
            base_url: Base URL for resolving relative URLs in the HTML
            
        Returns:
            PDF content as bytes
        """
        # Create page CSS for size and orientation
        page_css = self._get_page_css(page_size, orientation)
        
        # Create HTML document
        html_doc = HTML(string=html, base_url=base_url)
        
        # Create CSS stylesheet
        stylesheets = []
        if page_css:
            stylesheets.append(CSS(string=page_css, font_config=self.font_config))
        
        # Generate PDF to bytes
        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(
            pdf_buffer,
            stylesheets=stylesheets,
            font_config=self.font_config
        )
        
        pdf_buffer.seek(0)
        return pdf_buffer.read()
    
    def _get_page_css(self, page_size: str, orientation: str) -> str:
        """Generate CSS for page size and orientation"""
        # Map common page sizes
        size_map = {
            'A4': 'A4',
            'A3': 'A3',
            'A5': 'A5',
            'letter': 'letter',
            'legal': 'legal',
            'tabloid': 'ledger'
        }
        
        size = size_map.get(page_size.upper(), page_size)
        orient = 'landscape' if orientation.lower() == 'landscape' else 'portrait'
        
        return f"""
            @page {{
                size: {size} {orient};
                margin: 1cm;
            }}
        """
    
    def generate_pdf_with_options(
        self,
        html: str,
        options: dict
    ) -> bytes:
        """
        Generate PDF with comprehensive options
        
        Args:
            html: The HTML content
            options: Dict containing:
                - page_size: Paper size
                - orientation: Page orientation
                - margin: Margin settings (can be dict with top, right, bottom, left)
                - base_url: Base URL for resources
                
        Returns:
            PDF content as bytes
        """
        page_size = options.get('page_size', 'A4')
        orientation = options.get('orientation', 'portrait')
        margin = options.get('margin', '1cm')
        base_url = options.get('base_url')
        
        # Build margin CSS
        if isinstance(margin, dict):
            margin_css = f"""
                margin-top: {margin.get('top', '1cm')};
                margin-right: {margin.get('right', '1cm')};
                margin-bottom: {margin.get('bottom', '1cm')};
                margin-left: {margin.get('left', '1cm')};
            """
        else:
            margin_css = f"margin: {margin};"
        
        # Size mapping
        size_map = {
            'A4': 'A4',
            'A3': 'A3',
            'A5': 'A5',
            'LETTER': 'letter',
            'LEGAL': 'legal',
        }
        size = size_map.get(page_size.upper(), page_size)
        orient = 'landscape' if orientation.lower() == 'landscape' else 'portrait'
        
        page_css = f"""
            @page {{
                size: {size} {orient};
                {margin_css}
            }}
        """
        
        # Create HTML document
        html_doc = HTML(string=html, base_url=base_url)
        
        # Create CSS stylesheet
        stylesheets = [CSS(string=page_css, font_config=self.font_config)]
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(
            pdf_buffer,
            stylesheets=stylesheets,
            font_config=self.font_config
        )
        
        pdf_buffer.seek(0)
        return pdf_buffer.read()
