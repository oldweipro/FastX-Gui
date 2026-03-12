#!/usr/bin/env python3
"""
DEM Fault Analyzer - Core Business Logic
基于 AUTOSAR CP 和 ETAS DEM 的 DTC 故障状态分析工具
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class BitInfo:
    """状态位信息数据类"""
    bit: int
    name: str
    abbr: str
    intro: str
    desc_true: str
    desc_false: str
    detailed_desc: str
    set_conditions: List[str]
    clear_conditions: List[str]
    mask: int


class DTCStatusConfig:
    """DTC 状态配置表"""
    
    BIT_CONFIGS = [
        BitInfo(
            bit=0,
            name="testFailed",
            abbr="TF",
            intro="请求时刻测试结果为失败",
            desc_true="当前结果为故障状态",
            desc_false="当前结果不为故障状态",
            detailed_desc="通常来说，ECU 内部以循环的方式不断地针对预先定义好的错误路径进行测试。如果在最近的一次测试中，在某个错误路径中发现了故障，则相应 DTC 的这一个状态位就要被置 1，表征出错。",
            set_conditions=["周期性测试发现故障条件满足时立即置 1"],
            clear_conditions=["下一个周期测试故障条件未满足时立即恢复为 0", "Dem_ClearDTC 函数清除故障信息"],
            mask=0x01
        ),
        BitInfo(
            bit=1,
            name="testFailedThisOperationCycle",
            abbr="TFTOC",
            intro="在当前点火循环至少失败 1 次",
            desc_true="当前操作循环中至少检测到一次故障",
            desc_false="当前操作循环中没有检测到一次故障",
            detailed_desc="这个 bit 用于标识某个 DTC 在当前的 operation cycle 中是否出现过 testFailed 置 1 的情况，即是否出现过错误。",
            set_conditions=["一旦 testFailed 出现过置 1 的情况，立即置 1"],
            clear_conditions=["该运行循环结束或新的运行循环开始", "Dem_ClearDTC 函数清除故障信息"],
            mask=0x02
        ),
        BitInfo(
            bit=2,
            name="pendingDTC",
            abbr="PDTC",
            intro="在当前或者上一个点火循环测试结果不为失败",
            desc_true="当前操作循环或者上一个完成的操作循环期间至少检测到 1 次故障",
            desc_false="当前操作循环或者上一个完成的操作循环期间没有检测到 1 次故障",
            detailed_desc="pendingDTC 位其实是位于 testFailed 和 confirmedDTC 之间的一个状态。pendingDTC = 1 的时候，DTC 就要被存储下来了。",
            set_conditions=["故障在当前运行循环或者上一个运行循环出现过 testFailed 被置位为 1"],
            clear_conditions=["当前运行 TestFailedThisOperationCycle 未置为 1，且运行循环结束或者下一个运行循环开始", "Dem_ClearDTC 函数清除故障信息"],
            mask=0x04
        ),
        BitInfo(
            bit=3,
            name="confirmedDTC",
            abbr="CDTC",
            intro="请求时刻 DTC 被确认，一般确认是在一个点火周期内发生错误 1 次",
            desc_true="表示存在历史故障 - 故障已存储到非易失性内存",
            desc_false="表示不存在历史故障",
            detailed_desc="当 confirmedDTC = 1 时，则说明某个 DTC 已经被存储到 ECU 的 non-volatile memory 中，说明这个 DTC 曾经满足了被 confirmed 的条件。",
            set_conditions=["故障已经确认，故障数据存储至 EEPROM 或者 FEE", "满足确认条件时置 1"],
            clear_conditions=["故障老化", "故障替代", "Dem_ClearDTC 函数清除故障信息"],
            mask=0x08
        ),
        BitInfo(
            bit=4,
            name="testNotCompleteSinceLastClear",
            abbr="TNCSLC",
            intro="自上次清除 DTC 之后测试结果已完成，即测试结果为 PASS 或者 FAIL",
            desc_true="表示从上次进行清除诊断信息后，DTC 检测尚未完成",
            desc_false="自从清理 DTC 之后已经完成过针对该 DTC 的测试",
            detailed_desc="这个 bit 用于标识，自从上次调用了清理 DTC 的服务之后，是否成功地执行了对某个 DTC 的测试。",
            set_conditions=["自从上次调用 Dem_ClearDTC 函数清除故障信息后，尚未成功执行对故障进行检测"],
            clear_conditions=["成功执行对故障进行检测后自动清除"],
            mask=0x10
        ),
        BitInfo(
            bit=5,
            name="testFailedSinceLastClear",
            abbr="TFSLC",
            intro="自上次清除 DTC 后测试结果都不是 FAIL",
            desc_true="自从清理 DTC 之后该 DTC 出过至少一次错",
            desc_false="自从清理 DTC 之后该 DTC 没有出过错",
            detailed_desc="这个位与 bit 1:testFailedThisOperationCycle 有些类似，标识的是在上次执行过清理 DTC 之后某个 DTC 是否出过错。",
            set_conditions=["自从上次调用 Dem_ClearDTC 函数清除故障信息后，testFailed 出现过置位为 1"],
            clear_conditions=["Dem_ClearDTC 函数清除故障信息"],
            mask=0x20
        ),
        BitInfo(
            bit=6,
            name="testNotCompletedThisOperationCycle",
            abbr="TNCTOC",
            intro="在当前点火周期内测试结果已完成，即为 PASS 或 FAIL 状态",
            desc_true="在当前 operation cycle 中还没在完成过针对该 DTC 的测试",
            desc_false="在当前 operation cycle 中已经完成过针对该 DTC 的测试",
            detailed_desc="这个位与 bit 4: testNotCompletedSinceLastClear 类似，标识在当前 operation cycle 中是否成功地执行了对某个 DTC 的测试。",
            set_conditions=["当前循环还未对该故障进行检测测试"],
            clear_conditions=["当前循环已对该故障进行检测测试后自动清除"],
            mask=0x40
        ),
        BitInfo(
            bit=7,
            name="warningIndicatorRequested",
            abbr="WIR",
            intro="ECU 没有得到点亮警示灯请求",
            desc_true="表示该 bit 关联的特定 DTC 警告指示灯亮",
            desc_false="ECU 不请求激活警告指示",
            detailed_desc="某些比较严重的 DTC 会与用户可见的警告指示相关联，比如仪表上的报警灯，或者是文字，或者是声音。",
            set_conditions=["ECU 请求激活警告指示（如仪表 MIL 灯）", "严重故障发生时置 1"],
            clear_conditions=["ECU 不请求激活警告指示", "故障消失或降低严重程度后清除"],
            mask=0x80
        )
    ]
    
    @classmethod
    def get_bit_info(cls, bit: int) -> BitInfo | None:
        """获取指定 bit 的信息"""
        for config in cls.BIT_CONFIGS:
            if config.bit == bit:
                return config
        return None
    
    @classmethod
    def get_all_bits(cls) -> List[BitInfo]:
        """获取所有 bit 信息"""
        return cls.BIT_CONFIGS


class ISO14229DTCSTATUS:
    """DTC 状态位解析类"""
    
    @staticmethod
    def parse_status_code(status_hex: str) -> Dict:
        """解析 DTC 状态码"""
        status_int = int(status_hex.replace('0x', '').replace('0X', ''), 16)
        
        bits = {}
        for bit in range(8):
            bits[bit] = (status_int & (1 << bit)) != 0
        
        return {
            'hex': status_hex,
            'decimal': status_int,
            'binary': bin(status_int)[2:].zfill(8),
            'bits': bits
        }
    
    @staticmethod
    def analyze_status(status_hex: str) -> Dict:
        """分析 DTC 状态并返回详细结果"""
        result = ISO14229DTCSTATUS.parse_status_code(status_hex)
        
        analysis = {
            'basic_info': result,
            'set_bits': [],
            'cleared_bits': []
        }
        
        for bit in range(8):
            is_set = result['bits'][bit]
            bit_info = DTCStatusConfig.get_bit_info(bit)
            if bit_info:
                bit_analysis = {
                    'bit': bit,
                    'name': bit_info.name,
                    'abbr': bit_info.abbr,
                    'is_set': is_set,
                    'description': bit_info.desc_true if is_set else bit_info.desc_false,
                    'intro': bit_info.intro,
                    'detailed_desc': bit_info.detailed_desc,
                    'set_conditions': bit_info.set_conditions if is_set else [],
                    'clear_conditions': bit_info.clear_conditions if not is_set else [],
                    # 添加缺失的字段以匹配 BitInfo 数据类
                    'desc_true': bit_info.desc_true,
                    'desc_false': bit_info.desc_false,
                }
                
                if is_set:
                    analysis['set_bits'].append(bit_analysis)
                else:
                    analysis['cleared_bits'].append(bit_analysis)
        
        return analysis


class DEMFaultAnalyzer:
    """DEM 故障分析器业务逻辑类"""
    def __init__(self):
        """初始化业务逻辑"""
    def analyze_dtc_status(self, status_hex: str) -> Dict:
        """分析 DTC 状态码"""
        try:
            # 处理输入格式
            if not status_hex.startswith(('0x', '0X')):
                status_hex = '0x' + status_hex
            
            # 验证并解析
            status_int = int(status_hex, 16)
            if status_int < 0 or status_int > 255:
                return {
                    'success': False,
                    'error': '无效的 DTC 状态码！状态码必须是 1 字节（0x00-0xFF）。'
                }
            
            # 调用分析函数
            analysis = ISO14229DTCSTATUS.analyze_status(status_hex)
            analysis['success'] = True
            return analysis
            
        except ValueError:
            return {
                'success': False,
                'error': '无效的十六进制格式！请输入有效的 DTC 状态码。'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'解析过程中发生错误：{str(e)}'
            }
