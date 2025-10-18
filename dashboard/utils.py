"""
Utility functions for the dashboard
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import streamlit as st

def create_price_chart(data: List[Dict], title: str = "Price History") -> go.Figure:
    """Create price history chart"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines+markers',
        name='Price',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Add old price if available
    if 'old_price' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['old_price'],
            mode='lines',
            name='Previous Price',
            line=dict(color='#ff7f0e', width=1, dash='dash'),
            opacity=0.7
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode='x unified',
        template="plotly_white"
    )
    
    return fig

def create_marketplace_distribution(data: List[Dict]) -> go.Figure:
    """Create marketplace distribution chart"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    marketplace_counts = df['marketplace'].value_counts()
    
    fig = px.pie(
        values=marketplace_counts.values,
        names=marketplace_counts.index,
        title="Items by Marketplace",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_price_distribution(data: List[Dict]) -> go.Figure:
    """Create price distribution histogram"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    price_data = df['current_price'].dropna()
    
    if price_data.empty:
        return go.Figure()
    
    fig = px.histogram(
        price_data,
        nbins=20,
        title="Price Distribution",
        labels={'value': 'Price', 'count': 'Number of Items'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        template="plotly_white",
        showlegend=False
    )
    
    return fig

def create_trend_chart(data: List[Dict], metric: str = "price") -> go.Figure:
    """Create trend chart for specified metric"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Group by date and calculate average
    df_daily = df.groupby(df['timestamp'].dt.date)[metric].mean().reset_index()
    df_daily['timestamp'] = pd.to_datetime(df_daily['timestamp'])
    
    fig = px.line(
        df_daily,
        x='timestamp',
        y=metric,
        title=f"Average {metric.title()} Trend",
        labels={'timestamp': 'Date', metric: metric.title()}
    )
    
    fig.update_layout(
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig

def format_currency(amount: float, currency: str = "₽") -> str:
    """Format amount as currency"""
    if amount is None or pd.isna(amount):
        return "N/A"
    
    return f"{amount:,.2f} {currency}"

def format_percentage(value: float) -> str:
    """Format value as percentage"""
    if value is None or pd.isna(value):
        return "N/A"
    
    return f"{value:.1f}%"

def format_datetime(dt: str) -> str:
    """Format datetime string"""
    if not dt:
        return "N/A"
    
    try:
        dt_obj = pd.to_datetime(dt)
        return dt_obj.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt)

def calculate_price_change(current: float, previous: float) -> Dict[str, Any]:
    """Calculate price change metrics"""
    if not current or not previous or pd.isna(current) or pd.isna(previous):
        return {"change": 0, "change_percent": 0, "direction": "neutral"}
    
    change = current - previous
    change_percent = (change / previous) * 100
    
    if change > 0:
        direction = "up"
    elif change < 0:
        direction = "down"
    else:
        direction = "neutral"
    
    return {
        "change": change,
        "change_percent": change_percent,
        "direction": direction
    }

def get_marketplace_icon(marketplace: str) -> str:
    """Get icon for marketplace"""
    icons = {
        "wildberries": "🛒",
        "ozon": "🛍️",
        "yandex": "🔍",
        "aliexpress": "📦",
        "amazon": "📚",
        "ebay": "🏪"
    }
    return icons.get(marketplace.lower(), "🏪")

def create_metric_card(title: str, value: Any, delta: Any = None, delta_color: str = "normal") -> None:
    """Create a metric card in Streamlit"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )

def create_status_badge(status: bool, active_text: str = "Active", inactive_text: str = "Inactive") -> str:
    """Create status badge HTML"""
    if status:
        return f'<span style="background-color: #d4edda; color: #155724; padding: 2px 8px; border-radius: 12px; font-size: 12px;">✅ {active_text}</span>'
    else:
        return f'<span style="background-color: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 12px; font-size: 12px;">❌ {inactive_text}</span>'

def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if value and value != "All":
            if column in filtered_df.columns:
                if isinstance(value, str):
                    filtered_df = filtered_df[filtered_df[column].str.contains(value, case=False, na=False)]
                else:
                    filtered_df = filtered_df[filtered_df[column] == value]
    
    return filtered_df

def export_to_excel(data: List[Dict], filename: str = "universal_parser_export.xlsx") -> bytes:
    """Export data to Excel format"""
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Items', index=False)
    
    output.seek(0)
    return output.getvalue()

def export_to_csv(data: List[Dict], filename: str = "universal_parser_export.csv") -> str:
    """Export data to CSV format"""
    df = pd.DataFrame(data)
    return df.to_csv(index=False)
