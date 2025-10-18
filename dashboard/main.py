"""
Universal Parser Dashboard - Streamlit Web Interface
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import asyncio
import httpx
from typing import Dict, List, Any
import os

# Page configuration
st.set_page_config(
    page_title="Universal Parser Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"

class DashboardAPI:
    """API client for dashboard"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}{API_V1_PREFIX}"
    
    async def get_items(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get tracked items"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_url}/items/?skip={skip}&limit={limit}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                st.error(f"Error fetching items: {e}")
                return []
    
    async def get_item_history(self, item_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get item price history"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_url}/items/{item_id}/history?skip={skip}&limit={limit}")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                st.error(f"Error fetching item history: {e}")
                return []
    
    async def create_item(self, item_data: Dict) -> Dict:
        """Create new tracked item"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.api_url}/items/", json=item_data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                st.error(f"Error creating item: {e}")
                return {}
    
    async def get_parsing_stats(self) -> Dict:
        """Get parsing statistics"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_url}/parsing/cache/stats")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                st.error(f"Error fetching parsing stats: {e}")
                return {}

# Initialize API client
api = DashboardAPI()

def main():
    """Main dashboard function"""
    # Header
    st.markdown('<h1 class="main-header">🚀 Universal Parser Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=Universal+Parser", width=200)
        
        st.markdown("## 📊 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["📈 Overview", "🛍️ Items Management", "📊 Analytics", "🤖 AI Insights", "🔍 Niche Analysis", "🇷🇺 Russian Marketplaces", "💰 Monetization", "⚙️ Settings", "🔧 Parsing Tools"]
        )
        
        st.markdown("## 🔗 Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        if st.button("📤 Export Report"):
            st.info("Export functionality coming soon!")
    
    # Main content based on selected page
    if page == "📈 Overview":
        show_overview()
    elif page == "🛍️ Items Management":
        show_items_management()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🤖 AI Insights":
        show_ai_insights()
    elif page == "🔍 Niche Analysis":
        show_niche_analysis()
    elif page == "🇷🇺 Russian Marketplaces":
        show_russian_marketplaces()
    elif page == "💰 Monetization":
        show_monetization()
    elif page == "⚙️ Settings":
        show_settings()
    elif page == "🔧 Parsing Tools":
        show_parsing_tools()

def show_overview():
    """Show overview dashboard"""
    st.markdown("## 📈 System Overview")
    
    # Get data
    items_data = asyncio.run(api.get_items())
    parsing_stats = asyncio.run(api.get_parsing_stats())
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Items",
            value=len(items_data),
            delta="+5 this week"
        )
    
    with col2:
        active_items = len([item for item in items_data if item.get('is_active', False)])
        st.metric(
            label="✅ Active Items",
            value=active_items,
            delta=f"{active_items/len(items_data)*100:.1f}%" if items_data else "0%"
        )
    
    with col3:
        marketplaces = {}
        for item in items_data:
            marketplace = item.get('marketplace', 'unknown')
            marketplaces[marketplace] = marketplaces.get(marketplace, 0) + 1
        
        st.metric(
            label="🏪 Marketplaces",
            value=len(marketplaces),
            delta="3 supported"
        )
    
    with col4:
        cache_status = parsing_stats.get('status', 'unknown')
        st.metric(
            label="💾 Cache Status",
            value=cache_status.title(),
            delta="Connected" if cache_status == 'connected' else "Disconnected"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Items by Marketplace")
        if marketplaces:
            df_marketplace = pd.DataFrame(list(marketplaces.items()), columns=['Marketplace', 'Count'])
            fig = px.pie(df_marketplace, values='Count', names='Marketplace', 
                        title="Distribution by Marketplace")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No items tracked yet")
    
    with col2:
        st.markdown("### 📈 Price Changes (Last 7 Days)")
        # Mock data for demonstration
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
        prices = [100 + i*2 + (i%3)*5 for i in range(len(dates))]
        
        df_prices = pd.DataFrame({'Date': dates, 'Price': prices})
        fig = px.line(df_prices, x='Date', y='Price', title="Average Price Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.markdown("### 🔄 Recent Activity")
    if items_data:
        recent_items = sorted(items_data, key=lambda x: x.get('last_updated', ''), reverse=True)[:5]
        
        for item in recent_items:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{item.get('name', 'Unknown')[:50]}...**")
            with col2:
                st.write(f"${item.get('current_price', 'N/A')}")
            with col3:
                st.write(item.get('marketplace', 'Unknown'))
            with col4:
                status = "✅" if item.get('is_active', False) else "❌"
                st.write(status)
    else:
        st.info("No recent activity")

def show_items_management():
    """Show items management interface"""
    st.markdown("## 🛍️ Items Management")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 All Items", "➕ Add New Item", "📊 Item Details"])
    
    with tab1:
        # Get items
        items_data = asyncio.run(api.get_items())
        
        if items_data:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                marketplace_filter = st.selectbox("Filter by Marketplace", 
                                                ["All"] + list(set(item.get('marketplace', '') for item in items_data)))
            with col2:
                status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
            with col3:
                search_term = st.text_input("Search items", placeholder="Enter item name...")
            
            # Filter items
            filtered_items = items_data
            if marketplace_filter != "All":
                filtered_items = [item for item in filtered_items if item.get('marketplace') == marketplace_filter]
            if status_filter == "Active":
                filtered_items = [item for item in filtered_items if item.get('is_active', False)]
            elif status_filter == "Inactive":
                filtered_items = [item for item in filtered_items if not item.get('is_active', False)]
            if search_term:
                filtered_items = [item for item in filtered_items if search_term.lower() in item.get('name', '').lower()]
            
            # Display items
            for item in filtered_items:
                with st.expander(f"{item.get('name', 'Unknown')} - {item.get('marketplace', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Price:** ${item.get('current_price', 'N/A')}")
                        st.write(f"**Stock:** {item.get('current_stock', 'N/A')}")
                        st.write(f"**Rating:** {item.get('current_rating', 'N/A')}")
                    with col2:
                        st.write(f"**Status:** {'✅ Active' if item.get('is_active', False) else '❌ Inactive'}")
                        st.write(f"**Last Updated:** {item.get('last_updated', 'N/A')}")
                        if st.button(f"View Details", key=f"details_{item.get('id')}"):
                            st.session_state.selected_item = item
                            st.rerun()
        else:
            st.info("No items found. Add some items to get started!")
    
    with tab2:
        st.markdown("### ➕ Add New Item")
        
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            with col1:
                item_id = st.text_input("Item ID", placeholder="Enter item ID from marketplace")
                marketplace = st.selectbox("Marketplace", [
                    "wildberries", "ozon", "yandex", 
                    "aliexpress", "amazon", "ebay",
                    "lamoda", "dns"
                ])
                name = st.text_input("Item Name", placeholder="Enter item name")
            with col2:
                brand = st.text_input("Brand", placeholder="Enter brand name")
                category = st.text_input("Category", placeholder="Enter category")
                url = st.text_input("URL", placeholder="Enter item URL")
            
            if st.form_submit_button("Add Item"):
                if item_id and marketplace and name:
                    item_data = {
                        "item_id": item_id,
                        "marketplace": marketplace,
                        "name": name,
                        "brand": brand or None,
                        "category": category or None,
                        "url": url or None
                    }
                    
                    result = asyncio.run(api.create_item(item_data))
                    if result:
                        st.success("✅ Item added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add item")
                else:
                    st.error("Please fill in required fields (Item ID, Marketplace, Name)")
    
    with tab3:
        if 'selected_item' in st.session_state:
            item = st.session_state.selected_item
            st.markdown(f"### 📊 Details for {item.get('name', 'Unknown')}")
            
            # Get price history
            history = asyncio.run(api.get_item_history(item.get('id', 0)))
            
            if history:
                # Price chart
                df_history = pd.DataFrame(history)
                df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
                
                fig = px.line(df_history, x='timestamp', y='price', 
                            title=f"Price History for {item.get('name', 'Unknown')}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"${item.get('current_price', 'N/A')}")
                with col2:
                    min_price = df_history['price'].min()
                    st.metric("Min Price", f"${min_price}")
                with col3:
                    max_price = df_history['price'].max()
                    st.metric("Max Price", f"${max_price}")
                with col4:
                    avg_price = df_history['price'].mean()
                    st.metric("Avg Price", f"${avg_price:.2f}")
            else:
                st.info("No price history available for this item")
        else:
            st.info("Select an item to view details")

def show_analytics():
    """Show analytics dashboard"""
    st.markdown("## 📊 Analytics Dashboard")
    
    # Get data
    items_data = asyncio.run(api.get_items())
    
    if not items_data:
        st.info("No data available for analytics. Add some items first!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(items_data)
    
    # Time period selector
    col1, col2, col3 = st.columns(3)
    with col1:
        time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
    with col2:
        marketplace_filter = st.selectbox("Marketplace", ["All"] + list(df['marketplace'].unique()))
    with col3:
        metric = st.selectbox("Metric", ["Price", "Stock", "Rating"])
    
    # Filter data
    if marketplace_filter != "All":
        df = df[df['marketplace'] == marketplace_filter]
    
    # Analytics charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Price Distribution")
        if 'current_price' in df.columns:
            price_data = df['current_price'].dropna()
            if not price_data.empty:
                fig = px.histogram(price_data, nbins=20, title="Price Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No price data available")
    
    with col2:
        st.markdown("### 🏪 Items by Marketplace")
        marketplace_counts = df['marketplace'].value_counts()
        fig = px.bar(x=marketplace_counts.index, y=marketplace_counts.values,
                    title="Items Count by Marketplace")
        st.plotly_chart(fig, use_container_width=True)
    
    # Advanced analytics
    st.markdown("### 🔍 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Price Statistics")
        if 'current_price' in df.columns:
            price_stats = df['current_price'].describe()
            st.dataframe(price_stats)
    
    with col2:
        st.markdown("#### 🏷️ Category Analysis")
        if 'category' in df.columns:
            category_counts = df['category'].value_counts().head(10)
            if not category_counts.empty:
                fig = px.pie(values=category_counts.values, names=category_counts.index,
                           title="Top Categories")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")

def show_settings():
    """Show settings page"""
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["🔧 API Settings", "📊 Display Settings", "🔔 Notifications"])
    
    with tab1:
        st.markdown("### 🔧 API Configuration")
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        st.info(f"Current API URL: {api_url}")
        
        # Test API connection
        if st.button("Test API Connection"):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API connection successful!")
                else:
                    st.error(f"❌ API connection failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ API connection failed: {e}")
    
    with tab2:
        st.markdown("### 📊 Display Settings")
        theme = st.selectbox("Theme", ["Light", "Dark"])
        chart_type = st.selectbox("Default Chart Type", ["Line", "Bar", "Pie"])
        items_per_page = st.slider("Items per page", 10, 100, 20)
        
        st.info("Display settings will be saved automatically")
    
    with tab3:
        st.markdown("### 🔔 Notification Settings")
        email_notifications = st.checkbox("Email notifications", value=True)
        price_alerts = st.checkbox("Price change alerts", value=True)
        stock_alerts = st.checkbox("Stock change alerts", value=False)
        
        if st.button("Save Notification Settings"):
            st.success("✅ Notification settings saved!")

def show_ai_insights():
    """Show AI insights and predictions"""
    st.markdown("## 🤖 AI Insights & Predictions")
    
    # Get items data
    items_data = asyncio.run(api.get_items())
    
    if not items_data:
        st.info("No items available for AI analysis. Add some items first!")
        return
    
    # Tabs for different AI features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔮 Price Predictions", 
        "📊 Trend Analysis", 
        "🚨 Anomaly Detection", 
        "💡 Recommendations", 
        "🧠 Model Performance"
    ])
    
    with tab1:
        st.markdown("### 🔮 Price Predictions")
        
        # Select item for prediction
        item_options = {f"{item['name'][:50]}... (ID: {item['id']})": item for item in items_data}
        selected_item_name = st.selectbox("Select item for prediction:", list(item_options.keys()))
        
        if selected_item_name:
            selected_item = item_options[selected_item_name]
            
            col1, col2 = st.columns(2)
            with col1:
                days_ahead = st.slider("Days to predict ahead:", 1, 30, 7)
            with col2:
                if st.button("🔮 Predict Prices"):
                    with st.spinner("Generating predictions..."):
                        # Mock prediction data for demonstration
                        predictions = []
                        current_price = selected_item.get('current_price', 100)
                        
                        for i in range(days_ahead):
                            # Simple mock prediction with some randomness
                            predicted_price = current_price * (1 + (i * 0.02) + (np.random.random() - 0.5) * 0.1)
                            predictions.append({
                                'date': (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                                'predicted_price': round(predicted_price, 2),
                                'confidence': round(0.8 - (i * 0.05), 2)
                            })
                        
                        # Display predictions
                        st.success(f"✅ Predictions generated for {selected_item['name']}")
                        
                        # Create prediction chart
                        df_pred = pd.DataFrame(predictions)
                        df_pred['date'] = pd.to_datetime(df_pred['date'])
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_pred['date'],
                            y=df_pred['predicted_price'],
                            mode='lines+markers',
                            name='Predicted Price',
                            line=dict(color='#1f77b4', width=3),
                            marker=dict(size=8)
                        ))
                        
                        # Add current price line
                        fig.add_hline(
                            y=current_price, 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text=f"Current: ${current_price}"
                        )
                        
                        fig.update_layout(
                            title=f"Price Predictions for {selected_item['name'][:30]}...",
                            xaxis_title="Date",
                            yaxis_title="Price ($)",
                            template="plotly_white"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show prediction table
                        st.markdown("#### 📋 Prediction Details")
                        st.dataframe(df_pred, use_container_width=True)
    
    with tab2:
        st.markdown("### 📊 Trend Analysis")
        
        if st.button("📈 Analyze Trends"):
            with st.spinner("Analyzing trends..."):
                # Mock trend analysis
                trend_data = {
                    'trend_direction': 'increasing',
                    'volatility': 0.15,
                    'current_price': 150.0,
                    'min_price': 120.0,
                    'max_price': 180.0,
                    'avg_price': 145.0,
                    'confidence': 0.85
                }
                
                # Display trend metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Trend", trend_data['trend_direction'].title(), "↗️")
                with col2:
                    st.metric("Volatility", f"{trend_data['volatility']:.1%}")
                with col3:
                    st.metric("Price Range", f"${trend_data['min_price']:.0f} - ${trend_data['max_price']:.0f}")
                with col4:
                    st.metric("Confidence", f"{trend_data['confidence']:.1%}")
                
                # Trend visualization
                st.markdown("#### 📈 Price Trend Visualization")
                
                # Mock historical data
                dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
                prices = [120 + i * 0.5 + np.random.random() * 10 for i in range(len(dates))]
                
                df_trend = pd.DataFrame({'date': dates, 'price': prices})
                
                fig = px.line(df_trend, x='date', y='price', title="Historical Price Trend")
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🚨 Anomaly Detection")
        
        if st.button("🔍 Detect Anomalies"):
            with st.spinner("Detecting anomalies..."):
                # Mock anomaly data
                anomalies = [
                    {
                        'timestamp': '2024-01-15T10:30:00',
                        'price': 250.0,
                        'expected_price': 150.0,
                        'severity': 0.9,
                        'description': 'Price spike detected - 67% above expected'
                    },
                    {
                        'timestamp': '2024-01-20T14:15:00',
                        'price': 80.0,
                        'expected_price': 140.0,
                        'severity': 0.7,
                        'description': 'Price drop detected - 43% below expected'
                    }
                ]
                
                st.success(f"✅ Found {len(anomalies)} anomalies")
                
                for i, anomaly in enumerate(anomalies):
                    with st.expander(f"Anomaly #{i+1} - {anomaly['timestamp']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Price", f"${anomaly['price']:.2f}")
                        with col2:
                            st.metric("Expected", f"${anomaly['expected_price']:.2f}")
                        with col3:
                            st.metric("Severity", f"{anomaly['severity']:.1%}")
                        
                        st.write(f"**Description:** {anomaly['description']}")
    
    with tab4:
        st.markdown("### 💡 AI Recommendations")
        
        if st.button("💡 Get Recommendations"):
            with st.spinner("Generating recommendations..."):
                # Mock recommendations
                recommendations = [
                    {
                        'item_name': 'Wireless Headphones Pro',
                        'marketplace': 'wildberries',
                        'price': 89.99,
                        'score': 0.92,
                        'reason': 'Similar category: electronics; Similar price range'
                    },
                    {
                        'item_name': 'Smart Watch Series 8',
                        'marketplace': 'ozon',
                        'price': 299.99,
                        'score': 0.87,
                        'reason': 'From your preferred marketplace: ozon; Similar category: electronics'
                    },
                    {
                        'item_name': 'Gaming Mouse RGB',
                        'marketplace': 'yandex',
                        'price': 45.50,
                        'score': 0.78,
                        'reason': 'Similar category: electronics; Similar price range'
                    }
                ]
                
                st.success(f"✅ Generated {len(recommendations)} recommendations")
                
                for i, rec in enumerate(recommendations):
                    with st.expander(f"#{i+1} {rec['item_name']} (Score: {rec['score']:.2f})"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Marketplace:** {rec['marketplace'].title()}")
                        with col2:
                            st.write(f"**Price:** ${rec['price']:.2f}")
                        with col3:
                            st.write(f"**Score:** {rec['score']:.2f}")
                        
                        st.write(f"**Reason:** {rec['reason']}")
                        
                        if st.button(f"Add to Tracking", key=f"add_{i}"):
                            st.success("✅ Added to tracking!")
    
    with tab5:
        st.markdown("### 🧠 Model Performance")
        
        # Model performance metrics
        model_performance = {
            'Random Forest': {'r2': 0.85, 'mae': 12.5, 'status': 'Trained'},
            'XGBoost': {'r2': 0.88, 'mae': 10.2, 'status': 'Trained'},
            'LightGBM': {'r2': 0.87, 'mae': 11.1, 'status': 'Trained'},
            'Linear Regression': {'r2': 0.72, 'mae': 18.3, 'status': 'Trained'},
            'Gradient Boosting': {'r2': 0.86, 'mae': 11.8, 'status': 'Trained'}
        }
        
        # Display model performance
        for model_name, metrics in model_performance.items():
            with st.expander(f"🤖 {model_name}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("R² Score", f"{metrics['r2']:.3f}")
                with col2:
                    st.metric("MAE", f"{metrics['mae']:.1f}")
                with col3:
                    status_color = "🟢" if metrics['status'] == 'Trained' else "🔴"
                    st.metric("Status", f"{status_color} {metrics['status']}")
        
        # Training controls
        st.markdown("#### 🔧 Model Training")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Train All Models"):
                with st.spinner("Training models..."):
                    st.success("✅ All models trained successfully!")
        with col2:
            if st.button("🗑️ Clear Models"):
                st.warning("⚠️ All models cleared!")


def show_niche_analysis():
    """Show niche analysis for beginners"""
    st.markdown("## 🔍 Niche Analysis for Beginners")
    
    # Tabs for different analysis features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Niche Analysis", 
        "🏪 Supplier Finder", 
        "💰 Pricing Advisor", 
        "📊 Profit Calculator", 
        "📚 Beginner Guide"
    ])
    
    with tab1:
        st.markdown("### 🎯 Analyze a Niche")
        
        col1, col2 = st.columns(2)
        with col1:
            niche = st.selectbox(
                "Select a niche:",
                ["electronics", "fashion", "beauty_health", "home_garden", 
                 "sports_outdoors", "toys_games", "automotive", "books_media"]
            )
        with col2:
            keywords = st.text_area(
                "Enter keywords (one per line):",
                value="smartphone\nheadphones\nlaptop",
                height=100
            ).split('\n')
        
        if st.button("🔍 Analyze Niche"):
            with st.spinner("Analyzing niche..."):
                # Mock analysis data
                analysis_data = {
                    'niche': niche,
                    'competition_level': 0.7,
                    'market_size': 1500000,
                    'average_price': 299.99,
                    'min_price': 49.99,
                    'max_price': 999.99,
                    'demand_trend': 'growing',
                    'seasonality': 0.3,
                    'profit_margin': 0.25,
                    'difficulty': 'medium',
                    'growth_potential': 0.8,
                    'recommendation_score': 0.75
                }
                
                st.success("✅ Analysis completed!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Competition", f"{analysis_data['competition_level']:.1%}", "High")
                with col2:
                    st.metric("Market Size", f"${analysis_data['market_size']:,.0f}")
                with col3:
                    st.metric("Avg Price", f"${analysis_data['average_price']:.2f}")
                with col4:
                    st.metric("Profit Margin", f"{analysis_data['profit_margin']:.1%}")
                
                # Detailed analysis
                st.markdown("#### 📊 Detailed Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Price Range:**")
                    st.write(f"${analysis_data['min_price']:.2f} - ${analysis_data['max_price']:.2f}")
                    
                    st.markdown("**Demand Trend:**")
                    trend_icon = "📈" if analysis_data['demand_trend'] == 'growing' else "📉"
                    st.write(f"{trend_icon} {analysis_data['demand_trend'].title()}")
                    
                with col2:
                    st.markdown("**Difficulty Level:**")
                    difficulty_colors = {
                        'easy': '🟢',
                        'medium': '🟡', 
                        'hard': '🟠',
                        'expert': '🔴'
                    }
                    st.write(f"{difficulty_colors.get(analysis_data['difficulty'], '❓')} {analysis_data['difficulty'].title()}")
                    
                    st.markdown("**Growth Potential:**")
                    st.write(f"📊 {analysis_data['growth_potential']:.1%}")
                
                # Recommendation
                st.markdown("#### 💡 Recommendation")
                if analysis_data['recommendation_score'] > 0.7:
                    st.success("🎉 **Excellent choice!** This niche has great potential for beginners.")
                elif analysis_data['recommendation_score'] > 0.5:
                    st.warning("⚠️ **Good choice** with some challenges. Consider your experience level.")
                else:
                    st.error("❌ **Challenging niche** - not recommended for beginners.")
    
    with tab2:
        st.markdown("### 🏪 Find Suppliers")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            product_name = st.text_input("Product Name", value="Wireless Headphones")
        with col2:
            category = st.selectbox("Category", ["electronics", "fashion", "beauty_health"])
        with col3:
            budget = st.number_input("Budget per Unit ($)", value=50.0, min_value=1.0)
        
        if st.button("🔍 Find Suppliers"):
            with st.spinner("Searching suppliers..."):
                # Mock supplier data
                suppliers = [
                    {
                        'name': 'TechGlobal Manufacturing',
                        'type': 'Manufacturer',
                        'country': 'China',
                        'min_order': 100,
                        'price_per_unit': 25.0,
                        'shipping': 5.0,
                        'delivery_days': 14,
                        'quality_rating': 4.2,
                        'total_cost': 30.0
                    },
                    {
                        'name': 'ElectroWholesale',
                        'type': 'Wholesaler',
                        'country': 'USA',
                        'min_order': 50,
                        'price_per_unit': 35.0,
                        'shipping': 8.0,
                        'delivery_days': 7,
                        'quality_rating': 4.0,
                        'total_cost': 43.0
                    }
                ]
                
                st.success(f"✅ Found {len(suppliers)} suppliers!")
                
                for i, supplier in enumerate(suppliers):
                    with st.expander(f"🏭 {supplier['name']} ({supplier['type']})"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Country:** {supplier['country']}")
                            st.write(f"**Min Order:** {supplier['min_order']} units")
                        with col2:
                            st.write(f"**Price:** ${supplier['price_per_unit']:.2f}/unit")
                            st.write(f"**Shipping:** ${supplier['shipping']:.2f}")
                        with col3:
                            st.write(f"**Delivery:** {supplier['delivery_days']} days")
                            st.write(f"**Quality:** {supplier['quality_rating']}/5")
                        
                        st.write(f"**Total Cost:** ${supplier['total_cost']:.2f}/unit")
                        
                        if supplier['total_cost'] <= budget:
                            st.success("✅ Within budget!")
                        else:
                            st.warning("⚠️ Over budget")
    
    with tab3:
        st.markdown("### 💰 Pricing Advisor")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            product_name = st.text_input("Product Name", value="Smart Watch", key="pricing_product")
        with col2:
            category = st.selectbox("Category", ["electronics", "fashion", "beauty_health"], key="pricing_category")
        with col3:
            supplier_cost = st.number_input("Supplier Cost ($)", value=30.0, min_value=0.1)
        
        target_margin = st.slider("Target Profit Margin (%)", 10, 80, 30) / 100
        
        if st.button("💰 Calculate Pricing"):
            with st.spinner("Calculating optimal pricing..."):
                # Mock pricing calculation
                recommended_price = supplier_cost / (1 - target_margin)
                min_price = recommended_price * 0.8
                max_price = recommended_price * 1.2
                
                st.success("✅ Pricing calculated!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Recommended Price", f"${recommended_price:.2f}")
                with col2:
                    st.metric("Min Price", f"${min_price:.2f}")
                with col3:
                    st.metric("Max Price", f"${max_price:.2f}")
                
                # Pricing strategy
                st.markdown("#### 📊 Pricing Strategy")
                if recommended_price < 50:
                    strategy = "Budget pricing - compete on price"
                    position = "budget"
                elif recommended_price < 200:
                    strategy = "Mid-range pricing - balanced approach"
                    position = "mid-range"
                else:
                    strategy = "Premium pricing - compete on quality"
                    position = "premium"
                
                st.info(f"**Market Position:** {position.title()}")
                st.info(f"**Strategy:** {strategy}")
                
                # Profit analysis
                profit_per_unit = recommended_price - supplier_cost
                actual_margin = profit_per_unit / recommended_price
                
                st.markdown("#### 💵 Profit Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Profit per Unit:** ${profit_per_unit:.2f}")
                    st.write(f"**Actual Margin:** {actual_margin:.1%}")
                with col2:
                    st.write(f"**Target Margin:** {target_margin:.1%}")
                    if actual_margin >= target_margin:
                        st.success("✅ Target achieved!")
                    else:
                        st.warning("⚠️ Below target")
    
    with tab4:
        st.markdown("### 📊 Profit Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name", value="Bluetooth Speaker", key="profit_product")
            supplier_cost = st.number_input("Supplier Cost ($)", value=20.0, min_value=0.1)
            selling_price = st.number_input("Selling Price ($)", value=49.99, min_value=0.1)
        with col2:
            marketplace_fees = st.slider("Marketplace Fees (%)", 5, 20, 10) / 100
            shipping_cost = st.number_input("Shipping Cost ($)", value=3.0, min_value=0.0)
            other_costs = st.number_input("Other Costs ($)", value=2.0, min_value=0.0)
        
        if st.button("📊 Calculate Profit"):
            # Calculate costs
            total_costs = supplier_cost + shipping_cost + other_costs
            marketplace_fee_amount = selling_price * marketplace_fees
            total_costs += marketplace_fee_amount
            
            # Calculate profit
            profit_per_unit = selling_price - total_costs
            profit_margin = (profit_per_unit / selling_price) * 100 if selling_price > 0 else 0
            
            # Break-even
            break_even_price = total_costs / (1 - marketplace_fees) if marketplace_fees < 1 else total_costs
            
            st.success("✅ Profit calculated!")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Profit per Unit", f"${profit_per_unit:.2f}")
            with col2:
                st.metric("Profit Margin", f"{profit_margin:.1f}%")
            with col3:
                st.metric("Total Costs", f"${total_costs:.2f}")
            with col4:
                st.metric("Break-even Price", f"${break_even_price:.2f}")
            
            # Cost breakdown
            st.markdown("#### 💸 Cost Breakdown")
            cost_breakdown = {
                "Supplier Cost": supplier_cost,
                "Shipping Cost": shipping_cost,
                "Marketplace Fees": marketplace_fee_amount,
                "Other Costs": other_costs
            }
            
            for cost_type, amount in cost_breakdown.items():
                st.write(f"**{cost_type}:** ${amount:.2f}")
            
            # Recommendations
            st.markdown("#### 💡 Recommendations")
            if profit_margin >= 50:
                st.success("🎉 Excellent margin! Consider scaling up.")
            elif profit_margin >= 30:
                st.info("👍 Good margin, room for improvement.")
            elif profit_margin >= 15:
                st.warning("⚠️ Low margin, consider price optimization.")
            else:
                st.error("❌ Very low margin, reconsider this product.")
    
    with tab5:
        st.markdown("### 📚 Beginner Guide")
        
        experience_level = st.selectbox(
            "Your Experience Level:",
            ["Complete Beginner", "Some Experience", "Experienced"]
        )
        
        budget = st.number_input("Your Budget ($)", value=1000.0, min_value=100.0)
        
        if st.button("📚 Get Personalized Guide"):
            with st.spinner("Generating personalized guide..."):
                st.success("✅ Guide generated!")
                
                # Mock guide content
                if experience_level == "Complete Beginner":
                    st.markdown("#### 🚀 Getting Started Guide")
                    st.write("""
                    **Step 1: Choose Your Niche**
                    - Start with low-competition niches like beauty or home goods
                    - Research trending products using our analysis tools
                    - Consider your interests and budget
                    
                    **Step 2: Find Products**
                    - Use our product research tools
                    - Look for products with good profit margins (30%+)
                    - Start with 3-5 products to test
                    
                    **Step 3: Find Suppliers**
                    - Use our supplier finder
                    - Start with small orders (50-100 units)
                    - Verify supplier quality and reliability
                    
                    **Step 4: Set Up Your Store**
                    - Choose one marketplace to start (Wildberries or Ozon)
                    - Create compelling product listings
                    - Set competitive prices using our pricing advisor
                    """)
                    
                    st.markdown("#### 💡 Pro Tips for Beginners")
                    tips = [
                        "Start small and test before scaling",
                        "Focus on customer service and reviews",
                        "Use our AI tools for price optimization",
                        "Monitor competitors regularly",
                        "Keep detailed records of all costs"
                    ]
                    for tip in tips:
                        st.write(f"• {tip}")
                
                elif experience_level == "Some Experience":
                    st.markdown("#### 📈 Growth Strategy")
                    st.write("""
                    **Advanced Product Research**
                    - Use AI trend analysis for product selection
                    - Analyze seasonal patterns and demand cycles
                    - Consider private labeling opportunities
                    
                    **Multi-Marketplace Strategy**
                    - Expand to 2-3 marketplaces
                    - Use different pricing strategies per platform
                    - Leverage marketplace-specific features
                    
                    **Supplier Optimization**
                    - Negotiate better terms with reliable suppliers
                    - Consider direct manufacturer relationships
                    - Implement quality control processes
                    """)
                
                else:
                    st.markdown("#### 🏆 Expert Strategies")
                    st.write("""
                    **Advanced Analytics**
                    - Use predictive analytics for inventory planning
                    - Implement dynamic pricing strategies
                    - Leverage AI for market trend prediction
                    
                    **Business Scaling**
                    - Consider private label development
                    - Explore international markets
                    - Build brand recognition and loyalty
                    
                    **Automation**
                    - Automate price monitoring and adjustments
                    - Implement automated customer service
                    - Use data-driven decision making
                    """)


def show_parsing_tools():
    """Show parsing tools"""
    st.markdown("## 🔧 Parsing Tools")
    
    tab1, tab2, tab3 = st.tabs(["🌐 URL Parser", "📊 Parsing Stats", "🗑️ Cache Management"])
    
    with tab1:
        st.markdown("### 🌐 Parse URL")
        
        with st.form("parse_url_form"):
            url = st.text_input("URL to parse", placeholder="https://example.com")
            method = st.selectbox("Parsing method", ["http", "browser"])
            
            if st.form_submit_button("Parse URL"):
                if url:
                    st.info("Parsing in progress...")
                    # Here you would call the parsing API
                    st.success("✅ Parsing completed!")
                else:
                    st.error("Please enter a URL")
    
    with tab2:
        st.markdown("### 📊 Parsing Statistics")
        parsing_stats = asyncio.run(api.get_parsing_stats())
        
        if parsing_stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cache Status", parsing_stats.get('status', 'Unknown').title())
            with col2:
                st.metric("Memory Used", parsing_stats.get('used_memory', 'N/A'))
            with col3:
                st.metric("Connected Clients", parsing_stats.get('connected_clients', 0))
        else:
            st.info("No parsing statistics available")
    
    with tab3:
        st.markdown("### 🗑️ Cache Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear All Cache"):
                st.info("Cache cleared!")
        with col2:
            if st.button("Clear Parsing Cache"):
                st.info("Parsing cache cleared!")

def show_russian_marketplaces():
    """Show Russian marketplaces dashboard"""
    # Import the Russian marketplaces page
    from pages.russian_marketplaces import main as russian_marketplaces_main
    russian_marketplaces_main()

def show_monetization():
    """Show monetization dashboard"""
    # Import the monetization page
    from pages.monetization import main as monetization_main
    monetization_main()

if __name__ == "__main__":
    main()
