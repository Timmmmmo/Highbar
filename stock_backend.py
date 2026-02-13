# -*- coding: utf-8 -*-
"""
A股高标股Dashboard - 后端服务
使用东方财富API获取真实的A股连板数据
"""

from flask import Flask, jsonify, request, make_response
import requests
from datetime import datetime, timedelta
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/options', methods=['OPTIONS'])
def handle_options():
    return make_response('', 204)

executor = ThreadPoolExecutor(max_workers=5)

def get_all_stocks():
    """获取所有A股股票列表"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 5000,
            "po": 1,
            "np": 1,
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f4,f12,f13,f14"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        stocks = []
        if data.get('data') and data['data'].get('diff'):
            for stock in data['data']['diff']:
                stocks.append({
                    'code': stock.get('f12', ''),
                    'name': stock.get('f14', ''),
                    'price': stock.get('f2'),
                    'change': stock.get('f3'),
                    'market': stock.get('f13')  # 1=沪市 0=深市
                })
        return stocks
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []

def get_limit_up_stocks():
    """获取今日涨停股票"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 5000,
            "po": 1,
            "np": 1,
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f4,f12,f13,f14,f15,f16,f17,f18",
            "filters": "f3>=9.9"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        limit_stocks = []
        if data.get('data') and data['data'].get('diff'):
            for stock in data['data']['diff']:
                change = stock.get('f3', 0) or 0
                if change >= 9.9:
                    ts_code = str(stock.get('f12', ''))
                    market = 1 if stock.get('f13') == 1 else 0
                    full_code = f"{ts_code}.SH" if market == 1 else f"{ts_code}.SZ"
                    
                    limit_stocks.append({
                        'code': ts_code,
                        'full_code': full_code,
                        'name': stock.get('f14', ''),
                        'price': stock.get('f2'),
                        'change': change,
                        'high': stock.get('f15'),
                        'low': stock.get('f16'),
                        'volume': stock.get('f17'),
                        'amount': stock.get('f18')
                    })
        return limit_stocks
    except Exception as e:
        print(f"获取涨停股票失败: {e}")
        return []

def get_stock_history_days(code, days=30):
    """获取股票历史数据"""
    try:
        ts_code = code.replace('.SH', '').replace('.SZ', '')
        market = 1 if 'SH' in code else 0
        
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": f"{market}.{ts_code}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": 101,
            "fqt": 0,
            "end": datetime.now().strftime('%Y%m%d'),
            "lmt": days
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        klines = []
        if data.get('data') and data['data'].get('klines'):
            for kline in data['data']['klines']:
                parts = kline.split(',')
                klines.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]),
                    'change': float(parts[2]) - float(parts[1]) if len(parts) > 1 else 0
                })
        return klines
    except Exception as e:
        print(f"获取历史数据失败 {code}: {e}")
        return []

def calculate_board_count(history_data):
    """计算连板数"""
    if not history_data:
        return 0
    
    board_count = 0
    consecutive_up = True
    
    for i, day in enumerate(history_data):
        if i == 0:
            continue
        
        prev_close = history_data[i-1]['close']
        curr_close = day['close']
        
        change_pct = ((curr_close - prev_close) / prev_close) * 100
        
        if change_pct >= 9.9:
            if consecutive_up or i == 1:
                board_count += 1
                consecutive_up = True
        else:
            break
    
    return board_count

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """获取连板股票数据"""
    try:
        min_board = request.args.get('min_board', 2, type=int)
        
        today_limit = get_limit_up_stocks()
        
        if not today_limit:
            return jsonify([])
        
        result = []
        
        for stock in today_limit[:50]:
            code = stock['full_code']
            history = get_stock_history_days(code, days=30)
            
            board_count = calculate_board_count(history)
            
            if board_count >= min_board:
                result.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'board': board_count,
                    'price': stock['price'] if stock['price'] else 0,
                    'change': round(stock['change'], 2) if stock['change'] else 0,
                    'status': '新开' if board_count == 1 else '正常'
                })
        
        result.sort(key=lambda x: x['board'], reverse=True)
        
        return jsonify(result[:30])
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trend', methods=['GET'])
def get_trend():
    """获取近30日连板趋势"""
    try:
        days = request.args.get('days', 30, type=int)
        trend_data = []
        
        for i in range(days):
            target_date = datetime.now() - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            
            try:
                url = "https://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    "pn": 1,
                    "pz": 5000,
                    "po": 1,
                    "np": 1,
                    "fltt": 2,
                    "invt": 2,
                    "fid": "f3",
                    "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                    "fields": "f2,f3,f12,f13,f14",
                    "filters": "f3>=9.9",
                    "beg": date_str.replace('-', ''),
                    "end": date_str.replace('-', '')
                }
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                data = resp.json()
                
                count = 0
                if data.get('data') and data['data'].get('diff'):
                    count = len(data['data']['diff'])
            except:
                count = 0
            
            trend_data.append({
                'date': date_str,
                'count': count
            })
        
        trend_data.reverse()
        return jsonify(trend_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        stocks = get_limit_up_stocks()
        
        result = {
            'total_stocks': len(stocks),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'data_source': 'eastmoney',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("A股高标股Dashboard 后端服务")
    print("数据源: 东方财富")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
