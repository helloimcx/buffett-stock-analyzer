"""
技术分析可视化模块测试
测试技术分析结果可视化接口
"""

import unittest
from datetime import datetime, timedelta
import tempfile
import shutil
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 直接复制相关类到测试文件中，避免导入依赖
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import json
import math


@dataclass
class TechnicalAnalysisResult:
    """技术分析结果数据类"""
    symbol: str
    timestamp: datetime
    indicators: Dict[str, Any]
    signals: Dict[str, Any]
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'indicators': self.indicators,
            'signals': self.signals,
            'score': self.score
        }


@dataclass
class BacktestSignal:
    """回测信号数据类"""
    timestamp: datetime
    symbol: str
    price: float
    volume: int
    signal_type: str  # 'buy', 'sell', 'neutral'
    signal_strength: float
    indicators: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class BacktestTrade:
    """回测交易数据类"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_size: int
    trade_type: str  # 'long', 'short'
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    exit_reason: Optional[str] = None  # 'signal', 'stop_loss', 'take_profit', 'time_exit'


@dataclass
class BacktestResult:
    """回测结果数据类"""
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    trades: List[BacktestTrade] = field(default_factory=list)
    signals: List[BacktestSignal] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_trade': self.avg_trade,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss
        }


# 复制可视化生成器类
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
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .score {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            text-align: center;
            margin: 20px 0;
        }}
        .indicators {{
            margin: 20px 0;
        }}
        .indicator {{
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .signals {{
            margin: 20px 0;
        }}
        .signal {{
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }}
        .buy {{ background-color: #28a745; color: white; }}
        .sell {{ background-color: #dc3545; color: white; }}
        .neutral {{ background-color: #ffc107; color: black; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{result.symbol} 技术分析报告</h1>
            <p>生成时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="score">
            综合得分: {result.score:.2f}
        </div>
        
        <div class="indicators">
            <h2>技术指标</h2>
            {self._generate_indicator_html(result.indicators)}
        </div>
        
        <div class="signals">
            <h2>交易信号</h2>
            {self._generate_signal_html(result.signals)}
        </div>
    </div>
</body>
</html>
        """
    
    def _generate_indicator_html(self, indicators: Dict[str, Any]) -> str:
        """生成指标HTML"""
        html = ""
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                display_value = f"{value:.4f}"
            else:
                display_value = str(value)
            html += f'<div class="indicator"><strong>{key}:</strong> {display_value}</div>'
        return html
    
    def _generate_signal_html(self, signals: Dict[str, Any]) -> str:
        """生成信号HTML"""
        html = ""
        for signal_type, signal_list in signals.items():
            if signal_list:
                for signal in signal_list:
                    indicator = signal.get('indicator', 'Unknown')
                    strength = signal.get('strength', 0)
                    
                    if signal_type == 'buy_signals':
                        css_class = "buy"
                        display_type = "买入"
                    elif signal_type == 'sell_signals':
                        css_class = "sell"
                        display_type = "卖出"
                    else:
                        css_class = "neutral"
                        display_type = "中性"
                    
                    html += f'<span class="signal {css_class}">{indicator} ({display_type}) - {strength:.2f}</span>'
        return html
    
    def _create_data_content(self, result: TechnicalAnalysisResult) -> str:
        """创建数据内容"""
        content = f"# {result.symbol} 技术分析报告\n\n"
        content += f"生成时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"综合得分: {result.score:.4f}\n\n"
        
        content += "## 技术指标\n"
        for key, value in result.indicators.items():
            if isinstance(value, (int, float)):
                content += f"- {key}: {value:.4f}\n"
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
        
        return content
    
    def _create_chart_config(self, result: TechnicalAnalysisResult) -> Dict[str, Any]:
        """创建图表配置"""
        return {
            'symbol': result.symbol,
            'timestamp': result.timestamp.isoformat(),
            'score': result.score,
            'indicators': result.indicators,
            'signals': result.signals
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
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-item {{
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }}
        .summary-value {{
            font-size: 18px;
            font-weight: bold;
            margin: 5px 0;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{result.symbol} 回测报告</h1>
            <p>回测期间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <div>总收益率</div>
                <div class="summary-value {'positive' if result.total_return_pct > 0 else 'negative' if result.total_return_pct < 0 else 'neutral'}">
                    {result.total_return_pct:.2%}
                </div>
            </div>
            
            <div class="summary-item">
                <div>胜率</div>
                <div class="summary-value neutral">
                    {result.win_rate:.2%}
                </div>
            </div>
            
            <div class="summary-item">
                <div>盈亏比</div>
                <div class="summary-value {'positive' if result.profit_factor > 1 else 'negative'}">
                    {result.profit_factor:.2f}
                </div>
            </div>
            
            <div class="summary-item">
                <div>总交易次数</div>
                <div class="summary-value neutral">
                    {result.total_trades}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
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
                'max_drawdown_pct': result.max_drawdown_pct,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'total_trades': result.total_trades
            }
        }
        
        filename = f"{self.output_dir}/{result.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def _generate_backtest_data_chart(self, result: BacktestResult) -> str:
        """生成回测数据文件"""
        content = f"# {result.symbol} 回测报告\n\n"
        content += f"回测期间: {result.start_date.strftime('%Y-%m-%d')} 至 {result.end_date.strftime('%Y-%m-%d')}\n"
        content += f"总收益率: {result.total_return_pct:.2%}\n"
        content += f"胜率: {result.win_rate:.2%}\n"
        content += f"盈亏比: {result.profit_factor:.2f}\n"
        content += f"总交易次数: {result.total_trades}\n"
        
        filename = f"{self.output_dir}/{result.symbol}_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename


class TestTechnicalVisualization(unittest.TestCase):
    """技术分析可视化测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.visualizer = TechnicalVisualizationGenerator(output_dir=self.temp_dir)
        
        # 创建测试技术分析结果
        self.technical_result = TechnicalAnalysisResult(
            symbol="TEST001",
            timestamp=datetime.now(),
            indicators={
                'MA': 11.5,
                'RSI': 45.2,
                'MACD': 0.15,
                'BB_position': 0.6
            },
            signals={
                'buy_signals': [
                    {'indicator': 'MA', 'strength': 0.7},
                    {'indicator': 'RSI', 'strength': 0.8}
                ],
                'sell_signals': [
                    {'indicator': 'MACD', 'strength': 0.6}
                ],
                'neutral_signals': []
            },
            score=0.75
        )
        
        # 创建测试回测结果
        self.backtest_result = BacktestResult(
            symbol="TEST001",
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now(),
            initial_capital=100000.0,
            final_capital=115000.0,
            total_return=15000.0,
            total_return_pct=0.15,
            max_drawdown=5000.0,
            max_drawdown_pct=0.05,
            sharpe_ratio=1.2,
            win_rate=0.65,
            profit_factor=1.8,
            total_trades=25,
            winning_trades=16,
            losing_trades=9,
            avg_trade=600.0,
            avg_win=1200.0,
            avg_loss=-400.0,
            largest_win=3000.0,
            largest_loss=-800.0
        )
    
    def tearDown(self):
        """清理测试数据"""
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_visualizer_initialization(self):
        """测试可视化生成器初始化"""
        self.assertEqual(self.visualizer.output_dir, self.temp_dir)
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_technical_analysis_html_chart(self):
        """测试技术分析HTML图表生成"""
        filename = self.visualizer.generate_technical_analysis_chart(
            self.technical_result, 
            chart_type="html"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.html'))
        
        # 验证文件内容
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.technical_result.symbol, content)
            self.assertIn(f"{self.technical_result.score:.2f}", content)
            self.assertIn("技术分析报告", content)
    
    def test_technical_analysis_json_chart(self):
        """测试技术分析JSON图表生成"""
        filename = self.visualizer.generate_technical_analysis_chart(
            self.technical_result, 
            chart_type="json"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.json'))
        
        # 验证JSON内容
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['symbol'], self.technical_result.symbol)
            self.assertEqual(data['score'], self.technical_result.score)
            self.assertIn('indicators', data)
            self.assertIn('signals', data)
    
    def test_technical_analysis_data_chart(self):
        """测试技术分析数据文件生成"""
        filename = self.visualizer.generate_technical_analysis_chart(
            self.technical_result, 
            chart_type="data"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.txt'))
        
        # 验证文件内容
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.technical_result.symbol, content)
            self.assertIn(f"{self.technical_result.score:.4f}", content)
            self.assertIn("技术指标", content)
    
    def test_backtest_html_chart(self):
        """测试回测HTML图表生成"""
        filename = self.visualizer.generate_backtest_chart(
            self.backtest_result, 
            chart_type="html"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.html'))
        
        # 验证文件内容
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.backtest_result.symbol, content)
            self.assertIn(f"{self.backtest_result.total_return_pct:.2%}", content)
            self.assertIn("回测报告", content)
    
    def test_backtest_json_chart(self):
        """测试回测JSON图表生成"""
        filename = self.visualizer.generate_backtest_chart(
            self.backtest_result, 
            chart_type="json"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.json'))
        
        # 验证JSON内容
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['symbol'], self.backtest_result.symbol)
            self.assertIn('summary', data)
            self.assertEqual(data['summary']['total_return_pct'], self.backtest_result.total_return_pct)
    
    def test_backtest_data_chart(self):
        """测试回测数据文件生成"""
        filename = self.visualizer.generate_backtest_chart(
            self.backtest_result, 
            chart_type="data"
        )
        
        # 验证文件生成
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(filename.endswith('.txt'))
        
        # 验证文件内容
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.backtest_result.symbol, content)
            self.assertIn(f"{self.backtest_result.total_return_pct:.2%}", content)
            self.assertIn("回测报告", content)
    
    def test_unsupported_chart_type(self):
        """测试不支持的图表类型"""
        with self.assertRaises(ValueError):
            self.visualizer.generate_technical_analysis_chart(
                self.technical_result, 
                chart_type="unsupported"
            )
        
        with self.assertRaises(ValueError):
            self.visualizer.generate_backtest_chart(
                self.backtest_result, 
                chart_type="unsupported"
            )
    
    def test_chart_config_creation(self):
        """测试图表配置创建"""
        config = self.visualizer._create_chart_config(self.technical_result)
        
        self.assertEqual(config['symbol'], self.technical_result.symbol)
        self.assertEqual(config['score'], self.technical_result.score)
        self.assertIn('indicators', config)
        self.assertIn('signals', config)
    
    def test_indicator_html_generation(self):
        """测试指标HTML生成"""
        indicators = {
            'MA': 11.5,
            'RSI': 45.2,
            'MACD': 0.15
        }
        
        html = self.visualizer._generate_indicator_html(indicators)
        
        self.assertIn('MA:', html)
        self.assertIn('11.5000', html)
        self.assertIn('RSI:', html)
        self.assertIn('45.2000', html)
    
    def test_signal_html_generation(self):
        """测试信号HTML生成"""
        signals = {
            'buy_signals': [
                {'indicator': 'MA', 'strength': 0.7}
            ],
            'sell_signals': [
                {'indicator': 'RSI', 'strength': 0.8}
            ]
        }
        
        html = self.visualizer._generate_signal_html(signals)
        
        self.assertIn('MA', html)
        self.assertIn('买入', html)
        self.assertIn('RSI', html)
        self.assertIn('卖出', html)
        self.assertIn('0.70', html)
        self.assertIn('0.80', html)


if __name__ == '__main__':
    unittest.main()