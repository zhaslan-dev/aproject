"""
Генерация графиков: статические PNG (Matplotlib) и интерактивные HTML (Plotly).
"""

import io
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select
from models import async_session, CryptoPrice

async def get_price_data(ticker: str, hours: int = 24) -> pd.DataFrame:
    """Загружает цены за последние hours часов из БД и возвращает DataFrame."""
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    async with async_session() as session:
        query = select(CryptoPrice).where(
            CryptoPrice.ticker == ticker,
            CryptoPrice.timestamp >= start,
            CryptoPrice.timestamp <= end
        ).order_by(CryptoPrice.timestamp)
        result = await session.execute(query)
        records = result.scalars().all()
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame([(r.timestamp, r.price) for r in records], columns=['timestamp', 'price'])
    return df

def create_matplotlib_chart(df: pd.DataFrame, ticker: str) -> bytes:
    """Возвращает PNG‑изображение графика в виде bytes."""
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['price'], label='Price', color='blue', linewidth=1.5)
    plt.title(f'{ticker} Price (last {len(df)} records)')
    plt.xlabel('Time')
    plt.ylabel('Price (USDT)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    return buf.getvalue()

def create_plotly_chart(df: pd.DataFrame, ticker: str) -> str:
    """Возвращает HTML‑код интерактивного графика (без полной страницы)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['price'],
        mode='lines',
        name='Price',
        line=dict(color='royalblue', width=2)
    ))
    fig.update_layout(
        title=f'{ticker} Price Chart',
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        hovermode='x unified',
        template='plotly_white'
    )
    return fig.to_html(full_html=False)