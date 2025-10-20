"""
Dashboard configuration
"""
import os
from typing import Dict, Any

class DashboardConfig:
    """Configuration for the Streamlit dashboard"""
    
    def __init__(self):
        # API Configuration
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.api_v1_prefix = "/api/v1"
        
        # Dashboard Settings
        self.page_title = "Universal Parser Dashboard"
        self.page_icon = "🚀"
        self.layout = "wide"
        
        # Chart Settings
        self.default_chart_theme = "plotly_white"
        self.chart_colors = [
            "#1f77b4",  # Blue
            "#ff7f0e",  # Orange
            "#2ca02c",  # Green
            "#d62728",  # Red
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#7f7f7f",  # Gray
        ]
        
        # Data Settings
        self.default_items_per_page = 20
        self.max_items_per_page = 100
        self.cache_ttl = 300  # 5 minutes
        
        # Marketplaces
        self.supported_marketplaces = [
            "wildberries",
            "ozon", 
            "yandex",
            "aliexpress",
            "amazon",
            "ebay"
        ]
        
        # Chart Types
        self.chart_types = {
            "line": "Line Chart",
            "bar": "Bar Chart",
            "pie": "Pie Chart",
            "scatter": "Scatter Plot",
            "histogram": "Histogram"
        }
        
        # Time Periods
        self.time_periods = [
            "Last 7 days",
            "Last 30 days", 
            "Last 90 days",
            "Last 6 months",
            "Last year",
            "All time"
        ]
    
    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for endpoint"""
        return f"{self.api_base_url}{self.api_v1_prefix}{endpoint}"
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration"""
        return {
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "universal_parser_chart",
                "height": 500,
                "width": 700,
                "scale": 2
            }
        }

# Global config instance
config = DashboardConfig()


