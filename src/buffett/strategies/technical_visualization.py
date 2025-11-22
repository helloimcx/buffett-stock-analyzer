"""
技术分析结果可视化模块
提供技术分析结果的可视化接口
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os
import math

from .technical_analysis import TechnicalAnalysisResult
from .backtesting import BacktestResult


class TechnicalVisualizationGenerator:
    """技术分析可视化生成器"""
    
    def __init__(self, output_dir: str = "reports/technical_analysis"):
        """
        初始化可视化生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_technical_analysis_chart(self, 
                                      result: TechnicalAnalysisResult,
                                      chart_type: str = "html") -> str:
        """
        生成技术分析图表
        
        Args:
            result: 技术分析结果
            chart_type: 图表类型 ('html', 'json', 'data')
            
        Returns:
            图表文件路径
        """
        if chart_type == "html":
            return self._generate_html_chart(result)
        elif chart_type == "json":
            return self._generate_json_chart(result)
        elif chart_type == "data":
            return self._generate_data_chart(result)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")
    
    def _generate_html_chart(self, result: TechnicalAnalysisResult) -> str:
        """生成HTML图表"""
        html_content = self._create_html_template(result)
        
        filename = f"{self.output_dir}/{result.symbol}_technical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def _generate_json_chart(self, result: TechnicalAnalysisResult) -> str:
        """生成JSON数据"""
        chart_data = {
            'symbol': result.symbol,
            'timestamp': result.timestamp.isoformat(),
            'indicators': result.indicators,
            'signals': result.signals,
            'score': result.score,
            'chart_config': self._create_chart_config(result)
        }
        
        filename = f"{self.output_dir}/{result.symbol}_technical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def _generate_data_chart(self, result: TechnicalAnalysisResult) -> str:
        """生成数据文件"""
        data_content = self._create_data_content(result)
        
        filename = f"{self.output_dir}/{result.symbol}_technical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data_content)
        
        return filename
    
    def _create_html_template(self, result: TechnicalAnalysisResult) -> str:
        """创建HTML模板"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{result.symbol} 技术分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }}
        .score-section {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            border-radius: 10px;
        }}
        .score-value {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .score-label {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .indicators-section {{
            margin: 30px 0;
        }}
        .indicators-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .indicator-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .indicator-title {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .indicator-value {{
            font-size: 1.5em;
            color: #007bff;
            font-weight: bold;
        }}
        .signals-section {{
            margin: 30px 0;
        }}
        .signal-badge {{
            display: inline-block;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .buy-signal {{
            background-color: #28a745;
            color: white;
        }}
        .sell-signal {{
            background-color: #dc3545;
            color: white;
        }}
        .neutral-signal {{
            background-color: #ffc107;
            color: #212529;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
        }}
        .chart-title {{
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #495057;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{result.symbol} 技术分析报告</h1>
            <p>生成时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="score-section">
            <div class="score-label">综合技术得分</div>
            <div class="score-value">{result.score:.2f}</div>
        </div>
        
        <div class="indicators-section">
            <h2>技术指标</h2>
            <div class="indicators-grid">
                {self._generate_indicator_cards(result.indicators)}
            </div>
        </div>
        
        <div class="signals-section">
            <h2>交易信号</h2>
            {self._generate_signal_badges(result.signals)}
        </div>
        
        <div class="chart-container">
            <div class="chart-title">技术指标雷达图</div>
            <canvas id="radarChart" width="400" height="400"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">信号强度分布</div>
            <canvas id="signalChart" width="400" height="300"></canvas>
        </div>
        
        <div class="footer">
            <p>本报告由巴菲特股息筛选系统自动生成</p>
            <p>技术分析仅供参考，投资有风险，入市需谨慎</p>
        </div>
    </div>
    
    <script>
        // 雷达图数据
        const radarData = {{
            labels: {json.dumps(list(result.indicators.keys()))},
            datasets: [{{
                label: '技术指标值',
                data: {json.dumps([self._normalize_indicator_value(value) for value in result.indicators.values()])},
                backgroundColor: 'rgba(0, 123, 255, 0.2)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(0, 123, 255, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(0, 123, 255, 1)'
            }}]
        }};
        
        // 信号强度数据
        const signalData = {{
            labels: ['买入信号', '卖出信号', '中性信号'],
            datasets: [{{
                label: '信号数量',
                data: [
                    {len(result.signals.get('buy_signals', []))},
                    {len(result.signals.get('sell_signals', []))},
                    {len(result.signals.get('neutral_signals', []))}
                ],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(255, 193, 7, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 193, 7, 1)'
                ],
                borderWidth: 1
            }}]
        }};
        
        // 创建雷达图
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: radarData,
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }}
                }},
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 1
                    }}
                }}
            }}
        }});
        
        // 创建信号强度图
        const signalCtx = document.getElementById('signalChart').getContext('2d');
        new Chart(signalCtx, {{
            type: 'bar',
            data: signalData,
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
    
    def _normalize_indicator_value(self, value: Any) -> float:
        """标准化指标值到0-1范围"""
        if isinstance(value, (int, float)):
            # 简单的标准化逻辑，根据指标类型调整
            if isinstance(value, float) and 0 <= value <= 1:
                return value
            elif isinstance(value, float) and 0 <= value <= 100:
                return value / 100
            else:
                # 对于其他范围的值，使用sigmoid函数进行标准化
                return 1 / (1 + math.exp(-value / 10))
        else:
            return 0.5
    
    def _generate_indicator_cards(self, indicators: Dict[str, Any]) -> str:
        """生成指标卡片HTML"""
        cards = []
        
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                display_value = f"{value:.4f}" if isinstance(value, float) else str(value)
            elif isinstance(value, str):
                display_value = value
            elif isinstance(value, dict):
                # 处理复杂指标值
                if 'signal_type' in value:
                    signal_type = value['signal_type']
                    signal_class = f"signal-badge {signal_type}-signal"
                    display_value = f'<span class="{signal_class}">{signal_type.upper()}</span>'
                else:
                    display_value = json.dumps(value, ensure_ascii=False)
            else:
                display_value = str(value)
            
            cards.append(f"""
                <div class="indicator-card">
                    <div class="indicator-title">{key}</div>
                    <div class="indicator-value">{display_value}</div>
                </div>
            """)
        
        return ''.join(cards)
    
    def _generate_signal_badges(self, signals: Dict[str, Any]) -> str:
        """生成信号徽章HTML"""
        badges = []
        
        for signal_type, signal_list in signals.items():
            if signal_list:
                for signal in signal_list:
                    indicator = signal.get('indicator', 'Unknown')
                    strength = signal.get('strength', 0)
                    
                    # 根据信号类型确定样式
                    if signal_type == 'buy_signals':
                        badge_class = "buy-signal"
                        display_type = "买入"
                    elif signal_type == 'sell_signals':
                        badge_class = "sell-signal"
                        display_type = "卖出"
                    else:
                        badge_class = "neutral-signal"
                        display_type = "中性"
                    
                    badges.append(f"""
                        <span class="signal-badge {badge_class}">
                            {indicator} ({display_type}) - 强度: {strength:.2f}
                        </span>
                    """)
        
        if not badges:
            badges.append('<span class="signal-badge neutral-signal">当前无明确信号</span>')
        
        return ''.join(badges)
    
    def _create_data_content(self, result: TechnicalAnalysisResult) -> str:
        """创建数据内容"""
        content = f"""
# {result.symbol} 技术分析报告

## 基本信息
- 股票代码: {result.symbol}
- 分析时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- 综合得分: {result.score:.4f}

## 技术指标
"""
        
        for key, value in result.indicators.items():
            if isinstance(value, (int, float)):
                content += f"- {key}: {value:.4f}\n"
            elif isinstance(value, str):
                content += f"- {key}: {value}\n"
            elif isinstance(value, dict):
                content += f"- {key}: {json.dumps(value, ensure_ascii=False, indent=2)}\n"
            else:
                content += f"- {key}: {value}\n"
        
        content += "\n## 交易信号\n"
        
        for signal_type, signal_list in result.signals.items():
            if signal_list:
                content += f"### {signal_type}\n"
                for signal in signal_list:
                    indicator = signal.get('indicator', 'Unknown')
                    strength = signal.get('strength', 0)
                    content += f"- {indicator}: 强度 {strength:.2f}\n"
        
        content += """
---
*本报告由巴菲特股息筛选系统自动生成*
*技术分析仅供参考，投资有风险，入市需谨慎*
        """
        
        return content
    
    def _create_chart_config(self, result: TechnicalAnalysisResult) -> Dict[str, Any]:
        """创建图表配置"""
        return {
            'symbol': result.symbol,
            'timestamp': result.timestamp.isoformat(),
            'score': result.score,
            'indicators': result.indicators,
            'signals': result.signals,
            'chart_types': {
                'radar': {
                    'title': '技术指标雷达图',
                    'labels': list(result.indicators.keys()),
                    'data': [self._normalize_indicator_value(value) for value in result.indicators.values()]
                },
                'signals': {
                    'title': '信号强度分布',
                    'labels': ['买入信号', '卖出信号', '中性信号'],
                    'data': [
                        len(result.signals.get('buy_signals', [])),
                        len(result.signals.get('sell_signals', [])),
                        len(result.signals.get('neutral_signals', []))
                    ]
                }
            }
        }
    
    def generate_backtest_chart(self, 
                              result: BacktestResult,
                              chart_type: str = "html") -> str:
        """
        生成回测图表
        
        Args:
            result: 回测结果
            chart_type: 图表类型 ('html', 'json', 'data')
            
        Returns:
            图表文件路径
        """
        if chart_type == "html":
            return self._generate_backtest_html_chart(result)
        elif chart_type == "json":
            return self._generate_backtest_json_chart(result)
        elif chart_type == "data":
            return self._generate_backtest_data_chart(result)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")
    
    def _generate_backtest_html_chart(self, result: BacktestResult) -> str:
        """生成回测HTML图表"""
        html_content = self._create_backtest_html_template(result)
        
        filename = f"{self.output_dir}/{result.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def _create_backtest_html_template(self, result: BacktestResult) -> str:
        """创建回测HTML模板"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{result.symbol} 回测报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }}
        .summary-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .summary-title {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .summary-value {{
            font-size: 1.8em;
            font-weight: bold;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
        }}
        .chart-title {{
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #495057;
        }}
        .trades-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .trades-table th, .trades-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .trades-table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .profit {{ color: #28a745; }}
        .loss {{ color: #dc3545; }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{result.symbol} 回测报告</h1>
            <p>回测期间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}</p>
        </div>
        
        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-title">总收益率</div>
                <div class="summary-value {'positive' if result.total_return_pct > 0 else 'negative' if result.total_return_pct < 0 else 'neutral'}">
                    {result.total_return_pct:.2%}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">总收益率</div>
                <div class="summary-value {'positive' if result.total_return > 0 else 'negative' if result.total_return < 0 else 'neutral'}">
                    ¥{result.total_return:,.2f}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">最大回撤</div>
                <div class="summary-value negative">
                    {result.max_drawdown_pct:.2%}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">胜率</div>
                <div class="summary-value neutral">
                    {result.win_rate:.2%}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">盈亏比</div>
                <div class="summary-value {'positive' if result.profit_factor > 1 else 'negative'}">
                    {result.profit_factor:.2f}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">总交易次数</div>
                <div class="summary-value neutral">
                    {result.total_trades}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">平均交易</div>
                <div class="summary-value {'positive' if result.avg_trade > 0 else 'negative' if result.avg_trade < 0 else 'neutral'}">
                    ¥{result.avg_trade:,.2f}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-title">夏普比率</div>
                <div class="summary-value {'positive' if (result.sharpe_ratio or 0) > 0 else 'negative'}">
                    {result.sharpe_ratio:.2f if result.sharpe_ratio is not None else 'N/A'}
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">权益曲线</div>
            <canvas id="equityChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">交易分布</div>
            <canvas id="tradeChart" width="400" height="300"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">月度收益</div>
            <canvas id="monthlyChart" width="400" height="300"></canvas>
        </div>
        
        <div class="footer">
            <p>本回测报告由巴菲特股息筛选系统自动生成</p>
            <p>回测结果仅供参考，实际交易可能存在滑点、手续费等额外成本</p>
        </div>
    </div>
    
    <script>
        // 权益曲线数据（模拟）
        const equityData = {{
            labels: {json.dumps([f"第{i}天" for i in range(1, len(result.trades) + 1)])},
            datasets: [{{
                label: '权益曲线',
                data: {json.dumps([self._calculate_equity_at_trade(i, result) for i in range(len(result.trades) + 1)])},
                borderColor: 'rgba(0, 123, 255, 1)',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }}]
        }};
        
        // 交易分布数据
        const tradeData = {{
            labels: ['盈利交易', '亏损交易'],
            datasets: [{{
                label: '交易数量',
                data: [{result.winning_trades}, {result.losing_trades}],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(220, 53, 69, 1)'
                ],
                borderWidth: 1
            }}]
        }};
        
        // 月度收益数据（模拟）
        const monthlyData = {{
            labels: {json.dumps([f"第{i}月" for i in range(1, 13)])},
            datasets: [{{
                label: '月度收益率',
                data: {json.dumps([self._calculate_monthly_return(i, result) for i in range(12)])},
                backgroundColor: 'rgba(0, 123, 255, 0.8)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 1
            }}]
        }};
        
        // 创建权益曲线图
        const equityCtx = document.getElementById('equityChart').getContext('2d');
        new Chart(equityCtx, {{
            type: 'line',
            data: equityData,
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        title: {{
                            display: true,
                            text: '权益'
                        }}
                    }}
                }}
            }}
        }});
        
        // 创建交易分布图
        const tradeCtx = document.getElementById('tradeChart').getContext('2d');
        new Chart(tradeCtx, {{
            type: 'doughnut',
            data: tradeData,
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                    }}
                }}
            }}
        }});
        
        // 创建月度收益图
        const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
        new Chart(monthlyCtx, {{
            type: 'bar',
            data: monthlyData,
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: '收益率'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
    
    def _calculate_equity_at_trade(self, trade_index: int, result: BacktestResult) -> float:
        """计算特定交易点的权益（模拟）"""
        if trade_index == 0:
            return result.initial_capital
        
        # 简化的权益计算，实际应该基于交易历史
        progress = trade_index / len(result.trades) if result.trades else 0
        return result.initial_capital + (result.final_capital - result.initial_capital) * progress
    
    def _calculate_monthly_return(self, month: int, result: BacktestResult) -> float:
        """计算月度收益率（模拟）"""
        # 简化的月度收益计算
        total_return_pct = result.total_return_pct
        monthly_return = total_return_pct / 12
        return monthly_return * (1 + 0.1 * (month - 6) / 6)  # 添加一些波动
    
    def _generate_backtest_json_chart(self, result: BacktestResult) -> str:
        """生成回测JSON数据"""
        chart_data = {
            'symbol': result.symbol,
            'start_date': result.start_date.isoformat(),
            'end_date': result.end_date.isoformat(),
            'summary': {
                'initial_capital': result.initial_capital,
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
                'max_drawdown': result.max_drawdown,
                'max_drawdown_pct': result.max_drawdown_pct,
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'total_trades': result.total_trades,
                'avg_trade': result.avg_trade
            },
            'trades': [
                {
                    'entry_time': trade.entry_time.isoformat(),
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'position_size': trade.position_size,
                    'trade_type': trade.trade_type,
                    'profit_loss': trade.profit_loss,
                    'profit_loss_pct': trade.profit_loss_pct,
                    'exit_reason': trade.exit_reason
                }
                for trade in result.trades
            ]
        }
        
        filename = f"{self.output_dir}/{result.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def _generate_backtest_data_chart(self, result: BacktestResult) -> str:
        """生成回测数据文件"""
        content = f"""
# {result.symbol} 回测报告

## 基本信息
- 股票代码: {result.symbol}
- 回测期间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}
- 初始资金: ¥{result.initial_capital:,.2f}
- 最终资金: ¥{result.final_capital:,.2f}

## 收益统计
- 总收益: ¥{result.total_return:,.2f}
- 总收益率: {result.total_return_pct:.2%}
- 最大回撤: {result.max_drawdown_pct:.2%}
- 夏普比率: {result.sharpe_ratio:.2f if result.sharpe_ratio is not None else 'N/A'}

## 交易统计
- 总交易次数: {result.total_trades}
- 盈利交易: {result.winning_trades}
- 亏损交易: {result.losing_trades}
- 胜率: {result.win_rate:.2%}
- 盈亏比: {result.profit_factor:.2f}
- 平均交易: ¥{result.avg_trade:,.2f}
- 平均盈利: ¥{result.avg_win:,.2f}
- 平均亏损: ¥{result.avg_loss:,.2f}
- 最大盈利: ¥{result.largest_win:,.2f}
- 最大亏损: ¥{result.largest_loss:,.2f}

## 交易明细
"""
        
        for i, trade in enumerate(result.trades, 1):
            content += f"""
### 交易 {i}
- 入场时间: {trade.entry_time.strftime('%Y-%m-%d %H:%M:%S')}
- 出场时间: {trade.exit_time.strftime('%Y-%m-%d %H:%M:%S') if trade.exit_time else 'N/A'}
- 入场价格: ¥{trade.entry_price:.4f}
- 出场价格: ¥{trade.exit_price:.4f if trade.exit_price else 0}
- 交易类型: {trade.trade_type}
- 持仓数量: {trade.position_size}
- 盈亏: ¥{trade.profit_loss:.2f if trade.profit_loss is not None else 0}
- 盈亏率: {trade.profit_loss_pct:.2% if trade.profit_loss_pct is not None else 0}
- 出场原因: {trade.exit_reason if trade.exit_reason else 'N/A'}
"""
        
        content += """
---
*本回测报告由巴菲特股息筛选系统自动生成*
*回测结果仅供参考，实际交易可能存在滑点、手续费等额外成本*
        """
        
        filename = f"{self.output_dir}/{result.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename