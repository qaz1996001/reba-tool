#!/usr/bin/env python3
"""
資料記錄模組 (Data Logger Module)
記錄並保存REBA分析結果

功能：
1. 記錄每一幀的分析結果（角度、REBA分數、風險等級）
2. 保存為CSV表格格式（適合Excel分析）
3. 保存為JSON結構化格式（包含完整資訊和統計）
4. 自動計算統計資訊（平均值、標準差、分佈等）
5. 生成分析報告
6. 資料驗證和品質檢查

支援格式:
- CSV: 表格格式，適合統計分析和Excel處理
- JSON: 結構化格式，包含完整資訊和元資料
- Markdown: 分析報告格式

作者：人因工程研究團隊
日期：2025年1月
版本：1.0
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import deque
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas未安裝，某些功能可能受限")


# ==================== 線上統計累積器 ====================

class OnlineStats:
    """
    線上統計計算器（使用Welford算法）
    O(1)記憶體複雜度，適合處理無限資料流

    參考：https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford's_online_algorithm
    """

    def __init__(self):
        """初始化統計計算器"""
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0  # sum of squares of differences from mean
        self.min_val = float('inf')
        self.max_val = float('-inf')

    def update(self, value: float):
        """
        更新統計值

        Args:
            value: 新數據點
        """
        if value is None:
            return

        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)

    def get_stats(self) -> Dict[str, float]:
        """
        獲取統計結果

        Returns:
            統計字典，包含 count, mean, std, min, max
        """
        if self.count == 0:
            return {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0}

        variance = self.m2 / self.count if self.count > 0 else 0
        std = variance ** 0.5

        return {
            'count': self.count,
            'mean': round(self.mean, 2),
            'std': round(std, 2),
            'min': round(self.min_val, 2) if self.min_val != float('inf') else 0,
            'max': round(self.max_val, 2) if self.max_val != float('-inf') else 0
        }


class StatisticsAccumulator:
    """
    統計資料累積器
    使用線上演算法進行O(1)記憶體的統計計算
    """

    def __init__(self):
        """初始化所有統計追蹤器"""
        # REBA分數統計
        self.reba_stats = OnlineStats()

        # 角度統計
        self.angle_stats = {
            'neck_angle': OnlineStats(),
            'trunk_angle': OnlineStats(),
            'upper_arm_angle': OnlineStats(),
            'forearm_angle': OnlineStats(),
            'wrist_angle': OnlineStats(),
            'leg_angle': OnlineStats()
        }

        # 風險等級計數
        self.risk_counts = {
            'negligible': 0,
            'low': 0,
            'medium': 0,
            'high': 0,
            'very_high': 0
        }

        # 時間追蹤
        self.first_timestamp = None
        self.last_timestamp = None
        self.total_frames = 0
        self.valid_frames = 0

    def update(self, record: Dict):
        """
        更新累積統計

        Args:
            record: 單幀記錄
        """
        self.total_frames += 1

        # 更新REBA統計
        reba_score = record.get('reba_score')
        if reba_score is not None:
            self.valid_frames += 1
            self.reba_stats.update(float(reba_score))

        # 更新角度統計
        for angle_name in self.angle_stats:
            angle_value = record.get(angle_name)
            if angle_value is not None:
                self.angle_stats[angle_name].update(float(angle_value))

        # 更新風險等級計數
        risk_level = record.get('risk_level')
        if risk_level in self.risk_counts:
            self.risk_counts[risk_level] += 1

        # 更新時間追蹤
        timestamp = record.get('timestamp')
        if timestamp is not None:
            if self.first_timestamp is None:
                self.first_timestamp = timestamp
            self.last_timestamp = timestamp

    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取完整統計結果

        Returns:
            統計資訊字典
        """
        # 基本統計
        basic_stats = {
            'total_frames': self.total_frames,
            'valid_frames': self.valid_frames,
            'invalid_frames': self.total_frames - self.valid_frames,
            'success_rate': round(self.valid_frames / self.total_frames * 100, 2) if self.total_frames > 0 else 0
        }

        # REBA分數統計
        reba_stats = self.reba_stats.get_stats()
        if reba_stats['count'] > 0:
            # 計算中位數和四分位數需要實際資料，這裡提供基本估計
            reba_stats['median'] = reba_stats['mean']
            reba_stats['q25'] = max(1, reba_stats['mean'] - reba_stats['std'])
            reba_stats['q75'] = min(15, reba_stats['mean'] + reba_stats['std'])

        # 風險等級分佈
        total_risk = sum(self.risk_counts.values())
        risk_percentages = {
            level: round(count / total_risk * 100, 2) if total_risk > 0 else 0
            for level, count in self.risk_counts.items()
        }

        # 角度統計
        angle_stats_dict = {
            name: stats.get_stats()
            for name, stats in self.angle_stats.items()
            if stats.count > 0
        }

        # 時間統計
        duration = 0
        avg_fps = 0
        if self.first_timestamp is not None and self.last_timestamp is not None:
            duration = self.last_timestamp - self.first_timestamp
            avg_fps = self.total_frames / duration if duration > 0 else 0

        return {
            'basic': basic_stats,
            'reba_score': reba_stats,
            'risk_distribution': {
                'counts': self.risk_counts.copy(),
                'percentages': risk_percentages
            },
            'angles': angle_stats_dict,
            'time': {
                'duration_seconds': round(duration, 2),
                'average_fps': round(avg_fps, 2)
            }
        }


class DataLogger:
    """
    資料記錄器
    
    提供完整的資料記錄和保存功能，包括：
    - 幀資料記錄
    - CSV/JSON格式保存
    - 統計分析
    - 報告生成
    """
    
    def __init__(self, output_dir: str = './results'):
        """
        初始化資料記錄器

        Args:
            output_dir: 輸出目錄路徑
        """
        self.output_dir = Path(output_dir)

        # 使用固定大小的deque儲存最近1000幀（用於即時查詢）
        # 記憶體用量：1000幀 × 約2KB = 2MB（固定）
        self.recent_buffer = deque(maxlen=10000)

        # 串流寫入模式
        self.csv_file = None
        self.csv_writer = None
        self.is_recording = False

        # 線上統計累積器（O(1)記憶體）
        self.stats_accumulator = StatisticsAccumulator()

        self.session_start = datetime.now()  # 會話開始時間
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")  # 會話ID

        # 確保輸出目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 資料欄位定義
        self.data_fields = [
            'frame_id',          # 幀編號
            'timestamp',         # 時間戳
            'datetime',          # 日期時間
            'neck_angle',        # 頸部角度
            'trunk_angle',       # 軀幹角度
            'upper_arm_angle',   # 上臂角度
            'forearm_angle',     # 前臂角度
            'wrist_angle',       # 手腕角度
            'leg_angle',         # 腿部角度
            'reba_score',        # REBA分數
            'risk_level',        # 風險等級
        ]

        logger.info(f"資料記錄器初始化完成，輸出目錄: {self.output_dir}")
        logger.info(f"會話ID: {self.session_id}")
        logger.info(f"串流模式: 記憶體用量固定 < 10MB")
    
    # ==================== 串流錄製控制 ====================

    def start_recording(self, base_filename: Optional[str] = None):
        """
        開始串流錄製

        Args:
            base_filename: 檔案名稱（不含副檔名），None則自動生成
        """
        if self.is_recording:
            logger.warning("已在錄製中，請先停止")
            return

        # 生成檔案名稱
        if base_filename is None:
            base_filename = f"reba_analysis_{self.session_id}"

        filepath = self.output_dir / f"{base_filename}.csv"

        try:
            # 開啟CSV檔案進行串流寫入
            self.csv_file = open(filepath, 'w', newline='', encoding='utf-8-sig')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.data_fields)
            self.csv_writer.writeheader()

            self.is_recording = True
            logger.info(f"開始錄製: {filepath}")
            logger.info("串流模式: 每幀即時寫入，記憶體用量 < 10MB")

        except Exception as e:
            logger.error(f"無法開始錄製: {e}")
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None

    def stop_recording(self):
        """停止串流錄製"""
        if not self.is_recording:
            logger.warning("未在錄製中")
            return

        try:
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None

            self.csv_writer = None
            self.is_recording = False

            logger.info("錄製已停止")
            logger.info(f"總幀數: {self.stats_accumulator.total_frames}")

        except Exception as e:
            logger.error(f"停止錄製時發生錯誤: {e}")

    # ==================== 資料記錄方法 ====================

    def add_frame_data(self, frame_id: int, timestamp: float,
                      angles: Dict[str, Optional[float]],
                      reba_score: int,
                      risk_level: str,
                      details: Optional[Dict] = None,
                      metadata: Optional[Dict] = None):
        """
        添加一幀的資料（串流模式）

        Args:
            frame_id: 幀編號
            timestamp: 時間戳（秒）
            angles: 角度字典，包含6個關節角度
            reba_score: REBA分數
            risk_level: 風險等級
            details: 詳細分數字典（可選）
            metadata: 額外的元資料（可選）
        """
        # 構建基本記錄
        record = {
            'frame_id': frame_id,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat(),
            'neck_angle': angles.get('neck'),
            'trunk_angle': angles.get('trunk'),
            'upper_arm_angle': angles.get('upper_arm'),
            'forearm_angle': angles.get('forearm'),
            'wrist_angle': angles.get('wrist'),
            'leg_angle': angles.get('leg'),
            'reba_score': reba_score,
            'risk_level': risk_level
        }

        # 添加詳細分數（如果提供）
        if details:
            for key, value in details.items():
                if key not in record:
                    record[f'detail_{key}'] = value

        # 添加元資料（如果提供）
        if metadata:
            for key, value in metadata.items():
                if key not in record:
                    record[f'meta_{key}'] = value

        # 1. 即時寫入CSV（串流模式）
        if self.is_recording and self.csv_writer:
            try:
                self.csv_writer.writerow(record)
                self.csv_file.flush()  # 確保即時寫入磁碟
            except Exception as e:
                logger.error(f"CSV寫入失敗: {e}")

        # 2. 添加到recent_buffer（固定大小，自動淘汰舊資料）
        self.recent_buffer.append(record)

        # 3. 更新線上統計（O(1)記憶體）
        self.stats_accumulator.update(record)

        # 每100幀記錄一次日誌
        if self.stats_accumulator.total_frames % 100 == 0:
            logger.debug(f"已記錄 {self.stats_accumulator.total_frames} 幀資料（記憶體: {len(self.recent_buffer)} 幀快取）")
    
    def add_batch_data(self, batch_data: List[Dict]):
        """
        批次添加資料（用於相容性，不建議在串流模式使用）

        Args:
            batch_data: 資料列表，每個元素為一幀的資料字典
        """
        for data in batch_data:
            # 寫入CSV（如果正在錄製）
            if self.is_recording and self.csv_writer:
                try:
                    self.csv_writer.writerow(data)
                except Exception as e:
                    logger.error(f"批次寫入CSV失敗: {e}")

            # 添加到recent_buffer
            self.recent_buffer.append(data)

            # 更新統計
            self.stats_accumulator.update(data)

        # 確保批次寫入磁碟
        if self.is_recording and self.csv_file:
            self.csv_file.flush()

        logger.info(f"批次添加 {len(batch_data)} 筆資料")
    
    # ==================== CSV保存方法 ====================
    
    def save_to_csv(self, filename: Optional[str] = None,
                   include_details: bool = False) -> str:
        """
        保存recent_buffer為CSV檔案（僅包含最近1000幀）

        注意：在串流模式下，資料已即時寫入CSV，此方法僅保存recent_buffer

        Args:
            filename: 檔案名稱（不含副檔名），None則自動生成
            include_details: 是否包含詳細分數欄位

        Returns:
            保存的檔案路徑
        """
        if not self.recent_buffer:
            logger.warning("recent_buffer為空，無資料可保存")
            return ""

        # 生成檔案名稱
        if filename is None:
            filename = f"reba_recent_{self.session_id}"

        filepath = self.output_dir / f"{filename}.csv"

        try:
            if PANDAS_AVAILABLE:
                # 使用pandas保存
                df = pd.DataFrame(list(self.recent_buffer))

                # 選擇要保存的欄位
                if not include_details:
                    columns = [col for col in df.columns
                              if not col.startswith('detail_') and not col.startswith('meta_')]
                    df = df[columns]

                # 排序欄位
                if 'frame_id' in df.columns:
                    df = df.sort_values('frame_id')

                # 保存
                df.to_csv(filepath, index=False, encoding='utf-8-sig')

            else:
                # 使用標準庫保存
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    # 確定欄位
                    if include_details:
                        fieldnames = list(self.recent_buffer[0].keys())
                    else:
                        fieldnames = [f for f in self.recent_buffer[0].keys()
                                    if not f.startswith('detail_') and not f.startswith('meta_')]

                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()

                    # 寫入資料
                    for record in self.recent_buffer:
                        writer.writerow(record)

            logger.info(f"CSV檔案已保存: {filepath}")
            logger.info(f"記錄數: {len(self.recent_buffer)}（最近1000幀）")

            return str(filepath)

        except Exception as e:
            logger.error(f"CSV保存失敗: {e}")
            return ""
    
    # ==================== JSON保存方法 ====================
    
    def save_to_json(self, filename: Optional[str] = None,
                    include_statistics: bool = True,
                    pretty_print: bool = True) -> str:
        """
        保存統計資訊為JSON檔案

        Args:
            filename: 檔案名稱（不含副檔名），None則自動生成
            include_statistics: 是否包含統計資訊
            pretty_print: 是否格式化輸出（縮排）

        Returns:
            保存的檔案路徑
        """
        # 生成檔案名稱
        if filename is None:
            filename = f"reba_stats_{self.session_id}"

        filepath = self.output_dir / f"{filename}.json"

        try:
            # 構建JSON結構
            data = {
                'session_info': {
                    'session_id': self.session_id,
                    'start_time': self.session_start.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_frames': self.stats_accumulator.total_frames,
                    'recent_buffer_size': len(self.recent_buffer),
                    'output_directory': str(self.output_dir)
                },
                'recent_frames': list(self.recent_buffer)  # 最近1000幀
            }

            # 添加統計資訊
            if include_statistics:
                data['statistics'] = self.get_statistics()

            # 保存
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)

            logger.info(f"JSON檔案已保存: {filepath}")
            logger.info(f"總幀數: {self.stats_accumulator.total_frames}，recent_buffer: {len(self.recent_buffer)}幀")

            return str(filepath)

        except Exception as e:
            logger.error(f"JSON保存失敗: {e}")
            return ""
    
    # ==================== 統計分析方法 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取統計資訊（使用線上累積器，O(1)記憶體）

        Returns:
            統計資訊字典，包含：
            - 基本統計（總數、有效數）
            - REBA分數統計（平均、標準差、範圍）
            - 風險等級分佈
            - 角度統計（各關節）
            - 時間統計
        """
        try:
            return self.stats_accumulator.get_statistics()
        except Exception as e:
            logger.error(f"統計計算失敗: {e}")
            return {}
    
    # ==================== 報告生成方法 ====================
    
    def print_summary(self):
        """列印摘要資訊到控制台"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("REBA 分析摘要")
        print("="*60)
        
        if not stats:
            print("沒有統計資料")
            return
        
        # 基本資訊
        if 'basic' in stats:
            basic = stats['basic']
            print(f"\n📊 基本統計:")
            print(f"  總幀數: {basic.get('total_frames', 0)}")
            print(f"  有效幀數: {basic.get('valid_frames', 0)}")
            print(f"  成功率: {basic.get('success_rate', 0):.1f}%")
        
        # REBA分數統計
        if 'reba_score' in stats:
            reba = stats['reba_score']
            print(f"\n🎯 REBA分數統計:")
            print(f"  平均分數: {reba.get('mean', 0):.2f}")
            print(f"  標準差: {reba.get('std', 0):.2f}")
            print(f"  分數範圍: {reba.get('min', 0)} - {reba.get('max', 0)}")
            if 'median' in reba:
                print(f"  中位數: {reba.get('median', 0):.2f}")
        
        # 風險等級分佈
        if 'risk_distribution' in stats:
            print(f"\n⚠️  風險等級分佈:")
            
            risk_names = {
                'negligible': '可忽略',
                'low': '低風險',
                'medium': '中等風險',
                'high': '高風險',
                'very_high': '極高風險'
            }
            
            dist = stats['risk_distribution']
            counts = dist.get('counts', {})
            percentages = dist.get('percentages', {})
            
            for risk_level in ['negligible', 'low', 'medium', 'high', 'very_high']:
                if risk_level in counts:
                    count = counts[risk_level]
                    pct = percentages.get(risk_level, 0)
                    name = risk_names.get(risk_level, risk_level)
                    print(f"  {name}: {count}次 ({pct:.1f}%)")
        
        # 角度統計
        if 'angles' in stats and stats['angles']:
            print(f"\n📐 角度統計:")
            
            angle_names = {
                'neck_angle': '頸部',
                'trunk_angle': '軀幹',
                'upper_arm_angle': '上臂',
                'forearm_angle': '前臂',
                'wrist_angle': '手腕',
                'leg_angle': '腿部'
            }
            
            for angle_key, angle_data in stats['angles'].items():
                name = angle_names.get(angle_key, angle_key)
                mean = angle_data.get('mean', 0)
                std = angle_data.get('std', 0)
                print(f"  {name}: {mean:.1f}° (±{std:.1f}°)")
        
        # 時間統計
        if 'time' in stats:
            time_stats = stats['time']
            duration = time_stats.get('duration_seconds', 0)
            fps = time_stats.get('average_fps', 0)
            print(f"\n⏱️  時間統計:")
            print(f"  總時長: {duration:.2f}秒")
            print(f"  平均FPS: {fps:.2f}")
        
        print("="*60 + "\n")
    
    def generate_markdown_report(self, filename: Optional[str] = None) -> str:
        """
        生成Markdown格式的分析報告
        
        Args:
            filename: 檔案名稱（不含副檔名）
            
        Returns:
            保存的檔案路徑
        """
        if not self.data_buffer:
            logger.warning("沒有資料可生成報告")
            return ""
        
        # 生成檔案名稱
        if filename is None:
            filename = f"reba_report_{self.session_id}"
        
        filepath = self.output_dir / f"{filename}.md"
        
        try:
            stats = self.get_statistics()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # 標題
                f.write("# REBA 分析報告\n\n")
                f.write(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**會話ID**: {self.session_id}\n\n")
                f.write("---\n\n")
                
                # 基本統計
                if 'basic' in stats:
                    f.write("## 📊 基本統計\n\n")
                    basic = stats['basic']
                    f.write(f"- **總幀數**: {basic.get('total_frames', 0)}\n")
                    f.write(f"- **有效幀數**: {basic.get('valid_frames', 0)}\n")
                    f.write(f"- **無效幀數**: {basic.get('invalid_frames', 0)}\n")
                    f.write(f"- **成功率**: {basic.get('success_rate', 0):.1f}%\n\n")
                
                # REBA分數統計
                if 'reba_score' in stats:
                    f.write("## 🎯 REBA分數統計\n\n")
                    reba = stats['reba_score']
                    f.write(f"- **平均分數**: {reba.get('mean', 0):.2f}\n")
                    f.write(f"- **標準差**: {reba.get('std', 0):.2f}\n")
                    f.write(f"- **最小值**: {reba.get('min', 0)}\n")
                    f.write(f"- **最大值**: {reba.get('max', 0)}\n")
                    f.write(f"- **中位數**: {reba.get('median', 0):.2f}\n\n")
                
                # 風險等級分佈
                if 'risk_distribution' in stats:
                    f.write("## ⚠️ 風險等級分佈\n\n")
                    
                    risk_names = {
                        'negligible': '可忽略風險',
                        'low': '低風險',
                        'medium': '中等風險',
                        'high': '高風險',
                        'very_high': '極高風險'
                    }
                    
                    dist = stats['risk_distribution']
                    counts = dist.get('counts', {})
                    percentages = dist.get('percentages', {})
                    
                    f.write("| 風險等級 | 次數 | 百分比 |\n")
                    f.write("|---------|------|--------|\n")
                    
                    for risk_level in ['negligible', 'low', 'medium', 'high', 'very_high']:
                        if risk_level in counts:
                            count = counts[risk_level]
                            pct = percentages.get(risk_level, 0)
                            name = risk_names.get(risk_level, risk_level)
                            f.write(f"| {name} | {count} | {pct:.1f}% |\n")
                    
                    f.write("\n")
                
                # 角度統計
                if 'angles' in stats and stats['angles']:
                    f.write("## 📐 關節角度統計\n\n")
                    
                    angle_names = {
                        'neck_angle': '頸部',
                        'trunk_angle': '軀幹',
                        'upper_arm_angle': '上臂',
                        'forearm_angle': '前臂',
                        'wrist_angle': '手腕',
                        'leg_angle': '腿部'
                    }
                    
                    f.write("| 部位 | 平均值 | 標準差 | 最小值 | 最大值 |\n")
                    f.write("|------|--------|--------|--------|--------|\n")
                    
                    for angle_key, angle_data in stats['angles'].items():
                        name = angle_names.get(angle_key, angle_key)
                        mean = angle_data.get('mean', 0)
                        std = angle_data.get('std', 0)
                        min_val = angle_data.get('min', 0)
                        max_val = angle_data.get('max', 0)
                        f.write(f"| {name} | {mean:.1f}° | {std:.1f}° | {min_val:.1f}° | {max_val:.1f}° |\n")
                    
                    f.write("\n")
                
                # 時間統計
                if 'time' in stats:
                    f.write("## ⏱️ 時間統計\n\n")
                    time_stats = stats['time']
                    duration = time_stats.get('duration_seconds', 0)
                    fps = time_stats.get('average_fps', 0)
                    f.write(f"- **總時長**: {duration:.2f}秒\n")
                    f.write(f"- **平均FPS**: {fps:.2f}\n\n")
                
                # 建議
                f.write("## 💡 建議\n\n")
                
                # 根據風險分佈給出建議
                if 'risk_distribution' in stats:
                    counts = stats['risk_distribution'].get('counts', {})
                    total = sum(counts.values())
                    
                    high_risk_count = counts.get('high', 0) + counts.get('very_high', 0)
                    high_risk_pct = (high_risk_count / total * 100) if total > 0 else 0
                    
                    if high_risk_pct > 30:
                        f.write("⚠️ **警告**: 檢測到大量高風險動作（{:.1f}%）\n\n".format(high_risk_pct))
                        f.write("建議：\n")
                        f.write("1. 立即檢討工作流程和姿勢\n")
                        f.write("2. 提供人因工程培訓\n")
                        f.write("3. 考慮使用輔助設備\n")
                        f.write("4. 安排定期休息時間\n\n")
                    elif high_risk_pct > 10:
                        f.write("⚠️ **注意**: 檢測到部分高風險動作（{:.1f}%）\n\n".format(high_risk_pct))
                        f.write("建議：\n")
                        f.write("1. 識別並改善高風險動作\n")
                        f.write("2. 加強人因工程意識\n")
                        f.write("3. 定期進行姿勢評估\n\n")
                    else:
                        f.write("✅ **良好**: 大部分動作在可接受範圍內\n\n")
                        f.write("建議：\n")
                        f.write("1. 持續保持良好工作姿勢\n")
                        f.write("2. 定期進行自我檢查\n")
                        f.write("3. 注意避免疲勞累積\n\n")
                
                f.write("---\n\n")
                f.write("*本報告由REBA分析系統自動生成*\n")
            
            logger.info(f"Markdown報告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"報告生成失敗: {e}")
            return ""
    
    # ==================== 資料管理方法 ====================

    def clear_buffer(self):
        """清空recent_buffer和統計（不影響已寫入CSV的資料）"""
        self.recent_buffer.clear()
        self.stats_accumulator = StatisticsAccumulator()
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        logger.info("recent_buffer和統計已重置")

    def get_buffer_size(self) -> int:
        """
        獲取recent_buffer大小

        Returns:
            recent_buffer中的記錄筆數（最多1000）
        """
        return len(self.recent_buffer)

    def get_total_frames(self) -> int:
        """
        獲取總處理幀數

        Returns:
            累計處理的總幀數
        """
        return self.stats_accumulator.total_frames

    def get_frame_data(self, frame_id: int) -> Optional[Dict]:
        """
        獲取特定幀的資料（僅搜尋recent_buffer中的最近1000幀）

        Args:
            frame_id: 幀編號

        Returns:
            該幀的資料字典，若不存在則返回None
        """
        for record in self.recent_buffer:
            if record.get('frame_id') == frame_id:
                return record
        return None

    def get_data_by_time_range(self, start_time: float, end_time: float) -> List[Dict]:
        """
        獲取時間範圍內的資料（僅搜尋recent_buffer中的最近1000幀）

        Args:
            start_time: 起始時間戳
            end_time: 結束時間戳

        Returns:
            符合條件的資料列表
        """
        return [record for record in self.recent_buffer
                if start_time <= record.get('timestamp', 0) <= end_time]

    def filter_by_risk_level(self, risk_level: str) -> List[Dict]:
        """
        按風險等級篩選資料（僅搜尋recent_buffer中的最近1000幀）

        Args:
            risk_level: 風險等級

        Returns:
            符合條件的資料列表
        """
        return [record for record in self.recent_buffer
                if record.get('risk_level') == risk_level]

    def get_high_risk_frames(self, threshold: int = 8) -> List[Dict]:
        """
        獲取高風險幀（僅搜尋recent_buffer中的最近1000幀）

        Args:
            threshold: REBA分數閾值，大於等於此值視為高風險

        Returns:
            高風險幀列表
        """
        return [record for record in self.recent_buffer
                if record.get('reba_score', 0) >= threshold]
    
    # ==================== 資料匯出方法 ====================
    
    def export_summary_only(self, filename: Optional[str] = None) -> str:
        """
        僅匯出統計摘要（不含逐幀資料）
        
        Args:
            filename: 檔案名稱
            
        Returns:
            保存的檔案路徑
        """
        if filename is None:
            filename = f"reba_summary_{self.session_id}"
        
        filepath = self.output_dir / f"{filename}.json"
        
        try:
            summary = {
                'session_info': {
                    'session_id': self.session_id,
                    'start_time': self.session_start.isoformat(),
                    'end_time': datetime.now().isoformat()
                },
                'statistics': self.get_statistics()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"摘要已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"摘要匯出失敗: {e}")
            return ""
    
    def save_all_formats(self, base_filename: Optional[str] = None) -> Dict[str, str]:
        """
        保存所有格式（CSV、JSON、Markdown報告）
        
        Args:
            base_filename: 基礎檔案名稱
            
        Returns:
            各格式檔案路徑字典
        """
        if base_filename is None:
            base_filename = f"reba_analysis_{self.session_id}"
        
        results = {}
        
        # 保存CSV
        csv_path = self.save_to_csv(base_filename)
        if csv_path:
            results['csv'] = csv_path
        
        # 保存JSON
        json_path = self.save_to_json(base_filename)
        if json_path:
            results['json'] = json_path
        
        # 生成Markdown報告
        md_path = self.generate_markdown_report(base_filename)
        if md_path:
            results['markdown'] = md_path
        
        logger.info(f"已保存 {len(results)} 種格式")
        return results
    
    # ==================== 資料驗證方法 ====================
    
    def validate_data(self) -> Dict[str, Any]:
        """
        驗證recent_buffer資料品質

        Returns:
            驗證結果字典
        """
        if not self.recent_buffer:
            return {'valid': False, 'message': 'recent_buffer為空'}

        issues = []
        warnings = []

        # 檢查必要欄位
        required_fields = ['frame_id', 'timestamp', 'reba_score', 'risk_level']
        for i, record in enumerate(self.recent_buffer):
            for field in required_fields:
                if field not in record or record[field] is None:
                    issues.append(f"記錄{i}: 缺少欄位 {field}")

        # 檢查REBA分數範圍
        for i, record in enumerate(self.recent_buffer):
            score = record.get('reba_score')
            if score is not None and (score < 1 or score > 15):
                warnings.append(f"記錄{i}: REBA分數 {score} 超出正常範圍(1-15)")

        # 檢查角度範圍
        angle_ranges = {
            'neck_angle': (0, 90),
            'trunk_angle': (0, 90),
            'upper_arm_angle': (0, 180),
            'forearm_angle': (0, 180),
            'wrist_angle': (0, 90),
            'leg_angle': (0, 180)
        }

        for i, record in enumerate(self.recent_buffer):
            for angle_name, (min_val, max_val) in angle_ranges.items():
                angle = record.get(angle_name)
                if angle is not None and (angle < 0 or angle > max_val):
                    warnings.append(f"記錄{i}: {angle_name} {angle:.1f}° 可能異常")

        # 檢查時間順序
        timestamps = [r.get('timestamp', 0) for r in self.recent_buffer]
        if timestamps != sorted(timestamps):
            warnings.append("時間戳順序不連續")

        # 生成驗證結果
        validation = {
            'valid': len(issues) == 0,
            'total_records': len(self.recent_buffer),
            'total_frames_processed': self.stats_accumulator.total_frames,
            'issues': issues,
            'warnings': warnings,
            'issue_count': len(issues),
            'warning_count': len(warnings)
        }

        if validation['valid']:
            logger.info("資料驗證通過")
        else:
            logger.warning(f"資料驗證失敗: {len(issues)} 個問題")

        return validation


# ==================== 輔助函數 ====================

def create_sample_data(num_frames: int = 100) -> List[Dict]:
    """
    創建樣本資料（用於測試）
    
    Args:
        num_frames: 幀數
        
    Returns:
        樣本資料列表
    """
    import random
    
    sample_data = []
    start_time = datetime.now().timestamp()
    
    for i in range(num_frames):
        angles = {
            'neck': random.uniform(10, 40),
            'trunk': random.uniform(15, 60),
            'upper_arm': random.uniform(100, 160),
            'forearm': random.uniform(60, 120),
            'wrist': random.uniform(0, 30),
            'leg': random.uniform(150, 180)
        }
        
        # 簡單的REBA計算（僅用於示例）
        reba_score = random.randint(1, 12)
        
        if reba_score <= 3:
            risk_level = 'low'
        elif reba_score <= 7:
            risk_level = 'medium'
        elif reba_score <= 10:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        record = {
            'frame_id': i,
            'timestamp': start_time + i * 0.033,  # 約30fps
            'neck_angle': angles['neck'],
            'trunk_angle': angles['trunk'],
            'upper_arm_angle': angles['upper_arm'],
            'forearm_angle': angles['forearm'],
            'wrist_angle': angles['wrist'],
            'leg_angle': angles['leg'],
            'reba_score': reba_score,
            'risk_level': risk_level
        }
        
        sample_data.append(record)
    
    return sample_data


# ==================== 測試代碼 ====================

if __name__ == "__main__":
    print("="*60)
    print("資料記錄器測試")
    print("="*60)
    
    # 創建記錄器
    logger_test = DataLogger('./test_results')
    print(f"\n✓ 記錄器已創建，輸出目錄: {logger_test.output_dir}")
    
    # 生成測試資料
    print("\n📝 生成測試資料...")
    test_data = create_sample_data(200)
    logger_test.add_batch_data(test_data)
    print(f"✓ 已添加 {len(test_data)} 筆資料")
    
    # 列印摘要
    print("\n" + "-"*60)
    logger_test.print_summary()
    
    # 保存所有格式
    print("-"*60)
    print("\n💾 保存資料...")
    saved_files = logger_test.save_all_formats("test_analysis")
    
    for format_type, filepath in saved_files.items():
        print(f"✓ {format_type.upper()}: {filepath}")
    
    # 資料驗證
    print("\n🔍 驗證資料...")
    validation = logger_test.validate_data()
    if validation['valid']:
        print("✓ 資料驗證通過")
    else:
        print(f"⚠ 發現 {validation['issue_count']} 個問題")
        print(f"⚠ 發現 {validation['warning_count']} 個警告")
    
    # 高風險幀分析
    print("\n⚠️ 高風險幀分析...")
    high_risk_frames = logger_test.get_high_risk_frames(threshold=8)
    print(f"高風險幀數: {len(high_risk_frames)} / {logger_test.get_buffer_size()}")
    print(f"高風險比例: {len(high_risk_frames)/logger_test.get_buffer_size()*100:.1f}%")
    
    print("\n" + "="*60)
    print("測試完成！")
    print("="*60)